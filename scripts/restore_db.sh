#!/usr/bin/env bash
# Restore de un dump pg_dump -Fc generado por backup_db.sh.
# Para usar en máquina nueva luego de levantar `docker compose up -d`.
#
# Uso:
#     ./scripts/restore_db.sh data/db-backups/tukijuris-2026-06-24-1830.dump
#     ./scripts/restore_db.sh tukijuris-2026-06-24-1830.dump   # busca en data/db-backups/
#
# ⚠ DESTRUCTIVO: descarta cualquier dato existente en la BD agente_derecho.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Uso: $0 <ruta-al-dump>"
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR_HOST="${ROOT_DIR}/data/db-backups"
BACKUP_DIR_CONTAINER="/backups"
DB_CONTAINER="${DB_CONTAINER:-tukijuris-db-1}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-agente_derecho}"

input="$1"

# Si pasaron sólo el filename, resolver desde data/db-backups/
if [[ ! -f "${input}" && -f "${BACKUP_DIR_HOST}/${input}" ]]; then
    input="${BACKUP_DIR_HOST}/${input}"
fi

if [[ ! -f "${input}" ]]; then
    echo "❌ Archivo no encontrado: ${input}"
    exit 1
fi

filename="$(basename "${input}")"

echo "→ Container: ${DB_CONTAINER}"
echo "→ Restore desde: ${input}"
echo "⚠  Esto BORRARÁ los datos actuales de '${DB_NAME}'."
read -r -p "Continuar? [y/N] " confirm
if [[ "${confirm,,}" != "y" && "${confirm,,}" != "yes" ]]; then
    echo "Cancelado."
    exit 0
fi

# Drop & recreate database
echo "→ Drop & recreate ${DB_NAME}..."
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"

# Restore
echo "→ Restoring..."
docker exec "${DB_CONTAINER}" pg_restore \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    --verbose \
    "${BACKUP_DIR_CONTAINER}/${filename}" 2>&1 | tail -20

echo ""
echo "✓ Restore completo. Verificá con:"
echo "  docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'SELECT COUNT(*) FROM document_chunks;'"
