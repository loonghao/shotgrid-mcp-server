# Import built-in modules
import os
import sys

# Import third-party modules
import nox


ROOT = os.path.dirname(__file__)

# Ensure shotgrid_mcp_server is importable
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import local modules
from nox_actions import lint, release


@nox.session(name="tests")
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Use uv to install dependencies
    session.run("uv", "pip", "install", "-e", ".[test]", external=True)

    # Run tests
    session.run(
        "python",
        "-m",
        "pytest",
        "tests/test_server.py",
        "-v",
        "--cov=shotgrid_mcp_server",
        "--cov-report=term-missing",
        env={"PYTHONPATH": ROOT},
    )


@nox.session(name="lint")
def lint_check(session: nox.Session) -> None:
    """Run the linter."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Use uv to install dependencies
    session.run("uv", "pip", "install", "-e", ".[lint]", external=True)

    # Run linter
    commands = ["ruff check src", "ruff format --check src", "mypy src"]
    lint.lint(session, commands)


@nox.session(name="lint-fix")
def lint_fix(session: nox.Session) -> None:
    """Run the linter and fix issues."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Use uv to install dependencies
    session.run("uv", "pip", "install", "-e", ".[lint]", external=True)
    # Run linter
    lint.lint_fix(session)


@nox.session(name="build-wheel")
def build_wheel(session: nox.Session) -> None:
    """Build Python wheel package."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Use uv to install dependencies
    session.run("uv", "pip", "install", "-e", ".[build]", external=True)

    # Install build and hatchling
    session.run("python", "-m", "pip", "install", "uv", silent=True)
    session.run("uv", "pip", "install", "build", "hatchling", external=True)

    # Build wheel
    release.build_wheel(session)
