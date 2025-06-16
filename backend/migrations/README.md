# Alembic Migration Guide

This document describes how to manage database schema migrations using Alembic.

## 1. Initialize Alembic (if not already initialized)

If the `migrations/` directory does not exist, you can initialize Alembic with:
```bash
alembic init migrations
```

## 2. Create a New Migration Version

To generate a new migration script based on your current models:
```bash
alembic revision --autogenerate -m "Describe your changes here"
```
- The `--autogenerate` flag will compare your models and the current database schema, and generate the necessary changes.
- Edit the generated migration script if needed.

## 3. Upgrade the Database

To apply all pending migrations and upgrade the database to the latest version:
```bash
alembic upgrade head
```

## 4. Downgrade the Database

To revert the last migration:
```bash
alembic downgrade -1
```
To downgrade to a specific revision:
```bash
alembic downgrade <revision_id>
```

## 5. Check Current Migration Version

To see the current version of the database:
```bash
alembic current
```

## 6. Other Useful Commands

- Show migration history:
  ```bash
  alembic history
  ```
- Show current status:
  ```bash
  alembic heads
  ```

## Notes
- Always review the generated migration scripts before applying them to production.
- If you encounter merge conflicts in migration scripts, resolve them manually and test carefully.
- For more information, see the [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/).