#!/bin/sh

# Create log directory if it doesn't exist
mkdir -p /var/log/nginx

# Set correct permissions and ownership for log directory
chown -R root:root /var/log/nginx
chmod 755 /var/log/nginx

# Ensure log files exist with correct permissions
touch /var/log/nginx/nginx.log
touch /var/log/nginx/error.log
chown root:root /var/log/nginx/*.log
chmod 644 /var/log/nginx/*.log

# Set correct permissions for logrotate configuration
chmod 644 /etc/logrotate.d/nginx

# Overwrite /etc/crontab with correct content and logrotate job
cat > /etc/crontab <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

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