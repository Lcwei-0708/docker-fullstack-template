#!/bin/sh
set -eu

if [ -n "${TZ:-}" ]; then
  ln -sf "/usr/share/zoneinfo/${TZ}" /etc/localtime
  echo "${TZ}" > /etc/timezone
fi

setup_backup() {
  cat > /etc/backup.env <<EOF
export TZ="${TZ:-UTC}"
export MYSQL_HOST=localhost
export MYSQL_DATABASE="${MYSQL_DATABASE}"
export MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}"
export DB_BACKUP_RETENTION_DAYS="${DB_BACKUP_RETENTION_DAYS:-7}"
export DB_BACKUP_LOG_RETENTION_DAYS="${DB_BACKUP_LOG_RETENTION_DAYS:-7}"
EOF

  SCHEDULE="${DB_BACKUP_SCHEDULE:-0 2 * * *}"
  printf '%s . /etc/backup.env && /scripts/backup.sh\n' "${SCHEDULE}" | crontab -

  cron

  echo "DB backup scheduler started."
  echo "  schedule: ${SCHEDULE}"
  echo "  retention: ${DB_BACKUP_RETENTION_DAYS:-7} day(s)"
  echo "  log retention: ${DB_BACKUP_LOG_RETENTION_DAYS:-7} day(s)"
  echo "  format: mariadb-dump -> sql.gz"
}

if [ "${DB_BACKUP_ENABLE:-true}" = "true" ]; then
  setup_backup
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"
