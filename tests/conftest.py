"""Test fixtures for the ShotGrid MCP server (dcc-mcp-core era).

Provides mock ShotGrid connections, test data, and server fixtures
without depending on FastMCP.
"""

# Import built-in modules
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

# Import third-party modules
import pytest
import yaml

# Fixture-scoped path resolution (runs before test collection)
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
SKILLS_DIR = PROJECT_ROOT / "skills"


# ═══════════════════════════════════════════════════════════════════════════
# Mock ShotGrid connection fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_sg() -> MagicMock:
    """Create a mock ShotGrid (shotgun_api3.Shotgun) connection.

    Default return values cover the most common CRUD and search operations.
    Tests can override individual method return values on the fixture.
    """
    sg = MagicMock()
    sg.find.return_value = [{"type": "Shot", "id": 1, "code": "SH001"}]
    sg.find_one.return_value = {"type": "Shot", "id": 1, "code": "SH001"}
    sg.create.return_value = {"type": "Shot", "id": 2, "code": "SH002"}
    sg.update.return_value = {"type": "Shot", "id": 1, "code": "SH001_UPDATED"}
    sg.delete.return_value = True
    sg.revive.return_value = True
    sg.batch.return_value = [{"type": "Shot", "id": 3}]
    sg.text_search.return_value = [{"type": "Shot", "id": 1}]
    sg.summarize.return_value = {"groups": [{"value": "ip", "count": 5}]}

    # Schema responses
    sg.schema_field_read.return_value = {
        "code": {"data_type": {"value": "text"}, "properties": {"editable": {"value": True}}},
        "sg_status_list": {"data_type": {"value": "status_list"}, "properties": {"valid_values": {"value": ["wtg", "ip", "fin"]}}},
    }
    sg.schema_entity_read.return_value = {
        "Shot": {}, "Asset": {}, "Task": {}, "Version": {}, "Note": {},
        "PublishedFile": {}, "Playlist": {}, "Project": {}, "HumanUser": {},
    }
    return sg


@pytest.fixture
def mock_sg_with_projects(mock_sg: MagicMock) -> MagicMock:
    """Mock ShotGrid with 3 projects."""
    projects = [
        {"type": "Project", "id": 100, "name": "Project Alpha", "sg_status": "Active"},
        {"type": "Project", "id": 101, "name": "Project Beta", "sg_status": "Active"},
        {"type": "Project", "id": 102, "name": "Project Gamma", "sg_status": "Archived"},
    ]
    mock_sg.find.return_value = projects
    mock_sg.find_one.return_value = projects[0]
    return mock_sg


@pytest.fixture
def mock_sg_with_users(mock_sg: MagicMock) -> MagicMock:
    """Mock ShotGrid with 2 users."""
    users = [
        {"type": "HumanUser", "id": 1, "name": "Alice", "login": "alice", "email": "alice@example.com"},
        {"type": "HumanUser", "id": 2, "name": "Bob", "login": "bob", "email": "bob@example.com"},
    ]
    mock_sg.find.return_value = users
    return mock_sg


@pytest.fixture
def mock_sg_no_results(mock_sg: MagicMock) -> MagicMock:
    """Mock ShotGrid that returns empty results."""
    mock_sg.find.return_value = []
    mock_sg.find_one.return_value = None
    return mock_sg


# ═══════════════════════════════════════════════════════════════════════════
# Test data fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_shot_data() -> Dict[str, Any]:
    """Sample Shot entity data."""
    return {"code": "SH999", "description": "Test shot", "sg_status_list": "ip"}


@pytest.fixture
def sample_task_data() -> Dict[str, Any]:
    """Sample Task entity data."""
    return {"content": "Animation", "sg_status_list": "wtg"}


@pytest.fixture
def sample_note_data() -> Dict[str, Any]:
    """Sample Note data."""
    return {"subject": "Review feedback", "content": "Please fix the lighting in frame 42."}


@pytest.fixture
def sample_filters() -> List[List[Any]]:
    """Sample ShotGrid filter conditions."""
    return [["sg_status_list", "is", "ip"], ["project", "is", {"type": "Project", "id": 100}]]


# ═══════════════════════════════════════════════════════════════════════════
# Skill package fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def skills_dir() -> Path:
    """Path to the skills directory."""
    assert SKILLS_DIR.is_dir(), f"Skills dir not found: {SKILLS_DIR}"
    return SKILLS_DIR


@pytest.fixture
def skill_packages(skills_dir: Path) -> List[str]:
    """List of all skill package names."""
    return sorted(d.name for d in skills_dir.iterdir() if d.is_dir())


@pytest.fixture
def load_tools_yaml():
    """Helper to load tools.yaml for a skill."""

    def _load(skill_name: str) -> Dict[str, Any]:
        path = SKILLS_DIR / skill_name / "tools.yaml"
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    return _load


# ═══════════════════════════════════════════════════════════════════════════
# ShotGrid connection context fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def connection_context(mock_sg: MagicMock):
    """Provide a context-managed ShotGrid connection."""
    import sys

    sys.path.insert(0, str(SRC_DIR))
    from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext

    return ShotGridConnectionContext(factory_or_connection=mock_sg)
