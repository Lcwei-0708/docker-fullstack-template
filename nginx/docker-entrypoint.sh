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