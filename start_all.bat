@echo off
cd /d %~dp0

echo Starting ETS2 Telemetry Server...
start "" "ets2-telemetry-server-master\server\Ets2Telemetry.exe"

timeout /t 2 >nul

echo Starting ISOTP Simulator...
start "" python "can-isotp-simulator-main\isotp_simulator.py"

timeout /t 2 >nul

echo Starting FMC650 Bridge...
start "" python "ETS2_FMC650_Bridge_v4.py"

echo.
echo All systems started.
pause