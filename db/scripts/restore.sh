#!/bin/sh
set -eu

if [ -f /etc/backup.env ]; then
  # shellcheck disable=SC1091
  . /etc/backup.env
else
  export MYSQL_HOST=localhost
  export MYSQL_DATABASE="${MYSQL_DATABASE:?MYSQL_DATABASE is required}"
  export MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD is required}"
fi

usage() {
  cat <<EOF
Usage: restore.sh <backup.sql.gz>

Example:
  restore.sh /backups/2026-08-28_020001.sql.gz

Notes:
  - This script imports into the existing database on ${MYSQL_HOST}.
EOF
}

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

backup_file="$1"

if [ ! -f "${backup_file}" ]; then
  echo "ERROR: backup file not found: ${backup_file}"
  exit 1
fi

case "${backup_file}" in
  *.sql.gz) ;;
  *)
    echo "ERROR: backup file must be a .sql.gz file."
    exit 1
    ;;
esac

echo "Restoring ${backup_file} to ${MYSQL_DATABASE} on ${MYSQL_HOST}..."
gunzip -c "${backup_file}" | mariadb \
  --host="${MYSQL_HOST}" \
  --user=root \
  --password="${MYSQL_ROOT_PASSWORD}"

echo "Restore completed."
