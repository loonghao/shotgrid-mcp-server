import datetime
from typing import Any, Dict, List, Optional

from shotgun_api3 import ShotgunError
from shotgun_api3.lib.mockgun import Shotgun


class MockgunExt(Shotgun):
    """Extended Mockgun class with additional functionality"""

    def __init__(self, base_url, *args, **kwargs):
        """Initialize MockgunExt.

        Args:
            base_url: The base URL for the ShotGrid instance.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(base_url, *args, **kwargs)
        self._db = {}
        for entity_type in self._schema:
            self._db[entity_type] = {}

    def _validate_multi_entity_field(self, entity_type: str, field: str, item: Any, field_info: Dict[str, Any]) -> None:
        """Validate a multi-entity field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        if not isinstance(item, list):
            item = [item]

        if not item:
            return

        # Check if any item is missing type or id
        missing_fields = any("id" not in sub_item or "type" not in sub_item for sub_item in item)
        if missing_fields:
            err_msg = (
                f"{entity_type}.{field} is of type multi_entity, "
                f"but an item in data {item} does not contain 'type' and 'id'"
            )
            raise ShotgunError(err_msg)

        # Check if any item has invalid type
        valid_types = field_info["properties"]["valid_types"]["value"]
        invalid_types = any(sub_item.get("type") not in valid_types for sub_item in item if sub_item)
        if invalid_types:
            err_msg = (
                f"{entity_type}.{field} is of multi-type entity, "
                f"but an item in data {item} has an invalid type "
                f"(expected one of {valid_types})"
            )
            raise ShotgunError(err_msg)

    def _validate_entity_field(self, entity_type: str, field: str, item: Any, field_info: Dict[str, Any]) -> None:
        """Validate an entity field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        if item is None:
            return

        if not isinstance(item, dict):
            raise ShotgunError(f"{entity_type}.{field} is of type entity, but data {item} is not a dict")

        if "id" not in item or "type" not in item:
            raise ShotgunError(f"{entity_type}.{field} is of type entity, but data {item} does not contain type or id")

        valid_types = field_info["properties"]["valid_types"]["value"]
        if item["type"] not in valid_types:
            raise ShotgunError(
                f"{entity_type}.{field} is of type entity, "
                f"but data {item} has invalid type (expected one of {valid_types})"
            )

    def _validate_simple_field(self, entity_type: str, field: str, item: Any, field_info: Dict[str, Any]) -> None:
        """Validate a simple field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        sg_type = field_info["data_type"]["value"]
        try:
            python_type = {
                "number": int,
                "float": float,
                "text": str,
                "date": datetime.date,
                "date_time": datetime.datetime,
                "checkbox": bool,
                "percent": int,
                "url": dict,
                "status_list": str,
                "list": str,
                "color": str,
                "tag_list": list,
                "duration": int,
                "image": dict,
            }[sg_type]
        except KeyError as err:
            err_msg = (
                f"Field {entity_type}.{field}: "
                f"Handling for Flow Production Tracking type {sg_type} is not implemented"
            )
            raise ShotgunError(err_msg) from err

        if not isinstance(item, python_type):
            raise ShotgunError(
                f"{entity_type}.{field} is of type {sg_type}, but data {item} is not of type {python_type}"
            )

    def _validate_entity_data(self, entity_type: str, data: Dict[str, Any]) -> None:
        """Validate entity data before creation or update.

        Args:
            entity_type: Type of entity.
            data: Entity data.

        Raises:
            ShotgunError: If validation fails.
        """
        if "id" in data or "type" in data:
            raise ShotgunError("Can't include id or type fields in data dict")

        fields = self.schema_field_read(entity_type)

        for field, item in data.items():
            field_info = fields.get(field)
            if not field_info:
                continue

            if item is None:
                continue

            field_type = field_info["data_type"]["value"]
            if field_type == "multi_entity":
                self._validate_multi_entity_field(entity_type, field, item, field_info)
            elif field_type == "entity":
                self._validate_entity_field(entity_type, field, item, field_info)
            else:
                self._validate_simple_field(entity_type, field, item, field_info)

    def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an entity in the mock database.

        Args:
            entity_type: Type of entity to create.
            data: Entity data.

        Returns:
            Dict[str, Any]: Created entity data.
        """
        # Validate data
        self._validate_entity_data(entity_type, data)

        # Create entity
        entity_id = len(self._db[entity_type]) + 1
        entity = {"id": entity_id, "type": entity_type, **data}
        self._db[entity_type][entity_id] = entity

        return entity

    def delete(self, entity_type, entity_id):
        """Delete an entity from the mock database.

        Args:
            entity_type (str): Type of entity to delete.
            entity_id (int): ID of the entity.
        """
        if entity_type in self._db and entity_id in self._db[entity_type]:
            del self._db[entity_type][entity_id]

    def download_attachment(self, attachment_data, file_path=None):
        """Download an attachment from the mock database.

        Args:
            attachment_data (dict): Attachment data containing URL or ID.
            file_path (str, optional): Path to save the file. Defaults to None.

        Returns:
            bytes: Mock attachment data.
        """
        # For testing purposes, return some mock data
        mock_data = b"Mock attachment data"

        if file_path:
            with open(file_path, "wb") as f:
                f.write(mock_data)
            return file_path
        return mock_data

    def _apply_filter(self, entity: Any, filter_item: List[Any]) -> bool:
        """Apply a single filter to an entity.

        Args:
            entity: Entity to filter.
            filter_item: Filter condition.

        Returns:
            bool: True if entity matches filter, False otherwise.
        """
        field, operator, value = filter_item

        if operator == "is":
            if isinstance(entity, dict):
                return entity.get(field) == value
            return getattr(entity, field, None) == value

        if operator == "is_not":
            if isinstance(entity, dict):
                return entity.get(field) != value
            return getattr(entity, field, None) != value

        if operator == "in":
            if isinstance(entity, dict):
                return entity.get(field) in value
            return getattr(entity, field, None) in value

        if operator == "not_in":
            if isinstance(entity, dict):
                return entity.get(field) not in value
            return getattr(entity, field, None) not in value

        return False

    def _apply_filters(self, entity: Any, filters: List[List[Any]], filter_operator: str = "and") -> bool:
        """Apply filters to an entity.

        Args:
            entity: Entity to filter.
            filters: List of filter conditions.
            filter_operator: Operator to combine filters.

        Returns:
            bool: True if entity matches filters, False otherwise.
        """
        if not filters:
            return True

        results = [self._apply_filter(entity, filter_item) for filter_item in filters]

        if filter_operator == "or":
            return any(results)
        return all(results)

    def _format_entity(self, entity: Any, fields: List[str]) -> Dict[str, Any]:
        """Format an entity for output.

        Args:
            entity: Entity to format.
            fields: Fields to include.

        Returns:
            Dict[str, Any]: Formatted entity.
        """
        if isinstance(entity, dict):
            if fields:
                return {field: entity.get(field) for field in fields}
            return entity.copy()

        if fields:
            return {field: getattr(entity, field, None) for field in fields}
        return {k: v for k, v in vars(entity).items() if not k.startswith("_")}

    def find(
        self,
        entity_type: str,
        filters: List[List[Any]],
        fields: Optional[List[str]] = None,
        order: Optional[List[str]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find entities in the mock database.

        Args:
            entity_type: Type of entity to find.
            filters: List of filter conditions.
            fields: List of fields to return.
            order: List of fields to order by.
            filter_operator: Operator to combine filters.
            limit: Maximum number of entities to return.

        Returns:
            List[Dict[str, Any]]: List of found entities.
        """
        if entity_type not in self._db:
            return []

        # Apply filters
        entities = []
        for entity in self._db[entity_type].values():
            if self._apply_filters(entity, filters, filter_operator):
                formatted_entity = self._format_entity(entity, fields or [])
                entities.append(formatted_entity)

        # Sort entities if order is specified
        if order:
            for field in reversed(order):
                reverse = False
                if field.startswith("-"):
                    field = field[1:]
                    reverse = True
                entities.sort(key=lambda x: x.get(field), reverse=reverse)

        # Apply limit
        if limit is not None and limit > 0:
            entities = entities[:limit]

        return entities

    def find_one(
        self,
        entity_type: str,
        filters: List[List[Any]],
        fields: Optional[List[str]] = None,
        order: Optional[List[str]] = None,
        filter_operator: Optional[str] = None,
        retired_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Find a single entity in the mock database.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply.
            fields: List of fields to return.
            order: List of fields to order by.
            filter_operator: Operator to use for filters.
            retired_only: Whether to return only retired entities.

        Returns:
            Optional[Dict[str, Any]]: The found entity, or None if not found.
        """
        results = self.find(entity_type, filters, fields, order, filter_operator, limit=1)
        if not results:
            return None
            
        # Add type field to entity
        entity = results[0]
        if isinstance(entity, dict):
            entity["type"] = entity_type
        return entity

    def get_thumbnail_url(
        self,
        entity_type: str,
        entity_id: int,
        field_name: str = "image",
    ) -> str:
        """Get the URL for an entity's thumbnail.

        Args:
            entity_type: The entity type.
            entity_id: The entity ID.
            field_name: The field name for the thumbnail.

        Returns:
            str: The thumbnail URL.

        Raises:
            ShotgunError: If the entity is not found or has no thumbnail.
        """
        entity = self.find_one(entity_type, [["id", "is", entity_id]])
        if not entity:
            raise ShotgunError(f"Entity {entity_type} with id {entity_id} not found")
        
        if field_name not in entity or not entity[field_name]:
            raise ShotgunError(f"Entity {entity_type} with id {entity_id} has no {field_name}")
        
        return "https://example.com/thumbnail.jpg"

    def get_attachment_download_url(self, entity_type, entity_id, field_name):
        """Get the download URL for an attachment.

        Args:
            entity_type (str): Type of entity.
            entity_id (int): ID of the entity.
            field_name (str): Name of the attachment field.

        Returns:
            str: Mock download URL.

        Raises:
            ShotgunError: If the entity is not found or has no attachment.
        """
        # Find entity
        entity = self.find_one(entity_type, [["id", "is", entity_id]], [field_name])
        if not entity:
            raise ShotgunError(f"Entity {entity_type} with ID {entity_id} not found")

        # Check if entity has attachment field
        if field_name not in entity or not entity[field_name]:
            return None

        # Get URL from attachment field
        attachment = entity[field_name]
        if isinstance(attachment, dict):
            if "url" in attachment:
                return attachment["url"]
            elif "name" in attachment:
                return attachment["name"]
            elif "type" in attachment and attachment["type"] == "Attachment":
                return attachment.get("url", None)
        elif isinstance(attachment, str):
            return attachment

        # No valid URL found
        return None

    def schema_read(self, entity_type=None):
        """Read schema information from the mock database.

        Args:
            entity_type (str, optional): Type of entity to get schema for. Defaults to None.

        Returns:
            dict: Schema information for the entity type.
        """
        schema = {
            "Shot": {
                "type": "entity",
                "fields": {
                    "id": {
                        "data_type": {"value": "number"},
                        "properties": {"default_value": {"value": None}, "valid_types": {"value": ["number"]}},
                    },
                    "type": {
                        "data_type": {"value": "text"},
                        "properties": {"default_value": {"value": "Shot"}, "valid_types": {"value": ["text"]}},
                    },
                    "code": {
                        "data_type": {"value": "text"},
                        "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
                    },
                    "project": {
                        "data_type": {"value": "entity"},
                        "properties": {"default_value": {"value": None}, "valid_types": {"value": ["Project"]}},
                    },
                    "image": {
                        "data_type": {"value": "image"},
                        "properties": {"default_value": {"value": None}, "valid_types": {"value": ["image"]}},
                    },
                },
            }
        }
        if entity_type:
            return schema.get(entity_type, {"type": "entity", "fields": {}})
        return schema
