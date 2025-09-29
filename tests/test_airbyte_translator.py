"""Unit tests for AirbyteTranslator class."""

import tempfile
from pathlib import Path

import pytest
import yaml

from jafgen.airbyte.translator import AirbyteTranslator
from jafgen.schema.models import ValidationError, ValidationWarning


class TestAirbyteTranslator:
    """Test the AirbyteTranslator class."""
    
    def test_init(self):
        """Test AirbyteTranslator initialization."""
        translator = AirbyteTranslator()
        assert translator.warnings == []
        assert translator.errors == []
        assert len(translator.TYPE_MAPPINGS) > 0
    
    def test_type_mappings(self):
        """Test JSON Schema to Mimesis type mappings."""
        translator = AirbyteTranslator()
        
        # Test string types with formats
        assert translator._map_json_schema_type("string", "email", {}) == "person.email"
        assert translator._map_json_schema_type("string", "date-time", {}) == "datetime.datetime"
        assert translator._map_json_schema_type("string", "date", {}) == "datetime.date"
        assert translator._map_json_schema_type("string", "uuid", {}) == "cryptographic.uuid"
        
        # Test numeric types
        assert translator._map_json_schema_type("integer", None, {}) == "numeric.integer"
        assert translator._map_json_schema_type("number", None, {}) == "numeric.decimal"
        
        # Test boolean type
        assert translator._map_json_schema_type("boolean", None, {}) == "development.boolean"
        
        # Test default string type
        assert translator._map_json_schema_type("string", None, {}) == "text.word"
    
    def test_unsupported_type_warnings(self):
        """Test that unsupported types generate warnings."""
        translator = AirbyteTranslator()
        
        # Test array type
        result = translator._map_json_schema_type("array", None, {})
        assert result == "text.word"
        assert len(translator.warnings) > 0
        assert any("Array types not supported" in w.message for w in translator.warnings)
        
        # Reset warnings
        translator.warnings.clear()
        
        # Test object type
        result = translator._map_json_schema_type("object", None, {})
        assert result == "text.word"
        assert len(translator.warnings) > 0
        assert any("Object types not supported" in w.message for w in translator.warnings)
        
        # Reset warnings
        translator.warnings.clear()
        
        # Test unknown type
        result = translator._map_json_schema_type("unknown_type", None, {})
        assert result == "text.word"
        assert len(translator.warnings) > 0
        assert any("Unknown JSON Schema type" in w.message for w in translator.warnings)
    
    def test_enum_handling(self):
        """Test handling of enum fields."""
        translator = AirbyteTranslator()
        
        # Test string enum
        field_schema = {"enum": ["pending", "completed", "cancelled"]}
        result = translator._map_json_schema_type("string", None, field_schema)
        assert result == "choice"
        
        # Test mixed-type enum (should generate warning)
        translator.warnings.clear()
        field_schema = {"enum": ["pending", 1, True]}
        result = translator._map_json_schema_type("string", None, field_schema)
        assert result == "text.word"  # Falls back to default
        assert len(translator.warnings) > 0
        assert any("Mixed-type enum not fully supported" in w.message for w in translator.warnings)
    
    def test_constraint_extraction(self):
        """Test extraction of constraints from JSON Schema."""
        translator = AirbyteTranslator()
        
        # Test numeric constraints
        field_schema = {
            "minimum": 0,
            "maximum": 100,
            "exclusiveMinimum": 5,
            "exclusiveMaximum": 95
        }
        constraints = translator._extract_constraints(field_schema)
        assert constraints["min_value"] == 6  # exclusiveMinimum + 1
        assert constraints["max_value"] == 94  # exclusiveMaximum - 1
        
        # Test string constraints
        field_schema = {
            "minLength": 5,
            "maxLength": 50,
            "pattern": "^[A-Z]+$"
        }
        constraints = translator._extract_constraints(field_schema)
        assert constraints["min_length"] == 5
        assert constraints["max_length"] == 50
        assert constraints["pattern"] == "^[A-Z]+$"
        
        # Test enum constraints
        field_schema = {"enum": ["red", "green", "blue"]}
        constraints = translator._extract_constraints(field_schema)
        assert constraints["choices"] == ["red", "green", "blue"]
        
        # Test array constraints
        field_schema = {
            "minItems": 1,
            "maxItems": 10
        }
        constraints = translator._extract_constraints(field_schema)
        assert constraints["min_items"] == 1
        assert constraints["max_items"] == 10
    
    def test_unique_field_detection(self):
        """Test detection of unique fields."""
        translator = AirbyteTranslator()
        
        # Test ID fields
        attr_config = translator._convert_json_schema_field("id", {"type": "string"}, True)
        assert attr_config.unique is True
        
        attr_config = translator._convert_json_schema_field("uuid", {"type": "string"}, True)
        assert attr_config.unique is True
        
        attr_config = translator._convert_json_schema_field("user_id", {"type": "string"}, True)
        assert attr_config.unique is True
        
        # Test UUID format
        attr_config = translator._convert_json_schema_field("identifier", {"type": "string", "format": "uuid"}, True)
        assert attr_config.unique is True
        
        # Test non-unique fields
        attr_config = translator._convert_json_schema_field("name", {"type": "string"}, True)
        assert attr_config.unique is False
    
    def test_file_not_found_error(self):
        """Test error handling for missing manifest files."""
        translator = AirbyteTranslator()
        
        with pytest.raises(FileNotFoundError, match="Airbyte manifest file not found"):
            translator.translate_manifest(Path("/nonexistent/manifest.yaml"))
    
    def test_invalid_yaml_error(self, tmp_path: Path):
        """Test error handling for invalid YAML."""
        translator = AirbyteTranslator()
        
        manifest_file = tmp_path / "invalid.yaml"
        with open(manifest_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError, match="Invalid YAML in manifest file"):
            translator.translate_manifest(manifest_file)
    
    def test_invalid_manifest_structure(self, tmp_path: Path):
        """Test error handling for invalid manifest structure."""
        translator = AirbyteTranslator()
        
        # Test non-dict manifest
        manifest_file = tmp_path / "invalid_structure.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(["not", "a", "dict"], f)
        
        with pytest.raises(ValueError, match="Manifest file must contain a YAML object"):
            translator.translate_manifest(manifest_file)
    
    def test_empty_streams_warning(self, tmp_path: Path):
        """Test warning for manifests with no streams."""
        translator = AirbyteTranslator()
        
        manifest_data = {"version": "0.2.0", "streams": []}
        manifest_file = tmp_path / "empty_streams.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        schemas = translator.translate_manifest(manifest_file)
        assert len(schemas) == 0
        
        validation_result = translator.get_validation_result()
        assert len(validation_result.warnings) > 0
        assert any("No streams found" in w.message for w in validation_result.warnings)
    
    def test_stream_without_name_error(self, tmp_path: Path):
        """Test error handling for streams without names."""
        translator = AirbyteTranslator()
        
        manifest_data = {
            "version": "0.2.0",
            "streams": [
                {
                    "json_schema": {
                        "type": "object",
                        "properties": {"id": {"type": "string"}}
                    }
                }
            ]
        }
        manifest_file = tmp_path / "no_name.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        with pytest.raises(ValueError, match="No valid entities could be created"):
            translator.translate_manifest(manifest_file)
        
        validation_result = translator.get_validation_result()
        assert len(validation_result.errors) > 0
        assert any("Stream must have a name" in e.message for e in validation_result.errors)
    
    def test_stream_without_schema_error(self, tmp_path: Path):
        """Test error handling for streams without JSON schema."""
        translator = AirbyteTranslator()
        
        manifest_data = {
            "version": "0.2.0",
            "streams": [
                {
                    "name": "test_stream"
                }
            ]
        }
        manifest_file = tmp_path / "no_schema.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        with pytest.raises(ValueError, match="No valid entities could be created"):
            translator.translate_manifest(manifest_file)
        
        validation_result = translator.get_validation_result()
        assert len(validation_result.errors) > 0
        assert any("must have a json_schema" in e.message for e in validation_result.errors)
    
    def test_save_schema(self, tmp_path: Path):
        """Test saving schemas to YAML files."""
        translator = AirbyteTranslator()
        
        # Create a simple manifest and translate it
        manifest_data = {
            "version": "0.2.0",
            "streams": [
                {
                    "name": "users",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        },
                        "required": ["id", "name", "email"]
                    }
                }
            ]
        }
        
        manifest_file = tmp_path / "manifest.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest_data, f)
        
        schemas = translator.translate_manifest(manifest_file)
        
        # Save the schema
        output_file = tmp_path / "output_schema.yaml"
        translator.save_schema(schemas[0], output_file)
        
        # Verify the file was created and has correct structure
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert "system" in saved_data
        assert "entities" in saved_data
        assert saved_data["system"]["name"] == "manifest"
        assert "users" in saved_data["entities"]
        assert saved_data["entities"]["users"]["count"] == 1000
        assert "id" in saved_data["entities"]["users"]["attributes"]
    
    def test_relationship_detection_simple(self):
        """Test simple relationship detection."""
        translator = AirbyteTranslator()
        
        # Create schemas with potential relationships
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=100,
                    attributes={
                        "id": AttributeConfig(type="cryptographic.uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name")
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=500,
                    attributes={
                        "id": AttributeConfig(type="cryptographic.uuid", unique=True),
                        "user_id": AttributeConfig(type="text.word"),  # Should be detected as FK
                        "total": AttributeConfig(type="numeric.decimal")
                    }
                )
            }
        )
        
        schemas_with_relationships = translator.detect_relationships([schema])
        
        # Check that user_id was linked to users.id
        orders_entity = schemas_with_relationships[0].entities["orders"]
        user_id_attr = orders_entity.attributes["user_id"]
        assert user_id_attr.link_to == "test_system.users.id"
        assert user_id_attr.type == "cryptographic.uuid"  # Should match target type
        assert user_id_attr.unique is False  # Foreign keys are not unique
    
    def test_validation_result(self):
        """Test validation result functionality."""
        translator = AirbyteTranslator()
        
        # Initially should be valid with no errors/warnings
        result = translator.get_validation_result()
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        
        # Add some warnings and errors
        translator.warnings.append(ValidationWarning(
            type="test_warning",
            message="Test warning message"
        ))
        translator.errors.append(ValidationError(
            type="test_error",
            message="Test error message"
        ))
        
        result = translator.get_validation_result()
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.errors[0].message == "Test error message"
        assert result.warnings[0].message == "Test warning message"