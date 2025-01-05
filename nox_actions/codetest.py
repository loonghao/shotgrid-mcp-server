# Import built-in modules
import os

# Import third-party modules
import nox

from nox_actions.utils import PACKAGE_NAME, THIS_ROOT


def pytest(session: nox.Session) -> None:
    """Run pytest with coverage report."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Use uv to install dependencies
    session.run("uv", "pip", "install", ".", external=True)
    session.run("uv", "pip", "install", "pytest", "pytest-cov", "pytest-mock", external=True)

    # Run tests
    test_root = os.path.join(THIS_ROOT, "tests")
    session.run(
        "pytest",
        f"--cov={PACKAGE_NAME}",
        "--cov-report=xml:coverage.xml",
        f"--rootdir={test_root}",
        env={"PYTHONPATH": THIS_ROOT.as_posix()},
    )
