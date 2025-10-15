[![Testing](https://github.com/Lcwei-0708/cicd-test/actions/workflows/test_backend.yml/badge.svg)](https://github.com/Lcwei-0708/cicd-test/actions/workflows/test_backend.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://lcwei-0708.github.io/cicd-test/coverage.json)](https://lcwei-0708.github.io/cicd-test/)


# Docker Fullstack Template

This project is a ready-to-use fullstack template that leverages Docker Compose to seamlessly integrate Nginx, React, FastAPI, and MariaDB. It provides a modern, production-like environment for rapid development and deployment of web applications with a clear separation between frontend and backend services.


## Features

- ⚛️ **Frontend**: Built with React, offering a fast and modern user interface.
- 🚀 **Backend**: Powered by FastAPI, providing a robust and flexible API layer.
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

   Copy `.env.example` to `.env` and edit as needed.

   ```bash
   cp .env.example .env
   ```

   > Set the `COMPOSE_FILE` environment variable to switch between development and production modes.

#### 4. **Set up Nginx IP whitelist and SSL certificates**

   - Copy `whitelist.conf.example` to `whitelist.conf` and edit as needed.

      ```bash
      cp nginx/whitelist.conf.example nginx/whitelist.conf
      ```
  
   - To enable SSL (HTTPS), you need to configure SSL settings in your `.env` file and place your SSL certificates in the `nginx/ssl` directory.
      - Env setting: 
         ```bash
         SSL_ENABLE=true
         SSL_CERT_FILE=cert.pem
         SSL_KEY_FILE=privkey.pem
         ```

      - Place your certificates in the `nginx/ssl` directory:
         ```bash
         nginx/ssl/
         ├── cert.pem       # Your SSL certificate
         └── privkey.pem    # Your private key
         ```
   
   > See [Nginx Docs](./nginx/README.md) for more details.

#### 5. **Start the services**

   First run or after code changes:

   ```bash
   docker compose up -d --build
   ```

   Subsequent runs (no code changes):

   ```bash
   docker compose up -d
   ```

#### 6. **Stop the services**

   ```bash
   docker compose down
   ```

## Documentation

| Directory    | Link                                      |
|--------------|-------------------------------------------|
| Frontend     | [Docs](./frontend/README.md)              |
| Backend      | [Docs](./backend/README.md)               |
| Nginx        | [Docs](./nginx/README.md)                 |
| CICD         | [Docs](./.github/README.md)     |


## License

This project is licensed under the [MIT License](./LICENSE).