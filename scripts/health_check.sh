#!/bin/bash

# Health Check Script for Workout Analysis Application
# Verifies that backend service is running and responsive

set -e

echo "🏥 Running Health Checks..."
echo "================================"

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
MAX_RETRIES=5
RETRY_DELAY=2

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check backend health
check_backend() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo -n "Checking backend health (attempt $attempt/$MAX_RETRIES)... "
        
        if curl -f -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" | grep -q "200"; then
            echo -e "${GREEN}✓ Backend is healthy${NC}"
            
            # Get detailed health info
            health_info=$(curl -s "$BACKEND_URL/health")
            echo "Backend status: $health_info"
            return 0
        else
            echo -e "${YELLOW}⚠ Backend not ready${NC}"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                echo "Waiting ${RETRY_DELAY}s before retry..."
                sleep $RETRY_DELAY
            fi
        fi
        
        ((attempt++))
    done
    
    echo -e "${RED}✗ Backend health check failed${NC}"
    return 1
}

# Function to check Docker containers
check_docker() {
    echo -n "Checking Docker containers... "
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠ Docker not found (skipping)${NC}"
        return 0
    fi
    
    if docker ps | grep -q "bench-ai-ui"; then
        echo -e "${GREEN}✓ Docker containers running${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "bench-ai-ui" || true
        return 0
    else
        echo -e "${YELLOW}⚠ No containers found${NC}"
        return 0
    fi
}

# Function to check storage directories
check_storage() {
    echo -n "Checking storage directories... "
    
    local storage_dir="${STORAGE_DIR:-./storage}"
    
    if [ -d "$storage_dir" ]; then
        if [ -d "$storage_dir/original-videos" ] && [ -d "$storage_dir/processed-videos" ]; then
            echo -e "${GREEN}✓ Storage directories exist${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Storage subdirectories missing${NC}"
            echo "Creating storage directories..."
            mkdir -p "$storage_dir/original-videos" "$storage_dir/processed-videos"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠ Storage directory not found${NC}"
        echo "Creating storage directories..."
        mkdir -p "$storage_dir/original-videos" "$storage_dir/processed-videos"
        return 0
    fi
}

# Main execution
main() {
    echo ""
    
    # Run checks
    check_docker
    echo ""
    
    check_storage
    echo ""
    
    if check_backend; then
        echo ""
        echo -e "${GREEN}================================${NC}"
        echo -e "${GREEN}✓ All health checks passed${NC}"
        echo -e "${GREEN}================================${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}================================${NC}"
        echo -e "${RED}✗ Health checks failed${NC}"
        echo -e "${RED}================================${NC}"
        echo ""
        echo "Troubleshooting tips:"
        echo "1. Check if Docker containers are running: docker-compose ps"
        echo "2. Check backend logs: docker-compose logs backend"
        echo "3. Verify backend is listening on port 8000"
        echo "4. Ensure YOLO model is present in ml-backend/models/"
        exit 1
    fi
}

# Run main function
main
