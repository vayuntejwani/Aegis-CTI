@echo off
title CTI Threat Portal & Sensor Registry Launcher
echo =======================================================
echo Starting Defence Cyber Agency (DCyA) CTI Triage Engine
echo =======================================================
echo.

cd /d "%~dp0"

echo [1/2] Launching Flask REST API Server on http://localhost:5001...
start "Flask API Server (Port 5001)" cmd /k "python server.py"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Streamlit Analytics Dashboard on http://localhost:8501...
start "Streamlit Dashboard (Port 8501)" cmd /k ""C:\Users\Lenovo\AppData\Roaming\Python\Python312\Scripts\streamlit.exe" run streamlit/app.py --server.headless true"

timeout /t 2 /nobreak >nul

echo.
echo =======================================================
echo Servers launched successfully!
echo.
echo  - Main Website & Sensors: http://localhost:5001
echo  - Streamlit Analytics:    http://localhost:8501
echo =======================================================
echo.

echo Opening Main Portal in your browser...
start http://localhost:5001

pause
