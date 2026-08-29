#!/bin/sh
set -eu

. /etc/backup.env

BACKUP_DIR="/backups"
RUN_ID=""
RUN_LOG=""
START_EPOCH=""
BACKUP_STATUS="SUCCESS"

LOG_COMPONENT="backup"

log() {
  level="$1"
  shift
  printf '%s [%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S,%3N')" "${level}" "${LOG_COMPONENT}" "$*"
}

log_stderr() {
  level="$1"
  shift
  printf '%s [%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S,%3N')" "${level}" "${LOG_COMPONENT}" "$*" >&2
}

human_size() {
  size="$1"
  if command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec-i --suffix=B "${size}" 2>/dev/null || echo "${size} bytes"
  else
    echo "${size} bytes"
  fi
}

format_duration() {
  seconds="$1"
  if [ "${seconds}" -lt 60 ]; then
    printf '%ss' "${seconds}"
  else
    minutes=$((seconds / 60))
    remain=$((seconds % 60))
    printf '%sm %ss' "${minutes}" "${remain}"
  fi
}

setup_run_log() {
  LOG_DIR="${BACKUP_DIR}/logs"
  RUN_ID="$(date '+%Y-%m-%d_%H%M%S')"
  RUN_LOG="${LOG_DIR}/${RUN_ID}.log"
  START_EPOCH="$(date +%s)"
  exec >> "${RUN_LOG}" 2>&1
  log "INFO" "Backup run started"
  log "INFO" "Log file: ${RUN_LOG}"
}

ensure_backup_dir() {
  if ! mkdir -p "${BACKUP_DIR}/logs"; then
    log_stderr "ERROR" "Failed to create backup directories under ${BACKUP_DIR}"
    log_stderr "ERROR" "The bind mount may be broken if the host backup path was removed after the container started"
    log_stderr "ERROR" "Recreate the host backup path and run: docker compose up -d --force-recreate mariadb"
    exit 1
  fi

  if [ ! -d "${BACKUP_DIR}" ] || [ ! -w "${BACKUP_DIR}" ]; then
    log_stderr "ERROR" "Backup directory is missing or not writable: ${BACKUP_DIR}"
    exit 1
  fi
}

wait_for_mariadb() {
  log "INFO" "Checking MariaDB connection"

  retries=30
  while [ "${retries}" -gt 0 ]; do
    if mariadb-admin \
      --host="${MYSQL_HOST}" \
      --user=root \
      --password="${MYSQL_ROOT_PASSWORD}" \
      ping >/dev/null 2>&1; then
      log "INFO" "MariaDB is reachable"
      log "INFO" "Host: ${MYSQL_HOST}"
      return 0
    fi
    retries=$((retries - 1))
    sleep 2
  done

  log "ERROR" "MariaDB is not reachable"
  log "ERROR" "Host: ${MYSQL_HOST}"
  BACKUP_STATUS="FAILED"
  return 1
}

get_mariadb_version() {
  mariadb \
    --host="${MYSQL_HOST}" \
    --user=root \
    --password="${MYSQL_ROOT_PASSWORD}" \
    --batch --skip-column-names \
    -e "SELECT VERSION();" 2>/dev/null || echo "unknown"
}

get_database_size() {
  mariadb \
    --host="${MYSQL_HOST}" \
    --user=root \
    --password="${MYSQL_ROOT_PASSWORD}" \
    --batch --skip-column-names \
    -e "
      SELECT COALESCE(ROUND(SUM(data_length + index_length)), 0)
      FROM information_schema.tables
      WHERE table_schema = '${MYSQL_DATABASE}';
    " 2>/dev/null || echo "0"
}

log_dump_stderr() {
  dump_stderr="$1"

  if [ ! -s "${dump_stderr}" ]; then
    return 0
  fi

  while IFS= read -r line || [ -n "${line}" ]; do
    log "WARN" "${line}"
  done < "${dump_stderr}"

  if grep -q "mariadb-upgrade" "${dump_stderr}" 2>/dev/null \
    || grep -q "mysql.proc is wrong" "${dump_stderr}" 2>/dev/null \
    || grep -q "(1558)" "${dump_stderr}" 2>/dev/null; then
    BACKUP_STATUS="SUCCESS_WITH_WARNINGS"
    log "WARN" "Stored procedures, functions, or events may be missing from this backup"
    log "WARN" "Run mariadb-upgrade to fix system tables"
  elif grep -qi "error" "${dump_stderr}" 2>/dev/null; then
    BACKUP_STATUS="SUCCESS_WITH_WARNINGS"
  fi
}

run_backup() {
  backup_file="${BACKUP_DIR}/${RUN_ID}.sql.gz"
  dump_sql="${BACKUP_DIR}/.${RUN_ID}.sql.tmp"
  dump_stderr="$(mktemp)"
  dump_started_epoch="$(date +%s)"

  log "INFO" "Database: ${MYSQL_DATABASE}"

  db_size="$(get_database_size)"
  if [ "${db_size}" != "0" ]; then
    log "INFO" "Database size: $(human_size "${db_size}")"
  fi

  log "INFO" "MariaDB version: $(get_mariadb_version)"
  log "INFO" "Exporting database"
  log "INFO" "Backup path: ${backup_file}"

  set +e
  mariadb-dump \
    --host="${MYSQL_HOST}" \
    --user=root \
    --password="${MYSQL_ROOT_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --hex-blob \
    --databases "${MYSQL_DATABASE}" \
    > "${dump_sql}" 2>"${dump_stderr}"
  dump_rc=$?
  set -e

  dump_duration=$(( $(date +%s) - dump_started_epoch ))

  if [ ! -s "${dump_sql}" ]; then
    BACKUP_STATUS="FAILED"
    log "ERROR" "Database export failed"
    log "ERROR" "Exit code: ${dump_rc}"
    log "ERROR" "Duration: $(format_duration "${dump_duration}")"
    log_dump_stderr "${dump_stderr}"
    rm -f "${dump_sql}" "${dump_stderr}"
    return 1
  fi

  dump_bytes="$(stat -c '%s' "${dump_sql}")"

  if [ "${dump_rc}" -ne 0 ]; then
    log "WARN" "Database export finished with warnings"
    log_dump_stderr "${dump_stderr}"
  else
    log "INFO" "Database export finished"
    if [ -s "${dump_stderr}" ]; then
      log_dump_stderr "${dump_stderr}"
    fi
  fi

  log "INFO" "Export duration: $(format_duration "${dump_duration}")"
  log "INFO" "Export size: $(human_size "${dump_bytes}")"

  compress_started_epoch="$(date +%s)"
  log "INFO" "Compressing backup"

  set +e
  gzip -c "${dump_sql}" > "${backup_file}"
  gzip_rc=$?
  set -e

  rm -f "${dump_sql}" "${dump_stderr}"

  compress_duration=$(( $(date +%s) - compress_started_epoch ))

  if [ "${gzip_rc}" -ne 0 ]; then
    BACKUP_STATUS="FAILED"
    log "ERROR" "Compression failed"
    log "ERROR" "Exit code: ${gzip_rc}"
    rm -f "${backup_file}"
    return 1
  fi

  if [ ! -s "${backup_file}" ]; then
    BACKUP_STATUS="FAILED"
    log "ERROR" "Backup file is empty after compression"
    rm -f "${backup_file}"
    return 1
  fi

  backup_bytes="$(stat -c '%s' "${backup_file}")"
  total_duration=$(( $(date +%s) - START_EPOCH ))

  log "INFO" "Compression finished"
  log "INFO" "Compression duration: $(format_duration "${compress_duration}")"
  log "INFO" "Backup size: $(human_size "${backup_bytes}")"
  log "INFO" "Backup completed"
  log "INFO" "Backup path: ${backup_file}"
  log "INFO" "Total duration: $(format_duration "${total_duration}")"
  log "INFO" "Status: ${BACKUP_STATUS}"

  BACKUP_FILE="${backup_file}"
  BACKUP_BYTES="${backup_bytes}"
}

ensure_backup_dir
setup_run_log

if ! wait_for_mariadb; then
  exit 1
fi

if ! run_backup; then
  exit 1
fi

/scripts/retention.sh

if [ "${BACKUP_STATUS}" = "FAILED" ]; then
  exit 1
fi

exit 0
