[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "DEP3_BLOCKED: this initializer currently requires Windows PowerShell"
}

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$TargetPath = Join-Path $RepositoryRoot ".env.compose"

if (Test-Path -LiteralPath $TargetPath) {
    throw "DEP3_BLOCKED: Compose env file already exists; refusing overwrite"
}

function New-HexSecret {
    $Bytes = [byte[]]::new(32)
    $Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $Generator.GetBytes($Bytes)
    }
    finally {
        $Generator.Dispose()
    }
    return (($Bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

$SecurePin = Read-Host "Acceptance admin PIN (4 digits)" -AsSecureString
$PinPointer = [IntPtr]::Zero
$Pin = $null
try {
    $PinPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePin)
    $Pin = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($PinPointer)
    if ($Pin -notmatch '^\d{4}$') {
        throw "DEP3_BLOCKED: admin PIN must contain exactly 4 digits"
    }
    $Hasher = [Security.Cryptography.SHA256]::Create()
    try {
        $PinHashBytes = $Hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($Pin))
        $PinHash = (($PinHashBytes | ForEach-Object { $_.ToString("x2") }) -join "")
    }
    finally {
        $Hasher.Dispose()
    }
}
finally {
    if ($PinPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($PinPointer)
    }
    $Pin = $null
    $SecurePin = $null
}

$Lines = @(
    "# Generated locally by deployment/postgres/initialize_compose_env.ps1",
    "# Do not commit or share this file.",
    "COMPOSE_PROJECT_NAME=cheongnyeon-alimi-acceptance",
    "ACCEPTANCE_IMAGE_TAG=local",
    "",
    "POSTGRES_DB=cheongnyeon_alimi_acceptance",
    "POSTGRES_USER=cheongnyeon_acceptance",
    "POSTGRES_PASSWORD=$(New-HexSecret)",
    "",
    "TEST_POSTGRES_DB=cheongnyeon_alimi_acceptance_test",
    "TEST_POSTGRES_USER=cheongnyeon_acceptance_test",
    "TEST_POSTGRES_PASSWORD=$(New-HexSecret)",
    "",
    "BACKEND_SECRET_KEY=$(New-HexSecret)",
    "ADMIN_PIN_HASH=$PinHash",
    "ADMIN_TOKEN_SECRET=$(New-HexSecret)",
    "",
    "BACKEND_HOST_PORT=8000",
    "FRONTEND_HOST_PORT=3000",
    "POSTGRES_DEV_HOST_PORT=55432",
    "VITE_API_BASE_URL=http://127.0.0.1:8000",
    "VITE_USE_MOCK=false",
    'CORS_ORIGINS=["http://127.0.0.1:3000","http://localhost:3000"]',
    "",
    "# Optional live-collection credentials; add only to this ignored file.",
    "YOUTHCENTER_API_KEY=",
    "BOKJIRO_API_KEY=",
    "",
    "# Central queue defaults. Keep one scheduler instance.",
    "COLLECTION_WORKER_CONCURRENCY=2",
    "COLLECTION_TASK_MAX_RETRIES=5",
    "COLLECTION_TASK_RETRY_BACKOFF_MAX_SECONDS=300",
    "COLLECTION_TASK_RATE_LIMIT=6/m",
    "COLLECTION_SCHEDULE_ENABLED=false",
    "COLLECTION_SCHEDULE_SOURCE_ID=youthcenter-api",
    "COLLECTION_SCHEDULE_REQUESTED_COUNT=100",
    "COLLECTION_SCHEDULE_CRON_HOUR=3",
    "COLLECTION_SCHEDULE_CRON_MINUTE=0",
    "",
    "# restore.ps1 overrides these only after verifying the external snapshot.",
    "ACCEPTANCE_SNAPSHOT_DIR=C:/DEP3_INJECTS_VERIFIED_SNAPSHOT",
    "ACCEPTANCE_DUMP_FILENAME=acceptance-post-admission.dump",
    "ACCEPTANCE_DUMP_SHA256=DEP3_INJECTS_VERIFIED_SHA256",
    "ACCEPTANCE_ALEMBIC_REVISION=20260810_0006"
)

$Parent = Split-Path -Parent $TargetPath
if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
    throw "DEP3_BLOCKED: output parent directory does not exist"
}

$TemporaryPath = Join-Path $Parent (".env.compose." + [Guid]::NewGuid().ToString("N") + ".tmp")
try {
    [IO.File]::WriteAllText(
        $TemporaryPath,
        ($Lines -join "`r`n") + "`r`n",
        [Text.UTF8Encoding]::new($false)
    )

    $CurrentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $Acl = [Security.AccessControl.FileSecurity]::new()
    $Acl.SetAccessRuleProtection($true, $false)
    $Acl.SetOwner([Security.Principal.NTAccount]::new($CurrentIdentity))
    $Rule = [Security.AccessControl.FileSystemAccessRule]::new(
        $CurrentIdentity,
        [Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.AccessControlType]::Allow
    )
    [void]$Acl.AddAccessRule($Rule)
    [IO.File]::SetAccessControl($TemporaryPath, $Acl)

    Move-Item -LiteralPath $TemporaryPath -Destination $TargetPath
}
finally {
    if (Test-Path -LiteralPath $TemporaryPath) {
        Remove-Item -LiteralPath $TemporaryPath -Force
    }
}

$GitMetadataPath = Join-Path $RepositoryRoot ".git"
if (Test-Path -LiteralPath $GitMetadataPath) {
    git -C $RepositoryRoot check-ignore --quiet -- .env.compose
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -LiteralPath $TargetPath -Force
        throw "DEP3_BLOCKED: generated Compose env file is not ignored by Git"
    }
}
else {
    $GitIgnorePath = Join-Path $RepositoryRoot ".gitignore"
    $GitIgnoreRules = if (Test-Path -LiteralPath $GitIgnorePath -PathType Leaf) {
        @(Get-Content -LiteralPath $GitIgnorePath -Encoding UTF8)
    }
    else {
        @()
    }
    if ($GitIgnoreRules -notcontains ".env.*") {
        Remove-Item -LiteralPath $TargetPath -Force
        throw "DEP3_BLOCKED: ZIP .gitignore does not protect the Compose env file"
    }
}

Write-Output "DEP3_COMPOSE_ENV_CREATED: local secrets generated; PIN plaintext was not stored"
