#!/usr/bin/env bash
# Backup completo de la base de datos `agente_derecho` en formato custom (pg_dump -Fc).
# Genera un archivo timestampeado en data/db-backups/ desde el host.
#
# Uso:
#     ./scripts/backup_db.sh                # snapshot timestampeado
#     ./scripts/backup_db.sh nombre-extra   # añade tag al filename
#
# El volumen `./data/db-backups:/backups` está montado en el container `db`
# (ver docker-compose.yml), así que pg_dump escribe directo al host.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR_HOST="${ROOT_DIR}/data/db-backups"
BACKUP_DIR_CONTAINER="/backups"
DB_CONTAINER="${DB_CONTAINER:-tukijuris-db-1}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-agente_derecho}"

mkdir -p "${BACKUP_DIR_HOST}"

timestamp="$(date +%Y-%m-%d-%H%M)"
tag="${1:-}"
suffix="${tag:+-${tag}}"
filename="tukijuris-${timestamp}${suffix}.dump"
target="${BACKUP_DIR_CONTAINER}/${filename}"

echo "→ Backup ${DB_NAME} desde ${DB_CONTAINER}..."
docker exec "${DB_CONTAINER}" pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -Fc \
    -Z 6 \
    -f "${target}"

host_path="${BACKUP_DIR_HOST}/${filename}"
size="$(du -h "${host_path}" 2>/dev/null | cut -f1 || echo '?')"
echo "✓ Backup escrito: ${host_path} (${size})"
echo ""
echo "Para restaurar en otra máquina:"
echo "  ./scripts/restore_db.sh ${filename}"
