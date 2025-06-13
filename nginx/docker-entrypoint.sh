#!/bin/sh

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