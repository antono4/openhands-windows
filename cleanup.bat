@echo off
setlocal enableextensions

echo Stopping OpenHands containers...
docker rm -f openhands-app >nul 2>&1

echo Removing runtime containers...
for /f %%C in ('docker ps -aq --filter "name=openhands-runtime-"') do docker rm -f %%C >nul 2>&1

echo Done.
endlocal
