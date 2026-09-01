[![Testing](https://github.com/Lcwei-0708/docker-fullstack-template/actions/workflows/test-backend.yml/badge.svg)](https://github.com/Lcwei-0708/docker-fullstack-template/actions/workflows/test-backend.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://lcwei-0708.github.io/docker-fullstack-template/coverage.json)](https://lcwei-0708.github.io/docker-fullstack-template/)

# Docker Fullstack Template

This project is a ready-to-use fullstack template that leverages Docker Compose to seamlessly integrate Nginx, React, FastAPI, and MariaDB. It provides a modern, production-like environment for rapid development and deployment of web applications with a clear separation between frontend and backend services.

## Features

- ⚛️ **Frontend**: Built with React, offering a fast and modern user interface.
- 🚀 **Backend**: Powered by FastAPI, with dependency management via uv (`pyproject.toml` + `uv.lock`).
- 🛢️ **Database**: Uses MariaDB for reliable and high-performance data storage.
- 🗄️ **Database Management**: phpMyAdmin provides an intuitive web-based interface for managing MariaDB databases.
- 🔀 **Reverse Proxy**: Nginx serves as a reverse proxy, efficiently routing traffic to the appropriate services.
- 📊 **Log Management**: Grafana provides log visualization and monitoring dashboards.
- 🐳 **Dockerized**: All services are containerized with Docker Compose for easy deployment.
- ⚙️ **CI/CD Testing**: Automated testing and generate coverage reporting with GitHub Actions.

## How to Use

#### 1. **Clone the repository**

```bash
git clone https://github.com/Lcwei-0708/docker-fullstack-template.git
```

#### 2. **Move to project**

```bash
cd docker-fullstack-template
```

#### 3. **Configure environment variables**

Copy `.env.example` to `.env`, then edit as needed:

```bash
cp .env.example .env
```

> Set the `COMPOSE_FILE` environment variable to switch between development and production modes.

#### 4. **Start the services**

First run or after code changes:

```bash
docker compose up -d --build
```

Subsequent runs (no code changes):

```bash
docker compose up -d
```

#### 5. **Stop the services**

```bash
docker compose down
```

#### 6. **Set up Nginx IP whitelist and SSL certificates**

On first start, `nginx/whitelist.conf` is auto-created from `whitelist.conf.example`. Edit that file if you need to restrict allowed IP addresses.

To enable SSL (HTTPS), configure SSL settings in `.env` and place certificates in `nginx/ssl`:

```bash
SSL_ENABLE=true
SSL_CERT_FILE=cert.pem
SSL_KEY_FILE=privkey.pem
```

```bash
nginx/ssl/
├── cert.pem       # Your SSL certificate
└── privkey.pem    # Your private key
```

> See [Nginx Docs](./nginx/README.md) for more details.

#### 7. **Enable pre-commit hooks (for local development)**

Run once if you want lint/format checks on commit. Requires [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/) on the host.

```bash
./scripts/setup-pre-commit.sh
```

Hooks auto-fix on commit: backend (Ruff format + lint fix), frontend (Prettier + ESLint fix), then re-stage if files changed.

Re-enable hooks:

```bash
pre-commit install
```

Disable hooks before commit:

```bash
pre-commit uninstall
```

## Documentation

| Directory | Link                                  |
| --------- | ------------------------------------- |
| Frontend  | [Docs](./frontend/README.md)          |
| Backend   | [Docs](./backend/README.md)           |
| Nginx     | [Docs](./nginx/README.md)             |
| CICD      | [Docs](./.github/workflows/README.md) |

## License

This project is licensed under the [MIT License](./LICENSE).
