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
- **uv**: Fast Python package and project manager (`pyproject.toml` + `uv.lock`).
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

## Lint & format

### Standards

| Item | Value |
|------|--------|
| Config | [`pyproject.toml`](./pyproject.toml) — `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]` |
| Formatter | [Ruff format](https://docs.astral.sh/ruff/formatter/) (Black-compatible) |
| Line length | 100 |
| Indent | 4 spaces; tabs are rewritten on format |
| Quotes | Double quotes |
| Target Python | 3.14 |

| Rule set | Source | Purpose |
|----------|--------|---------|
| `E` | pycodestyle | PEP 8 style |
| `F` | Pyflakes | Unused imports, syntax issues |
| `I` | isort | Import order |
| `UP` | pyupgrade | Modern Python syntax |
| `B` | flake8-bugbear | Common bug patterns |

| Ignored | Reason |
|---------|--------|
| `B008` | FastAPI `Depends()` in default arguments |
| `B` in `tests/**` | Relaxed rules for tests |

### Manual commands

> Run from the `backend/` directory. Requires [uv](https://docs.astral.sh/uv/) and dev dependencies (`uv sync`).

Lint the project; report issues without changing files:

```bash
uv run ruff check .
```

Check formatting only; report mismatches without writing:

```bash
uv run ruff format --check .
```

Lint and auto-fix what Ruff can (imports, safe rewrites):

```bash
uv run ruff check --fix .
```

Apply formatting to all Python files (including tab → spaces):

```bash
uv run ruff format .
```
