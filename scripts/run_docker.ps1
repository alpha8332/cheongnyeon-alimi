[CmdletBinding()]
param(
    [string]$DatasetPointerUrl = "https://github.com/alpha8332/cheongnyeon-alimi/releases/download/dataset-latest/public-dataset-pointer.json",
    [string]$DatasetManifestPath,
    [string]$DatasetCacheDir,
    [string]$ComposeEnvFile,
    [ValidatePattern("^[a-z0-9][a-z0-9_-]*$")]
    [string]$ComposeProjectName,
    [ValidateRange(0, 65535)]
    [int]$BackendPort = 0,
    [ValidateRange(0, 65535)]
    [int]$FrontendPort = 0,
    [ValidateRange(30, 900)]
    [int]$HealthTimeoutSeconds = 300,
    [switch]$Offline,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ComposeFile = Join-Path $RepositoryRoot "compose.yaml"
$Initializer = Join-Path $RepositoryRoot "deployment\postgres\initialize_compose_env.ps1"
$DefaultProjectName = "cheongnyeon-alimi-acceptance"
$DefaultCacheRoot = if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    Join-Path $RepositoryRoot "runtime\public_dataset_cache"
}
else {
    Join-Path $env:LOCALAPPDATA "cheongnyeon-alimi\public-dataset"
}

if ([string]::IsNullOrWhiteSpace($DatasetCacheDir)) {
    $DatasetCacheDir = $DefaultCacheRoot
}
if ([string]::IsNullOrWhiteSpace($ComposeEnvFile)) {
    $ComposeEnvFile = Join-Path $RepositoryRoot ".env.compose"
}
$DatasetCacheDir = [IO.Path]::GetFullPath($DatasetCacheDir)
$ComposeEnvFile = [IO.Path]::GetFullPath($ComposeEnvFile)

function Stop-WithCode {
    param([Parameter(Mandatory = $true)][string]$Message)
    throw "W6_P3_BLOCKED: $Message"
}

function Invoke-Docker {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        Stop-WithCode "Docker command failed"
    }
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        Stop-WithCode "downloaded JSON is invalid"
    }
}

function Test-TcpPort {
    param([Parameter(Mandatory = $true)][int]$Port)
    $Client = [Net.Sockets.TcpClient]::new()
    try {
        $Result = $Client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $Result.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $Client.EndConnect($Result)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $Client.Dispose()
    }
}

function Test-ProjectOwnsPort {
    param(
        [Parameter(Mandatory = $true)][string[]]$ComposeArguments,
        [Parameter(Mandatory = $true)][string]$Service,
        [Parameter(Mandatory = $true)][int]$ContainerPort,
        [Parameter(Mandatory = $true)][int]$HostPort
    )
    $Mappings = & docker @ComposeArguments port $Service $ContainerPort 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    return @($Mappings) | Where-Object {
        $_ -match ":$HostPort$"
    } | Select-Object -First 1
}

function Get-EnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )
    foreach ($Line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($Line -match "^$([Regex]::Escape($Name))=(.*)$") {
            return $Matches[1]
        }
    }
    return $null
}

function Assert-PointerContract {
    param([Parameter(Mandatory = $true)]$Pointer)
    $ExpectedNames = @(
        "pointer_version",
        "dataset_version",
        "manifest_url",
        "manifest_sha256",
        "updated_at"
    )
    $ActualNames = @($Pointer.PSObject.Properties.Name)
    $Unexpected = @($ActualNames | Where-Object { $_ -notin $ExpectedNames })
    $Missing = @($ExpectedNames | Where-Object { $_ -notin $ActualNames })
    if ($Unexpected.Count -gt 0 -or $Missing.Count -gt 0) {
        Stop-WithCode "dataset pointer fields do not match the 1.0.0 contract"
    }
    if ($Pointer.pointer_version -ne "1.0.0") {
        Stop-WithCode "unsupported dataset pointer version"
    }
    if ([string]$Pointer.dataset_version -notmatch '^public-bootstrap-[0-9]{8}-[0-9a-f]{7,40}$') {
        Stop-WithCode "dataset pointer version is invalid"
    }
    if ([string]$Pointer.manifest_url -notmatch '^https://') {
        Stop-WithCode "dataset manifest URL must use HTTPS"
    }
    if ([string]$Pointer.manifest_sha256 -notmatch '^[0-9a-f]{64}$') {
        Stop-WithCode "dataset manifest SHA-256 is invalid"
    }
    $Timestamp = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$Pointer.updated_at, [ref]$Timestamp)) {
        Stop-WithCode "dataset pointer updated_at is invalid"
    }
}

function Assert-CacheEntry {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$ExpectedManifestSha256
    )
    $ManifestPath = Join-Path $Directory "manifest.json"
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        Stop-WithCode "cached manifest is missing"
    }
    if ((Get-FileSha256 -Path $ManifestPath) -ne $ExpectedManifestSha256) {
        Stop-WithCode "cached manifest SHA-256 mismatch"
    }
    $Manifest = Read-JsonFile -Path $ManifestPath
    $Filename = [string]$Manifest.artifact.filename
    if (
        [string]::IsNullOrWhiteSpace($Filename) -or
        [IO.Path]::GetFileName($Filename) -ne $Filename
    ) {
        Stop-WithCode "manifest artifact filename is unsafe"
    }
    $DatasetPath = Join-Path $Directory $Filename
    if (-not (Test-Path -LiteralPath $DatasetPath -PathType Leaf)) {
        Stop-WithCode "cached dataset is missing"
    }
    if ((Get-FileSha256 -Path $DatasetPath) -ne [string]$Manifest.artifact.sha256) {
        Stop-WithCode "cached dataset SHA-256 mismatch"
    }
    if ((Get-Item -LiteralPath $DatasetPath).Length -ne [long]$Manifest.artifact.bytes) {
        Stop-WithCode "cached dataset byte count mismatch"
    }
    return @{
        Directory = $Directory
        Manifest = $Manifest
        ManifestSha256 = $ExpectedManifestSha256
    }
}

function Read-LatestCache {
    $PointerPath = Join-Path $DatasetCacheDir "latest.pointer.json"
    if (-not (Test-Path -LiteralPath $PointerPath -PathType Leaf)) {
        Stop-WithCode "network unavailable and no verified offline cache exists"
    }
    $Pointer = Read-JsonFile -Path $PointerPath
    Assert-PointerContract -Pointer $Pointer
    $Version = [string]$Pointer.dataset_version
    $Directory = Join-Path (Join-Path $DatasetCacheDir "immutable") $Version
    return Assert-CacheEntry `
        -Directory $Directory `
        -ExpectedManifestSha256 ([string]$Pointer.manifest_sha256)
}

function Write-LatestPointerAtomically {
    param([Parameter(Mandatory = $true)][string]$SourcePath)
    $TargetPath = Join-Path $DatasetCacheDir "latest.pointer.json"
    $TemporaryPath = "$TargetPath.$([Guid]::NewGuid().ToString('N')).partial"
    Copy-Item -LiteralPath $SourcePath -Destination $TemporaryPath
    Move-Item -LiteralPath $TemporaryPath -Destination $TargetPath -Force
}

function Write-LocalCachePointer {
    param(
        [Parameter(Mandatory = $true)][string]$DatasetVersion,
        [Parameter(Mandatory = $true)][string]$ManifestSha256
    )
    $TemporaryPath = Join-Path $DatasetCacheDir (
        "local-pointer-" + [Guid]::NewGuid().ToString("N") + ".json"
    )
    $Pointer = [ordered]@{
        pointer_version = "1.0.0"
        dataset_version = $DatasetVersion
        manifest_url = "https://local-cache.invalid/$DatasetVersion/manifest.json"
        manifest_sha256 = $ManifestSha256
        updated_at = [DateTime]::UtcNow.ToString("o")
    }
    [IO.File]::WriteAllText(
        $TemporaryPath,
        ($Pointer | ConvertTo-Json) + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    try {
        Write-LatestPointerAtomically -SourcePath $TemporaryPath
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }
    }
}

function Remove-DownloadDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $ResolvedCache = [IO.Path]::GetFullPath($DatasetCacheDir).TrimEnd('\')
    $ResolvedPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $ExpectedPrefix = $ResolvedCache + [IO.Path]::DirectorySeparatorChar + "download-"
    if (-not $ResolvedPath.StartsWith($ExpectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Stop-WithCode "refusing to remove an unexpected temporary directory"
    }
    Remove-Item -LiteralPath $ResolvedPath -Recurse -Force
}

function Invoke-DatasetDownload {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$OutFile,
        [Parameter(Mandatory = $true)][int]$TimeoutSec
    )
    try {
        Invoke-WebRequest `
            -UseBasicParsing `
            -Uri $Uri `
            -OutFile $OutFile `
            -TimeoutSec $TimeoutSec
    }
    catch {
        throw "W6_P3_NETWORK_FAILED: dataset distribution endpoint is unavailable"
    }
}

function Save-RemoteDataset {
    if ($DatasetPointerUrl -notmatch '^https://') {
        Stop-WithCode "remote dataset pointer must use HTTPS"
    }
    $DownloadRoot = Join-Path $DatasetCacheDir ("download-" + [Guid]::NewGuid().ToString("N"))
    [void](New-Item -ItemType Directory -Path $DownloadRoot)
    try {
        $PointerPath = Join-Path $DownloadRoot "pointer.json"
        Invoke-DatasetDownload `
            -Uri $DatasetPointerUrl `
            -OutFile $PointerPath `
            -TimeoutSec 30
        $Pointer = Read-JsonFile -Path $PointerPath
        Assert-PointerContract -Pointer $Pointer
        $Version = [string]$Pointer.dataset_version
        $ManifestUrl = [string]$Pointer.manifest_url
        $ManifestSha256 = [string]$Pointer.manifest_sha256

        $ManifestPath = Join-Path $DownloadRoot "manifest.json"
        Invoke-DatasetDownload `
            -Uri $ManifestUrl `
            -OutFile $ManifestPath `
            -TimeoutSec 60
        if ((Get-FileSha256 -Path $ManifestPath) -ne $ManifestSha256) {
            Stop-WithCode "downloaded manifest SHA-256 mismatch"
        }
        $Manifest = Read-JsonFile -Path $ManifestPath
        if ([string]$Manifest.dataset_version -ne $Version) {
            Stop-WithCode "pointer and manifest dataset versions differ"
        }
        $Filename = [string]$Manifest.artifact.filename
        if (
            [string]::IsNullOrWhiteSpace($Filename) -or
            [IO.Path]::GetFileName($Filename) -ne $Filename
        ) {
            Stop-WithCode "manifest artifact filename is unsafe"
        }
        $ArtifactUri = [Uri]::new([Uri]$ManifestUrl, $Filename)
        if ($ArtifactUri.Scheme -ne "https") {
            Stop-WithCode "dataset artifact URL must use HTTPS"
        }
        $DatasetPath = Join-Path $DownloadRoot $Filename
        Invoke-DatasetDownload `
            -Uri $ArtifactUri.AbsoluteUri `
            -OutFile $DatasetPath `
            -TimeoutSec 180
        if ((Get-FileSha256 -Path $DatasetPath) -ne [string]$Manifest.artifact.sha256) {
            Stop-WithCode "downloaded dataset SHA-256 mismatch"
        }
        if ((Get-Item -LiteralPath $DatasetPath).Length -ne [long]$Manifest.artifact.bytes) {
            Stop-WithCode "downloaded dataset byte count mismatch"
        }

        $ImmutableRoot = Join-Path $DatasetCacheDir "immutable"
        $TargetDirectory = Join-Path $ImmutableRoot $Version
        if (Test-Path -LiteralPath $TargetDirectory) {
            $Cached = Assert-CacheEntry `
                -Directory $TargetDirectory `
                -ExpectedManifestSha256 $ManifestSha256
        }
        else {
            [void](New-Item -ItemType Directory -Path $ImmutableRoot -Force)
            Move-Item -LiteralPath $DownloadRoot -Destination $TargetDirectory
            $DownloadRoot = $null
            $PointerPath = Join-Path $TargetDirectory "pointer.json"
            $Cached = Assert-CacheEntry `
                -Directory $TargetDirectory `
                -ExpectedManifestSha256 $ManifestSha256
        }
        return $Cached
    }
    finally {
        if ($null -ne $DownloadRoot -and (Test-Path -LiteralPath $DownloadRoot)) {
            Remove-DownloadDirectory -Path $DownloadRoot
        }
    }
}

function Save-LocalDataset {
    $SourceManifest = (Resolve-Path -LiteralPath $DatasetManifestPath).Path
    $Manifest = Read-JsonFile -Path $SourceManifest
    $Version = [string]$Manifest.dataset_version
    $Filename = [string]$Manifest.artifact.filename
    if ($Version -notmatch '^public-bootstrap-[0-9]{8}-[0-9a-f]{7,40}$') {
        Stop-WithCode "local manifest dataset version is invalid"
    }
    if (
        [string]::IsNullOrWhiteSpace($Filename) -or
        [IO.Path]::GetFileName($Filename) -ne $Filename
    ) {
        Stop-WithCode "local manifest artifact filename is unsafe"
    }
    $SourceDataset = Join-Path (Split-Path -Parent $SourceManifest) $Filename
    if (-not (Test-Path -LiteralPath $SourceDataset -PathType Leaf)) {
        Stop-WithCode "local manifest sibling dataset is missing"
    }
    $ManifestSha256 = Get-FileSha256 -Path $SourceManifest
    $ImmutableRoot = Join-Path $DatasetCacheDir "immutable"
    $TargetDirectory = Join-Path $ImmutableRoot $Version
    if (-not (Test-Path -LiteralPath $TargetDirectory)) {
        $TemporaryDirectory = Join-Path $DatasetCacheDir ("local-" + [Guid]::NewGuid().ToString("N"))
        [void](New-Item -ItemType Directory -Path $TemporaryDirectory)
        Copy-Item -LiteralPath $SourceManifest -Destination (Join-Path $TemporaryDirectory "manifest.json")
        Copy-Item -LiteralPath $SourceDataset -Destination (Join-Path $TemporaryDirectory $Filename)
        [void](New-Item -ItemType Directory -Path $ImmutableRoot -Force)
        Move-Item -LiteralPath $TemporaryDirectory -Destination $TargetDirectory
    }
    $Cached = Assert-CacheEntry `
        -Directory $TargetDirectory `
        -ExpectedManifestSha256 $ManifestSha256
    return $Cached
}

function Wait-HttpHealth {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $Deadline = [DateTime]::UtcNow.AddSeconds($HealthTimeoutSeconds)
    while ([DateTime]::UtcNow -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 3
            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 400) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    Stop-WithCode "$Label health check timed out"
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Stop-WithCode "run_docker.bat currently requires Windows"
}
if (-not (Test-Path -LiteralPath $ComposeFile -PathType Leaf)) {
    Stop-WithCode "compose.yaml is missing"
}
if ($null -eq (Get-Command docker.exe -ErrorAction SilentlyContinue)) {
    Stop-WithCode "Docker Desktop is not installed or docker.exe is not on PATH"
}
& docker info --format "{{.ServerVersion}}" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Stop-WithCode "Docker Desktop engine is not running"
}
& docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Stop-WithCode "Docker Compose v2 is unavailable"
}

[void](New-Item -ItemType Directory -Path $DatasetCacheDir -Force)
$CacheRoot = [IO.Path]::GetPathRoot($DatasetCacheDir)
$CacheDrive = Get-PSDrive -Name $CacheRoot.TrimEnd('\').TrimEnd(':')
if ($CacheDrive.Free -lt 2GB) {
    Stop-WithCode "at least 2 GiB of free disk space is required"
}

if (-not (Test-Path -LiteralPath $ComposeEnvFile -PathType Leaf)) {
    if ($ComposeEnvFile -ne (Join-Path $RepositoryRoot ".env.compose")) {
        Stop-WithCode "the requested Compose env file does not exist"
    }
    $OwnershipProjectName = if (
        [string]::IsNullOrWhiteSpace($ComposeProjectName)
    ) {
        $DefaultProjectName
    }
    else {
        $ComposeProjectName
    }
    $ExistingVolumeNames = @(& docker volume ls --quiet)
    if ($LASTEXITCODE -ne 0) {
        Stop-WithCode "failed to inspect existing Docker Volumes"
    }
    if ($ExistingVolumeNames -contains "$OwnershipProjectName`_acceptance-db") {
        Stop-WithCode (
            "an existing database Volume for Compose project " +
            "'$OwnershipProjectName' was found without its env file"
        )
    }
    & powershell.exe `
        -NoLogo `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Initializer
    if ($LASTEXITCODE -ne 0) {
        Stop-WithCode "local Compose environment initialization failed"
    }
}

if ([string]::IsNullOrWhiteSpace($ComposeProjectName)) {
    $ComposeProjectName = Get-EnvValue -Path $ComposeEnvFile -Name "COMPOSE_PROJECT_NAME"
    if ([string]::IsNullOrWhiteSpace($ComposeProjectName)) {
        $ComposeProjectName = $DefaultProjectName
    }
}
if ($BackendPort -eq 0) {
    $ConfiguredBackendPort = Get-EnvValue `
        -Path $ComposeEnvFile `
        -Name "BACKEND_HOST_PORT"
    $BackendPort = if ($ConfiguredBackendPort -match '^\d+$') {
        [int]$ConfiguredBackendPort
    }
    else {
        8000
    }
}
if ($FrontendPort -eq 0) {
    $ConfiguredFrontendPort = Get-EnvValue `
        -Path $ComposeEnvFile `
        -Name "FRONTEND_HOST_PORT"
    $FrontendPort = if ($ConfiguredFrontendPort -match '^\d+$') {
        [int]$ConfiguredFrontendPort
    }
    else {
        3000
    }
}
foreach ($ResolvedPort in @($BackendPort, $FrontendPort)) {
    if ($ResolvedPort -lt 1 -or $ResolvedPort -gt 65535) {
        Stop-WithCode "configured host port is outside 1..65535"
    }
}

$ComposeArguments = @(
    "compose",
    "--env-file", $ComposeEnvFile,
    "--project-name", $ComposeProjectName,
    "--file", $ComposeFile
)

foreach ($PortCheck in @(
    @{ Port = $BackendPort; Service = "backend"; ContainerPort = 8000 },
    @{ Port = $FrontendPort; Service = "frontend"; ContainerPort = 3000 }
)) {
    if (Test-TcpPort -Port $PortCheck.Port) {
        if (-not (Test-ProjectOwnsPort `
            -ComposeArguments $ComposeArguments `
            -Service $PortCheck.Service `
            -ContainerPort $PortCheck.ContainerPort `
            -HostPort $PortCheck.Port
        )) {
            Stop-WithCode "port $($PortCheck.Port) is already used by another process"
        }
    }
}

$env:BACKEND_HOST_PORT = [string]$BackendPort
$env:FRONTEND_HOST_PORT = [string]$FrontendPort
$env:VITE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
$env:CORS_ORIGINS = "[`"http://127.0.0.1:$FrontendPort`",`"http://localhost:$FrontendPort`"]"

$Dataset = $null
if (-not [string]::IsNullOrWhiteSpace($DatasetManifestPath)) {
    $Dataset = Save-LocalDataset
}
elseif ($Offline) {
    $Dataset = Read-LatestCache
}
else {
    try {
        $Dataset = Save-RemoteDataset
    }
    catch {
        if ($_.Exception.Message -notlike "W6_P3_NETWORK_FAILED:*") {
            throw
        }
        Write-Warning "Dataset endpoint unavailable; using the last verified cache."
        $Dataset = Read-LatestCache
    }
}

$env:PUBLIC_DATASET_DIR = $Dataset.Directory.Replace('\', '/')
Write-Output (
    "W6_P3_DATASET_VERIFIED: version={0} rows={1} sha256={2}" -f
    $Dataset.Manifest.dataset_version,
    $Dataset.Manifest.artifact.row_count,
    $Dataset.Manifest.artifact.sha256
)

Invoke-Docker -Arguments ($ComposeArguments + @("build", "backend", "frontend"))
Invoke-Docker -Arguments ($ComposeArguments + @("up", "-d", "database", "redis"))
Invoke-Docker -Arguments ($ComposeArguments + @("run", "--rm", "migrate"))
Invoke-Docker -Arguments (
    $ComposeArguments + @(
        "--profile", "bootstrap", "run", "--rm", "--no-deps",
        "public-dataset-bootstrap"
    )
)
Write-LocalCachePointer `
    -DatasetVersion ([string]$Dataset.Manifest.dataset_version) `
    -ManifestSha256 ([string]$Dataset.ManifestSha256)
Invoke-Docker -Arguments ($ComposeArguments + @("up", "-d", "--no-build"))

$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
Wait-HttpHealth -Uri "$BackendUrl/health" -Label "Backend"
Wait-HttpHealth -Uri "$FrontendUrl/health" -Label "Frontend"

Write-Output (
    "W6_P3_BOOTSTRAP_READY: url={0} dataset={1} project={2}" -f
    $FrontendUrl,
    $Dataset.Manifest.dataset_version,
    $ComposeProjectName
)
if (-not $NoBrowser) {
    Start-Process -FilePath "$FrontendUrl/"
}
