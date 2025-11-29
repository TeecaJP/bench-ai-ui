#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}   ⚠️  DATA RESET UTILITY  ⚠️${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""
echo -e "${RED}WARNING: This will DELETE ALL DATA including:${NC}"
echo -e "  - All uploaded original videos"
echo -e "  - All processed videos and JSON results"
echo -e "  - The entire database (all records will be wiped)"
echo ""

# 1. Confirmation Prompt
read -p "Are you sure you want to proceed? (y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""

# 2. Storage Cleanup
echo -e "${GREEN}Cleaning up storage directories...${NC}"

# Define directories
ORIGINAL_DIR="storage/original-videos"
PROCESSED_DIR="storage/processed-videos"

# Function to clean directory
clean_dir() {
    local dir=$1
    if [ -d "$dir" ]; then
        echo "  Cleaning $dir..."
        # Remove all files inside
        rm -rf "$dir"/*
        # Recreate .gitkeep if needed (optional, but good for git tracking)
        touch "$dir/.gitkeep"
    else
        echo "  Directory $dir does not exist, creating it..."
        mkdir -p "$dir"
        touch "$dir/.gitkeep"
    fi
}

clean_dir "$ORIGINAL_DIR"
clean_dir "$PROCESSED_DIR"

echo -e "${GREEN}Storage cleanup complete.${NC}"
echo ""

# 3. Database Cleanup via Docker
echo -e "${GREEN}Resetting database...${NC}"

# Check if frontend container is running
if ! docker compose ps | grep -q "bench-ai-ui_frontend_1"; then
    echo -e "${RED}Error: Frontend container is not running.${NC}"
    echo "Please run './scripts/start.sh' first to start the containers."
    exit 1
fi

echo "Running 'prisma migrate reset' inside frontend container..."
docker compose exec frontend npx prisma migrate reset --force

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database reset successfully.${NC}"
else
    echo -e "${RED}Database reset failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   ✅  RESET COMPLETE  ✅${NC}"
echo -e "${GREEN}   Application is now in a clean state.${NC}"
echo -e "${GREEN}======================================${NC}"
