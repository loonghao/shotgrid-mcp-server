# Import built-in modules
import os
import platform

# Import third-party modules
import nox

from nox_actions.utils import THIS_ROOT


def build_exe(session: nox.Session) -> None:
    """Build executable using PyInstaller."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install build dependencies using uv
    session.run("uv", "pip", "install", "pyinstaller", external=True)
    session.run("uv", "pip", "install", "-e", ".", external=True)

    # Get platform-specific settings
    is_windows = platform.system().lower() == "windows"
    exe_ext = ".exe" if is_windows else ""

    # Build executable
    session.run(
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name",
        f"shotgrid_mcp_server{exe_ext}",
        os.path.join("src", "shotgrid_mcp_server", "__main__.py"),
        env={"PYTHONPATH": THIS_ROOT.as_posix()},
    )


def build_wheel(session: nox.Session) -> None:
    """Build Python wheel package.

    Uses `python -m build` with the default isolated build environment.
    This avoids any interference from the current environment that could
    produce non-standard ZIP archives rejected by PyPI.
    """
    # Install the build helper into the nox environment. `python -m build`
    # will then create an isolated PEP 517 environment based on
    # ``[build-system]`` in ``pyproject.toml``.
    session.install("build")

    # Build wheel using an isolated PEP 517 environment.
    session.run("python", "-m", "build", "--wheel")
