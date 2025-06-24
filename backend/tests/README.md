# Test Suite Documentation

This directory contains tests for the backend API, using pytest and async support.

## Common Test Commands

### Basic Testing
Run all tests:
```bash
pytest
```

Run a specific test file:
```bash
pytest tests/yourTestFile.py
```

Run with verbose output:
```bash
pytest -v
```

### Coverage Testing
Run with coverage report:
```bash
pytest --cov=.
```

Show missing lines in terminal:
```bash
pytest --cov=. --cov-report=term-missing
```

Generate HTML coverage report:
```bash
pytest --cov=. --cov-report=html
```

Generate XML coverage report (for CI/CD):
```bash
pytest --cov=. --cov-report=xml
```

Fail if coverage is below 80%:
```bash
pytest --cov=. --cov-fail-under=80
```

## Notes
- Tests are designed to be run in a clean environment.
- Coverage format, omit rules, and other options can be adjusted in `pyproject.toml`.
- For more details, see comments in `conftest.py`. 