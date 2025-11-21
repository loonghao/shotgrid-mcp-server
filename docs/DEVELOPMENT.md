# Development Guide

## Code Style and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting Python code.

### Running Ruff Manually

```bash
# Check for linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit Hooks (Optional)

The project includes pre-commit configuration for automatic code quality checks.

#### Installation

1. Install pre-commit (if not already installed):
   ```bash
   pip install pre-commit
   # or
   uv pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

#### Usage

Once installed, pre-commit will automatically run on every commit:

```bash
git commit -m "your message"
# Pre-commit hooks will run automatically
```

To run pre-commit manually on all files:

```bash
pre-commit run --all-files
```

#### Configured Hooks

- **no-commit-to-branch**: Prevents direct commits to main branch
- **check-yaml**: Validates YAML files
- **check-toml**: Validates TOML files
- **end-of-file-fixer**: Ensures files end with a newline
- **trailing-whitespace**: Removes trailing whitespace
- **ruff**: Lints and fixes Python code
- **ruff-format**: Formats Python code

### Import Sorting

Ruff automatically sorts imports according to the `isort` rules. The import order is:

1. Standard library imports
2. Third-party imports
3. Local application imports

Example:
```python
# Standard library
import os
from typing import Any, Dict

# Third-party
from fastmcp import FastMCP
from shotgun_api3 import Shotgun

# Local
from shotgrid_mcp_server.models import EntityDict
```

## Testing

Run tests with pytest:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_filters.py

# Run with coverage
uv run pytest --cov=src/shotgrid_mcp_server
```

## Keeping Local and CI in Sync

To ensure your local development environment matches the CI environment:

### Ruff Version Consistency

The project uses a specific version of Ruff defined in two places:
- `.pre-commit-config.yaml` - for pre-commit hooks
- `nox_actions/lint.py` - for CI linting

**Important**: These versions must match to avoid inconsistent linting results.

Current version: **0.8.6**

### Running the Same Checks as CI

Before pushing, run the same checks that CI will run:

```bash
# Run linting (same as CI)
uv run nox -s lint

# Run tests (same as CI)
uv run nox -s tests

# Or run both
uv run nox -s lint tests
```

### Line Ending Consistency

The project uses LF (Unix-style) line endings for all text files, enforced by `.gitattributes`.

If you're on Windows, configure Git:

```bash
# Set Git to convert CRLF to LF on commit
git config core.autocrlf input
```

This ensures that:
- Files are committed with LF endings
- `ruff format --check` passes on all platforms (Windows, macOS, Linux)

### Updating Ruff Version

When updating Ruff, update both files:

1. `.pre-commit-config.yaml`:
   ```yaml
   - repo: https://github.com/astral-sh/ruff-pre-commit
     rev: v0.8.6  # Update this version
   ```

2. `nox_actions/lint.py`:
   ```python
   RUFF_VERSION = "0.8.6"  # Update this version
   ```

Then update pre-commit hooks:
```bash
pre-commit autoupdate
pre-commit install
```

## Building Documentation

```bash
# Build documentation
uv run tox -e docs

# Serve documentation locally
uv run tox -e docs-server
```

## Common Issues

### Import Sorting Errors

If you see import sorting errors, run:

```bash
uv run ruff check --select I --fix .
```

### Whitespace Issues

If you see trailing whitespace or blank line issues, run:

```bash
uv run ruff format .
```

### Pre-commit Fails

If pre-commit fails, you can:

1. Fix the issues manually
2. Run `uv run ruff check --fix .` and `uv run ruff format .`
3. Stage the changes and commit again

Or skip pre-commit (not recommended):

```bash
git commit --no-verify -m "your message"
```

