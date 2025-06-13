FROM nginx:latest

# Install required tools: logrotate for log management, curl for downloading gomplate, gomplate for template processing
RUN apt-get update && apt-get install -y logrotate curl \
    && curl -L https://github.com/hairyhenderson/gomplate/releases/download/v3.11.5/gomplate_linux-amd64 -o /usr/local/bin/gomplate \
    && chmod +x /usr/local/bin/gomplate \
    && rm -rf /var/lib/apt/lists/*

# Copy logrotate configuration for nginx
COPY logrotate/nginx /etc/logrotate.d/nginx

# Copy main nginx configuration and template files
COPY nginx.conf /etc/nginx/nginx.conf
COPY templates/ /etc/nginx/templates/

# Copy custom entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set working directory
WORKDIR /etc/nginx

# Use root user to allow environment variable substitution and file operations
USER root

# Set entrypoint and default command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]