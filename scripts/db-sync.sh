#!/usr/bin/env bash
# ==============================================================================
# FinanceTrackingApp Database Sync & Backup Manager
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"

# --- Nilai Default ---
DOCKER_CONTAINER="finance_db"
DB_USER="postgres"
DB_NAME="finance_db"
DB_PASS=""
HOST_DB_HOST="localhost"
HOST_DB_PORT="5432"

# Muat variabel dari .env jika tersedia
if [ -f "${PROJECT_ROOT}/.env" ]; then
  ENV_USER=$(grep "^POSTGRES_USER=" "${PROJECT_ROOT}/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  ENV_PASS=$(grep "^POSTGRES_PASSWORD=" "${PROJECT_ROOT}/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  ENV_DB=$(grep "^POSTGRES_DB=" "${PROJECT_ROOT}/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  ENV_HOST=$(grep "^HOST_DB_HOST=" "${PROJECT_ROOT}/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  ENV_PORT=$(grep "^HOST_DB_PORT=" "${PROJECT_ROOT}/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
  
  [ -n "$ENV_USER" ] && DB_USER="$ENV_USER"
  [ -n "$ENV_PASS" ] && DB_PASS="$ENV_PASS"
  [ -n "$ENV_DB" ] && DB_NAME="$ENV_DB"
  [ -n "$ENV_HOST" ] && HOST_DB_HOST="$ENV_HOST"
  [ -n "$ENV_PORT" ] && HOST_DB_PORT="$ENV_PORT"
fi

mkdir -p "${BACKUP_DIR}"

# --- Utility Functions ---
color_cyan()   { echo -e "\033[0;36m$*\033[0m"; }
color_green()  { echo -e "\033[0;32m$*\033[0m"; }
color_yellow() { echo -e "\033[0;33m$*\033[0m"; }
color_red()    { echo -e "\033[0;31m$*\033[0m"; }

check_docker_db() {
  if ! docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
    color_red "❌ Container '${DOCKER_CONTAINER}' tidak berjalan!"
    return 1
  fi
  return 0
}

check_host_db() {
  if ! PGPASSWORD="${DB_PASS}" pg_isready -h "${HOST_DB_HOST}" -p "${HOST_DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; then
    color_red "❌ Host PostgreSQL di ${HOST_DB_HOST}:${HOST_DB_PORT} tidak terjangkau!"
    return 1
  fi
  return 0
}

# --- Actions ---
do_status() {
  color_cyan "========================================================"
  color_cyan "      FinanceTrackingApp Database Status Monitor        "
  color_cyan "========================================================"
  echo ""
  
  echo -n "🐳 Docker Container DB (${DOCKER_CONTAINER}): "
  if check_docker_db >/dev/null 2>&1; then
    color_green "ONLINE"
    echo "   Database : ${DB_NAME} | User: ${DB_USER}"
  else
    color_red "OFFLINE"
  fi

  echo ""
  echo -n "🖥️  Host Native DB (${HOST_DB_HOST}:${HOST_DB_PORT}): "
  if check_host_db >/dev/null 2>&1; then
    color_green "ONLINE"
    echo "   Database : ${DB_NAME} | User: ${DB_USER}"
  else
    color_red "OFFLINE"
  fi

  echo ""
  echo "📦 Backup Tersimpan di ${BACKUP_DIR}:"
  local count=$(find "${BACKUP_DIR}" -maxdepth 1 -name "*.sql.gz" -o -name "*.sql" 2>/dev/null | wc -l)
  if [ "${count}" -eq 0 ]; then
    echo "   (Belum ada file backup)"
  else
    ls -lh "${BACKUP_DIR}" | grep -E '\.sql' | awk '{print "   • " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
  fi
  echo ""
}

do_backup() {
  check_docker_db || exit 1
  local TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  local BACKUP_FILE="${BACKUP_DIR}/finance_backup_${TIMESTAMP}.sql.gz"

  color_cyan "📦 Membuat snapshot backup dari Docker (${DOCKER_CONTAINER})..."
  docker exec "${DOCKER_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"
  
  local SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
  color_green "✅ Backup BERHASIL dibuat: ${BACKUP_FILE} (${SIZE})"
}

do_sync_to_host() {
  check_docker_db || exit 1
  check_host_db || exit 1

  color_cyan "🔄 Memulai Sinkronisasi: [Docker] ──► [Host]..."
  docker exec "${DOCKER_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | \
    PGPASSWORD="${DB_PASS}" psql -h "${HOST_DB_HOST}" -p "${HOST_DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null

  color_green "✅ Sinkronisasi SELESAI! Host DB kini 100% identik dengan Docker DB."
}

do_sync_to_docker() {
  check_docker_db || exit 1
  check_host_db || exit 1

  color_cyan "🔄 Memulai Sinkronisasi: [Host] ──► [Docker]..."
  PGPASSWORD="${DB_PASS}" pg_dump -h "${HOST_DB_HOST}" -p "${HOST_DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | \
    docker exec -i "${DOCKER_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" >/dev/null

  color_green "✅ Sinkronisasi SELESAI! Docker DB kini 100% identik dengan Host DB."
}

do_restore() {
  local FILE="$1"
  if [ -z "${FILE}" ] || [ ! -f "${FILE}" ]; then
    color_red "❌ File backup tidak ditemukan: ${FILE}"
    echo "Penggunaan: $0 restore <path_ke_file.sql.gz>"
    exit 1
  fi
  check_docker_db || exit 1

  color_yellow "⚠️  PERINGATAN: Memulihkan database akan menimpa seluruh data Docker!"
  read -p "Lanjutkan? (y/N): " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    color_cyan "Operasi dibatalkan."
    exit 0
  fi

  color_cyan "📥 Memulihkan data dari ${FILE}..."
  if [[ "${FILE}" == *.gz ]]; then
    gunzip -c "${FILE}" | docker exec -i "${DOCKER_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" >/dev/null
  else
    docker exec -i "${DOCKER_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${FILE}" >/dev/null
  fi
  color_green "✅ Pemulihan database BERHASIL!"
}

do_auto_sync_and_backup() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Memulai Auto Backup & Sync..."
  do_backup >/dev/null 2>&1
  do_sync_to_host >/dev/null 2>&1
  find "${BACKUP_DIR}" -name "finance_backup_*.sql.gz" -type f -mtime +7 -delete
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Selesai."
}

# --- Main Entrypoint ---
case "${1:-}" in
  status) do_status ;;
  backup) do_backup ;;
  sync-to-host|docker-to-host) do_sync_to_host ;;
  sync-to-docker|host-to-docker) do_sync_to_docker ;;
  restore) do_restore "$2" ;;
  auto-sync) do_auto_sync_and_backup ;;
  cron)
    color_yellow "Tambahkan cronjob ini (crontab -e):"
    echo "0 23 * * * ${PROJECT_ROOT}/scripts/db-sync.sh auto-sync >> ${PROJECT_ROOT}/backups/cron.log 2>&1"
    ;;
  *)
    color_cyan "Penggunaan:"
    echo "  $0 status                : Cek status database (Docker & Host)"
    echo "  $0 backup                : Buat snapshot backup (.sql.gz)"
    echo "  $0 sync-to-host          : Sinkronisasi data [Docker] ke [Host DB]"
    echo "  $0 sync-to-docker        : Sinkronisasi data [Host DB] ke [Docker]"
    echo "  $0 restore <file.sql.gz> : Restore database dari snapshot backup"
    echo "  $0 cron                  : Panduan instalasi cron job"
    exit 0
    ;;
esac
