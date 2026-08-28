@echo off
echo ============================================================
# LENNY GROWTH ASSISTANT - ONE-COMMAND STARTUP UTILITY
echo ============================================================
echo Checking Docker service availability...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running or not installed on this system.
    echo Please make sure Docker Desktop is open and running!
    pause
    exit /b 1
)

echo Starting Docker Compose pipeline...
docker-compose up --build -d

echo ============================================================
echo Services are booting up in the background!
echo - Frontend will load at http://localhost:3000
echo - Backend will run at http://localhost:8000
echo - Local Ollama is downloading llama3.1 at http://localhost:11434
echo ============================================================
echo Waiting for Frontend to load...
timeout /t 5 /nobreak >nul

echo Launching browser to Frontend...
start http://localhost:3000

echo Done! Press any key to stop all Docker containers.
pause

echo Stopping all Docker containers...
docker-compose down
echo Done!
