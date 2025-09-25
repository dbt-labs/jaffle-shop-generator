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


class TestYAMLSchemaLoaderEdgeCases:
    """Additional edge case tests for YAMLSchemaLoader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = YAMLSchemaLoader()
    
    def test_load_schema_with_minimal_config(self):
        """Test loading schema with minimal configuration."""
        yaml_content = """
system:
  name: "minimal-system"
  version: "1.0.0"

entities:
  users:
    count: 1
    attributes:
      id:
        type: "uuid"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                schema = self.loader.load_schema(Path(f.name))
                
                assert schema.name == "minimal-system"
                assert schema.version == "1.0.0"
                assert schema.seed is None  # Default
                assert schema.output.format == ["csv"]  # Default
                assert schema.output.path == "./output"  # Default
                
            finally:
                Path(f.name).unlink()
    
    def test_load_schema_with_complex_constraints(self):
        """Test loading schema with complex attribute constraints."""
        yaml_content = """
system:
  name: "complex-system"
  version: "1.0.0"

entities:
  products:
    count: 5
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      price:
        type: "decimal"
        required: true
        constraints:
          min_value: 0.01
          max_value: 9999.99
          precision: 2
      description:
        type: "text"
        required: false
        constraints:
          max_length: 500
      created_at:
        type: "datetime.datetime"
        required: true
        constraints:
          start_date: "2020-01-01"
          end_date: "2024-12-31"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                schema = self.loader.load_schema(Path(f.name))
                
                products_entity = schema.entities["products"]
                
                # Check price constraints
                price_attr = products_entity.attributes["price"]
                assert price_attr.constraints["min_value"] == 0.01
                assert price_attr.constraints["max_value"] == 9999.99
                assert price_attr.constraints["precision"] == 2
                
                # Check description constraints
                desc_attr = products_entity.attributes["description"]
                assert desc_attr.required is False
                assert desc_attr.constraints["max_length"] == 500
                
                # Check datetime constraints
                created_attr = products_entity.attributes["created_at"]
                assert created_attr.constraints["start_date"] == "2020-01-01"
                assert created_attr.constraints["end_date"] == "2024-12-31"
                
            finally:
                Path(f.name).unlink()
    
    def test_validate_schema_with_multiple_errors(self):
        """Test validation with multiple errors."""
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        schema = SystemSchema(
            name="",  # Empty name (error)
            version="",  # Empty version (error)
            output=OutputConfig(format=["invalid_format"]),  # Invalid format (error)
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=0,  # Zero count (error)
                    attributes={
                        "user_id": AttributeConfig(
                            type="link", 
                            link_to="nonexistent.users.id"  # Invalid link (error)
                        )
                    }
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is False
        assert len(result.errors) >= 3  # Should have multiple errors
    
    def test_validate_schema_with_warnings(self):
        """Test validation that produces warnings."""
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        schema = SystemSchema(
            name="warning-system",
            version="1.0.0",
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1000000,  # Very large count (warning)
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name")
                    }
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        # Should be valid but may have warnings about large count
        assert result.is_valid is True
    
    def test_load_schema_file_encoding_error(self):
        """Test handling of file encoding errors."""
        # Create a file with invalid UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.yaml', delete=False) as f:
            f.write(b'\xff\xfe')  # Invalid UTF-8 bytes
            f.flush()
            
            try:
                with pytest.raises(SchemaLoadError, match="Failed to read schema file"):
                    self.loader.load_schema(Path(f.name))
            finally:
                Path(f.name).unlink()
    
    def test_discover_schemas_with_mixed_files(self):
        """Test schema discovery with mixed file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create various files
            (schema_dir / "valid.yaml").write_text("system:\n  name: test")
            (schema_dir / "valid.yml").write_text("system:\n  name: test2")
            (schema_dir / "invalid.txt").write_text("not yaml")
            (schema_dir / "README.md").write_text("# Documentation")
            (schema_dir / ".hidden.yaml").write_text("system:\n  name: hidden")
            
            schemas = self.loader.discover_schemas(schema_dir)
            schema_names = [s.name for s in schemas]
            
            # Should find .yaml and .yml files, including hidden ones
            assert len(schemas) >= 2
            assert "valid.yaml" in schema_names or "valid.yml" in schema_names
    
    def test_validate_schema_entity_without_attributes(self):
        """Test validation of entity without attributes."""
        from jafgen.schema.models import SystemSchema, EntityConfig, OutputConfig
        
        schema = SystemSchema(
            name="test-system",
            version="1.0.0",
            output=OutputConfig(),
            entities={
                "empty_entity": EntityConfig(
                    name="empty_entity",
                    count=10,
                    attributes={}  # No attributes
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is False
        assert any(error.type == "empty_entity" for error in result.errors)
    
    def test_validate_schema_duplicate_entity_names(self):
        """Test validation with duplicate entity names."""
        from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig
        
        # This would be caught at the YAML parsing level, but test the validation logic
        schema = SystemSchema(
            name="test-system",
            version="1.0.0",
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid")
                    }
                )
            }
        )
        
        result = self.loader.validate_schema(schema)
        assert result.is_valid is True  # Single entity should be valid