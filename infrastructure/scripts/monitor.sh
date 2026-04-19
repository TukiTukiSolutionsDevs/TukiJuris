#!/bin/bash
# TukiJuris -- Quick System Monitor
# Usage: bash infrastructure/scripts/monitor.sh

APP_DIR="/opt/tukijuris/app"

# Change to app dir if it exists; fall back to current dir (local dev)
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
fi

echo "=== TukiJuris System Monitor ==="
echo "$(date)"
echo ""

# Container status
echo "--- Containers ---"
docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo "  Could not reach Docker"
echo ""

# API health
echo "--- API Health ---"
curl -s --max-time 5 http://localhost:8000/api/health | jq . 2>/dev/null || echo "  API unreachable"
echo ""

# DB + pgvector readiness
echo "--- Database ---"
curl -s --max-time 5 http://localhost:8000/api/health/ready | jq . 2>/dev/null || echo "  DB check failed"
echo ""

# Knowledge base stats
echo "--- Knowledge Base ---"
curl -s --max-time 5 http://localhost:8000/api/health/knowledge | jq . 2>/dev/null || echo "  KB check failed"
echo ""

# Request/response metrics
echo "--- Metrics ---"
curl -s --max-time 5 http://localhost:8000/api/health/metrics | jq .metrics 2>/dev/null || echo "  Metrics unavailable"
echo ""

# Disk usage
echo "--- Disk ---"
df -h / | tail -1
echo ""

# Memory
echo "--- Memory ---"
free -h | head -2
echo ""

# Docker disk usage
echo "--- Docker Disk ---"
docker system df
echo ""

# Backup status
echo "--- Backups ---"
BACKUP_DIR="/opt/tukijuris/backups"
if [ -d "$BACKUP_DIR" ]; then
    LATEST=$(ls -t "$BACKUP_DIR"/db-*.dump.gz 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo "  Latest: $LATEST ($(du -h "$LATEST" | cut -f1))"
        echo "  Total backups: $(ls "$BACKUP_DIR"/db-*.dump.gz 2>/dev/null | wc -l)"
    else
        echo "  No backups found in $BACKUP_DIR"
    fi
else
    echo "  Backup dir not found: $BACKUP_DIR"
fi
