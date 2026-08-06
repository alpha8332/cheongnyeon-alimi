[CmdletBinding()]
param(
    [ValidateSet("Start", "Stop", "Status")]
    [string]$Action = "Start",
    [string]$PgpassFile,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = Join-Path $RepoRoot "runtime"
$StateFile = Join-Path $RuntimeRoot "release_1_review_processes.json"
$BackendStdout = Join-Path $RuntimeRoot "release_1_review_backend.stdout.log"
$BackendStderr = Join-Path $RuntimeRoot "release_1_review_backend.stderr.log"
$FrontendStdout = Join-Path $RuntimeRoot "release_1_review_frontend.stdout.log"
$FrontendStderr = Join-Path $RuntimeRoot "release_1_review_frontend.stderr.log"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:3000"
$GoldenQuery = "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?"
$ReviewUrl = "$FrontendUrl/search?q=$([Uri]::EscapeDataString($GoldenQuery))"

function Test-TcpPort {
    param(
        [Parameter(Mandatory = $true)][string]$Address,
        [Parameter(Mandatory = $true)][int]$Port,
        [int]$TimeoutMilliseconds = 2000
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect($Address, $Port, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) {
            return $false
        }
        $client.EndConnect($result)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-HttpEndpoint {
    param([Parameter(Mandatory = $true)][string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
    }
    catch {
        return $false
    }
}

function Wait-HttpEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Label
    )

    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        if (Test-HttpEndpoint -Uri $Uri) {
            return
        }
        Start-Sleep -Milliseconds 250
    }
    throw "$Label did not become ready: $Uri"
}

function Get-ListenerProcessId {
    param([Parameter(Mandatory = $true)][int]$Port)

    $connection = Get-NetTCPConnection `
        -LocalAddress "127.0.0.1" `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $connection) {
        return $null
    }
    return [int]$connection.OwningProcess
}

function Test-TrackedService {
    param([Parameter(Mandatory = $true)]$Service)

    $listenerId = Get-ListenerProcessId -Port ([int]$Service.port)
    return $null -ne $listenerId -and `
        $listenerId -eq [int]$Service.listener_process_id
}

function Test-TrackedProcessIdentity {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $processInfo = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue
    if ($null -eq $processInfo) {
        return $false
    }
    $identity = "$($processInfo.ExecutablePath) $($processInfo.CommandLine)"
    return $identity.Contains($RepoRoot) -and $identity.Contains($Marker)
}

function Stop-TrackedService {
    param([Parameter(Mandatory = $true)]$Service)

    $listenerId = Get-ListenerProcessId -Port ([int]$Service.port)
    if ($null -ne $listenerId -and `
        $listenerId -eq [int]$Service.listener_process_id -and `
        (Test-TrackedProcessIdentity `
            -ProcessId $listenerId `
            -Marker ([string]$Service.marker))) {
        Stop-Process -Id $listenerId -Force -ErrorAction SilentlyContinue
    }

    $starterId = [int]$Service.starter_process_id
    if ($starterId -eq [int]$Service.listener_process_id) {
        return
    }
    if (Test-TrackedProcessIdentity `
        -ProcessId $starterId `
        -Marker ([string]$Service.marker)) {
        Stop-Process -Id $starterId -Force -ErrorAction SilentlyContinue
    }
}

function Remove-ReviewRuntimeFiles {
    foreach ($path in @(
        $StateFile,
        $BackendStdout,
        $BackendStderr,
        $FrontendStdout,
        $FrontendStderr
    )) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Force
        }
    }
}

function Show-StartupDiagnostics {
    foreach ($path in @($BackendStderr, $FrontendStderr)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            continue
        }
        $lines = @(Get-Content -LiteralPath $path -Tail 20 -ErrorAction SilentlyContinue)
        if ($lines.Count -gt 0) {
            Write-Warning "Startup diagnostic from $path"
            $lines | ForEach-Object { Write-Warning $_ }
        }
    }
}

function Stop-ReviewEnvironment {
    if (Test-Path -LiteralPath $StateFile) {
        try {
            $state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 |
                ConvertFrom-Json
            if ($null -ne $state.frontend) {
                Stop-TrackedService -Service $state.frontend
            }
            if ($null -ne $state.backend) {
                Stop-TrackedService -Service $state.backend
            }
            Start-Sleep -Milliseconds 300
        }
        catch {
            Write-Warning "Could not fully read the saved process state: $($_.Exception.Message)"
        }
    }
    Remove-ReviewRuntimeFiles
}

function Resolve-PgpassFile {
    $candidates = @(
        $PgpassFile,
        $env:PGPASSFILE,
        (Join-Path $env:LOCALAPPDATA "Temp\cheongnyeon-alimi-pgpass.conf"),
        (Join-Path $env:APPDATA "postgresql\pgpass.conf")
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw (
        "PostgreSQL pgpass was not found. Set PGPASSFILE or pass its path " +
        "as the first argument to start_release_1_review.bat."
    )
}

function Resolve-RuntimeRole {
    param([Parameter(Mandatory = $true)][string]$Path)

    foreach ($line in Get-Content -LiteralPath $Path) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        if ($line -notmatch "^(?<host>[^:]+):(?<port>[^:]+):(?<database>[^:]+):(?<role>[^:]+):") {
            continue
        }
        $hostMatches = $Matches.host -in @("127.0.0.1", "localhost", "*")
        $portMatches = $Matches.port -in @("5432", "*")
        $databaseMatches = $Matches.database -in @("cheongnyeon_alimi", "*")
        if ($hostMatches -and $portMatches -and $databaseMatches) {
            return $Matches.role
        }
    }
    throw "pgpass has no entry usable for 127.0.0.1:5432/cheongnyeon_alimi."
}

function Show-Status {
    if (-not (Test-Path -LiteralPath $StateFile)) {
        Write-Host "Release 1 review environment: stopped"
        return
    }
    try {
        $state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 |
            ConvertFrom-Json
        $backendReady = (Test-TrackedService -Service $state.backend) -and `
            (Test-HttpEndpoint -Uri "$BackendUrl/health")
        $frontendReady = (Test-TrackedService -Service $state.frontend) -and `
            (Test-HttpEndpoint -Uri $FrontendUrl)
        Write-Host "Release 1 review environment: backend=$backendReady frontend=$frontendReady"
    }
    catch {
        Write-Host "Release 1 review environment: stale state"
    }
}

if ($Action -eq "Stop") {
    Stop-ReviewEnvironment
    Write-Host "Release 1 review Backend and Frontend stopped."
    exit 0
}

if ($Action -eq "Status") {
    Show-Status
    exit 0
}

$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BackendRoot = Join-Path $RepoRoot "backend"
$FrontendRoot = Join-Path $RepoRoot "frontend"
$ViteBin = Join-Path $FrontendRoot "node_modules\vite\bin\vite.js"
$AuditScript = Join-Path $RepoRoot "scripts\audit_release_1.py"

foreach ($requiredFile in @($PythonExe, $ViteBin, $AuditScript)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required local dependency is missing: $requiredFile"
    }
}
$NodeExe = (Get-Command node.exe -ErrorAction Stop).Source

if (Test-Path -LiteralPath $StateFile) {
    $existing = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 |
        ConvertFrom-Json
    if (
        (Test-TrackedService -Service $existing.backend) -and
        (Test-TrackedService -Service $existing.frontend) -and
        (Test-HttpEndpoint -Uri "$BackendUrl/health") -and
        (Test-HttpEndpoint -Uri $FrontendUrl)
    ) {
        Write-Host "Release 1 review environment is already running."
        if (-not $NoBrowser) {
            Start-Process -FilePath $ReviewUrl
        }
        exit 0
    }
    Stop-ReviewEnvironment
}

if (-not (Test-TcpPort -Address "127.0.0.1" -Port 5432)) {
    throw "PostgreSQL is not listening on 127.0.0.1:5432."
}
foreach ($port in @(8000, 3000)) {
    if ($null -ne (Get-ListenerProcessId -Port $port)) {
        throw "Port $port is already used by a process not started by this launcher."
    }
}

$ResolvedPgpass = Resolve-PgpassFile
$RuntimeRole = Resolve-RuntimeRole -Path $ResolvedPgpass
$EncodedRole = [Uri]::EscapeDataString($RuntimeRole)
$DatabaseUrl = "postgresql+psycopg2://$EncodedRole@127.0.0.1:5432/cheongnyeon_alimi"

if (-not (Test-Path -LiteralPath $RuntimeRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $RuntimeRoot | Out-Null
}
Remove-ReviewRuntimeFiles

$backendProcess = $null
$frontendProcess = $null
$backendListenerId = $null
$frontendListenerId = $null
$previousPgpass = $env:PGPASSFILE
$previousDatabaseUrl = $env:DATABASE_URL
$previousMock = $env:VITE_USE_MOCK
$previousApiBase = $env:VITE_API_BASE_URL

try {
    $env:PGPASSFILE = $ResolvedPgpass
    $env:DATABASE_URL = $DatabaseUrl
    $backendProcess = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @(
            "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "8000"
        ) `
        -WorkingDirectory $BackendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $BackendStdout `
        -RedirectStandardError $BackendStderr `
        -PassThru

    Wait-HttpEndpoint -Uri "$BackendUrl/health" -Label "Backend"
    $backendListenerId = Get-ListenerProcessId -Port 8000
    if ($null -eq $backendListenerId) {
        throw "Backend health responded without a tracked listener."
    }

    & $PythonExe -B $AuditScript --base-url $BackendUrl | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Actual snapshot acceptance failed; the review UI was not opened."
    }

    $env:VITE_USE_MOCK = "false"
    $env:VITE_API_BASE_URL = $BackendUrl
    $frontendProcess = Start-Process `
        -FilePath $NodeExe `
        -ArgumentList @($ViteBin, "--host", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory $FrontendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $FrontendStdout `
        -RedirectStandardError $FrontendStderr `
        -PassThru

    Wait-HttpEndpoint -Uri $FrontendUrl -Label "Frontend"
    $frontendListenerId = Get-ListenerProcessId -Port 3000
    if ($null -eq $frontendListenerId) {
        throw "Frontend responded without a tracked listener."
    }

    $state = [ordered]@{
        state_version = "1.0.0"
        started_at = [DateTimeOffset]::Now.ToString("o")
        backend = [ordered]@{
            starter_process_id = $backendProcess.Id
            listener_process_id = $backendListenerId
            port = 8000
            marker = "uvicorn"
        }
        frontend = [ordered]@{
            starter_process_id = $frontendProcess.Id
            listener_process_id = $frontendListenerId
            port = 3000
            marker = "vite.js"
        }
    }
    $state | ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath $StateFile -Encoding UTF8

    if (-not $NoBrowser) {
        Start-Process -FilePath $ReviewUrl
    }
    Write-Host "Release 1 actual review UI is ready: $ReviewUrl"
    Write-Host "Use stop_release_1_review.bat when the review is finished."
}
catch {
    $startupError = $_
    Show-StartupDiagnostics
    if ($null -ne $frontendListenerId) {
        Stop-Process -Id $frontendListenerId -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $backendListenerId) {
        Stop-Process -Id $backendListenerId -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $frontendProcess) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-ReviewRuntimeFiles
    throw $startupError
}
finally {
    if ($null -eq $previousPgpass) {
        Remove-Item Env:PGPASSFILE -ErrorAction SilentlyContinue
    }
    else {
        $env:PGPASSFILE = $previousPgpass
    }
    if ($null -eq $previousDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $previousDatabaseUrl
    }
    if ($null -eq $previousMock) {
        Remove-Item Env:VITE_USE_MOCK -ErrorAction SilentlyContinue
    }
    else {
        $env:VITE_USE_MOCK = $previousMock
    }
    if ($null -eq $previousApiBase) {
        Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:VITE_API_BASE_URL = $previousApiBase
    }
}
