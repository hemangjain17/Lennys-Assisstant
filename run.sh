#!/bin/bash
echo "============================================================"
echo "LENNY GROWTH ASSISTANT - ONE-COMMAND STARTUP UTILITY"
echo "============================================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running or not installed on this system."
    echo "Please make sure Docker Desktop is open and running!"
    exit 1
fi

echo "Starting Docker Compose pipeline..."
docker-compose up --build -d

echo "============================================================"
echo "Services are booting up in the background!"
echo "- Frontend will load at http://localhost:3000"
echo "- Backend will run at http://localhost:8000"
echo "- Local Ollama is downloading llama3.1 at http://localhost:11434"
echo "============================================================"

echo "Waiting for Frontend to load..."
sleep 5

# Open browser based on OS
if [ "$(uname)" == "Darwin" ]; then
    open http://localhost:3000
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    xdg-open http://localhost:3000
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    start http://localhost:3000
fi

echo "Done! Press Ctrl+C or run 'docker-compose down' to stop all containers."
