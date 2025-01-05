"""Import Test."""

# Import built-in modules
import importlib
import pkgutil

# Import local modules
import shotgrid_mcp_server


def test_imports():
    """Test import modules."""
    prefix = f"{shotgrid_mcp_server.__name__}."
    iter_packages = pkgutil.walk_packages(
        shotgrid_mcp_server.__path__,  # noqa: WPS609
        prefix,
    )
    for _, name, _ in iter_packages:
        module_name = name if name.startswith(prefix) else prefix + name
        importlib.import_module(module_name)
