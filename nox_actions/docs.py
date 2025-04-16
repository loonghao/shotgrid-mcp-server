"""Nox actions for documentation tasks."""

import os
import shutil
from pathlib import Path

import nox


def generate_api_docs(session: nox.Session) -> None:
    """Generate API documentation using Python introspection.

    Args:
        session: Nox session.
    """
    # Install dependencies
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

    # Create a simple module documentation file
    module_md = api_dir / "shotgrid_mcp_server.md"
    module_md.write_text(
        "# shotgrid_mcp_server\n\n"
        "ShotGrid MCP Server is a Model Context Protocol (MCP) server implementation for Autodesk ShotGrid.\n\n"
        "## Core Modules\n\n"
        "- [shotgrid_mcp_server.server](shotgrid_mcp_server.server.md) - Server implementation\n"
        "- [shotgrid_mcp_server.models](shotgrid_mcp_server.models.md) - Data models\n"
        "- [shotgrid_mcp_server.filters](shotgrid_mcp_server.filters.md) - Filter utilities\n"
        "- [shotgrid_mcp_server.data_types](shotgrid_mcp_server.data_types.md) - Data type utilities\n"
        "- [shotgrid_mcp_server.constants](shotgrid_mcp_server.constants.md) - Constants\n"
        "- [shotgrid_mcp_server.utils](shotgrid_mcp_server.utils.md) - Utility functions\n"
        "- [shotgrid_mcp_server.mockgun_ext](shotgrid_mcp_server.mockgun_ext.md) - Mockgun extensions\n\n"
        "## Tools\n\n"
        "- [shotgrid_mcp_server.tools](shotgrid_mcp_server.tools.md) - Tools package\n"
        "- [shotgrid_mcp_server.tools.base](shotgrid_mcp_server.tools.base.md) - Base tool functionality\n"
        "- [shotgrid_mcp_server.tools.search_tools](shotgrid_mcp_server.tools.search_tools.md) - Search tools\n"
        "- [shotgrid_mcp_server.tools.entity_tools](shotgrid_mcp_server.tools.entity_tools.md) - Entity tools\n"
        "- [shotgrid_mcp_server.tools.schema_tools](shotgrid_mcp_server.tools.schema_tools.md) - Schema tools\n"
    )

    # Create module documentation files
    modules = [
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
        module_file = api_dir / f"{module}.md"
        module_file.write_text(
            f"# {module}\n\n"
            f"This module is part of the ShotGrid MCP Server package.\n\n"
            f"## Module Reference\n\n"
            f"Please refer to the source code for detailed information about this module.\n"
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

        # Mintlify no longer supports the build command
        # Instead, we'll just log a message
        session.log("Mintlify no longer supports the build command. Use 'mintlify dev' to preview documentation locally.")
        session.log("To deploy documentation, use 'mintlify deploy' command.")


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
