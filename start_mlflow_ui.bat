@echo off
REM Start MLflow UI from project root
cd /d "%~dp0"
echo Starting MLflow UI...
echo MLruns directory: %CD%\mlruns
if not exist "mlruns" (
    echo WARNING: mlruns directory does not exist yet.
    echo Run your training notebook first to create experiments.
    echo.
)
mlflow ui --host 127.0.0.1 --port 5000
pause

