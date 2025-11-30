#!/bin/bash

# Stop script for the Workout Analysis App

echo "🛑 Stopping Workout Analysis App..."
echo "======================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Stop Docker Compose services
echo "🐳 Stopping Docker containers..."
docker compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ Application stopped successfully!"
    echo ""
    echo "Your data is preserved."
    echo "To remove all data, run: ./scripts/reset_data.sh"
    echo "To restart: ./scripts/start.sh"
    echo "======================================"
else
    echo ""
    echo "❌ Failed to stop containers"
    echo "Please check Docker status and try again"
    exit 1
fi
