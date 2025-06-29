# Backend - FastAPI

This backend project is built with modern Python technologies to provide a robust, maintainable, and scalable API service.

## Tech Stack

- **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+ and full async/await support.
- **SQLAlchemy (Async)**: Powerful and flexible ORM for database operations, using async engine and sessions.
- **Alembic**: Database migrations tool for SQLAlchemy.  
  _See [Migration Docs](./migrations/README.md) for details._
- **Pydantic**: Data validation and settings management using Python type annotations.
- **Redis (Async)**: Used for rate limiting, integrated via `redis.asyncio`.
- **Uvicorn**: Lightning-fast ASGI server for running FastAPI applications.
- **Docker**: Containerization for development and deployment.
- **Asyncio**: Native Python async event loop for high concurrency and performance.
- **Testing**: Pytest (asyncio, coverage); fully isolated environment with a dedicated test database.  
  _See [Test Docs](./tests/README.md) for details._

## Features

- 🚀 High-performance async API with FastAPI
- 🗄️ Async database integration with SQLAlchemy and Alembic
- 🧩 Modular, scalable project structure
- 🔒 Middleware support (CORS, custom middlewares)
- 📝 Data validation with Pydantic
- ⚡ Full async/await support for endpoints and database operations
- 🧠 Redis integration for caching, rate limiting, and fast in-memory operations
- 🐳 Easy containerization with Docker
- ✅ Async Testing & coverage with a fully isolated test environment