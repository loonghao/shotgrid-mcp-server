# Import built-in modules

# Import third-party modules
import nox


def lint(session: nox.Session) -> None:
    """Run linters."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install linting tools using uv
    session.run("uv", "pip", "install", "ruff", "black", "mypy", external=True)

    # Run black check
    session.run("black", ".", "--check")

    # Run ruff
    session.run("ruff", "check", ".")

    # Run mypy
    session.run("mypy", "src", "--ignore-missing-imports")


def lint_fix(session: nox.Session) -> None:
    """Run linters and fix issues."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install linting tools using uv
    session.run("uv", "pip", "install", "ruff", "black", external=True)

    # Run black with fix
    session.run("black", ".")

    # Run ruff with fix
    session.run("ruff", "check", ".", "--fix")
