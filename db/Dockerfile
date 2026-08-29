FROM mariadb:12.3.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY scripts/backup.sh /scripts/backup.sh
COPY scripts/retention.sh /scripts/retention.sh
COPY scripts/restore.sh /scripts/restore.sh

RUN chmod +x /docker-entrypoint.sh /scripts/*.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["mariadbd"]
