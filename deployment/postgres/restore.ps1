[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SnapshotDir,

    [string]$EnvFile = ".env.compose",
    [string]$ComposeFile = "compose.yaml",
    [string]$PythonExe,
    [switch]$SkipBuild,
    [switch]$StartServices
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Resolve-RepositoryPath([string]$Value) {
    $Candidate = if ([System.IO.Path]::IsPathRooted($Value)) {
        $Value
    }
    else {
        Join-Path $RepositoryRoot $Value
    }
    return (Resolve-Path -LiteralPath $Candidate).Path
}

$ResolvedSnapshotDir = (Resolve-Path -LiteralPath $SnapshotDir).Path
$ResolvedEnvFile = Resolve-RepositoryPath $EnvFile
$ResolvedComposeFile = Resolve-RepositoryPath $ComposeFile
$Verifier = Join-Path $PSScriptRoot "verify_snapshot.py"

$RepositoryPrefix = $RepositoryRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
if (
    $ResolvedSnapshotDir.Equals($RepositoryRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $ResolvedSnapshotDir.StartsWith($RepositoryPrefix, [System.StringComparison]::OrdinalIgnoreCase)
) {
    throw "DEP2_BLOCKED: snapshot directory must be outside the workspace"
}

if (-not $PythonExe) {
    $WorkspacePython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $WorkspacePython) {
        $PythonExe = $WorkspacePython
    }
    else {
        $PythonExe = (Get-Command python.exe -ErrorAction Stop).Source
    }
}

$RequiredEnvKeys = @(
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "TEST_POSTGRES_DB",
    "TEST_POSTGRES_USER",
    "TEST_POSTGRES_PASSWORD",
    "BACKEND_SECRET_KEY",
    "ADMIN_PIN_HASH",
    "ADMIN_TOKEN_SECRET",
    "VITE_API_BASE_URL",
    "CORS_ORIGINS"
)
$EnvValues = @{}
foreach ($Line in Get-Content -LiteralPath $ResolvedEnvFile) {
    if ($Line -match '^\s*#' -or $Line -notmatch '=') {
        continue
    }
    $Key, $Value = $Line -split '=', 2
    $EnvValues[$Key.Trim()] = $Value.Trim()
}
foreach ($Key in $RequiredEnvKeys) {
    if (-not $EnvValues.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace($EnvValues[$Key])) {
        throw "DEP2_BLOCKED: $Key is missing from the Compose env file"
    }
    if ($EnvValues[$Key] -match 'CHANGE_ME') {
        throw "DEP2_BLOCKED: $Key still contains a CHANGE_ME placeholder"
    }
}
foreach ($Key in @("POSTGRES_DB", "POSTGRES_USER", "TEST_POSTGRES_DB", "TEST_POSTGRES_USER")) {
    if ($EnvValues[$Key] -notmatch '^[A-Za-z][A-Za-z0-9_]*$') {
        throw "DEP2_BLOCKED: $Key must contain only a leading letter and alphanumeric or underscore characters"
    }
}
foreach ($Key in @("POSTGRES_PASSWORD", "TEST_POSTGRES_PASSWORD")) {
    if ($EnvValues[$Key] -notmatch '^[A-Za-z0-9_-]{32,}$') {
        throw "DEP2_BLOCKED: $Key must be at least 32 URL-safe characters"
    }
}
if ($EnvValues["BACKEND_SECRET_KEY"].Length -lt 32) {
    throw "DEP2_BLOCKED: BACKEND_SECRET_KEY must be at least 32 characters"
}
if ($EnvValues["ADMIN_TOKEN_SECRET"].Length -lt 32) {
    throw "DEP2_BLOCKED: ADMIN_TOKEN_SECRET must be at least 32 characters"
}
if ($EnvValues["ADMIN_PIN_HASH"] -notmatch '^[0-9a-fA-F]{64}$') {
    throw "DEP2_BLOCKED: ADMIN_PIN_HASH must be a SHA-256 hexadecimal digest"
}
if (-not $EnvValues["TEST_POSTGRES_DB"].EndsWith("_test", [System.StringComparison]::Ordinal)) {
    throw "DEP2_BLOCKED: TEST_POSTGRES_DB must end with _test"
}
if ($EnvValues["POSTGRES_PASSWORD"] -eq $EnvValues["TEST_POSTGRES_PASSWORD"]) {
    throw "DEP2_BLOCKED: service and test database passwords must differ"
}

$VerificationOutput = & $PythonExe $Verifier `
    --snapshot-dir $ResolvedSnapshotDir `
    --repository-root $RepositoryRoot
if ($LASTEXITCODE -ne 0) {
    throw "DEP2_BLOCKED: snapshot verification failed"
}
$Verification = $VerificationOutput | Out-String | ConvertFrom-Json

$Injected = @{
    ACCEPTANCE_SNAPSHOT_DIR = $ResolvedSnapshotDir.Replace('\', '/')
    ACCEPTANCE_DUMP_FILENAME = [string]$Verification.dump_filename
    ACCEPTANCE_DUMP_SHA256 = [string]$Verification.dump_sha256
}
$Previous = @{}
foreach ($Name in $Injected.Keys) {
    $Previous[$Name] = [Environment]::GetEnvironmentVariable($Name, "Process")
    [Environment]::SetEnvironmentVariable($Name, $Injected[$Name], "Process")
}

$ComposeArgs = @(
    "compose",
    "--env-file", $ResolvedEnvFile,
    "--file", $ResolvedComposeFile
)

try {
    & docker @ComposeArgs config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "DEP2_BLOCKED: docker compose config validation failed"
    }

    if (-not $SkipBuild) {
        & docker @ComposeArgs build backend frontend
        if ($LASTEXITCODE -ne 0) {
            throw "DEP2_BLOCKED: application image build failed"
        }
    }

    & docker @ComposeArgs up --detach --wait database
    if ($LASTEXITCODE -ne 0) {
        throw "DEP2_BLOCKED: database did not become healthy"
    }

    & docker @ComposeArgs --profile restore run --rm restore
    if ($LASTEXITCODE -ne 0) {
        throw "DEP2_BLOCKED: one-shot restore failed; the existing volume was preserved"
    }

    & docker @ComposeArgs run --rm migrate
    if ($LASTEXITCODE -ne 0) {
        throw "DEP2_BLOCKED: migration failed; the existing volume was preserved"
    }

    if ($StartServices) {
        & docker @ComposeArgs up --detach --wait backend frontend
        if ($LASTEXITCODE -ne 0) {
            throw "DEP2_BLOCKED: application services did not become healthy"
        }
    }

    [pscustomobject]@{
        status = "DEP2_RESTORE_PASS"
        snapshot_version = $Verification.snapshot_version
        dump_sha256 = $Verification.dump_sha256
        policy_count = $Verification.policy_count
        collection_run_count = $Verification.collection_run_count
        services_started = [bool]$StartServices
    } | ConvertTo-Json
}
finally {
    foreach ($Name in $Injected.Keys) {
        [Environment]::SetEnvironmentVariable($Name, $Previous[$Name], "Process")
    }
}
