# Import built-in modules

# Import third-party modules
import nox


def get_default_commands() -> list[str]:
    """Get default linting commands."""
    return ["ruff check .", "ruff format --check .", "mypy ."]


def lint(session: nox.Session, commands: list[str] | None = None) -> None:
    """Run linters."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install linting tools using uv
    session.run("uv", "pip", "install", "ruff", "black", "mypy", external=True)

    if commands is None:
        # Run default linting commands
        commands = get_default_commands()

    # Run commands
    for cmd in commands:
        parts = cmd.split()
        session.run(*parts)


def lint_fix(session: nox.Session) -> None:
    """Run linters and fix issues."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install linting tools using uv
    session.run("uv", "pip", "install", "ruff", "black", "mypy", external=True)

    # Run ruff format
    session.run("ruff", "format", "src")

    # Run ruff check with fix
    session.run("ruff", "check", "src", "--fix")
