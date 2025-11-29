#!/bin/bash

# Quick start script for the Workout Analysis App

echo "🚀 Starting Workout Analysis App..."
echo "======================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if YOLO model exists
if [ ! -f "ml-backend/models/best.pt" ]; then
    echo "⚠️  Warning: YOLO model not found at ml-backend/models/best.pt"
    echo "The backend will start but analysis will fail without the model"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo "📁 Creating storage directories..."
mkdir -p storage/original-videos
mkdir -p storage/processed-videos
mkdir -p db

# Start Docker Compose
echo "🐳 Starting Docker containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Run health check
echo "🏥 Running health check..."
./scripts/health_check.sh

echo ""
echo "======================================"
echo "✅ Application is running!"
echo ""
echo "Access the application at:"
echo "  Frontend:  http://localhost:3333"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo "======================================"
