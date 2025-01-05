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
    """Build Python wheel package."""
    # Install uv if not already installed
    session.run("python", "-m", "pip", "install", "uv", silent=True)

    # Install build dependencies using uv
    session.run("uv", "pip", "install", "build", external=True)

    # Build wheel
    session.run("python", "-m", "build", "--wheel", "--no-isolation")
