[CmdletBinding()]
param(
    [string]$PgpassFile,
    [switch]$NoBrowser,
    [switch]$ExitAfterReady
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $RepoRoot "backend"
$FrontendRoot = Join-Path $RepoRoot "frontend"
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ViteBin = Join-Path $FrontendRoot "node_modules\vite\bin\vite.js"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:3000"

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

function Test-LocalProcessIdentity {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][string]$Marker,
        [bool]$RequireRepoRoot = $true
    )

    $processInfo = Get-CimInstance Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue
    if ($null -eq $processInfo) {
        return $false
    }
    $identity = "$($processInfo.ExecutablePath) $($processInfo.CommandLine)"
    return $identity.Contains($Marker) -and (
        -not $RequireRepoRoot -or $identity.Contains($RepoRoot)
    )
}

function Stop-LocalService {
    param(
        [AllowNull()][Nullable[int]]$ListenerProcessId,
        [AllowNull()][System.Diagnostics.Process]$StarterProcess,
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $currentListenerId = Get-ListenerProcessId -Port $Port
    if (
        $null -ne $ListenerProcessId -and
        $currentListenerId -eq $ListenerProcessId -and
        (Test-LocalProcessIdentity `
            -ProcessId $ListenerProcessId `
            -Marker $Marker `
            -RequireRepoRoot $false)
    ) {
        Stop-Process -Id $ListenerProcessId -Force -ErrorAction SilentlyContinue
    }
    if (
        $null -ne $StarterProcess -and
        $StarterProcess.Id -ne $ListenerProcessId -and
        (Test-LocalProcessIdentity -ProcessId $StarterProcess.Id -Marker $Marker)
    ) {
        Stop-Process -Id $StarterProcess.Id -Force -ErrorAction SilentlyContinue
    }
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
        "as the first argument to run.bat."
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

foreach ($requiredFile in @($PythonExe, $ViteBin)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required local dependency is missing: $requiredFile"
    }
}
$NodeExe = (Get-Command node.exe -ErrorAction Stop).Source

if (-not (Test-TcpPort -Address "127.0.0.1" -Port 5432)) {
    throw "PostgreSQL is not listening on 127.0.0.1:5432."
}
foreach ($port in @(8000, 3000)) {
    if ($null -ne (Get-ListenerProcessId -Port $port)) {
        throw "Port $port is already in use. Stop that process before running run.bat."
    }
}

$ResolvedPgpass = Resolve-PgpassFile
$RuntimeRole = Resolve-RuntimeRole -Path $ResolvedPgpass
$EncodedRole = [Uri]::EscapeDataString($RuntimeRole)
$DatabaseUrl = "postgresql+psycopg2://$EncodedRole@127.0.0.1:5432/cheongnyeon_alimi"

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
        -NoNewWindow `
        -PassThru

    Wait-HttpEndpoint -Uri "$BackendUrl/health" -Label "Backend"
    $backendListenerId = Get-ListenerProcessId -Port 8000
    if ($null -eq $backendListenerId) {
        throw "Backend health responded without a tracked listener."
    }

    $env:VITE_USE_MOCK = "false"
    $env:VITE_API_BASE_URL = $BackendUrl
    $frontendProcess = Start-Process `
        -FilePath $NodeExe `
        -ArgumentList @($ViteBin, "--host", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory $FrontendRoot `
        -NoNewWindow `
        -PassThru

    Wait-HttpEndpoint -Uri $FrontendUrl -Label "Frontend"
    $frontendListenerId = Get-ListenerProcessId -Port 3000
    if ($null -eq $frontendListenerId) {
        throw "Frontend responded without a tracked listener."
    }

    Write-Host ""
    Write-Host "Cheongnyeon Alimi is ready: $FrontendUrl"
    Write-Host "Backend API: $BackendUrl"
    Write-Host "Press Ctrl+C in this terminal to stop both services."
    Write-Host ""

    if (-not $NoBrowser) {
        Start-Process -FilePath "$FrontendUrl/"
    }
    if ($ExitAfterReady) {
        return
    }

    while ($true) {
        $backendProcess.Refresh()
        $frontendProcess.Refresh()
        if ($backendProcess.HasExited) {
            throw "Backend exited unexpectedly with code $($backendProcess.ExitCode)."
        }
        if ($frontendProcess.HasExited) {
            throw "Frontend exited unexpectedly with code $($frontendProcess.ExitCode)."
        }
        Start-Sleep -Milliseconds 500
    }
}
finally {
    Stop-LocalService `
        -ListenerProcessId $frontendListenerId `
        -StarterProcess $frontendProcess `
        -Port 3000 `
        -Marker "vite.js"
    Stop-LocalService `
        -ListenerProcessId $backendListenerId `
        -StarterProcess $backendProcess `
        -Port 8000 `
        -Marker "uvicorn"

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

    Write-Host "Backend and Frontend stopped."
}
