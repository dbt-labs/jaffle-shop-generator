"""Tests for schema constants."""

import pytest

from jafgen.schema.constants import (
    SUPPORTED_ATTRIBUTE_TYPES,
    SUPPORTED_OUTPUT_FORMATS,
    REQUIRED_SYSTEM_FIELDS,
    REQUIRED_ENTITY_FIELDS,
    REQUIRED_ATTRIBUTE_FIELDS
)


class TestSchemaConstants:
    """Test cases for schema constants."""
    
    def test_supported_attribute_types(self):
        """Test that supported attribute types are defined."""
        assert isinstance(SUPPORTED_ATTRIBUTE_TYPES, (list, tuple, set))
        assert len(SUPPORTED_ATTRIBUTE_TYPES) > 0
        
        # Check for common types that should be supported
        expected_types = [
            "uuid", "person.full_name", "person.email", 
            "boolean", "text.word", "numeric.decimal",
            "datetime.datetime", "datetime.date", "link"
        ]
        
        for expected_type in expected_types:
            assert expected_type in SUPPORTED_ATTRIBUTE_TYPES
    
    def test_supported_output_formats(self):
        """Test that supported output formats are defined."""
        assert isinstance(SUPPORTED_OUTPUT_FORMATS, (list, tuple, set))
        assert len(SUPPORTED_OUTPUT_FORMATS) > 0
        
        # Check for expected formats
        expected_formats = ["csv", "json", "parquet", "duckdb"]
        
        for expected_format in expected_formats:
            assert expected_format in SUPPORTED_OUTPUT_FORMATS
    
    def test_required_system_fields(self):
        """Test that required system fields are defined."""
        assert isinstance(REQUIRED_SYSTEM_FIELDS, set)
        assert len(REQUIRED_SYSTEM_FIELDS) > 0
        
        expected_fields = {"name", "version", "entities"}
        assert expected_fields.issubset(REQUIRED_SYSTEM_FIELDS)
    
    def test_required_entity_fields(self):
        """Test that required entity fields are defined."""
        assert isinstance(REQUIRED_ENTITY_FIELDS, set)
        assert len(REQUIRED_ENTITY_FIELDS) > 0
        
        expected_fields = {"name", "count", "attributes"}
        assert expected_fields.issubset(REQUIRED_ENTITY_FIELDS)
    
    def test_required_attribute_fields(self):
        """Test that required attribute fields are defined."""
        assert isinstance(REQUIRED_ATTRIBUTE_FIELDS, set)
        assert len(REQUIRED_ATTRIBUTE_FIELDS) > 0
        
        expected_fields = {"type"}
        assert expected_fields.issubset(REQUIRED_ATTRIBUTE_FIELDS)