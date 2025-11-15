"""Type definitions for ShotGrid MCP server.

This module provides type definitions for ShotGrid API data custom_types.py
"""

# Import built-in modules
import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union

# Attachment result type
AttachmentResult = Union[bytes, str]

# ShotGrid entity types
# This is a fallback list of common entity types
# The actual list should be retrieved from ShotGrid schema at runtime
# using schema_loader.get_entity_types_from_schema
EntityType = str  # Use string type instead of Literal for flexibility

# Common entity type constants
PROJECT_ENTITY_TYPE = "Project"
SHOT_ENTITY_TYPE = "Shot"
ASSET_ENTITY_TYPE = "Asset"
TASK_ENTITY_TYPE = "Task"
VERSION_ENTITY_TYPE = "Version"
NOTE_ENTITY_TYPE = "Note"
PLAYLIST_ENTITY_TYPE = "Playlist"
HUMAN_USER_ENTITY_TYPE = "HumanUser"
GROUP_ENTITY_TYPE = "Group"
PUBLISHED_FILE_ENTITY_TYPE = "PublishedFile"

# Default field lists
DEFAULT_FIELDS = ["id", "code", "sg_status", "sg_status_list", "description"]
SHOT_FIELDS = DEFAULT_FIELDS + ["sg_camera_lens", "sg_camera_framing", "sg_camera_description", "sg_sequence"]

# ShotGrid data types
ShotGridDataType = Literal[
    "addressing",
    "checkbox",
    "color",
    "currency",
    "date",
    "date_time",
    "duration",
    "entity",
    "float",
    "footage",
    "image",
    "list",
    "multi_entity",
    "number",
    "password",
    "percent",
    "serializable",
    "status_list",
    "system_task_type",
    "tag_list",
    "text",
    "timecode",
    "url",
]

# ShotGrid filter operators
FilterOperator = Literal[
    "is",
    "is_not",
    "less_than",
    "greater_than",
    "contains",
    "not_contains",
    "starts_with",
    "ends_with",
    "between",
    "not_between",
    "in",
    "not_in",
    "in_last",
    "not_in_last",
    "in_next",
    "not_in_next",
    "in_calendar_day",
    "in_calendar_week",
    "in_calendar_month",
    "in_calendar_year",
    "name_contains",
    "name_not_contains",
    "name_is",
    "type_is",
    "type_is_not",
]


# ShotGrid entity reference
class EntityRef(TypedDict):
    """ShotGrid entity reference."""

    type: str
    id: int
    name: Optional[str]


# ShotGrid URL field
class UrlField(TypedDict):
    """ShotGrid URL field."""

    content_type: str
    link_type: Literal["local", "url", "upload"]
    name: str
    url: str


# ShotGrid local file URL field
class LocalUrlField(UrlField):
    """ShotGrid local file URL field."""

    # Note: link_type is already defined in UrlField
    local_path: Optional[str]
    local_path_linux: Optional[str]
    local_path_mac: Optional[str]
    local_path_windows: Optional[str]
    local_storage: Dict[str, Any]


# ShotGrid filter
Filter = Tuple[str, FilterOperator, Any]


# ShotGrid batch request
class BatchRequest(TypedDict):
    """ShotGrid batch request."""

    request_type: Literal["create", "update", "delete"]
    entity_type: str
    data: Dict[str, Any]
    entity_id: Optional[int]  # Required for update and delete


# ShotGrid field schema
class FieldSchema(TypedDict):
    """ShotGrid field schema."""

    data_type: Dict[str, str]
    properties: Dict[str, Dict[str, Any]]


# ShotGrid entity schema
class EntitySchema(TypedDict):
    """ShotGrid entity schema."""

    type: str
    fields: Dict[str, Dict[str, Any]]


# ShotGrid value types
ShotGridValue = Union[
    None,
    bool,
    int,
    float,
    str,
    datetime.datetime,
    datetime.date,
    Dict[str, Any],
    List[Dict[str, Any]],
    List[str],
]


# ShotGrid entity
class Entity(TypedDict, total=False):
    """ShotGrid entity."""

    type: str
    id: int
    name: Optional[str]
    code: Optional[str]
    project: Optional[EntityRef]
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]
    created_by: Optional[EntityRef]
    updated_by: Optional[EntityRef]
    sg_status_list: Optional[str]
    description: Optional[str]
    image: Optional[str]
    tags: Optional[List[EntityRef]]
    attachments: Optional[Union[str, List[Dict[str, Any]]]]


# ShotGrid event types
EventType = Literal[
    "Shotgun_Asset_Change",
    "Shotgun_Asset_New",
    "Shotgun_Asset_Retirement",
    "Shotgun_Asset_Revival",
    "Shotgun_Attachment_Change",
    "Shotgun_Attachment_New",
    "Shotgun_Attachment_Retirement",
    "Shotgun_Attachment_Revival",
    "Shotgun_Attachment_View",
    "Shotgun_Department_Change",
    "Shotgun_Department_New",
    "Shotgun_Department_Retirement",
    "Shotgun_Department_Revival",
    "Shotgun_Group_Change",
    "Shotgun_Group_New",
    "Shotgun_Group_Retirement",
    "Shotgun_Group_Revival",
    "Shotgun_HumanUser_Change",
    "Shotgun_HumanUser_New",
    "Shotgun_HumanUser_Retirement",
    "Shotgun_HumanUser_Revival",
    "Shotgun_Note_Change",
    "Shotgun_Note_New",
    "Shotgun_Note_Retirement",
    "Shotgun_Note_Revival",
    "Shotgun_Pipeline_Change",
    "Shotgun_Pipeline_New",
    "Shotgun_Pipeline_Retirement",
    "Shotgun_Pipeline_Revival",
    "Shotgun_Project_Change",
    "Shotgun_Project_New",
    "Shotgun_Project_Retirement",
    "Shotgun_Project_Revival",
    "Shotgun_PublishedFile_Change",
    "Shotgun_PublishedFile_New",
    "Shotgun_PublishedFile_Retirement",
    "Shotgun_PublishedFile_Revival",
    "Shotgun_Reading_Change",
    "Shotgun_Sequence_Change",
    "Shotgun_Sequence_New",
    "Shotgun_Sequence_Retirement",
    "Shotgun_Sequence_Revival",
    "Shotgun_Shot_Change",
    "Shotgun_Shot_New",
    "Shotgun_Shot_Retirement",
    "Shotgun_Shot_Revival",
    "Shotgun_Step_Change",
    "Shotgun_Step_New",
    "Shotgun_Step_Retirement",
    "Shotgun_Step_Revival",
    "Shotgun_Task_Change",
    "Shotgun_Task_New",
    "Shotgun_Task_Retirement",
    "Shotgun_Task_Revival",
    "Shotgun_User_Login",
    "Shotgun_User_Logout",
    "Shotgun_Version_Change",
    "Shotgun_Version_New",
    "Shotgun_Version_Retirement",
    "Shotgun_Version_Revival",
]


# ShotGrid additional filter presets
class AdditionalFilterPreset(TypedDict, total=False):
    """ShotGrid additional filter preset."""

    preset_name: str
    latest_by: str
    cut_id: int
