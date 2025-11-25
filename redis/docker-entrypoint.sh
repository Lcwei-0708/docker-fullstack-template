#!/bin/sh

# Set timezone
if [ -n "$TZ" ]; then
  ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime
  echo "$TZ" > /etc/timezone
fi

# Fix /data directory permissions
chown -R 999:999 /data 2>/dev/null
chmod -R 755 /data 2>/dev/null

# Read configuration file
CONFIG_FILE="/usr/local/etc/redis/redis.conf"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: Redis configuration file not found at $CONFIG_FILE"
  exit 1
fi

# Set password in the configuration file
if [ -n "$REDIS_PASSWORD" ]; then
  cp "$CONFIG_FILE" /tmp/redis.conf
  
  # Remove existing requirepass lines
  grep -v "^requirepass" /tmp/redis.conf > /tmp/redis.conf.tmp || cp /tmp/redis.conf /tmp/redis.conf.tmp
  
  # Add requirepass at the beginning
  printf "requirepass %s\n\n" "$REDIS_PASSWORD" > /tmp/redis.conf
  cat /tmp/redis.conf.tmp >> /tmp/redis.conf
  rm -f /tmp/redis.conf.tmp
  
  CONFIG_FILE="/tmp/redis.conf"
fi

# Start Redis
exec redis-server "$CONFIG_FILE"