#!/bin/bash
# Deploy: pull → build → migrate → status
# Run on server: bash scripts/deploy.sh
# Or: cd /opt/remnatgseller && bash scripts/deploy.sh

set -e

COMPOSE_FILES="-f docker-compose.prod.internal.yml -f docker-compose.build.yml"
SERVICE="remnatgseller"

echo "=== 1. Git pull ==="
git pull

echo ""
echo "=== 2. Docker build & up ==="
docker compose $COMPOSE_FILES up -d --build

echo ""
echo "=== 3. Wait for app to start ==="
sleep 5

echo ""
echo "=== 4. Run migration ==="
docker compose $COMPOSE_FILES exec -T $SERVICE alembic upgrade head

echo ""
echo "=== 5. Status ==="
docker compose $COMPOSE_FILES ps

echo ""
echo "=== Done. Test: Users → select user → Audit ==="
