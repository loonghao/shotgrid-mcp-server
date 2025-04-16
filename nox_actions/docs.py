"""Nox actions for documentation tasks."""

import os
import shutil
from pathlib import Path

import nox


def generate_api_docs(session: nox.Session) -> None:
    """Generate API documentation using Sphinx.

    Args:
        session: Nox session.
    """
    # Install dependencies
    session.install("sphinx", "sphinx-markdown-builder", "sphinx-autodoc-typehints")
    session.install("-e", ".")

    # Create output directory
    root = os.path.dirname(os.path.dirname(__file__))
    api_dir = Path(root) / "docs" / "api"
    if api_dir.exists():
        shutil.rmtree(api_dir)
    api_dir.mkdir(parents=True, exist_ok=True)

    # Generate API documentation
    session.run(
        "sphinx-build",
        "-b", "markdown",
        "-c", "docs/sphinx_conf",
        "src/shotgrid_mcp_server",
        str(api_dir),
    )

    # Clean up and format the generated markdown files
    for md_file in api_dir.glob("**/*.md"):
        content = md_file.read_text()
        # Convert top-level headers to second-level
        content = content.replace("# ", "## ")
        # Convert module headers back to top-level
        content = content.replace("## Module", "# Module")
        md_file.write_text(content)

    session.log(f"API documentation generated in {api_dir}")


def preview_docs(session: nox.Session) -> None:
    """Preview documentation locally using Mintlify.

    Args:
        session: Nox session.
    """
    # First generate API docs
    generate_api_docs(session)

    # Change to docs directory
    root = os.path.dirname(os.path.dirname(__file__))
    docs_dir = Path(root) / "docs"
    with session.chdir(str(docs_dir)):
        # Install Node.js dependencies
        if (docs_dir / "package.json").exists():
            session.run("npm", "install", external=True)

        # Install Mintlify CLI if not already installed
        try:
            session.run("mintlify", "--version", external=True, silent=True)
        except Exception:
            session.run("npm", "install", "-g", "mintlify@latest", external=True)

        # Start Mintlify dev server
        session.run("npx", "mintlify", "dev", external=True)


def build_docs(session: nox.Session) -> None:
    """Build documentation using Mintlify.

    Args:
        session: Nox session.
    """
    # First generate API docs
    generate_api_docs(session)

    # Change to docs directory
    root = os.path.dirname(os.path.dirname(__file__))
    docs_dir = Path(root) / "docs"
    with session.chdir(str(docs_dir)):
        # Install Node.js dependencies
        if (docs_dir / "package.json").exists():
            session.run("npm", "install", external=True)

        # Install Mintlify CLI if not already installed
        try:
            session.run("mintlify", "--version", external=True, silent=True)
        except Exception:
            session.run("npm", "install", "-g", "mintlify@latest", external=True)

        # Build documentation
        session.run("npx", "mintlify", "build", external=True)

        session.log(f"Documentation built in {docs_dir / '.mintlify' / 'build'}")


def deploy_docs(session: nox.Session) -> None:
    """Deploy documentation to Mintlify.

    Args:
        session: Nox session.
    """
    # First generate API docs
    generate_api_docs(session)

    # Change to docs directory
    root = os.path.dirname(os.path.dirname(__file__))
    docs_dir = Path(root) / "docs"
    with session.chdir(str(docs_dir)):
        # Install Node.js dependencies
        if (docs_dir / "package.json").exists():
            session.run("npm", "install", external=True)

        # Install Mintlify CLI if not already installed
        try:
            session.run("mintlify", "--version", external=True, silent=True)
        except Exception:
            session.run("npm", "install", "-g", "mintlify@latest", external=True)

        # Deploy documentation
        session.run("npx", "mintlify", "deploy", external=True)

        session.log("Documentation deployed to Mintlify")
