#!/bin/bash
# TukiJuris -- Database Restore
# Usage: bash infrastructure/scripts/restore.sh <backup-file>

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup-file>"
    echo ""
    echo "Available backups:"
    ls -lh /opt/tukijuris/backups/db-*.dump.gz 2>/dev/null || echo "  No daily backups found"
    ls -lh /opt/tukijuris/backups/pre-deploy-*.sql.gz 2>/dev/null || echo "  No pre-deploy backups found"
    exit 1
fi

BACKUP_FILE="$1"
APP_DIR="/opt/tukijuris/app"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

cd "$APP_DIR"

echo "=== TukiJuris Database Restore ==="
echo "WARNING: This will REPLACE the current database!"
echo "Backup: $BACKUP_FILE"
read -r -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# 1. Stop API (prevent writes during restore)
echo "--- Stopping API ---"
docker compose -f docker-compose.prod.yml stop api

# 2. Decompress if gzipped
RESTORE_FILE="$BACKUP_FILE"
DECOMPRESSED=0
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "--- Decompressing ---"
    RESTORE_FILE="${BACKUP_FILE%.gz}"
    gunzip -k "$BACKUP_FILE"
    DECOMPRESSED=1
fi

# 3. Restore based on file format
echo "--- Restoring database ---"
if [[ "$RESTORE_FILE" == *.dump ]]; then
    # pg_restore custom format (from backup.sh)
    docker compose -f docker-compose.prod.yml exec -T db \
        pg_restore -U postgres -d agente_derecho --clean --if-exists < "$RESTORE_FILE"
elif [[ "$RESTORE_FILE" == *.sql ]]; then
    # Plain SQL format (from deploy pre-deploy backups)
    docker compose -f docker-compose.prod.yml exec -T db \
        psql -U postgres -d agente_derecho < "$RESTORE_FILE"
else
    echo "ERROR: Unknown backup format. Expected .dump or .sql (optionally .gz)"
    # Cleanup before exit
    if [ "$DECOMPRESSED" -eq 1 ]; then
        rm -f "$RESTORE_FILE"
    fi
    docker compose -f docker-compose.prod.yml start api
    exit 1
fi

# 4. Cleanup decompressed file
if [ "$DECOMPRESSED" -eq 1 ]; then
    rm -f "$RESTORE_FILE"
    echo "--- Cleaned up decompressed file ---"
fi

# 5. Restart API
echo "--- Restarting API ---"
docker compose -f docker-compose.prod.yml start api

# 6. Health check
echo "--- Waiting for API health ---"
sleep 5
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    curl -s http://localhost:8000/api/health | jq .
    echo ""
    echo "=== Restore complete ==="
else
    echo "WARNING: API health check failed after restore. Check logs:"
    echo "  docker compose -f docker-compose.prod.yml logs api --tail 50"
    exit 1
fi
