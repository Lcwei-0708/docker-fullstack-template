# CI/CD

This project uses GitHub Actions for automated testing and deployment of test coverage reports.

## Required Setup

### GitHub Pages Setting

1. Go to `Settings` → `Pages`.
2. Under `Source`, select `GitHub Actions`.

### Coverage Reports

- HTML Coverage Report:
   - **URL**: `https://yourusername.github.io/your-repo/`
   - **Purpose**: Detailed coverage analysis with line-by-line coverage information.

- Coverage Badge ([shields.io](https://shields.io/)):
   - **Format**: Dynamic badge showing current coverage percentage with Python logo.
   - **Colors**: Green (≥80%), Yellow (60-79%), Red (<60%)
   - **Features**: Automatically updates after each test run.

## Workflow Files

### Testing Workflow (`test-backend.yml`)

**Purpose**: Runs tests and generates coverage reports.

**Triggers**:
- Push to `main` branch
- Pull requests to `main` branch

**Services**:
- MariaDB 11.3 (for database testing)
- Redis 7 (for session testing)

### Deploy Coverage Report (`deploy-coverage.yml`)

**Purpose**: Deploys coverage reports to GitHub Pages after successful testing.

**Triggers**:
- Automatically runs after the Testing workflow completes successfully.