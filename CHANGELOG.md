## v0.3.4 (2025-04-15)

### Fix

- use uvx nox -s build-wheel for package building

## v0.3.3 (2025-04-15)

### Fix

- use uvx for all commands to avoid pip module issues
- use Python built-in venv module instead of uv venv

## v0.3.2 (2025-04-15)

### Fix

- handle direct git dependencies for PyPI publishing
- ensure virtual environment is activated in all workflow steps

## v0.3.1 (2025-04-15)

### Refactor

- **workflows**: Update dependency installation in workflows

## v0.3.0 (2025-04-15)

### Feat

- add Mintlify docs deployment workflow
- update PyPI publishing workflow to improve build and release process\

### Fix

- standardize uv usage in CI workflow to use uvx for nox execution

## v0.2.6 (2025-04-15)

### Fix

- resolve ruff linting issues with unused imports
- resolve type checking issues and update tests
- resolve ruff linting issues with imports

## v0.2.5 (2025-01-05)

### Refactor

- **server**: Refactor imports and add serialization method for entities
- **server**: Update environment variable names and logging for ShotGrid connection pool

## v0.2.4 (2025-01-05)

### Refactor

- **deps**: Update shotgun-api3 dependency and add uvx tool configuration

## v0.2.3 (2025-01-05)

### Refactor

- **deps**: Update dependencies and lock file

## v0.2.2 (2025-01-05)

### Refactor

- **server**: Refactor import statements in connection_pool and add test_imports script

## v0.2.1 (2025-01-05)

### Refactor

- **workflows**: Update dependency installation in workflows

## v0.2.0 (2025-01-05)

### Feat

- Implement ShotGrid client factories and enhance connection pool

### Refactor

- **server**: Refactor server tools registration and error handling

## v0.1.0 (2025-01-05)

### Feat

- Initialize ShotGrid MCP Server project structure and dependencies Add initial files and directories for the ShotGrid MCP Server project, including examples, src, tests, and documentation.
