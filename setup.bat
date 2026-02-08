@echo off
setlocal enableextensions enabledelayedexpansion

rem Resolve repo root (folder containing this script)
set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
cd /d "%REPO_ROOT%"

echo [1/7] Checking Docker...
where docker >nul 2>&1
if errorlevel 1 (
  where winget >nul 2>&1
  if not errorlevel 1 (
    echo Docker not found. Attempting to install Docker Desktop with winget...
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
  )
)
where docker >nul 2>&1
if errorlevel 1 (
  echo Docker is not installed. Please install Docker Desktop, then re-run setup.bat.
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker is installed but not running.
  echo Start Docker Desktop, wait for it to be ready, then re-run setup.bat.
  exit /b 1
)

echo [2/7] Checking required files...
if not exist "%REPO_ROOT%\open hand\docker_runtime.py" (
  echo Missing file: %REPO_ROOT%\open hand\docker_runtime.py
  exit /b 1
)
if not exist "%REPO_ROOT%\open hand\openhands_cli.py" (
  echo Missing file: %REPO_ROOT%\open hand\openhands_cli.py
  exit /b 1
)

echo [3/7] Detecting local model...
if not defined LLM_MODEL (
  for /f "usebackq delims=" %%M in (`powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; try { $r = Invoke-RestMethod -UseBasicParsing -TimeoutSec 3 http://localhost:8000/v1/models; if ($r.data) { ($r.data | Select-Object -ExpandProperty id) -join \"`n\" } } catch { }"`) do (
    if /i "%%M"=="gpt-oss-120b" set "LLM_MODEL=%%M"
    if not defined LLM_MODEL set "LLM_MODEL=%%M"
  )
)
if not defined LLM_MODEL set "LLM_MODEL=gpt-oss-120b"
echo Using model: %LLM_MODEL%

echo [4/7] Computing workspace mount path...
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$p = Resolve-Path '%REPO_ROOT%'; $p = $p.Path; $drive = $p.Substring(0,1).ToLower(); $rest = $p.Substring(2) -replace '\\\\','/'; Write-Output \"/run/desktop/mnt/host/$drive$rest\""` ) do set "WORKSPACE_POSIX=%%P"
if not defined WORKSPACE_POSIX (
  echo Failed to compute workspace path for Docker.
  exit /b 1
)

if not defined LLM_BASE_URL set "LLM_BASE_URL=http://host.docker.internal:8000/v1"
if not defined LLM_API_KEY set "LLM_API_KEY=local-llm"

echo [5/7] Cleaning old containers...
docker rm -f openhands-app >nul 2>&1
for /f %%C in ('docker ps -aq --filter "name=openhands-runtime-"') do docker rm -f %%C >nul 2>&1

echo [6/7] Starting OpenHands...
docker run -d --pull=missing ^
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.openhands.dev/openhands/runtime:1.1-nikolaik ^
  -e LOG_ALL_EVENTS=true ^
  -e LLM_MODEL=%LLM_MODEL% ^
  -e LLM_API_KEY=%LLM_API_KEY% ^
  -e LLM_BASE_URL=%LLM_BASE_URL% ^
  -e LLM_CUSTOM_LLM_PROVIDER=openai ^
  -e ENABLE_BROWSER=false ^
  -e "SANDBOX_VOLUMES=%WORKSPACE_POSIX%:/workspace:rw" ^
  -v /var/run/docker.sock:/var/run/docker.sock ^
  -v openhands_data:/.openhands ^
  -p 3000:3000 ^
  --add-host host.docker.internal:host-gateway ^
  --name openhands-app ^
  docker.openhands.dev/openhands/openhands:1.1
if errorlevel 1 (
  echo Failed to start OpenHands container.
  exit /b 1
)

echo [7/7] Applying runtime patch and restarting...
docker cp "%REPO_ROOT%\open hand\docker_runtime.py" openhands-app:/app/openhands/runtime/impl/docker/docker_runtime.py >nul 2>&1
docker restart openhands-app >nul 2>&1

echo.
echo Setup complete.
echo Run the CLI:
echo   python "%REPO_ROOT%\open hand\openhands_cli.py"
echo.
echo Note: Your local model server must be running at http://localhost:8000/v1
echo If you move this repo, just run setup.bat again.
endlocal
