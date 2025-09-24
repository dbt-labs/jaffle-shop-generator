"""Unit tests for CLI validate-schema and list-schemas commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jafgen.cli import app


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        schema_dir = temp_path / "schemas"
        schema_dir.mkdir()
        yield schema_dir


@pytest.fixture
def valid_schema(temp_dirs):
    """Create a valid test schema."""
    schema_dir = temp_dirs
    
    schema_content = """
system:
  name: "test-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
    path: "."

entities:
  users:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
"""
    
    schema_file = schema_dir / "valid-schema.yaml"
    schema_file.write_text(schema_content.strip())
    
    return schema_file


@pytest.fixture
def invalid_schema(temp_dirs):
    """Create an invalid test schema."""
    schema_dir = temp_dirs
    
    # Missing required system section
    schema_content = """
entities:
  users:
    count: 10
    attributes:
      id:
        type: "invalid_type"
"""
    
    schema_file = schema_dir / "invalid-schema.yaml"
    schema_file.write_text(schema_content.strip())
    
    return schema_file


@pytest.fixture
def multiple_schemas(temp_dirs):
    """Create multiple test schemas."""
    schema_dir = temp_dirs
    
    # Schema 1
    schema1_content = """
system:
  name: "users-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
    path: "users"

entities:
  users:
    count: 5
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
"""
    
    # Schema 2
    schema2_content = """
system:
  name: "orders-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["json", "csv"]
    path: "orders"

entities:
  orders:
    count: 15
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      user_id:
        type: "link"
        link_to: "users-system.users.id"
        required: true
"""
    
    schema1_file = schema_dir / "users.yaml"
    schema2_file = schema_dir / "orders.yaml"
    
    schema1_file.write_text(schema1_content.strip())
    schema2_file.write_text(schema2_content.strip())
    
    return schema1_file, schema2_file


class TestValidateSchemaCommand:
    """Test cases for the validate-schema CLI command."""
    
    def test_validate_valid_schema(self, valid_schema, temp_dirs):
        """Test validation of a valid schema."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate-schema",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "All schemas are valid" in clean_output
        assert "Schema Summary" in clean_output
    
    def test_validate_invalid_schema(self, invalid_schema, temp_dirs):
        """Test validation of an invalid schema."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate-schema",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 1
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "Schema validation failed" in clean_output
        assert "Errors" in clean_output
    
    def test_validate_multiple_schemas(self, multiple_schemas, temp_dirs):
        """Test validation of multiple schemas."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate-schema",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "Validation Results for 2 schema" in clean_output
    
    def test_validate_empty_directory(self, temp_dirs):
        """Test validation of empty schema directory."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate-schema",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "No schema files found" in clean_output
    
    def test_validate_nonexistent_directory(self):
        """Test validation with non-existent directory."""
        nonexistent_dir = Path("/nonexistent/path")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate-schema",
            "--schema-dir", str(nonexistent_dir)
        ])
        
        assert result.exit_code == 1
        assert "Schema directory does not exist" in result.stdout
    
    def test_validate_help(self):
        """Test validate-schema command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["validate-schema", "--help"])
        
        assert result.exit_code == 0
        assert "Validate YAML schema files" in result.stdout
        assert "--schema-dir" in result.stdout


class TestListSchemasCommand:
    """Test cases for the list-schemas CLI command."""
    
    def test_list_single_schema(self, valid_schema, temp_dirs):
        """Test listing a single schema."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "list-schemas",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "Found 1 schema" in clean_output
        assert "test-system" in clean_output
    
    def test_list_multiple_schemas(self, multiple_schemas, temp_dirs):
        """Test listing multiple schemas."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "list-schemas",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "Found 2 schema" in clean_output
        assert "users-system" in clean_output
        assert "orders-system" in clean_output
    
    def test_list_schemas_detailed(self, multiple_schemas, temp_dirs):
        """Test listing schemas with detailed information."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "list-schemas",
            "--schema-dir", str(schema_dir),
            "--detailed"
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "users-system" in clean_output
        assert "orders-system" in clean_output
        assert "Entities:" in clean_output
        assert "Seed:" in clean_output
        assert "Output:" in clean_output
    
    def test_list_empty_directory(self, temp_dirs):
        """Test listing schemas in empty directory."""
        schema_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "list-schemas",
            "--schema-dir", str(schema_dir)
        ])
        
        assert result.exit_code == 0
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "No schema files found" in clean_output
    
    def test_list_nonexistent_directory(self):
        """Test listing schemas with non-existent directory."""
        nonexistent_dir = Path("/nonexistent/path")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "list-schemas",
            "--schema-dir", str(nonexistent_dir)
        ])
        
        assert result.exit_code == 1
        assert "Schema directory does not exist" in result.stdout
    
    def test_list_help(self):
        """Test list-schemas command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["list-schemas", "--help"])
        
        assert result.exit_code == 0
        assert "List discovered schema files" in result.stdout
        assert "--schema-dir" in result.stdout
        assert "--detailed" in result.stdout


class TestVersionCommand:
    """Test cases for version information."""
    
    def test_version_flag(self):
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "jafgen version" in result.stdout
    
    def test_version_short_flag(self):
        """Test -v flag."""
        runner = CliRunner()
        result = runner.invoke(app, ["-v"])
        
        assert result.exit_code == 0
        assert "jafgen version" in result.stdout
    
    def test_main_help(self):
        """Test main app help."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Jafgen - A synthetic data generator" in result.stdout
        assert "generate" in result.stdout
        assert "validate-schema" in result.stdout
        assert "list-schemas" in result.stdout
        assert "--version" in result.stdout


class TestCLIErrorHandling:
    """Test error handling scenarios for CLI commands."""
    
    def test_validate_with_discovery_error(self, temp_dirs):
        """Test validate command with discovery engine error."""
        schema_dir = temp_dirs
        
        with patch('jafgen.cli.SchemaDiscoveryEngine') as mock_discovery:
            mock_discovery_instance = mock_discovery.return_value
            mock_discovery_instance.discover_and_load_schemas.side_effect = Exception("Discovery failed")
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "validate-schema",
                "--schema-dir", str(schema_dir)
            ])
            
            assert result.exit_code == 1
            assert "Unexpected error during validation" in result.stdout
    
    def test_list_with_discovery_error(self, temp_dirs):
        """Test list command with discovery engine error."""
        schema_dir = temp_dirs
        
        with patch('jafgen.cli.SchemaDiscoveryEngine') as mock_discovery:
            mock_discovery_instance = mock_discovery.return_value
            mock_discovery_instance.discover_and_load_schemas.side_effect = Exception("Discovery failed")
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "list-schemas",
                "--schema-dir", str(schema_dir)
            ])
            
            assert result.exit_code == 1
            assert "Unexpected error" in result.stdout