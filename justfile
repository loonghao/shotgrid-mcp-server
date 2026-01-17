# Justfile for shotgrid-mcp-server
# Usage: vx just <recipe>
# See: https://github.com/loonghao/vx

# Default recipe - show available commands
default:
    @just --list

# Build wheel package
build:
    vx uvx nox -s build-wheel

# Run linter checks
lint:
    vx uvx nox -s lint

# Run linter and fix issues
lint-fix:
    vx uvx nox -s lint-fix

# Run tests
test *args='':
    vx uvx nox -s tests -- {{args}}

# Run ruff check
check:
    vx uvx ruff check .

# Format code with ruff
format:
    vx uvx ruff format .

# Run type checking
typecheck:
    vx uvx mypy src

# Generate API documentation
docs-api:
    vx uvx nox -s docs-api

# Preview documentation locally
docs-preview:
    vx uvx nox -s docs-preview

# Build documentation
docs-build:
    vx uvx nox -s docs-build

# Deploy documentation
docs-deploy:
    vx uvx nox -s docs-deploy

# Generate static documentation site
docs-static:
    vx uvx nox -s docs-static

# Clean build artifacts
clean:
    rm -rf dist build *.egg-info .nox .pytest_cache .mypy_cache .ruff_cache coverage.xml .coverage

# Install development dependencies
install-dev:
    vx uv pip install -e ".[dev,test,lint]"
