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

    # Create a simple index.md file
    index_md = api_dir / "index.md"
    index_md.write_text(
        "# ShotGrid MCP Server API Documentation\n\n"
        "This documentation provides details about the ShotGrid MCP Server API.\n\n"
        "## Modules\n\n"
        "- [shotgrid_mcp_server](shotgrid_mcp_server.md)\n"
    )

    # Generate module documentation manually
    modules = [
        "shotgrid_mcp_server",
        "shotgrid_mcp_server.server",
        "shotgrid_mcp_server.models",
        "shotgrid_mcp_server.filters",
        "shotgrid_mcp_server.data_types",
        "shotgrid_mcp_server.constants",
        "shotgrid_mcp_server.utils",
        "shotgrid_mcp_server.mockgun_ext",
        "shotgrid_mcp_server.tools",
        "shotgrid_mcp_server.tools.base",
        "shotgrid_mcp_server.tools.search_tools",
        "shotgrid_mcp_server.tools.entity_tools",
        "shotgrid_mcp_server.tools.schema_tools",
    ]

    for module in modules:
        # Generate documentation for each module
        output_file = api_dir / f"{module}.md"
        session.run(
            "python", "-c",
            f"import {module}; print('# ' + {module}.__name__ + '\\n\\n' + ({module}.__doc__ or '').strip() + '\\n\\n## Module Reference\\n\\n')",
            silent=True,
            out=str(output_file),
        )

        # Append module members
        session.run(
            "python", "-c",
            f"import inspect, {module}; "
            f"print('\\n'.join(['### ' + name + '\\n\\n```python\\n' + inspect.getsource(getattr({module}, name)) + '\\n```\\n' "
            f"for name, obj in inspect.getmembers({module}) "
            f"if not name.startswith('_') and (inspect.isfunction(obj) or inspect.isclass(obj)) and obj.__module__ == '{module}']))",
            silent=True,
            out=str(output_file),
            append=True,
        )

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
