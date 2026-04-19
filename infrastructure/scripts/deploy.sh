#!/bin/bash
# TukiJuris -- Deploy Update
# Usage: bash infrastructure/scripts/deploy.sh [--no-migrate]

set -euo pipefail

APP_DIR="/opt/tukijuris/app"
BACKUP_DIR="/opt/tukijuris/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== TukiJuris Deploy -- $TIMESTAMP ==="

cd "$APP_DIR"

# 1. Pre-deploy backup
echo "--- Backing up database ---"
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U postgres agente_derecho | gzip > "$BACKUP_DIR/pre-deploy-$TIMESTAMP.sql.gz"
echo "Backup saved: $BACKUP_DIR/pre-deploy-$TIMESTAMP.sql.gz"

# 2. Pull latest code
echo "--- Pulling latest code ---"
git pull origin main

# 3. Build new images
echo "--- Building images ---"
docker compose -f docker-compose.prod.yml build

# 4. Run migrations (unless --no-migrate flag)
if [[ "${1:-}" != "--no-migrate" ]]; then
    echo "--- Running migrations ---"
    docker compose -f docker-compose.prod.yml exec api alembic upgrade head
    echo "Migrations complete"
else
    echo "--- Skipping migrations (--no-migrate) ---"
fi

# 5. Rolling restart (zero-downtime attempt)
echo "--- Restarting services ---"
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 6. Wait for health check
echo "--- Waiting for health check ---"
HEALTHY=0
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "  API is healthy!"
        HEALTHY=1
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

if [ "$HEALTHY" -eq 0 ]; then
    echo "ERROR: API did not become healthy after 60s"
    echo "Check logs: docker compose -f docker-compose.prod.yml logs api --tail 50"
    exit 1
fi

# 7. Show status
echo ""
echo "=== Deploy complete ==="
docker compose -f docker-compose.prod.yml ps
echo ""
curl -s http://localhost:8000/api/health | jq .
