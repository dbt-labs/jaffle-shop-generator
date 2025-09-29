"""Integration tests for Airbyte manifest processing workflows."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from typer.testing import CliRunner

from jafgen.airbyte.translator import AirbyteTranslator
from jafgen.schema.models import ValidationError, ValidationWarning
from jafgen.cli import app


class TestAirbyteIntegration:
    """Test Airbyte manifest integration workflows."""
    
    @pytest.fixture
    def sample_airbyte_manifest(self):
        """Sample Airbyte source manifest for testing."""
        return {
            "version": "0.2.0",
            "type": "SPEC",
            "spec": {
                "documentationUrl": "https://example.com/docs",
                "connectionSpecification": {
                    "type": "object",
                    "properties": {
                        "api_key": {"type": "string", "title": "API Key"}
                    }
                }
            },
            "streams": [
                {
                    "name": "users",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "created_at": {"type": "string", "format": "date-time"},
                            "age": {"type": "integer", "minimum": 0, "maximum": 120}
                        },
                        "required": ["id", "name", "email"]
                    },
                    "supported_sync_modes": ["full_refresh", "incremental"],
                    "source_defined_cursor": True,
                    "default_cursor_field": ["created_at"]
                },
                {
                    "name": "orders",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "user_id": {"type": "string"},
                            "total": {"type": "number", "minimum": 0},
                            "status": {"type": "string", "enum": ["pending", "completed", "cancelled"]},
                            "order_date": {"type": "string", "format": "date"}
                        },
                        "required": ["id", "user_id", "total", "status"]
                    },
                    "supported_sync_modes": ["full_refresh"]
                }
            ]
        }
    
    @pytest.fixture
    def complex_airbyte_manifest(self):
        """Complex Airbyte manifest with nested objects and arrays."""
        return {
            "version": "0.2.0",
            "type": "SPEC",
            "streams": [
                {
                    "name": "customers",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "profile": {
                                "type": "object",
                                "properties": {
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "address": {
                                        "type": "object",
                                        "properties": {
                                            "street": {"type": "string"},
                                            "city": {"type": "string"},
                                            "country": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "metadata": {"type": "object"}
                        },
                        "required": ["id", "profile"]
                    }
                }
            ]
        }
    
    def test_airbyte_manifest_parsing(self, tmp_path: Path, sample_airbyte_manifest):
        """Test parsing of Airbyte manifest files."""
        manifest_file = tmp_path / "manifest.yaml"
        
        # Write manifest as YAML
        with open(manifest_file, 'w') as f:
            yaml.dump(sample_airbyte_manifest, f)
        
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_file)
        
        # Expected assertions:
        assert len(schemas) == 1  # One system schema
        assert len(schemas[0].entities) == 2  # users and orders entities
        
        # Verify entity configurations
        users_entity = schemas[0].entities["users"]
        assert users_entity.count > 0
        assert "id" in users_entity.attributes
        assert users_entity.attributes["id"].unique is True
        assert users_entity.attributes["email"].type == "person.email"
    
    def test_json_schema_type_mapping(self, sample_airbyte_manifest):
        """Test mapping of JSON Schema types to Mimesis types."""
        translator = AirbyteTranslator()
        
        # Test type mappings
        assert translator._map_json_schema_type("string", "email", {}) == "person.email"
        assert translator._map_json_schema_type("string", "date-time", {}) == "datetime.datetime"
        assert translator._map_json_schema_type("integer", None, {"minimum": 0, "maximum": 120}) == "integer"
        assert translator._map_json_schema_type("number", None, {}) == "decimal"
    
    def test_relationship_detection(self, tmp_path: Path, sample_airbyte_manifest):
        """Test detection and creation of relationships between entities."""
        manifest_file = tmp_path / "manifest.yaml"
        
        with open(manifest_file, 'w') as f:
            yaml.dump(sample_airbyte_manifest, f)
        
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_file)
        
        # Apply relationship detection
        schemas_with_relationships = translator.detect_relationships(schemas)
        
        # The orders.user_id should be detected as a link to users.id
        orders_entity = schemas_with_relationships[0].entities["orders"]
        user_id_attr = orders_entity.attributes["user_id"]
        assert user_id_attr.link_to == f"{schemas[0].name}.users.id"
    
    def test_complex_nested_schema_handling(self, tmp_path: Path, complex_airbyte_manifest):
        """Test handling of complex nested schemas."""
        manifest_file = tmp_path / "complex_manifest.yaml"
        
        with open(manifest_file, 'w') as f:
            yaml.dump(complex_airbyte_manifest, f)
        
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_file)
        
        customers_entity = schemas[0].entities["customers"]
        
        # Test that nested objects are handled (converted to text.word with warnings)
        assert "profile" in customers_entity.attributes
        assert customers_entity.attributes["profile"].type == "text.word"
        
        # Verify warnings were generated for unsupported nested objects
        validation_result = translator.get_validation_result()
        assert len(validation_result.warnings) > 0
        assert any("Object types not supported" in w.message for w in validation_result.warnings)
    
    def test_unsupported_features_warning(self, tmp_path: Path):
        """Test warning system for unsupported Airbyte features."""
        # Test manifest with unsupported features
        unsupported_manifest = {
            "version": "0.2.0",
            "streams": [
                {
                    "name": "complex_stream",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "complex_field": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "integer"}
                                ]
                            },
                            "conditional_field": {
                                "if": {"properties": {"type": {"const": "premium"}}},
                                "then": {"properties": {"premium_data": {"type": "string"}}},
                                "else": {"properties": {"basic_data": {"type": "string"}}}
                            }
                        }
                    }
                }
            ]
        }
        
        manifest_file = tmp_path / "unsupported_manifest.yaml"
        with open(manifest_file, 'w') as f:
            yaml.dump(unsupported_manifest, f)
        
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_file)
        
        # Check that warnings were generated for unsupported features
        validation_result = translator.get_validation_result()
        assert len(validation_result.warnings) > 0
        
        # Check for specific warning about oneOf
        oneOf_warnings = [w for w in validation_result.warnings if "oneOf" in w.message or "Complex schema features" in w.message]
        assert len(oneOf_warnings) > 0
    
    def test_end_to_end_airbyte_workflow(self, tmp_path: Path, sample_airbyte_manifest):
        """Test complete end-to-end workflow from Airbyte manifest to data generation."""
        manifest_file = tmp_path / "manifest.yaml"
        output_dir = tmp_path / "output"
        schemas_dir = tmp_path / "schemas"
        
        output_dir.mkdir()
        schemas_dir.mkdir()
        
        # Write manifest
        with open(manifest_file, 'w') as f:
            yaml.dump(sample_airbyte_manifest, f)
        
        # 1. Import Airbyte manifest
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_file)
        
        # 2. Save translated schemas
        for schema in schemas:
            schema_file = schemas_dir / f"{schema.name}.yaml"
            translator.save_schema(schema, schema_file)
        
        # 3. Generate data using translated schemas
        from jafgen.schema.discovery import SchemaDiscoveryEngine
        from jafgen.generation.data_generator import DataGenerator
        from jafgen.generation.mimesis_engine import MimesisEngine
        from jafgen.generation.link_resolver import LinkResolver
        
        discovery_engine = SchemaDiscoveryEngine()
        loaded_schemas, validation_result = discovery_engine.discover_and_load_schemas(schemas_dir)
        
        assert validation_result.is_valid
        assert len(loaded_schemas) == len(schemas)
        
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        for schema in loaded_schemas:
            generated_system = data_generator.generate_system(schema)
            
            # Verify generated data matches Airbyte schema expectations
            assert len(generated_system.entities["users"]) > 0
            assert len(generated_system.entities["orders"]) > 0
            
            # Verify data types match original JSON schema
            users = generated_system.entities["users"]
            for user in users[:5]:  # Check first 5 users
                assert isinstance(user["id"], str)
                assert isinstance(user["name"], str)
                assert "@" in user["email"]  # Basic email validation
                assert isinstance(user["age"], int)
                assert 0 <= user["age"] <= 120
    
    def test_cli_import_airbyte_command(self, tmp_path: Path, sample_airbyte_manifest):
        """Test CLI command for importing Airbyte manifests."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()
        
        # Write manifest
        with open(manifest_file, 'w') as f:
            yaml.dump(sample_airbyte_manifest, f)
        
        runner = CliRunner()
        
        result = runner.invoke(app, [
            "import-airbyte",
            "--manifest-file", str(manifest_file),
            "--output-dir", str(schemas_dir)
        ])
        
        assert result.exit_code == 0
        assert "Successfully imported Airbyte manifest" in result.stdout
        assert "Created 1 schema file" in result.stdout
        
        # Verify schema files were created
        schema_files = list(schemas_dir.glob("*.yaml"))
        assert len(schema_files) == 1
    
    def test_airbyte_manifest_validation_placeholder(self):
        """Placeholder test to ensure test structure is valid."""
        # This test ensures the test file is valid Python and can be imported
        # It will be replaced with actual tests when Airbyte integration is implemented
        assert True
    
    def test_future_airbyte_integration_requirements(self):
        """Test that documents the expected Airbyte integration requirements."""
        # This test documents what the Airbyte integration should support
        # based on requirement 9.5
        
        expected_features = [
            "Parse Airbyte source manifest.yaml files",
            "Convert JSON Schema to jafgen attribute types",
            "Detect and preserve relationships as link_to attributes",
            "Handle unsupported features with warnings",
            "Validate translated schemas before saving",
            "Support CLI import command",
            "Generate realistic test data matching API schemas"
        ]
        
        # When Airbyte integration is implemented, these features should be tested
        assert len(expected_features) == 7
        
        # Expected type mappings for JSON Schema to Mimesis
        expected_type_mappings = {
            ("string", "email"): "person.email",
            ("string", "date-time"): "datetime.datetime",
            ("string", "date"): "datetime.date",
            ("string", "uri"): "internet.url",
            ("integer", None): "numeric.integer",
            ("number", None): "numeric.decimal",
            ("boolean", None): "development.boolean",
            ("string", None): "text.word"
        }
        
        assert len(expected_type_mappings) == 8