# Justfile for shotgrid-mcp-server
# Usage: vx just <recipe>
# See: https://github.com/loonghao/vx

# Default recipe - show available commands
default:
    @just --list

# Build wheel package
build:
    uvx nox -s build-wheel

# Run linter checks
lint:
    uvx nox -s lint

# Run linter and fix issues
lint-fix:
    uvx nox -s lint-fix

# Run tests
test *args='':
    uvx nox -s tests -- {{args}}

# Run ruff check
check:
    uvx ruff check .

# Format code with ruff
format:
    uvx ruff format .

# Run type checking
typecheck:
    uvx mypy src

# Generate API documentation
docs-api:
    uvx nox -s docs-api

# Preview documentation locally
docs-preview:
    uvx nox -s docs-preview

# Build documentation
docs-build:
    uvx nox -s docs-build

# Deploy documentation
docs-deploy:
    uvx nox -s docs-deploy

# Generate static documentation site
docs-static:
    uvx nox -s docs-static

# Clean build artifacts
clean:
    rm -rf dist build *.egg-info .nox .pytest_cache .mypy_cache .ruff_cache coverage.xml .coverage

# Install development dependencies
install-dev:
    uv pip install -e ".[dev,test,lint]"
