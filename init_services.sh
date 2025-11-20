#!/bin/bash

# ============================================================================
# Food4Kids - Backend & Database Full Reset Script
# This script tears down existing services, resets database, and initializes
# backend and database with a clean rebuild
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env file exists
if [ ! -f ./.env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

echo "🚀 Food4Kids - Full Reset (Clean Rebuild)"
echo "==========================================="
echo ""

echo -e "${BLUE}🧹 Tearing down existing services...${NC}"
docker-compose down --remove-orphans 2>/dev/null || echo "No existing containers"

echo -e "${YELLOW}🗑️  Removing database volume...${NC}"
docker volume rm food4kids_postgres_data 2>/dev/null || echo "Volume removed"

echo -e "${BLUE}📦 Building and starting services...${NC}"
docker-compose up --build -d backend db

echo -e "${YELLOW}⏳ Waiting for services...${NC}"
sleep 10

echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
until docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; do
    echo -e "${YELLOW}⏳ Database not ready, waiting...${NC}"
    sleep 3
done

echo -e "${GREEN}✅ Database is ready!${NC}"

echo -e "${BLUE}🔄 Running migrations...${NC}"
rm -rf backend/python/migrations/versions/__pycache__/ 2>/dev/null
docker-compose exec -T backend alembic upgrade head

echo -e "${GREEN}✅ Database migrations completed!${NC}"

echo ""
docker-compose ps

echo ""
echo -e "${GREEN}🎉 Backend & Database initialized!${NC}"
echo -e "${BLUE}📍 Services:${NC}"
echo -e "  • Backend:  http://localhost:8080"
echo -e "  • API Docs: http://localhost:8080/docs"
echo -e "  • Database: localhost:5432"
echo ""

echo -e "${YELLOW}📊 Streaming backend & database logs (Press Ctrl+C to stop):${NC}"
echo ""

# Stream logs from backend and database
docker-compose logs -f --tail=50 backend db