# Nginx

This Nginx configuration provides a secure, high-performance reverse proxy service for the full-stack application, handling both frontend and backend services.

## Tech Stack

- **Nginx**: High-performance web server and reverse proxy.
- **TLS / HTTPS**: Certificate-based encryption via nginx (certs in `nginx/certs`).
- **Docker**: Containerization for development and deployment.
- **HTTP/2**: Modern protocol for improved performance.
- **WebSocket**: Support for real-time communication.
- **Templated Configuration**: gomplate templates rendered at container start.

## Structure

```text
nginx/
├── templates/                 # Server templates (frontend, backend, …)
├── custom.d/                  # Generated configs from templates at start
├── certs/                     # SSL certificate and private key
├── logrotate/                 # Logrotate rules for nginx logs
├── nginx.conf                 # Main nginx config (logging, whitelist geo)
├── whitelist.conf.example     # Whitelist template (copied on first start)
├── docker-entrypoint.sh       # Bootstrap: templates, whitelist, cron
└── Dockerfile
```

## Quick Setup

### 1. IP Whitelist Setup

On first `docker compose up`, `whitelist.conf` is auto-created from
`whitelist.conf.example`. Edit `whitelist.conf` to add allowed IPs:

```bash
# Example entries in whitelist.conf:
192.168.1.0/24 1;    # Allow specific subnet
192.168.0.1 1;       # Allow specific IP
```

Default mode allows all requests (`default 1;` in `nginx.conf`). To enforce the whitelist,
change `nginx.conf` to `default 0;`.

### 2. SSL Certificates Setup

To enable SSL (HTTPS), you need to configure SSL settings in your `.env` file and place your SSL certificates.

**Basic setup:**

```env
SSL_ENABLE=true
SSL_CERT_FILE=cert.pem
SSL_KEY_FILE=privkey.pem
```

Place your certificates in the `nginx/certs` directory:

```bash
nginx/certs/
├── cert.pem         # Your SSL certificate
└── privkey.pem      # Your private key
```
