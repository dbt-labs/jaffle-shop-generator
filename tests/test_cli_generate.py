"""Integration tests for CLI generate command."""

import json
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
        output_dir = temp_path / "output"
        schema_dir.mkdir()
        output_dir.mkdir()
        yield schema_dir, output_dir


@pytest.fixture
def simple_schema(temp_dirs):
    """Create a simple test schema."""
    schema_dir, _ = temp_dirs
    
    schema_content = """
system:
  name: "test-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "json"]
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
      email:
        type: "person.email"
        unique: true
        required: true
"""
    
    schema_file = schema_dir / "test-schema.yaml"
    schema_file.write_text(schema_content.strip())
    
    return schema_file


@pytest.fixture
def linked_schemas(temp_dirs):
    """Create schemas with linked entities."""
    schema_dir, _ = temp_dirs
    
    # Schema 1: Users
    users_schema = """
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
    
    # Schema 2: Orders (links to users)
    orders_schema = """
system:
  name: "orders-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
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
      amount:
        type: "decimal"
        required: true
        constraints:
          min_value: 10.0
          max_value: 100.0
"""
    
    users_file = schema_dir / "users.yaml"
    orders_file = schema_dir / "orders.yaml"
    
    users_file.write_text(users_schema.strip())
    orders_file.write_text(orders_schema.strip())
    
    return users_file, orders_file


class TestGenerateCommand:
    """Test cases for the generate CLI command."""
    
    def test_generate_simple_schema_success(self, simple_schema, temp_dirs):
        """Test successful generation with a simple schema."""
        schema_dir, output_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(schema_dir),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        assert "Successfully loaded 1 schema(s)" in result.stdout
        assert "Generation Summary" in result.stdout
        
        # Check that output files were created
        csv_file = output_dir / "users.csv"
        json_file = output_dir / "users.json"
        
        assert csv_file.exists()
        assert json_file.exists()
        
        # Verify CSV content
        csv_content = csv_file.read_text()
        lines = csv_content.strip().split('\n')
        assert len(lines) == 11  # Header + 10 data rows
        assert "id,name,email" in lines[0]
        
        # Verify JSON content
        json_content = json.loads(json_file.read_text())
        assert len(json_content) == 10
        assert all("id" in record and "name" in record and "email" in record for record in json_content)
    
    def test_generate_with_seed_override(self, simple_schema, temp_dirs):
        """Test generation with seed override."""
        schema_dir, output_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(schema_dir),
            "--output-dir", str(output_dir),
            "--seed", "123"
        ])
        
        assert result.exit_code == 0
        assert "Seed Used" in result.stdout
        assert "123" in result.stdout
    
    def test_generate_linked_schemas(self, linked_schemas, temp_dirs):
        """Test generation with linked entities across schemas."""
        schema_dir, output_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(schema_dir),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        # Remove ANSI color codes for easier string matching
        clean_output = result.stdout.encode('ascii', 'ignore').decode('ascii')
        assert "Successfully loaded 2" in clean_output
        
        # Check output files
        users_csv = output_dir / "users" / "users.csv"
        orders_csv = output_dir / "orders" / "orders.csv"
        
        assert users_csv.exists()
        assert orders_csv.exists()
        
        # Verify users data
        users_content = users_csv.read_text()
        users_lines = users_content.strip().split('\n')
        assert len(users_lines) == 6  # Header + 5 users
        
        # Verify orders data
        orders_content = orders_csv.read_text()
        orders_lines = orders_content.strip().split('\n')
        assert len(orders_lines) == 16  # Header + 15 orders
        
        # Extract user IDs from users file
        user_ids = set()
        for line in users_lines[1:]:  # Skip header
            user_id = line.split(',')[0]
            user_ids.add(user_id)
        
        # Verify that all order user_ids reference valid users
        for line in orders_lines[1:]:  # Skip header
            parts = line.split(',')
            user_id = parts[1]
            assert user_id in user_ids, f"Order references non-existent user: {user_id}"
    
    def test_generate_nonexistent_schema_dir(self, temp_dirs):
        """Test error handling for non-existent schema directory."""
        _, output_dir = temp_dirs
        nonexistent_dir = Path("/nonexistent/path")
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(nonexistent_dir),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 1
        assert "Schema directory does not exist" in result.stdout
    
    def test_generate_empty_schema_dir(self, temp_dirs):
        """Test handling of empty schema directory."""
        schema_dir, output_dir = temp_dirs
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(schema_dir),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        assert "No schemas found to process" in result.stdout
    
    def test_generate_invalid_schema(self, temp_dirs):
        """Test error handling for invalid schema."""
        schema_dir, output_dir = temp_dirs
        
        # Create invalid schema
        invalid_schema = """
invalid_yaml: [
  missing_closing_bracket
"""
        
        schema_file = schema_dir / "invalid.yaml"
        schema_file.write_text(invalid_schema)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate",
            "--schema-dir", str(schema_dir),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 1
        assert "Schema validation failed" in result.stdout
    
    def test_generate_default_directories(self, simple_schema):
        """Test generation with default schema and output directories."""
        # This test uses mocking since we don't want to create actual ./schemas and ./output dirs
        with patch('jafgen.cli.SchemaDiscoveryEngine') as mock_discovery:
            with patch('jafgen.cli.DataGenerator') as mock_generator:
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('pathlib.Path.is_dir') as mock_is_dir:
                        with patch('pathlib.Path.mkdir') as mock_mkdir:
                            
                            # Setup mocks
                            mock_exists.return_value = True
                            mock_is_dir.return_value = True
                            
                            mock_discovery_instance = mock_discovery.return_value
                            mock_discovery_instance.discover_and_load_schemas.return_value = ([], type('ValidationResult', (), {
                                'is_valid': True,
                                'errors': [],
                                'warnings': []
                            })())
                            
                            runner = CliRunner()
                            result = runner.invoke(app, ["generate"])
                            
                            assert result.exit_code == 0
                            assert "No schemas found to process" in result.stdout
    
    def test_generate_help(self):
        """Test generate command help."""
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--help"])
        
        assert result.exit_code == 0
        assert "Generate synthetic data from YAML schema definitions" in result.stdout
        assert "--schema-dir" in result.stdout
        assert "--output-dir" in result.stdout
        assert "--seed" in result.stdout


class TestGenerateCommandErrorHandling:
    """Test error handling scenarios for generate command."""
    
    def test_generation_engine_failure(self, simple_schema, temp_dirs):
        """Test handling of data generation engine failures."""
        schema_dir, output_dir = temp_dirs
        
        with patch('jafgen.cli.DataGenerator') as mock_generator:
            mock_generator_instance = mock_generator.return_value
            mock_generator_instance.generate_multiple_systems.side_effect = Exception("Generation failed")
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "generate",
                "--schema-dir", str(schema_dir),
                "--output-dir", str(output_dir)
            ])
            
            assert result.exit_code == 1
            assert "Data generation failed" in result.stdout
    
    def test_output_writer_failure(self, simple_schema, temp_dirs):
        """Test handling of output writer failures."""
        schema_dir, output_dir = temp_dirs
        
        with patch('jafgen.cli.CSVWriter') as mock_csv_writer:
            mock_csv_writer_instance = mock_csv_writer.return_value
            mock_csv_writer_instance.write.side_effect = Exception("Write failed")
            
            runner = CliRunner()
            result = runner.invoke(app, [
                "generate",
                "--schema-dir", str(schema_dir),
                "--output-dir", str(output_dir)
            ])
            
            # Should not exit with error, but should show write failure
            assert result.exit_code == 0
            assert "Failed to write CSV" in result.stdout