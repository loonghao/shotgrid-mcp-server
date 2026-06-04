"""Unit tests for ShotGridServer adapter."""

# Import built-in modules
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestShotGridServer:
    """Test the ShotGridServer adapter class."""

    def test_import(self):
        """Can import ShotGridServer."""
        from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer

        assert ShotGridServer is not None

    def test_is_dcc_server_base(self):
        """ShotGridServer extends DccServerBase."""
        from dcc_mcp_core import DccServerBase
        from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer

        assert issubclass(ShotGridServer, DccServerBase)

    def test_create_instance(self):
        """Can create a ShotGridServer instance."""
        from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            assert server._dcc_name == "shotgrid"
            assert server._builtin_skills_dir is not None
        finally:
            server.stop()

    def test_skills_dir_exists(self):
        """Skills directory points to a valid location."""
        from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            from pathlib import Path

            skills_dir = Path(server._builtin_skills_dir)
            assert skills_dir.is_dir(), f"Skills dir not found: {skills_dir}"
            assert (skills_dir / "shotgrid-crud").is_dir()
            assert (skills_dir / "shotgrid-search").is_dir()
        finally:
            server.stop()

    def test_eight_skill_packages(self):
        """All 8 skill packages are present."""
        from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            from pathlib import Path

            skills_dir = Path(server._builtin_skills_dir)
            packages = [d.name for d in skills_dir.iterdir() if d.is_dir()]
            assert len(packages) == 8, f"Expected 8 skill packages, got {packages}"
        finally:
            server.stop()

    def test_version_string(self):
        """_version_string returns a version."""
        from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            version = server._version_string()
            assert version is not None
            assert len(version) > 0
        finally:
            server.stop()

    def test_context_manager(self):
        """Can use ShotGridServer as context manager."""
        from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            with server as handle:
                assert handle is not None
        finally:
            pass  # Context manager auto-stops


class TestAdapterFactory:
    """Test the create_shotgrid_server factory."""

    def test_factory_returns_server(self):
        """Factory returns a ShotGridServer."""
        from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer, create_shotgrid_server

        server = create_shotgrid_server(port=0)
        try:
            assert isinstance(server, ShotGridServer)
        finally:
            server.stop()
