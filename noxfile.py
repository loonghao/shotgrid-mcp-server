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
from nox_actions import docs, lint, release
from nox_actions.utils import PACKAGE_NAME, THIS_ROOT

@nox.session(name="tests")
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest."""

    # Install test + runtime dependencies into the nox virtualenv using pip
    # We deliberately avoid `uv pip` here to sidestep Windows permission issues
    # when uv tries to manage its own wheel cache.
    session.install("-r", "requirements-test.txt")

    # Run tests
    test_root = os.path.join(ROOT, "tests")

    # Get any additional arguments passed after --
    pytest_args = session.posargs if session.posargs else []

    # Default arguments
    default_args = [
        f"--cov={PACKAGE_NAME}",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term",
        f"--rootdir={test_root}",
    ]

    # Ensure src/ is on PYTHONPATH so we can import the package without installing it
    src_root = os.path.join(ROOT, "src")
    env = {"PYTHONPATH": os.pathsep.join([src_root, THIS_ROOT.as_posix()])}

    # Run pytest with all arguments
    session.run("pytest", *default_args, *pytest_args, env=env)


@nox.session(name="lint")
def lint_check(session: nox.Session) -> None:
    """Run the linter."""
    # Run ruff and mypy via the shared lint helpers
    commands = ["ruff check src", "ruff format --check src"]
    lint.lint(session, commands)

    # Run mypy but ignore errors for now
    try:
        session.run("mypy", "src")
    except Exception:
        session.log("mypy found errors, but we're ignoring them for now")


@nox.session(name="lint-fix")
def lint_fix(session: nox.Session) -> None:
    """Run the linter and fix issues."""
    # Run ruff format and ruff check --fix via the shared lint helpers
    lint.lint_fix(session)


@nox.session(name="build-wheel")
def build_wheel(session: nox.Session) -> None:
    """Build Python wheel package."""
    # Delegate to the shared release helper, which uses ``python -m build``
    # with an isolated PEP 517 environment.
    release.build_wheel(session)


@nox.session(name="docs-api")
def docs_api(session: nox.Session) -> None:
    """Generate API documentation using Sphinx."""
    docs.generate_api_docs(session)


@nox.session(name="docs-preview")
def docs_preview(session: nox.Session) -> None:
    """Preview documentation locally using Mintlify."""
    docs.preview_docs(session)


@nox.session(name="docs-build")
def docs_build(session: nox.Session) -> None:
    """Build documentation using Mintlify."""
    docs.build_docs(session)


@nox.session(name="docs-deploy")
def docs_deploy(session: nox.Session) -> None:
    """Deploy documentation to Mintlify."""
    docs.deploy_docs(session)


@nox.session(name="docs-static")
def docs_static(session: nox.Session) -> None:
    """Generate a static website from Mintlify documentation."""
    docs.generate_static_site(session)
