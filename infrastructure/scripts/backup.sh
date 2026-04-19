#!/bin/bash
# TukiJuris -- Database Backup
# Cron: 0 2 * * * /opt/tukijuris/app/infrastructure/scripts/backup.sh

set -euo pipefail

APP_DIR="/opt/tukijuris/app"
BACKUP_DIR="/opt/tukijuris/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30
LOG_FILE="/var/log/tukijuris-backup.log"

cd "$APP_DIR"

# 1. Dump database (custom format for pg_restore compatibility)
echo "$(date): Starting backup..."
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U postgres -Fc agente_derecho > "$BACKUP_DIR/db-$TIMESTAMP.dump"

# 2. Compress
gzip "$BACKUP_DIR/db-$TIMESTAMP.dump"
SIZE=$(du -h "$BACKUP_DIR/db-$TIMESTAMP.dump.gz" | cut -f1)
echo "$(date): Backup complete -- $SIZE -- $BACKUP_DIR/db-$TIMESTAMP.dump.gz"

# 3. Cleanup old backups (idempotent -- only deletes if files exist)
find "$BACKUP_DIR" -name "db-*.dump.gz" -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name "pre-deploy-*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "$(date): Cleaned backups older than $KEEP_DAYS days"

# 4. Log
echo "$(date): backup size=$SIZE file=db-$TIMESTAMP.dump.gz" >> "$LOG_FILE"
