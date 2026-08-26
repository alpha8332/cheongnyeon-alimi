[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ComposeFile = Join-Path $RepositoryRoot "compose.yaml"
$ComposeEnvFile = Join-Path $RepositoryRoot ".env.compose"

if (-not (Test-Path -LiteralPath $ComposeEnvFile -PathType Leaf)) {
    throw "PIN_RESET_BLOCKED: .env.compose does not exist; run run_docker.bat first"
}

$RunningServices = @(
    & docker compose --env-file $ComposeEnvFile -f $ComposeFile `
        ps --status running --services
)
if ($LASTEXITCODE -ne 0 -or $RunningServices -notcontains "backend") {
    throw "PIN_RESET_BLOCKED: backend is not running; run run_docker.bat first"
}

$FirstSecurePin = Read-Host "New admin PIN (4 digits)" -AsSecureString
$SecondSecurePin = Read-Host "Confirm new admin PIN" -AsSecureString
$FirstPointer = [IntPtr]::Zero
$SecondPointer = [IntPtr]::Zero
$FirstPin = $null
$SecondPin = $null

try {
    $FirstPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
        $FirstSecurePin
    )
    $SecondPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
        $SecondSecurePin
    )
    $FirstPin = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($FirstPointer)
    $SecondPin = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($SecondPointer)

    if ($FirstPin -notmatch '^\d{4}$') {
        throw "PIN_RESET_BLOCKED: admin PIN must contain exactly 4 digits"
    }
    if ($FirstPin -cne $SecondPin) {
        throw "PIN_RESET_BLOCKED: PIN confirmation does not match"
    }

    @($FirstPin, $SecondPin) |
        & docker compose --env-file $ComposeEnvFile -f $ComposeFile `
            exec -T backend python -m app.cli.reset_admin_pin
    if ($LASTEXITCODE -ne 0) {
        throw "PIN_RESET_BLOCKED: backend recovery command failed"
    }
}
finally {
    if ($FirstPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($FirstPointer)
    }
    if ($SecondPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($SecondPointer)
    }
    $FirstPin = $null
    $SecondPin = $null
    $FirstSecurePin = $null
    $SecondSecurePin = $null
}
