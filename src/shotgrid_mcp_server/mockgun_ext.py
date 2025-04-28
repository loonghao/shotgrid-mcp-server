"""ShotGrid mock client implementation with extended functionality."""

# Import built-in modules
import datetime
from typing import Any, Dict, List, Optional, TypeVar

# Import third-party modules
from shotgun_api3 import ShotgunError
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.custom_types import (
    AttachmentResult,
    Entity,
    EntityType,
    FieldSchema,
    Filter,
    ShotGridDataType,
    ShotGridValue,
)

T = TypeVar("T")


class MockgunExt(Shotgun):  # type: ignore[misc]
    """Extended Mockgun class with additional functionality."""

    def __init__(self, base_url: str, *args: Any, **kwargs: Any) -> None:
        """Initialize MockgunExt.

        Args:
            base_url: The base URL for the ShotGrid instance.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(base_url, *args, **kwargs)
        self._db: Dict[str, Dict[int, Dict[str, Any]]] = {}
        for entity_type in self._schema:
            self._db[entity_type] = {}

    # Type mapping from ShotGrid types to Python types
    _TYPE_MAPPING = {
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
    }

    def _validate_field(self, entity_type: str, field: str, item: ShotGridValue, field_info: FieldSchema) -> None:
        """Validate a field value against its schema definition.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        # Skip validation for None values
        if item is None:
            return

        # Get field type
        field_type = field_info["data_type"]["value"]

        # Validate based on field type
        if field_type == "multi_entity":
            self._validate_multi_entity_field(entity_type, field, item, field_info)
        elif field_type == "entity":
            self._validate_entity_field(entity_type, field, item, field_info)
        else:
            self._validate_simple_field(entity_type, field, item, field_info, field_type)

    def _validate_multi_entity_field(self, entity_type: str, field: str, item: Any, field_info: FieldSchema) -> None:
        """Validate a multi-entity field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        # Ensure item is a list
        if not isinstance(item, list):
            item = [item]

        # Empty list is valid
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

    def _validate_entity_field(self, entity_type: str, field: str, item: Any, field_info: FieldSchema) -> None:
        """Validate an entity field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.

        Raises:
            ShotgunError: If validation fails.
        """
        # Check if item is a dictionary
        if not isinstance(item, dict):
            raise ShotgunError(f"{entity_type}.{field} is of type entity, but data {item} is not a dict")

        # Check if item has required fields
        if "id" not in item or "type" not in item:
            raise ShotgunError(f"{entity_type}.{field} is of type entity, but data {item} does not contain type or id")

        # Check if item has valid type
        valid_types = field_info["properties"]["valid_types"]["value"]
        if item["type"] not in valid_types:
            raise ShotgunError(
                f"{entity_type}.{field} is of type entity, "
                f"but data {item} has invalid type (expected one of {valid_types})"
            )

    def _validate_simple_field(
        self,
        entity_type: str,
        field: str,
        item: Any,
        field_info: FieldSchema,
        field_type: ShotGridDataType,  # type: ignore[arg-type]
    ) -> None:
        """Validate a simple field.

        Args:
            entity_type: Type of entity.
            field: Field name.
            item: Field value.
            field_info: Field information.
            field_type: Type of field.

        Raises:
            ShotgunError: If validation fails.
        """
        try:
            # Get expected Python type for this field type
            python_type = self._TYPE_MAPPING[field_type]
        except KeyError as err:
            err_msg = (
                f"Field {entity_type}.{field}: "
                f"Handling for Flow Production Tracking type {field_type} is not implemented"
            )
            raise ShotgunError(err_msg) from err

        # Check if item is of expected type
        if not isinstance(item, python_type):
            raise ShotgunError(
                f"{entity_type}.{field} is of type {field_type}, but data {item} is not of type {python_type}"
            )

    def _validate_entity_data(self, entity_type: EntityType, data: Dict[str, ShotGridValue]) -> None:
        """Validate entity data before creation or update.

        Args:
            entity_type: Type of entity.
            data: Entity data.

        Raises:
            ShotgunError: If validation fails.
        """
        # Check for reserved fields
        if "id" in data or "type" in data:
            raise ShotgunError("Can't include id or type fields in data dict")

        # Get schema for entity type
        fields = self.schema_field_read(entity_type)

        # Validate each field
        for field, item in data.items():
            field_info = fields.get(field)
            if not field_info or item is None:
                continue

            # Validate field value
            self._validate_field(entity_type, field, item, field_info)

    def _validate_entity_exists(self, entity_type: str, entity_id: int) -> bool:
        """Validate that an entity exists in the database.

        Args:
            entity_type: Type of entity.
            entity_id: ID of the entity.

        Returns:
            bool: True if entity exists, False otherwise.
        """
        return entity_type in self._db and entity_id in self._db[entity_type]

    def _validate_entity_type(self, entity_type: str) -> bool:
        """Validate that an entity type exists in the schema.

        Args:
            entity_type: Type of entity.

        Returns:
            bool: True if entity type exists, False otherwise.
        """
        return entity_type in self._schema

    def _get_field_info(self, entity_type: EntityType, field: str) -> FieldSchema:  # type: ignore[return-value]
        """Get field information from the schema.

        Args:
            entity_type: Type of entity.
            field: Field name.

        Returns:
            dict: Field information from schema.
        """
        if entity_type in self._schema and field in self._schema[entity_type]:
            return self._schema[entity_type][field]
        return {}

    def create(self, entity_type: EntityType, data: Dict[str, ShotGridValue]) -> Entity:  # type: ignore[return-value]
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

    def delete(self, entity_type: str, entity_id: int) -> None:
        """Delete an entity from the mock database.

        Args:
            entity_type: Type of entity to delete.
            entity_id: ID of the entity.
        """
        if entity_type in self._db and entity_id in self._db[entity_type]:
            del self._db[entity_type][entity_id]

    def download_attachment(self, attachment_data: Dict[str, Any], file_path: Optional[str] = None) -> AttachmentResult:
        """Download an attachment from the mock database.

        Args:
            attachment_data: Attachment data containing URL or ID.
            file_path: Path to save the file.

        Returns:
            Union[bytes, str]: Mock attachment data or file path.
        """
        # For testing purposes, return some mock data
        mock_data = b"Mock attachment data"

        if file_path:
            with open(file_path, "wb") as f:
                f.write(mock_data)
            return file_path
        return mock_data

    def _apply_filter(self, entity: Entity, filter_item: Filter) -> bool:  # type: ignore[arg-type]
        """Apply a single filter to an entity.

        Args:
            entity: Entity to filter.
            filter_item: Filter condition.

        Returns:
            bool: True if entity matches filter, False otherwise.
        """
        # Handle both tuple format and dict format
        if (
            isinstance(filter_item, dict)
            and "field" in filter_item
            and "operator" in filter_item
            and "value" in filter_item
        ):
            field_name = filter_item["field"]
            operator = filter_item["operator"]
            value = filter_item["value"]
        else:
            # Assume tuple format
            field_name = filter_item[0]
            operator = filter_item[1]
            value = filter_item[2]

        if field_name not in entity:
            return False

        entity_value = entity[field_name]

        if operator == "is":
            return bool(entity_value == value)
        if operator == "is_not":
            return bool(entity_value != value)
        if operator == "less_than":
            return bool(entity_value < value)
        if operator == "greater_than":
            return bool(entity_value > value)
        if operator == "contains":
            return bool(value in entity_value)
        if operator == "in":
            return bool(entity_value in value)

        return False

    def _apply_filters(self, entity: Entity, filters: List[Filter], filter_operator: Optional[str] = "and") -> bool:  # type: ignore[arg-type]
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

    def _format_entity(self, entity: Any, fields: List[str]) -> Entity:  # type: ignore[return-value]
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

    def _parse_order_item(self, order_item):
        """Parse an order item into field name and sort direction.

        Args:
            order_item: The order item to parse.

        Returns:
            tuple: (field_name, reverse) or (None, None) if invalid.
        """
        if isinstance(order_item, str):
            field_name = order_item
            reverse = False
            if field_name.startswith("-"):
                field_name = field_name[1:]
                reverse = True
            return field_name, reverse
        elif isinstance(order_item, dict):
            field_name = order_item.get("field_name", "")
            reverse = order_item.get("direction", "") == "desc"
            return field_name, reverse
        else:
            # Invalid order item
            return None, None

    def _sort_entities(self, entities, order):
        """Sort entities based on order specifications.

        Args:
            entities: List of entities to sort.
            order: List of order specifications.

        Returns:
            list: Sorted entities.
        """
        if not order:
            return entities

        sorted_entities = entities.copy()
        for order_item in reversed(order):
            field_name, reverse = self._parse_order_item(order_item)
            if field_name is None:
                continue

            # Create a closure to capture field_name
            def make_sort_key(field):
                def sort_key(x):
                    value = x.get(field)
                    if isinstance(value, dict):
                        # Use the id field if available, otherwise use str representation
                        return value.get("id", str(value))
                    return value

                return sort_key

            # Sort entities
            sorted_entities.sort(key=make_sort_key(field_name), reverse=reverse)  # type: ignore[arg-type]

        return sorted_entities

    def find(
        self,
        entity_type: EntityType,
        filters: List[Filter],
        fields: Optional[List[str]] = None,
        order: Optional[List[str]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
        retired_only: bool = False,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[Entity]:
        """Find entities in the mock database.

        Args:
            entity_type: Type of entity to find.
            filters: List of filter conditions.
            fields: List of fields to return.
            order: List of fields to order by.
            filter_operator: Operator to combine filters.
            limit: Maximum number of entities to return.
            retired_only: Whether to return only retired entities (not used in mock).
            page: Page number for pagination.
            page_size: Page size for pagination.

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
            entities = self._sort_entities(entities, order)

        # Apply pagination if both page and page_size are specified
        if page is not None and page_size is not None and page > 0 and page_size > 0:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            entities = entities[start_idx:end_idx]
        # Otherwise apply limit
        elif limit is not None and limit > 0:
            entities = entities[:limit]

        return entities

    def find_one(
        self,
        entity_type: EntityType,
        filters: List[Filter],
        fields: Optional[List[str]] = None,
        order: Optional[List[str]] = None,
        filter_operator: Optional[str] = None,
        retired_only: bool = False,
        page: Optional[int] = None,
    ) -> Optional[Entity]:
        """Find a single entity in the mock database.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply.
            fields: List of fields to return.
            order: List of fields to order by.
            filter_operator: Operator to use for filters.
            retired_only: Whether to return only retired entities (not used in mock).
            page: Page number for pagination (not used in find_one).

        Returns:
            Optional[Dict[str, Any]]: The found entity, or None if not found.
        """
        # For find_one, we always limit to 1 result regardless of pagination
        results = self.find(
            entity_type,
            filters,
            fields,
            order,
            filter_operator,
            limit=1,
            retired_only=retired_only,
            page=page,
            page_size=1 if page is not None else None,
        )
        if not results:
            return None

        # Add type field to entity
        entity = results[0]
        if isinstance(entity, dict):
            entity["type"] = entity_type
        return entity

    def get_thumbnail_url(
        self,
        entity_type: EntityType,
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
        entity = self.find_one(entity_type, [{"field": "id", "operator": "is", "value": entity_id}])
        if not entity:
            raise ShotgunError(f"Entity {entity_type} with id {entity_id} not found")

        if field_name not in entity or not entity[field_name]:
            raise ShotgunError(f"Entity {entity_type} with id {entity_id} has no {field_name}")

        return "https://example.com/thumbnail.jpg"

    def get_attachment_download_url(self, entity_type: EntityType, entity_id: int, field_name: str) -> str:
        """Get the download URL for an attachment.

        Args:
            entity_type: Type of entity.
            entity_id: ID of the entity.
            field_name: Name of the attachment field.

        Returns:
            str: Mock download URL.

        Raises:
            ShotgunError: If the entity is not found or has no attachment.
        """
        # Find entity
        entity = self.find_one(entity_type, [{"field": "id", "operator": "is", "value": entity_id}], [field_name])
        if not entity:
            raise ShotgunError(f"Entity {entity_type} with ID {entity_id} not found")

        # Check if entity has attachment field
        if field_name not in entity or not entity[field_name]:
            raise ShotgunError(f"Entity {entity_type} with ID {entity_id} has no attachment in field {field_name}")

        # Get URL from attachment field
        attachment = entity[field_name]
        if isinstance(attachment, dict):
            if "url" in attachment:
                return str(attachment["url"])
            elif "name" in attachment:
                return str(attachment["name"])
            elif "type" in attachment and attachment["type"] == "Attachment":
                if "url" not in attachment:
                    raise ShotgunError(f"Attachment in {entity_type}.{field_name} has no URL")
                return str(attachment["url"])
        elif isinstance(attachment, str):
            return attachment

        raise ShotgunError(f"Invalid attachment format in {entity_type}.{field_name}")

    def schema_read(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Read schema information from the mock database.

        Args:
            entity_type: Type of entity to get schema for.

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

    def batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch request.

        Args:
            requests: List of request dictionaries.
                Each request should have:
                - request_type: Type of request (create, update, delete)
                - entity_type: Type of entity
                - data: Entity data for create/update
                - entity_id: Entity ID for update/delete

        Returns:
            List[Dict[str, Any]]: List of results, one per request.

        Raises:
            ShotgunError: If any request fails.
        """
        results = []
        for request in requests:
            request_type = request["request_type"]
            entity_type = request["entity_type"]

            try:
                if request_type == "create":
                    # Validate data
                    self._validate_entity_data(entity_type, request["data"])

                    # Create entity
                    entity_id = len(self._db[entity_type]) + 1
                    entity = {"id": entity_id, "type": entity_type, **request["data"]}
                    self._db[entity_type][entity_id] = entity
                    results.append(entity)
                elif request_type == "update":
                    result = self.update(entity_type, request["entity_id"], request["data"])
                    results.append(result)
                elif request_type == "delete":
                    self.delete(entity_type, request["entity_id"])
                    # Return a dictionary for delete operation to maintain consistent return type
                    results.append({"id": request["entity_id"], "type": entity_type, "status": "deleted"})
                else:
                    raise ShotgunError(f"Unknown request type: {request_type}")
            except Exception as err:
                raise ShotgunError(f"Batch operation failed: {str(err)}") from err

        return results
