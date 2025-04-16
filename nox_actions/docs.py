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

    # Create a temporary Python script to generate documentation
    temp_script = Path(root) / "temp_doc_generator.py"
    temp_script.write_text(
        """import inspect
import os
import sys
from pathlib import Path

# Get the module name from command line arguments
module_name = sys.argv[1]
output_file = sys.argv[2]

# Import the module
module = __import__(module_name, fromlist=[''])

# Create the output directory if it doesn't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Generate the module documentation
with open(output_file, 'w') as f:
    # Write the module header
    f.write(f"# {module.__name__}\n\n")
    if module.__doc__:
        f.write(f"{module.__doc__.strip()}\n\n")
    f.write("## Module Reference\n\n")

    # Write the module members
    for name, obj in inspect.getmembers(module):
        if not name.startswith('_') and (inspect.isfunction(obj) or inspect.isclass(obj)) and obj.__module__ == module.__name__:
            f.write(f"### {name}\n\n```python\n{inspect.getsource(obj)}\n```\n\n")
"""
    )

    try:
        # Generate documentation for each module
        for module in modules:
            output_file = api_dir / f"{module}.md"
            session.run("python", str(temp_script), module, str(output_file))
            session.log(f"Generated documentation for {module}")

        session.log(f"API documentation generated in {api_dir}")
    finally:
        # Clean up the temporary script
        if temp_script.exists():
            temp_script.unlink()


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
