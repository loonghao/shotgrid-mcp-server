"""Tests for schema caching functionality."""

import tempfile

import pytest

from shotgrid_mcp_server.schema_cache import SchemaCache, get_schema_cache


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def schema_cache(temp_cache_dir):
    """Create a schema cache instance for testing."""
    cache = SchemaCache(cache_dir=temp_cache_dir, ttl=60)
    yield cache
    cache.close()


def test_entity_schema_cache(schema_cache):
    """Test caching and retrieving entity schemas."""
    # Initially, cache should be empty
    assert schema_cache.get_entity_schema("Shot") is None

    # Set schema
    schema_data = {
        "code": {"data_type": "text", "editable": True},
        "sg_status_list": {"data_type": "status_list", "editable": True},
    }
    schema_cache.set_entity_schema("Shot", schema_data)

    # Retrieve schema
    cached_schema = schema_cache.get_entity_schema("Shot")
    assert cached_schema == schema_data


def test_field_schema_cache(schema_cache):
    """Test caching and retrieving field schemas."""
    # Initially, cache should be empty
    assert schema_cache.get_field_schema("Shot", "code") is None

    # Set field schema
    field_schema = {"data_type": "text", "editable": True, "name": "Shot Code"}
    schema_cache.set_field_schema("Shot", "code", field_schema)

    # Retrieve field schema
    cached_field = schema_cache.get_field_schema("Shot", "code")
    assert cached_field == field_schema


def test_entity_types_cache(schema_cache):
    """Test caching and retrieving entity types."""
    # Initially, cache should be empty
    assert schema_cache.get_entity_types() is None

    # Set entity types
    entity_types = {"Shot": {"name": "Shot", "visible": True}, "Asset": {"name": "Asset", "visible": True}}
    schema_cache.set_entity_types(entity_types)

    # Retrieve entity types
    cached_types = schema_cache.get_entity_types()
    assert cached_types == entity_types


def test_cache_clear(schema_cache):
    """Test clearing the cache."""
    # Add some data
    schema_cache.set_entity_schema("Shot", {"code": {"data_type": "text"}})
    schema_cache.set_field_schema("Shot", "code", {"data_type": "text"})
    schema_cache.set_entity_types({"Shot": {"name": "Shot"}})

    # Verify data is cached
    assert schema_cache.get_entity_schema("Shot") is not None
    assert schema_cache.get_field_schema("Shot", "code") is not None
    assert schema_cache.get_entity_types() is not None

    # Clear cache
    schema_cache.clear()

    # Verify cache is empty
    assert schema_cache.get_entity_schema("Shot") is None
    assert schema_cache.get_field_schema("Shot", "code") is None
    assert schema_cache.get_entity_types() is None


def test_global_cache_instance():
    """Test getting the global cache instance."""
    # Import the module to reset global cache
    import shotgrid_mcp_server.schema_cache as schema_cache_module

    # Reset global cache before test
    if schema_cache_module._global_cache is not None:
        schema_cache_module._global_cache.close()
        schema_cache_module._global_cache = None

    try:
        cache1 = get_schema_cache()
        cache2 = get_schema_cache()

        # Should return the same instance
        assert cache1 is cache2
    finally:
        # Clean up global cache after test
        if schema_cache_module._global_cache is not None:
            schema_cache_module._global_cache.close()
            schema_cache_module._global_cache = None


def test_cache_persistence(temp_cache_dir):
    """Test that cache persists across instances."""
    # Create first cache instance and add data
    cache1 = SchemaCache(cache_dir=temp_cache_dir, ttl=60)
    schema_data = {"code": {"data_type": "text"}}
    cache1.set_entity_schema("Shot", schema_data)
    cache1.close()

    # Create second cache instance with same directory
    cache2 = SchemaCache(cache_dir=temp_cache_dir, ttl=60)
    cached_schema = cache2.get_entity_schema("Shot")
    cache2.close()

    # Data should persist
    assert cached_schema == schema_data


@pytest.mark.skip(reason="diskcache_rs 0.4.4 TTL expiration not yet implemented")
def test_cache_ttl_expiration(temp_cache_dir):
    """Test that cache entries expire after TTL."""
    import time

    # Create cache with very short TTL (1 second)
    cache = SchemaCache(cache_dir=temp_cache_dir, ttl=1)

    # Add data
    schema_data = {"code": {"data_type": "text"}}
    cache.set_entity_schema("Shot", schema_data)

    # Immediately retrieve - should be cached
    assert cache.get_entity_schema("Shot") == schema_data

    # Wait for TTL to expire
    time.sleep(2)

    # Should be expired
    assert cache.get_entity_schema("Shot") is None

    cache.close()
