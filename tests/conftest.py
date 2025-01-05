"""Test fixtures for the ShotGrid MCP server."""

# Import built-in modules
import pickle
from pathlib import Path

# Import third-party modules
import pytest
import yaml
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.connection_pool import MockShotgunFactory, ShotGridConnectionContext
from shotgrid_mcp_server.server import ShotGridTools


@pytest.fixture(scope="session")
def schema_paths():
    """Get schema paths for testing."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    schema_path = data_dir / "schema.bin"
    entity_schema_path = data_dir / "entity_schema.bin"

    # Load schema from YAML
    yaml_dir = data_dir / "yaml"
    with open(yaml_dir / "schema.yaml", "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Add Sequence schema
    schema["Sequence"] = {
        "code": {
            "data_type": {"value": "text"},
            "properties": {
                "default_value": {"value": None},
                "valid_types": {"value": ["text"]},
            },
        },
        "description": {
            "data_type": {"value": "text"},
            "properties": {
                "default_value": {"value": None},
                "valid_types": {"value": ["text"]},
            },
        },
        "project": {
            "data_type": {"value": "entity"},
            "properties": {
                "default_value": {"value": None},
                "valid_types": {"value": ["Project"]},
            },
        },
        "sg_status_list": {
            "data_type": {"value": "text"},
            "properties": {
                "default_value": {"value": None},
                "valid_types": {"value": ["text"]},
            },
        },
    }

    # Save schema to binary files
    with open(schema_path, "wb") as f:
        pickle.dump(schema, f)
    with open(entity_schema_path, "wb") as f:
        pickle.dump(schema, f)

    return {"schema_path": str(schema_path), "schema_entity_path": str(entity_schema_path)}


@pytest.fixture
def mock_factory(schema_paths):
    """Create a MockShotgunFactory instance."""
    return MockShotgunFactory(
        schema_path=schema_paths["schema_path"], schema_entity_path=schema_paths["schema_entity_path"]
    )


@pytest.fixture
def mock_sg(mock_factory):
    """Create a mock ShotGrid client with test data."""
    sg = mock_factory.create_client()

    # Create test groups
    admin_group = sg.create("Group", {"code": "Admin"})

    artist_group = sg.create("Group", {"code": "Artist"})

    producer_group = sg.create("Group", {"code": "Producer"})

    # Create test departments
    it_department = sg.create("Department", {"code": "IT"})

    anim_department = sg.create("Department", {"code": "Animation"})

    prod_department = sg.create("Department", {"code": "Production"})

    # Create test permission rule sets
    admin_rule_set = sg.create("PermissionRuleSet", {"code": "Admin"})

    artist_rule_set = sg.create("PermissionRuleSet", {"code": "Artist"})

    producer_rule_set = sg.create("PermissionRuleSet", {"code": "Producer"})

    # Create test users
    admin = sg.create(
        "HumanUser",
        {
            "login": "admin",
            "name": "Admin User",
            "email": "admin@example.com",
            "groups": [admin_group],
            "department": {"type": "Department", "id": it_department["id"]},
            "permission_rule_set": {"type": "PermissionRuleSet", "id": admin_rule_set["id"]},
        },
    )

    artist = sg.create(
        "HumanUser",
        {
            "login": "artist",
            "name": "Test Artist",
            "email": "artist@example.com",
            "groups": [artist_group],
            "department": {"type": "Department", "id": anim_department["id"]},
            "permission_rule_set": {"type": "PermissionRuleSet", "id": artist_rule_set["id"]},
        },
    )

    producer = sg.create(
        "HumanUser",
        {
            "login": "producer",
            "name": "Test Producer",
            "email": "producer@example.com",
            "groups": [producer_group],
            "department": {"type": "Department", "id": prod_department["id"]},
            "permission_rule_set": {"type": "PermissionRuleSet", "id": producer_rule_set["id"]},
        },
    )

    # Create multiple test projects
    main_project = sg.create(
        "Project",
        {
            "name": "Main Project",
            "code": "main",
            "sg_status": "Active",
            "sg_type": "Feature Film",
            "users": [admin, artist, producer],
            "sg_description": "Main test project",
        },
    )

    sg.create(
        "Project",
        {
            "name": "Archived Project",
            "code": "arch",
            "sg_status": "Archived",
            "sg_type": "Commercial",
            "users": [admin],
            "sg_description": "Archived test project",
        },
    )

    # Create test project
    project = sg.create(
        "Project",
        {
            "name": "Test Project",
            "code": "test",
            "description": "Test project for unit tests",
        },
    )

    # Create test sequences
    seq_01 = sg.create(
        "Sequence",
        {"project": main_project, "code": "SEQ_01", "description": "Opening sequence", "sg_status_list": "ip"},
    )

    sg.create(
        "Sequence",
        {"project": main_project, "code": "SEQ_02", "description": "Middle sequence", "sg_status_list": "wtg"},
    )

    # Create test shots with various states and data
    shot_010 = sg.create(
        "Shot",
        {
            "project": main_project,
            "code": "SEQ_01_010",
            "sg_sequence": seq_01,
            "sg_status_list": "fin",
            "description": "Opening shot",
            "sg_cut_in": 1001,
            "sg_cut_out": 1086,
            "sg_cut_duration": 86,
            "sg_working_duration": 90,
            "created_by": admin,
            "updated_by": artist,
        },
    )

    sg.create(
        "Shot",
        {
            "project": main_project,
            "code": "SEQ_01_020",
            "sg_sequence": seq_01,
            "sg_status_list": "ip",
            "description": "Character introduction",
            "sg_cut_in": 1087,
            "sg_cut_out": 1156,
            "sg_cut_duration": 70,
            "sg_working_duration": 75,
            "created_by": admin,
            "updated_by": artist,
        },
    )

    sg.create(
        "Shot",
        {
            "code": "test_shot",
            "project": {"type": "Project", "id": project["id"]},
            "description": "Test shot for unit tests",
        },
    )

    char_asset = sg.create(
        "Asset",
        {
            "project": main_project,
            "code": "CHAR_hero",
            "sg_asset_type": "Character",
            "description": "Hero character",
            "sg_status_list": "fin",
            "created_by": admin,
        },
    )

    sg.create(
        "Asset",
        {
            "project": main_project,
            "code": "PROP_weapon",
            "sg_asset_type": "Prop",
            "description": "Hero's weapon",
            "sg_status_list": "ip",
            "created_by": admin,
        },
    )

    sg.create(
        "Asset",
        {
            "project": main_project,
            "code": "ENV_castle",
            "sg_asset_type": "Environment",
            "description": "Castle environment",
            "sg_status_list": "wtg",
            "created_by": admin,
        },
    )

    # Create test steps
    model_step = sg.create("Step", {"code": "Model", "short_name": "mod", "description": "Modeling step"})

    rig_step = sg.create("Step", {"code": "Rig", "short_name": "rig", "description": "Rigging step"})

    anim_step = sg.create("Step", {"code": "Anim", "short_name": "anim", "description": "Animation step"})

    # Create test tasks with dependencies
    model_task = sg.create(
        "Task",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "content": "Hero Modeling",
            "step": {"type": "Step", "id": model_step["id"]},
            "entity": {"type": "Asset", "id": char_asset["id"]},
            "task_assignees": [{"type": "HumanUser", "id": artist["id"]}],
            "sg_status_list": "ip",
            "due_date": "2025-02-01",
            "duration": 5,
            "created_by": {"type": "HumanUser", "id": producer["id"]},
        },
    )

    rig_task = sg.create(
        "Task",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "content": "Hero Rigging",
            "step": {"type": "Step", "id": rig_step["id"]},
            "entity": {"type": "Asset", "id": char_asset["id"]},
            "task_assignees": [{"type": "HumanUser", "id": artist["id"]}],
            "sg_status_list": "wtg",
            "due_date": "2025-02-10",
            "duration": 7,
            "created_by": {"type": "HumanUser", "id": producer["id"]},
            "upstream_tasks": [model_task],
        },
    )

    anim_task = sg.create(
        "Task",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "content": "Shot Animation",
            "step": {"type": "Step", "id": anim_step["id"]},
            "entity": {"type": "Shot", "id": shot_010["id"]},
            "task_assignees": [{"type": "HumanUser", "id": artist["id"]}],
            "sg_status_list": "rdy",
            "due_date": "2025-02-20",
            "duration": 10,
            "created_by": {"type": "HumanUser", "id": producer["id"]},
            "upstream_tasks": [rig_task],
        },
    )

    # Create test versions
    model_version = sg.create(
        "Version",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "code": "hero_model_v001",
            "entity": {"type": "Asset", "id": char_asset["id"]},
            "sg_task": {"type": "Task", "id": model_task["id"]},
            "user": {"type": "HumanUser", "id": artist["id"]},
            "description": "Initial modeling",
            "sg_status_list": "rev",
            "sg_path_to_frames": "/path/to/model/v001",
            "sg_path_to_movie": "/path/to/model/v001/preview.mov",
            "created_by": {"type": "HumanUser", "id": artist["id"]},
            "sg_first_frame": 1001,
            "sg_last_frame": 1001,
            "frame_count": 1,
        },
    )

    anim_version = sg.create(
        "Version",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "code": "shot_010_anim_v001",
            "entity": {"type": "Shot", "id": shot_010["id"]},
            "sg_task": {"type": "Task", "id": anim_task["id"]},
            "user": {"type": "HumanUser", "id": artist["id"]},
            "description": "First pass animation",
            "sg_status_list": "rev",
            "sg_path_to_frames": "/path/to/anim/v001",
            "sg_path_to_movie": "/path/to/anim/v001/preview.mov",
            "created_by": {"type": "HumanUser", "id": artist["id"]},
            "sg_first_frame": 1001,
            "sg_last_frame": 1086,
            "frame_count": 86,
        },
    )

    # Create test playlists
    sg.create(
        "Playlist",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "code": "daily_review_0105",
            "description": "Daily review playlist",
            "versions": [model_version, anim_version],
            "created_by": {"type": "HumanUser", "id": producer["id"]},
        },
    )

    sg.create(
        "Playlist",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "code": "client_review_0105",
            "description": "Client review playlist",
            "versions": [anim_version],
            "created_by": {"type": "HumanUser", "id": producer["id"]},
        },
    )

    # Create test notes
    sg.create(
        "Note",
        {
            "project": {"type": "Project", "id": main_project["id"]},
            "content": "Please refine the topology around the eyes",
            "note_links": [model_version],
            "user": {"type": "HumanUser", "id": producer["id"]},
            "addressings_to": [artist],
            "tasks": [model_task],
            "created_by": {"type": "HumanUser", "id": producer["id"]},
            "sg_status_list": "opn",
        },
    )

    return sg


@pytest.fixture
def mock_context(mock_factory):
    """Create a mock ShotGrid connection context."""
    return ShotGridConnectionContext(factory=mock_factory)


@pytest.fixture
def server(mock_context, mock_sg):
    """Create a FastMCP server instance."""
    server = FastMCP(name="test-server")

    # Initialize tools with mock context and client
    ShotGridTools(server=server, sg=mock_sg)

    return server
