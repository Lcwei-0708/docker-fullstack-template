#!/bin/sh

# Set timezone
if [ -n "$TZ" ]; then
  ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime
  echo "$TZ" > /etc/timezone
else
  # Default timezone
  ln -sf "/usr/share/zoneinfo/UTC" /etc/localtime
  echo "UTC" > /etc/timezone
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/nginx

# Set correct permissions and ownership for all nginx-related directories and files
chown -R root:root /var/log/nginx /etc/logrotate.d /var/lib/logrotate
chmod 755 /var/log/nginx /etc/logrotate.d /var/lib/logrotate

# Ensure log files exist with correct permissions
touch /var/log/nginx/nginx.log /var/log/nginx/error.log
chown root:root /var/log/nginx/*.log /etc/logrotate.d/nginx
chmod 644 /var/log/nginx/*.log /etc/logrotate.d/nginx

# Setup Redis Insight authentication if environment variables are provided
if [ ! -z "$REDIS_INSIGHT_USER" ] && [ ! -z "$REDIS_INSIGHT_PASSWORD" ]; then
    echo "Setting up Redis Insight authentication..."
    # htpasswd should already be installed via Dockerfile
    if command -v htpasswd >/dev/null 2>&1; then
        # Create password file
        htpasswd -cb /etc/nginx/.htpasswd "$REDIS_INSIGHT_USER" "$REDIS_INSIGHT_PASSWORD"
        echo "Redis Insight authentication configured for user: $REDIS_INSIGHT_USER"
    else
        echo "ERROR: htpasswd command not found. Please ensure apache2-utils is installed in Dockerfile."
        exit 1
    fi
fi

# Overwrite /etc/crontab with correct content and logrotate job
cat > /etc/crontab <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
TZ=${TZ}

0 0 * * * root /usr/sbin/logrotate -f -v /etc/logrotate.conf > /tmp/logrotate_cron.log 2>&1
EOF

# Start cron service
service cron start

# Process all template files
for template in /etc/nginx/templates/*.conf; do
    if [ -f "$template" ]; then
        filename=$(basename "$template")
        gomplate -f "$template" -o "/etc/nginx/custom.d/${filename}"
    fi
done

# Start nginx
exec nginx -g 'daemon off;'