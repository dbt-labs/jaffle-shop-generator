"""Tests for YAML schema loader."""

import pytest
import tempfile
from pathlib import Path

from jafgen.schema import YAMLSchemaLoader, SchemaLoadError, ValidationError


class TestYAMLSchemaLoader:
    """Test cases for YAMLSchemaLoader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = YAMLSchemaLoader()
    
    def test_discover_schemas_empty_directory(self):
        """Test schema discovery in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            schemas = self.loader.discover_schemas(schema_dir)
            assert schemas == []
    
    def test_discover_schemas_nonexistent_directory(self):
        """Test schema discovery with nonexistent directory."""
        nonexistent = Path("/nonexistent/directory")
        schemas = self.loader.discover_schemas(nonexistent)
        assert schemas == []
    
    def test_discover_schemas_with_yaml_files(self):
        """Test schema discovery with YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create test YAML files
            (schema_dir / "schema1.yaml").write_text("test: content")
            (schema_dir / "schema2.yml").write_text("test: content")
            (schema_dir / "not_yaml.txt").write_text("test: content")
            
            schemas = self.loader.discover_schemas(schema_dir)
            schema_names = [s.name for s in schemas]
            
            assert len(schemas) == 2
            assert "schema1.yaml" in schema_names
            assert "schema2.yml" in schema_names
            assert "not_yaml.txt" not in schema_names
    
    def test_load_schema_valid_yaml(self):
        """Test loading a valid YAML schema."""
        yaml_content = """
system:
  name: "test-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "json"]
    path: "./output"

entities:
  users:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
      email:
        type: "person.email"
        unique: true
        constraints:
          domain: "example.com"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                schema = self.loader.load_schema(Path(f.name))
                
                assert schema.name == "test-system"
                assert schema.version == "1.0.0"
                assert schema.seed == 42
                assert schema.output.format == ["csv", "json"]
                assert schema.output.path == "./output"
                
                assert "users" in schema.entities
                users_entity = schema.entities["users"]
                assert users_entity.count == 100
                assert "id" in users_entity.attributes
                assert "name" in users_entity.attributes
                assert "email" in users_entity.attributes
                
                id_attr = users_entity.attributes["id"]
                assert id_attr.type == "uuid"
                assert id_attr.unique is True
                assert id_attr.required is True
                
                email_attr = users_entity.attributes["email"]
                assert email_attr.constraints == {"domain": "example.com"}
                
            finally:
                Path(f.name).unlink()
    
    def test_load_schema_invalid_yaml(self):
        """Test loading invalid YAML syntax."""
        invalid_yaml = """
system:
  name: "test"
  invalid: [unclosed list
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                with pytest.raises(SchemaLoadError, match="Invalid YAML syntax"):
                    self.loader.load_schema(Path(f.name))
            finally:
                Path(f.name).unlink()
    
    def test_load_schema_missing_file(self):
        """Test loading nonexistent schema file."""
        with pytest.raises(SchemaLoadError, match="Schema file not found"):
            self.loader.load_schema(Path("/nonexistent/schema.yaml"))
    
    def test_validate_schema_valid(self):
        """Test validation of a valid schema."""
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        schema = SystemSchema(
            name="test-system",
            version="1.0.0",
            seed=42,
            output=OutputConfig(format=["csv"], path="./output"),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=100,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_schema_missing_name(self):
        """Test validation with missing system name."""
        from jafgen.schema.models import SystemSchema, OutputConfig
        
        schema = SystemSchema(
            name="",  # Empty name
            version="1.0.0",
            output=OutputConfig(),
            entities={}
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].type == "missing_field"
        assert "name is required" in result.errors[0].message
    
    def test_validate_schema_invalid_link(self):
        """Test validation with invalid link_to reference."""
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        schema = SystemSchema(
            name="test-system",
            version="1.0.0",
            output=OutputConfig(),
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=50,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(type="link", link_to="test-system.users.id")  # users entity doesn't exist
                    }
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is False
        assert any(error.type == "broken_link" for error in result.errors)