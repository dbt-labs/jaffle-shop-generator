"""End-to-end integration tests for complete workflows."""

import json
from pathlib import Path

from jafgen.cli import app
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.output_manager import OutputManager
from jafgen.schema.discovery import SchemaDiscoveryEngine


class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""

    def test_complete_schema_to_output_workflow(self, tmp_path: Path):
        """Test complete workflow from schema discovery to output generation."""
        # Create schema directory and files
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "output"
        schema_dir.mkdir()
        output_dir.mkdir()

        # Create a comprehensive schema
        schema_content = """
system:
  name: "e2e-test-system"
  version: "1.0.0"
  seed: 12345
  output:
    format: ["csv", "json"]
    path: "."

entities:
  customers:
    count: 50
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
      age:
        type: "numeric.integer"
        required: true
        constraints:
          min_value: 18
          max_value: 80
      created_at:
        type: "datetime.datetime"
        required: true

  orders:
    count: 150
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "e2e-test-system.customers.id"
        required: true
      total:
        type: "decimal"
        required: true
        constraints:
          min_value: 5.0
          max_value: 500.0
      order_date:
        type: "datetime.date"
        required: true
"""

        schema_file = schema_dir / "e2e-test.yaml"
        schema_file.write_text(schema_content.strip())

        # Step 1: Schema Discovery
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        assert len(schemas) == 1
        assert validation_result.is_valid

        schema = schemas[0]
        assert schema.name == "e2e-test-system"
        assert len(schema.entities) == 2

        # Step 2: Data Generation
        mimesis_engine = MimesisEngine(seed=12345)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        generated_system = data_generator.generate_system(schema)

        assert generated_system.schema.name == "e2e-test-system"
        assert len(generated_system.entities) == 2
        assert len(generated_system.entities["customers"]) == 50
        assert len(generated_system.entities["orders"]) == 150

        # Verify data integrity
        customer_ids = {
            customer["id"] for customer in generated_system.entities["customers"]
        }
        order_customer_ids = {
            order["customer_id"] for order in generated_system.entities["orders"]
        }

        # All order customer_ids should reference valid customers
        assert order_customer_ids.issubset(customer_ids)

        # Step 3: Output Generation
        writers = {"csv": CSVWriter(), "json": JSONWriter()}
        output_manager = OutputManager(writers)

        # Write to output directory
        output_manager.prepare_output_directory(output_dir)

        # Write each entity
        for format_name in ["csv", "json"]:
            writer = writers[format_name]
            writer.write(generated_system.entities, output_dir)

        # Step 4: Verify Output Files
        customers_csv = output_dir / "customers.csv"
        customers_json = output_dir / "customers.json"
        orders_csv = output_dir / "orders.csv"
        orders_json = output_dir / "orders.json"

        assert customers_csv.exists()
        assert customers_json.exists()
        assert orders_csv.exists()
        assert orders_json.exists()

        # Verify CSV content
        csv_content = customers_csv.read_text()
        csv_lines = csv_content.strip().split("\n")
        assert len(csv_lines) == 51  # Header + 50 customers

        # Verify JSON content
        with open(customers_json, "r") as f:
            json_data = json.load(f)
        assert len(json_data) == 50

        # Verify data consistency between formats
        csv_first_line = csv_lines[1].split(",")
        json_first_record = json_data[0]

        # IDs should match (assuming same order)
        assert csv_first_line[0] == json_first_record["id"]

    def test_cli_end_to_end_workflow(self, tmp_path: Path):
        """Test complete CLI workflow from command to output."""
        from typer.testing import CliRunner

        # Create schema directory and files
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "output"
        schema_dir.mkdir()

        # Create a simple schema
        schema_content = """
system:
  name: "cli-test"
  version: "1.0.0"
  seed: 999
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

        schema_file = schema_dir / "cli-test.yaml"
        schema_file.write_text(schema_content.strip())

        runner = CliRunner()

        # Test validate command
        result = runner.invoke(
            app, ["validate-schema", "--schema-dir", str(schema_dir)]
        )
        assert result.exit_code == 0
        assert "All schemas are valid" in result.stdout

        # Test list command
        result = runner.invoke(app, ["list-schemas", "--schema-dir", str(schema_dir)])
        assert result.exit_code == 0
        assert "cli-test" in result.stdout

        # Test generate command
        result = runner.invoke(
            app,
            [
                "generate",
                "--schema-dir",
                str(schema_dir),
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Successfully loaded 1 schema" in result.stdout

        # Verify output file was created
        users_csv = output_dir / "users.csv"
        assert users_csv.exists()

        # Verify content
        csv_content = users_csv.read_text()
        lines = csv_content.strip().split("\n")
        assert len(lines) == 11  # Header + 10 users

    def test_multiple_schema_cross_references(self, tmp_path: Path):
        """Test workflow with multiple schemas that reference each other."""
        schema_dir = tmp_path / "schemas"
        tmp_path / "output"
        schema_dir.mkdir()

        # Schema 1: Users
        users_schema = """
system:
  name: "users-schema"
  version: "1.0.0"
  seed: 100
  output:
    format: ["csv"]
    path: "users"

entities:
  users:
    count: 20
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
"""

        # Schema 2: Products
        products_schema = """
system:
  name: "products-schema"
  version: "1.0.0"
  seed: 200
  output:
    format: ["csv"]
    path: "products"

entities:
  products:
    count: 30
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      price:
        type: "decimal"
        required: true
        constraints:
          min_value: 1.0
          max_value: 100.0
"""

        # Schema 3: Orders (references both users and products)
        orders_schema = """
system:
  name: "orders-schema"
  version: "1.0.0"
  seed: 300
  output:
    format: ["csv"]
    path: "orders"

entities:
  orders:
    count: 50
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      user_id:
        type: "link"
        link_to: "users-schema.users.id"
        required: true
      product_id:
        type: "link"
        link_to: "products-schema.products.id"
        required: true
      quantity:
        type: "numeric.integer"
        required: true
        constraints:
          min_value: 1
          max_value: 10
"""

        (schema_dir / "users.yaml").write_text(users_schema.strip())
        (schema_dir / "products.yaml").write_text(products_schema.strip())
        (schema_dir / "orders.yaml").write_text(orders_schema.strip())

        # Run complete workflow
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        assert len(schemas) == 3
        assert validation_result.is_valid

        # Generate data for all schemas
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        generated_systems = data_generator.generate_multiple_systems(schemas)

        assert len(generated_systems) == 3

        # Verify cross-references
        users_data = None
        products_data = None
        orders_data = None

        for system in generated_systems:
            if system.schema.name == "users-schema":
                users_data = system.entities["users"]
            elif system.schema.name == "products-schema":
                products_data = system.entities["products"]
            elif system.schema.name == "orders-schema":
                orders_data = system.entities["orders"]

        assert users_data is not None
        assert products_data is not None
        assert orders_data is not None

        # Verify referential integrity
        user_ids = {user["id"] for user in users_data}
        product_ids = {product["id"] for product in products_data}

        for order in orders_data:
            assert order["user_id"] in user_ids
            assert order["product_id"] in product_ids

    def test_error_recovery_workflow(self, tmp_path: Path):
        """Test workflow error recovery and graceful handling."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create a schema with intentional errors
        invalid_schema = """
system:
  name: "error-test"
  version: "1.0.0"

entities:
  orders:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
      user_id:
        type: "link"
        link_to: "nonexistent.users.id"  # Invalid reference
"""

        schema_file = schema_dir / "error-test.yaml"
        schema_file.write_text(invalid_schema.strip())

        # Test that discovery catches the error
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        assert len(schemas) == 1  # Schema loads but validation fails
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0

        # Verify error contains useful information
        error_messages = [error.message for error in validation_result.errors]
        assert any("nonexistent.users" in msg for msg in error_messages)

    def test_all_output_formats_integration(self, tmp_path: Path):
        """Test integration with all supported output formats (requirement 9.4)."""
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "output"
        schema_dir.mkdir()
        output_dir.mkdir()

        # Create schema that uses all output formats
        all_formats_schema = """
system:
  name: "all-formats-test"
  version: "1.0.0"
  seed: 777
  output:
    format: ["csv", "json", "parquet", "duckdb"]
    path: "."

entities:
  products:
    count: 25
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      price:
        type: "decimal"
        required: true
        constraints:
          min_value: 1.0
          max_value: 100.0
      category:
        type: "text.word"
        required: true
      in_stock:
        type: "development.boolean"
        required: true
      created_at:
        type: "datetime.datetime"
        required: true
"""

        schema_file = schema_dir / "all-formats.yaml"
        schema_file.write_text(all_formats_schema.strip())

        # Run complete workflow
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        assert validation_result.is_valid

        # Generate data
        mimesis_engine = MimesisEngine(seed=777)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        generated_system = data_generator.generate_system(schemas[0])

        # Write to all formats
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.duckdb_writer import DuckDBWriter
        from jafgen.output.json_writer import JSONWriter
        from jafgen.output.parquet_writer import ParquetWriter

        writers = {
            "csv": CSVWriter(),
            "json": JSONWriter(),
            "parquet": ParquetWriter(),
            "duckdb": DuckDBWriter(),
        }

        for format_name, writer in writers.items():
            writer.write(generated_system.entities, output_dir)

        # Verify all output files exist
        csv_file = output_dir / "products.csv"
        json_file = output_dir / "products.json"
        parquet_file = output_dir / "products.parquet"
        duckdb_file = output_dir / "generated_data.duckdb"

        assert csv_file.exists(), "CSV file should be created"
        assert json_file.exists(), "JSON file should be created"
        assert parquet_file.exists(), "Parquet file should be created"
        assert duckdb_file.exists(), "DuckDB file should be created"

        # Verify file contents are valid
        # CSV
        csv_content = csv_file.read_text()
        csv_lines = csv_content.strip().split("\n")
        assert len(csv_lines) == 26  # Header + 25 products

        # JSON
        import json

        with open(json_file, "r") as f:
            json_data = json.load(f)
        assert len(json_data) == 25

        # Verify data consistency across formats
        csv_first_line = csv_lines[1].split(",")
        json_first_record = json_data[0]
        assert csv_first_line[0] == json_first_record["id"]

        # Parquet (if pandas available)
        try:
            import pandas as pd

            parquet_df = pd.read_parquet(parquet_file)
            assert len(parquet_df) == 25
            assert parquet_df.iloc[0]["id"] == json_first_record["id"]
        except ImportError:
            # Skip parquet validation if pandas not available
            pass

        # DuckDB
        try:
            import duckdb

            conn = duckdb.connect(str(duckdb_file))
            result = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            assert result[0] == 25
            conn.close()
        except ImportError:
            # Skip DuckDB validation if duckdb not available
            pass

    def test_large_scale_integration_workflow(self, tmp_path: Path):
        """Test integration workflow with larger datasets."""
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "output"
        schema_dir.mkdir()
        output_dir.mkdir()

        # Create schema with moderate size for integration testing
        large_schema = """
system:
  name: "large-integration-test"
  version: "1.0.0"
  seed: 12345
  output:
    format: ["csv", "json"]
    path: "."

entities:
  customers:
    count: 500
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
      phone:
        type: "person.phone_number"
        required: true
      created_at:
        type: "datetime.datetime"
        required: true

  orders:
    count: 2000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "large-integration-test.customers.id"
        required: true
      total:
        type: "decimal"
        required: true
        constraints:
          min_value: 5.0
          max_value: 1000.0
      status:
        type: "text.word"
        required: true
      order_date:
        type: "datetime.date"
        required: true
"""

        schema_file = schema_dir / "large-integration.yaml"
        schema_file.write_text(large_schema.strip())

        import time

        start_time = time.time()

        # Run complete workflow
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        assert validation_result.is_valid

        # Generate data
        mimesis_engine = MimesisEngine(seed=12345)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        generated_system = data_generator.generate_system(schemas[0])

        # Write outputs
        csv_writer = CSVWriter()
        json_writer = JSONWriter()

        csv_writer.write(generated_system.entities, output_dir)
        json_writer.write(generated_system.entities, output_dir)

        total_time = time.time() - start_time

        # Verify results
        assert len(generated_system.entities["customers"]) == 500
        assert len(generated_system.entities["orders"]) == 2000

        # Verify referential integrity
        customer_ids = {
            customer["id"] for customer in generated_system.entities["customers"]
        }
        order_customer_ids = {
            order["customer_id"] for order in generated_system.entities["orders"]
        }
        assert order_customer_ids.issubset(customer_ids)

        # Verify files exist and have correct size
        customers_csv = output_dir / "customers.csv"
        orders_csv = output_dir / "orders.csv"
        customers_json = output_dir / "customers.json"
        orders_json = output_dir / "orders.json"

        assert customers_csv.exists()
        assert orders_csv.exists()
        assert customers_json.exists()
        assert orders_json.exists()

        # Performance check
        assert total_time < 30.0  # Should complete within 30 seconds

        print(
            f"Large integration test: Generated 2,500 records in {total_time:.2f} seconds"
        )

    def test_schema_validation_integration(self, tmp_path: Path):
        """Test integration of schema validation with error reporting."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create multiple schemas with various validation issues
        valid_schema = """
system:
  name: "valid-schema"
  version: "1.0.0"
  seed: 100

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

        invalid_syntax_schema = """
system:
  name: "invalid-syntax"
  version: "1.0.0"
  # Missing required fields
entities:
  # Invalid YAML structure
  users
    count: 10
"""

        invalid_reference_schema = """
system:
  name: "invalid-reference"
  version: "1.0.0"
  seed: 200

entities:
  orders:
    count: 5
    attributes:
      id:
        type: "uuid"
        unique: true
      user_id:
        type: "link"
        link_to: "nonexistent.users.id"  # Invalid reference
"""

        # Write schemas
        (schema_dir / "valid.yaml").write_text(valid_schema.strip())
        (schema_dir / "invalid-syntax.yaml").write_text(invalid_syntax_schema.strip())
        (schema_dir / "invalid-reference.yaml").write_text(
            invalid_reference_schema.strip()
        )

        # Test discovery and validation
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(
            schema_dir
        )

        # Should load valid schemas but report validation errors
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0

        # Should have loaded at least the valid schema
        valid_schemas = [s for s in schemas if s.name == "valid-schema"]
        assert len(valid_schemas) == 1

        # Verify error reporting includes useful information
        error_messages = [error.message for error in validation_result.errors]
        assert any(
            "syntax" in msg.lower() or "yaml" in msg.lower() for msg in error_messages
        )
        assert any("nonexistent" in msg for msg in error_messages)

    def test_idempotency_across_runs(self, tmp_path: Path):
        """Test that multiple runs produce identical results."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()

        # Create schema
        schema_content = """
system:
  name: "idempotency-test"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "json"]
    path: "."

entities:
  users:
    count: 25
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

        schema_file = schema_dir / "idempotency-test.yaml"
        schema_file.write_text(schema_content.strip())

        # Run generation twice
        def run_generation(output_dir):
            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=42)  # Same seed
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            writers = {"csv": CSVWriter(), "json": JSONWriter()}

            for format_name, writer in writers.items():
                writer.write(generated_system.entities, output_dir)

            return generated_system

        # Generate data twice
        system1 = run_generation(output_dir1)
        system2 = run_generation(output_dir2)

        # Compare generated data
        assert len(system1.entities["users"]) == len(system2.entities["users"])

        # Data should be identical
        for i in range(len(system1.entities["users"])):
            user1 = system1.entities["users"][i]
            user2 = system2.entities["users"][i]
            assert user1["id"] == user2["id"]
            assert user1["name"] == user2["name"]
            assert user1["email"] == user2["email"]

        # Files should be identical
        csv1_content = (output_dir1 / "users.csv").read_text()
        csv2_content = (output_dir2 / "users.csv").read_text()
        assert csv1_content == csv2_content

        json1_content = (output_dir1 / "users.json").read_text()
        json2_content = (output_dir2 / "users.json").read_text()
        assert json1_content == json2_content
