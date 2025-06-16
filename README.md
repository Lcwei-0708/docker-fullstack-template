# Docker Fullstack Template

This project is a ready-to-use fullstack template that leverages Docker Compose to seamlessly integrate Nginx, React, FastAPI, and MariaDB. It provides a modern, production-like environment for rapid development and deployment of web applications with a clear separation between frontend and backend services.


## Features

- ⚛️ **Frontend**: Built with React, offering a fast and modern user interface.
- 🚀 **Backend**: Powered by FastAPI, providing a robust and flexible API layer.
- 🛢️ **Database**: Uses MariaDB for reliable and high-performance data storage.
- 🔀 **Reverse Proxy**: Nginx serves as a reverse proxy, efficiently routing traffic to the appropriate services.
- 🐳 **Dockerized**: All services are containerized and orchestrated with Docker Compose, ensuring easy setup and consistent environments across development and production.


## How to Use

1. **Clone the repository**

   ```bash
   git clone https://github.com/Lcwei-0708/docker-fullstack-template.git
   ```

2. **Move to project**

   ```bash
   cd docker-fullstack-template
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and edit as needed.

   ```bash
   cp .env.example .env
   ```

   > Set the `COMPOSE_FILE` environment variable to switch between development and production modes.

4. **Set up Nginx SSL certificates and IP whitelist**

   - Place your SSL certificates in the `nginx/ssl` directory
   - Copy `whitelist.conf.example` to `whitelist.conf` and edit as needed.

      ```bash
      cp nginx/whitelist.conf.example nginx/whitelist.conf
      ```
  
   > See [Nginx Docs](./nginx/README.md) for more details.

5. **Start the services**

   ```bash
   docker compose up -d
   ```

6. **Stop the services**

   ```bash
   docker compose down
   ```

## Documentation

| Directory    | Link                            |
|--------------|---------------------------------|
| Frontend     | [Docs](./frontend/README.md)    |
| Backend      | [Docs](./backend/README.md)     |
| Nginx        | [Docs](./nginx/README.md)       |


## License

This project is licensed under the [MIT License](./LICENSE).