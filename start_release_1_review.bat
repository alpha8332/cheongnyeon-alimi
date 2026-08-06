@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if "%~1"=="" (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\release_1_review.ps1" -Action Start
) else (
  powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\release_1_review.ps1" -Action Start -PgpassFile "%~1"
)

set "review_exit=%ERRORLEVEL%"
if not "%review_exit%"=="0" (
  echo.
  echo Release 1 review environment failed to start.
  pause
)
exit /b %review_exit%
