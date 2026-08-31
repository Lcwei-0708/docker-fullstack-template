# Nginx

This Nginx configuration provides a secure, high-performance reverse proxy service for the full-stack application, handling both frontend and backend services.

## Tech Stack

- **Nginx**: High-performance web server and reverse proxy.
- **OpenSSL**: SSL/TLS implementation for secure connections.
- **Docker**: Containerization for development and deployment.
- **HTTP/2**: Modern protocol for improved performance.
- **WebSocket**: Support for real-time communication.
- **Templated Configuration**: Easily customizable Nginx configuration using environment variables and templates.

## Features

- 🔒 SSL/TLS encryption with modern cipher configurations
- 🌐 HTTP/2 support for improved performance
- 🔄 Intelligent routing for frontend and backend services
- 🛡️ IP whitelisting for enhanced security
- 📦 Static file serving in production mode
- 🔌 WebSocket support for real-time features
- 📝 Templated configuration for flexible and dynamic setup

## Quick Setup

### 1. IP Whitelist Setup

On first `docker compose up`, `whitelist.conf` is auto-created from
`whitelist.conf.example` (not tracked by git). Edit `whitelist.conf` to add allowed IPs:

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

Place your certificates in the `nginx/ssl` directory:
```bash
nginx/ssl/
├── cert.pem         # Your SSL certificate
└── privkey.pem      # Your private key
```