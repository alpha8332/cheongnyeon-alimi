[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SnapshotDir,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [string]$PythonExe,
    [string]$SevenZipExe
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ResolvedSnapshotDir = (Resolve-Path -LiteralPath $SnapshotDir).Path
$Verifier = Join-Path $PSScriptRoot "verify_snapshot.py"

function Test-IsWithinRepository([string]$CandidatePath) {
    $RepositoryPrefix = $RepositoryRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    return (
        $CandidatePath.Equals($RepositoryRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $CandidatePath.StartsWith($RepositoryPrefix, [StringComparison]::OrdinalIgnoreCase)
    )
}

$OutputFullPath = [IO.Path]::GetFullPath($OutputDir)
if (Test-IsWithinRepository $OutputFullPath) {
    throw "DEP5_BLOCKED: transfer package output must stay outside the workspace"
}
if (-not (Test-Path -LiteralPath $OutputFullPath)) {
    [void](New-Item -ItemType Directory -Path $OutputFullPath)
}
$ResolvedOutputDir = (Resolve-Path -LiteralPath $OutputFullPath).Path

$Dirty = @(git -C $RepositoryRoot status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0) {
    throw "DEP5_BLOCKED: Git worktree status could not be read"
}
if ($Dirty.Count -ne 0) {
    throw "DEP5_BLOCKED: commit the handoff contract before creating a receipt"
}

$GitSha = (git -C $RepositoryRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $GitSha -notmatch '^[0-9a-f]{40}$') {
    throw "DEP5_BLOCKED: current Git SHA could not be resolved"
}
$GitBranch = (git -C $RepositoryRoot branch --show-current).Trim()

if (-not $PythonExe) {
    $WorkspacePython = Join-Path $RepositoryRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $WorkspacePython) {
        $PythonExe = $WorkspacePython
    }
    else {
        $PythonExe = (Get-Command python.exe -ErrorAction Stop).Source
    }
}

if (-not $SevenZipExe) {
    $SevenZipCommand = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($SevenZipCommand) {
        $SevenZipExe = $SevenZipCommand.Source
    }
    else {
        $DefaultSevenZip = Join-Path $env:ProgramFiles "7-Zip\7z.exe"
        $PortableSevenZip = Join-Path $env:LOCALAPPDATA "cheongnyeon-alimi\tools\7zip-portable\7zr.exe"
        if (Test-Path -LiteralPath $DefaultSevenZip -PathType Leaf) {
            $SevenZipExe = $DefaultSevenZip
        }
        elseif (Test-Path -LiteralPath $PortableSevenZip -PathType Leaf) {
            $SevenZipExe = $PortableSevenZip
        }
        else {
            throw "DEP5_BLOCKED: 7-Zip console is required to create the AES-256 transfer package"
        }
    }
}
$SevenZipExe = (Resolve-Path -LiteralPath $SevenZipExe).Path

$VerificationOutput = & $PythonExe $Verifier `
    --snapshot-dir $ResolvedSnapshotDir `
    --repository-root $RepositoryRoot
if ($LASTEXITCODE -ne 0) {
    throw "DEP5_BLOCKED: snapshot verification failed"
}
$Verification = $VerificationOutput | Out-String | ConvertFrom-Json
if ($Verification.current_git_sha -ne $GitSha) {
    throw "DEP5_BLOCKED: verifier Git SHA differs from the handoff checkout"
}
if ($Verification.snapshot_version -notmatch '^[A-Za-z0-9._-]+$') {
    throw "DEP5_BLOCKED: snapshot version is unsafe for a package filename"
}

$ShortGitSha = $GitSha.Substring(0, 7)
$PackageBaseName = "cheongnyeon-alimi-$($Verification.snapshot_version)-$ShortGitSha"
$ArchivePath = Join-Path $ResolvedOutputDir "$PackageBaseName.7z"
$ReceiptPath = Join-Path $ResolvedOutputDir "$PackageBaseName.receipt.json"
$PartialArchivePath = Join-Path $ResolvedOutputDir ".$PackageBaseName.$([Guid]::NewGuid().ToString('N')).partial"

foreach ($Target in @($ArchivePath, $ReceiptPath)) {
    if (Test-Path -LiteralPath $Target) {
        throw "DEP5_BLOCKED: refusing to overwrite an existing transfer artifact"
    }
}

$ManifestFilename = "acceptance-snapshot.manifest.json"
$DumpFilename = [string]$Verification.dump_filename
foreach ($Filename in @($DumpFilename, $ManifestFilename)) {
    if ($Filename -match '[/\\]' -or -not (Test-Path -LiteralPath (Join-Path $ResolvedSnapshotDir $Filename) -PathType Leaf)) {
        throw "DEP5_BLOCKED: verified snapshot member is missing or not a basename"
    }
}

$PushedLocation = $false
try {
    Push-Location $ResolvedSnapshotDir
    $PushedLocation = $true
    Write-Output "DEP5_PASSPHRASE_PROMPT: enter a strong package passphrase in 7-Zip; it is not read by this script"
    & $SevenZipExe @(
        "a",
        "-t7z",
        "-m0=lzma2",
        "-mx=9",
        "-mhe=on",
        "-p",
        "--",
        $PartialArchivePath,
        $DumpFilename,
        $ManifestFilename
    )
    if ($LASTEXITCODE -ne 0) {
        throw "DEP5_BLOCKED: encrypted archive creation failed"
    }

    Write-Output "DEP5_PASSPHRASE_VERIFY: enter the same passphrase again to test the archive"
    & $SevenZipExe @("t", "--", $PartialArchivePath)
    if ($LASTEXITCODE -ne 0) {
        throw "DEP5_BLOCKED: encrypted archive verification failed"
    }
}
catch {
    if (Test-Path -LiteralPath $PartialArchivePath) {
        Remove-Item -LiteralPath $PartialArchivePath -Force
    }
    throw
}
finally {
    if ($PushedLocation) {
        Pop-Location
    }
}

Move-Item -LiteralPath $PartialArchivePath -Destination $ArchivePath

$ComposePath = Join-Path $RepositoryRoot "compose.yaml"
$SetupDocumentPath = Join-Path $RepositoryRoot "docs\operations\docker_first_run.md"
$ArchiveItem = Get-Item -LiteralPath $ArchivePath
$Receipt = [ordered]@{
    receipt_version = "1.0.0"
    status = "DEP5_TRANSFER_PACKAGE_VERIFIED"
    created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    git_sha = $GitSha
    git_branch = $GitBranch
    git_worktree_clean = $true
    snapshot_version = [string]$Verification.snapshot_version
    snapshot_git_sha = [string]$Verification.snapshot_git_sha
    alembic_revision = [string]$Verification.alembic_revision
    dump_filename = $DumpFilename
    dump_bytes = [long]$Verification.dump_bytes
    dump_sha256 = [string]$Verification.dump_sha256
    manifest_filename = $ManifestFilename
    manifest_sha256 = [string]$Verification.manifest_sha256
    manifest_file_sha256 = [string]$Verification.manifest_file_sha256
    policy_count = [int]$Verification.policy_count
    collection_run_count = [int]$Verification.collection_run_count
    archive_filename = $ArchiveItem.Name
    archive_bytes = [long]$ArchiveItem.Length
    archive_sha256 = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    archive_format = "7z"
    archive_encryption = "AES-256 with encrypted headers"
    passphrase_delivery = "separate-channel-required"
    compose_sha256 = (Get-FileHash -LiteralPath $ComposePath -Algorithm SHA256).Hash.ToLowerInvariant()
    setup_document_sha256 = (Get-FileHash -LiteralPath $SetupDocumentPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

[IO.File]::WriteAllText(
    $ReceiptPath,
    ($Receipt | ConvertTo-Json -Depth 4) + "`r`n",
    [Text.UTF8Encoding]::new($false)
)

[pscustomobject]@{
    status = "DEP5_TRANSFER_PACKAGE_CREATED"
    archive_path = $ArchivePath
    receipt_path = $ReceiptPath
    archive_sha256 = $Receipt.archive_sha256
    git_sha = $GitSha
    snapshot_version = $Receipt.snapshot_version
} | ConvertTo-Json
