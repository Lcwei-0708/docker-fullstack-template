#!/bin/sh
set -eu

. /etc/backup.env

BACKUP_DIR="/backups"
LOG_DIR="${BACKUP_DIR}/logs"
RETENTION_DAYS="${DB_BACKUP_RETENTION_DAYS:-7}"
LOG_RETENTION_DAYS="${DB_BACKUP_LOG_RETENTION_DAYS:-7}"

LOG_COMPONENT="backup.retention"

log() {
  level="$1"
  shift
  printf '%s [%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S,%3N')" "${level}" "${LOG_COMPONENT}" "$*"
}

mkdir -p "${BACKUP_DIR}" 2>/dev/null || exit 0

# Remove legacy files from older backup scripts
rm -f "${BACKUP_DIR}/.state" "${BACKUP_DIR}/backup.log"

now_epoch="$(date +%s)"
backup_cutoff_epoch=$((now_epoch - RETENTION_DAYS * 86400))
log_cutoff_epoch=$((now_epoch - LOG_RETENTION_DAYS * 86400))

removed_backups=0
removed_logs=0

for item in "${BACKUP_DIR}"/*.sql.gz; do
  [ -e "${item}" ] || continue

  file_epoch="$(stat -c '%Y' "${item}")"
  if [ "${file_epoch}" -lt "${backup_cutoff_epoch}" ]; then
    log "INFO" "Removing expired backup"
    log "INFO" "Path: ${item}"
    rm -f "${item}"
    removed_backups=$((removed_backups + 1))
  fi
done

if [ -d "${LOG_DIR}" ]; then
  for item in "${LOG_DIR}"/*.log; do
    [ -e "${item}" ] || continue

    file_epoch="$(stat -c '%Y' "${item}")"
    if [ "${file_epoch}" -lt "${log_cutoff_epoch}" ]; then
      log "INFO" "Removing expired log"
      log "INFO" "Path: ${item}"
      rm -f "${item}"
      removed_logs=$((removed_logs + 1))
    fi
  done
fi

if [ "${removed_backups}" -gt 0 ] || [ "${removed_logs}" -gt 0 ]; then
  log "INFO" "Retention cleanup finished"
  log "INFO" "Removed backups: ${removed_backups}"
  log "INFO" "Removed logs: ${removed_logs}"
fi
