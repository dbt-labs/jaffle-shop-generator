"""Tests for the import-airbyte CLI command."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from jafgen.cli import app


class TestImportAirbyteCommand:
    """Test the import-airbyte CLI command."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_manifest(self):
        """Sample Airbyte manifest for testing."""
        return {
            "version": "0.2.0",
            "type": "SPEC",
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
                        },
                        "required": ["id", "name", "email"],
                    },
                },
                {
                    "name": "orders",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "user_id": {"type": "string"},
                            "total": {"type": "number", "minimum": 0},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "completed", "cancelled"],
                            },
                        },
                        "required": ["id", "user_id", "total", "status"],
                    },
                },
            ],
        }

    def test_import_airbyte_success(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test successful import of Airbyte manifest."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        # Check command succeeded
        assert result.exit_code == 0
        assert "Successfully imported Airbyte manifest" in result.stdout
        assert "Created 1 schema file" in result.stdout

        # Verify schema file was created
        schema_files = list(schemas_dir.glob("*.yaml"))
        assert len(schema_files) == 1

        # Verify schema content
        with open(schema_files[0], "r") as f:
            schema_data = yaml.safe_load(f)

        assert "system" in schema_data
        assert "entities" in schema_data
        assert "users" in schema_data["entities"]
        assert "orders" in schema_data["entities"]

    def test_import_airbyte_with_relationships(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test import with relationship detection enabled."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command with relationship detection
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
                "--detect-relationships",
            ],
        )

        assert result.exit_code == 0

        # Verify schema file was created
        schema_files = list(schemas_dir.glob("*.yaml"))
        assert len(schema_files) == 1

        # Verify relationship was detected
        with open(schema_files[0], "r") as f:
            schema_data = yaml.safe_load(f)

        # Check that user_id in orders has a link_to attribute
        orders_user_id = schema_data["entities"]["orders"]["attributes"]["user_id"]
        assert "link_to" in orders_user_id
        assert "users.id" in orders_user_id["link_to"]

    def test_import_airbyte_without_relationships(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test import with relationship detection disabled."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command without relationship detection
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
                "--no-detect-relationships",
            ],
        )

        assert result.exit_code == 0

        # Verify schema file was created
        schema_files = list(schemas_dir.glob("*.yaml"))
        assert len(schema_files) == 1

        # Verify no relationships were created
        with open(schema_files[0], "r") as f:
            schema_data = yaml.safe_load(f)

        # Check that user_id in orders does NOT have a link_to attribute
        orders_user_id = schema_data["entities"]["orders"]["attributes"]["user_id"]
        assert "link_to" not in orders_user_id

    def test_import_airbyte_file_not_found(self, runner: CliRunner, tmp_path: Path):
        """Test error handling when manifest file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.yaml"
        schemas_dir = tmp_path / "schemas"

        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(nonexistent_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 1
        assert "Manifest file does not exist" in result.stdout

    def test_import_airbyte_invalid_yaml(self, runner: CliRunner, tmp_path: Path):
        """Test error handling for invalid YAML."""
        manifest_file = tmp_path / "invalid.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write invalid YAML
        with open(manifest_file, "w") as f:
            f.write("invalid: yaml: content: [")

        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 1
        assert "Import failed" in result.stdout

    def test_import_airbyte_no_validation(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test import without validation."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command without validation
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
                "--no-validate",
            ],
        )

        assert result.exit_code == 0
        assert "Successfully imported Airbyte manifest" in result.stdout

    def test_import_airbyte_with_warnings(self, runner: CliRunner, tmp_path: Path):
        """Test import with manifest that generates warnings."""
        manifest_with_warnings = {
            "version": "0.2.0",
            "streams": [
                {
                    "name": "complex_stream",
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "complex_field": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                            "nested_object": {
                                "type": "object",
                                "properties": {"nested_field": {"type": "string"}},
                            },
                        },
                    },
                }
            ],
        }

        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(manifest_with_warnings, f)

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Translation Warnings" in result.stdout
        assert "Successfully imported Airbyte manifest" in result.stdout

    def test_import_airbyte_empty_manifest(self, runner: CliRunner, tmp_path: Path):
        """Test import with manifest that has no streams."""
        empty_manifest = {"version": "0.2.0", "streams": []}

        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(empty_manifest, f)

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 0
        assert "No schemas were generated" in result.stdout

    def test_import_airbyte_help(self, runner: CliRunner):
        """Test help text for import-airbyte command."""
        result = runner.invoke(app, ["import-airbyte", "--help"])

        assert result.exit_code == 0
        assert "Import Airbyte source manifest.yaml file" in result.stdout
        assert "--manifest-file" in result.stdout
        assert "--output-dir" in result.stdout
        assert "--detect-relations" in result.stdout  # Truncated in help output
        assert "--validate" in result.stdout

    def test_import_airbyte_creates_output_directory(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test that import command creates output directory if it doesn't exist."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "nonexistent_schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Ensure output directory doesn't exist
        assert not schemas_dir.exists()

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 0
        assert schemas_dir.exists()
        assert schemas_dir.is_dir()

        # Verify schema file was created
        schema_files = list(schemas_dir.glob("*.yaml"))
        assert len(schema_files) == 1

    def test_import_airbyte_summary_table(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test that import command shows summary table."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Schema Summary" in result.stdout
        assert "Entities" in result.stdout
        assert "Total Records" in result.stdout
        assert "Links" in result.stdout
        assert "Output Formats" in result.stdout

    def test_import_airbyte_next_steps(
        self, runner: CliRunner, tmp_path: Path, sample_manifest
    ):
        """Test that import command shows next steps."""
        manifest_file = tmp_path / "manifest.yaml"
        schemas_dir = tmp_path / "schemas"

        # Write manifest file
        with open(manifest_file, "w") as f:
            yaml.dump(sample_manifest, f)

        # Run import command
        result = runner.invoke(
            app,
            [
                "import-airbyte",
                "--manifest-file",
                str(manifest_file),
                "--output-dir",
                str(schemas_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Next Steps" in result.stdout
        assert "Review the generated schema files" in result.stdout
        assert "jafgen generate" in result.stdout
