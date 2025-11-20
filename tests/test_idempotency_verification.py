"""Tests for idempotency verification across multiple runs."""

import hashlib
import json
from pathlib import Path

from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.parquet_writer import ParquetWriter
from jafgen.schema.discovery import SchemaDiscoveryEngine


class TestIdempotencyVerification:
    """Test idempotency verification across multiple runs."""

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def test_identical_generation_same_seed(self, tmp_path: Path):
        """Test that identical seeds produce identical results."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create test schema
        schema_content = """
system:
  name: "idempotency-test"
  version: "1.0.0"
  seed: 12345
  output:
    format: ["csv", "json"]
    path: "."

entities:
  users:
    count: 100
    attributes:
      id:
        type: "integer"
        unique: true
        required: true
        constraints:
          min_value: 1
          max_value: 100000
      name:
        type: "person.full_name"
        required: true
      email:
        type: "person.email"
        unique: true
        required: true
      age:
        type: "integer"
        required: true
        constraints:
          min_value: 18
          max_value: 80

  orders:
    count: 300
    attributes:
      id:
        type: "integer"
        unique: true
        required: true
        constraints:
          min_value: 1
          max_value: 100000
      user_id:
        type: "link"
        link_to: "idempotency-test.users.id"
        required: true
      total:
        type: "decimal"
        required: true
        constraints:
          min_value: 10.0
          max_value: 1000.0
"""

        schema_file = schema_dir / "idempotency-test.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_data_run():
            """Run a complete data generation cycle."""
            # Fresh imports to ensure clean state
            from jafgen.generation.data_generator import DataGenerator
            from jafgen.generation.link_resolver import LinkResolver
            from jafgen.generation.mimesis_engine import MimesisEngine
            from jafgen.schema.discovery import SchemaDiscoveryEngine

            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            # Create completely fresh instances
            mimesis_engine = MimesisEngine(seed=12345)  # Same seed
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            return data_generator.generate_system(schemas[0])

        # Run generation multiple times
        run1 = generate_data_run()
        run2 = generate_data_run()
        run3 = generate_data_run()

        # Verify identical results
        assert (
            len(run1.entities["users"])
            == len(run2.entities["users"])
            == len(run3.entities["users"])
        )
        assert (
            len(run1.entities["orders"])
            == len(run2.entities["orders"])
            == len(run3.entities["orders"])
        )

        # Compare deterministic data (skip UUIDs as they're inherently non-deterministic)
        for i in range(len(run1.entities["users"])):
            user1 = run1.entities["users"][i]
            user2 = run2.entities["users"][i]
            user3 = run3.entities["users"][i]

            # All attributes should be deterministic with same seed
            assert user1["id"] == user2["id"] == user3["id"]
            assert user1["name"] == user2["name"] == user3["name"]
            assert user1["email"] == user2["email"] == user3["email"]
            assert user1["age"] == user2["age"] == user3["age"]

        for i in range(len(run1.entities["orders"])):
            order1 = run1.entities["orders"][i]
            order2 = run2.entities["orders"][i]
            order3 = run3.entities["orders"][i]

            # All attributes should be deterministic with same seed
            assert order1["id"] == order2["id"] == order3["id"]
            assert order1["user_id"] == order2["user_id"] == order3["user_id"]
            assert order1["total"] == order2["total"] == order3["total"]

    def test_different_seeds_produce_different_results(self, tmp_path: Path):
        """Test that different seeds produce different results."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema_content = """
system:
  name: "seed-test"
  version: "1.0.0"
  seed: 100
  output:
    format: ["csv"]
    path: "."

entities:
  users:
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
"""

        schema_file = schema_dir / "seed-test.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_with_seed(seed):
            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=seed)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            return data_generator.generate_system(schemas[0])

        # Generate with different seeds
        result1 = generate_with_seed(100)
        result2 = generate_with_seed(200)
        result3 = generate_with_seed(300)

        # Results should be different
        users1 = result1.entities["users"]
        users2 = result2.entities["users"]
        users3 = result3.entities["users"]

        # At least some values should be different
        names1 = [user["name"] for user in users1]
        names2 = [user["name"] for user in users2]
        names3 = [user["name"] for user in users3]

        assert names1 != names2
        assert names2 != names3
        assert names1 != names3

        emails1 = [user["email"] for user in users1]
        emails2 = [user["email"] for user in users2]
        emails3 = [user["email"] for user in users3]

        assert emails1 != emails2
        assert emails2 != emails3
        assert emails1 != emails3

    def test_file_output_idempotency(self, tmp_path: Path):
        """Test that file outputs are identical across runs."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"
        output_dir3 = tmp_path / "output3"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()
        output_dir3.mkdir()

        schema_content = """
system:
  name: "file-idempotency"
  version: "1.0.0"
  seed: 999
  output:
    format: ["csv", "json"]
    path: "."

entities:
  products:
    count: 75
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
"""

        schema_file = schema_dir / "file-idempotency.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_and_write(output_dir):
            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=999)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            # Write to files
            csv_writer = CSVWriter()
            json_writer = JSONWriter()

            csv_writer.write(generated_system.entities, output_dir)
            json_writer.write(generated_system.entities, output_dir)

        # Generate files three times
        generate_and_write(output_dir1)
        generate_and_write(output_dir2)
        generate_and_write(output_dir3)

        # Compare file hashes
        csv_hash1 = self.calculate_file_hash(output_dir1 / "products.csv")
        csv_hash2 = self.calculate_file_hash(output_dir2 / "products.csv")
        csv_hash3 = self.calculate_file_hash(output_dir3 / "products.csv")

        json_hash1 = self.calculate_file_hash(output_dir1 / "products.json")
        json_hash2 = self.calculate_file_hash(output_dir2 / "products.json")
        json_hash3 = self.calculate_file_hash(output_dir3 / "products.json")

        # All hashes should be identical
        assert csv_hash1 == csv_hash2 == csv_hash3
        assert json_hash1 == json_hash2 == json_hash3

        # Verify file contents are actually identical
        csv_content1 = (output_dir1 / "products.csv").read_text()
        csv_content2 = (output_dir2 / "products.csv").read_text()
        csv_content3 = (output_dir3 / "products.csv").read_text()

        assert csv_content1 == csv_content2 == csv_content3

        json_content1 = (output_dir1 / "products.json").read_text()
        json_content2 = (output_dir2 / "products.json").read_text()
        json_content3 = (output_dir3 / "products.json").read_text()

        assert json_content1 == json_content2 == json_content3

    def test_cross_format_consistency(self, tmp_path: Path):
        """Test that data is consistent across different output formats."""
        schema_dir = tmp_path / "schemas"
        output_dir = tmp_path / "output"

        schema_dir.mkdir()
        output_dir.mkdir()

        schema_content = """
system:
  name: "format-consistency"
  version: "1.0.0"
  seed: 555
  output:
    format: ["csv", "json", "parquet"]
    path: "."

entities:
  customers:
    count: 30
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
      balance:
        type: "decimal"
        required: true
        constraints:
          min_value: 0.0
          max_value: 10000.0
"""

        schema_file = schema_dir / "format-consistency.yaml"
        schema_file.write_text(schema_content.strip())

        # Generate data
        discovery_engine = SchemaDiscoveryEngine()
        schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

        mimesis_engine = MimesisEngine(seed=555)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        generated_system = data_generator.generate_system(schemas[0])

        # Write to different formats
        csv_writer = CSVWriter()
        json_writer = JSONWriter()
        parquet_writer = ParquetWriter()

        csv_writer.write(generated_system.entities, output_dir)
        json_writer.write(generated_system.entities, output_dir)
        parquet_writer.write(generated_system.entities, output_dir)

        # Read back and compare
        # CSV
        import csv

        with open(output_dir / "customers.csv", "r") as f:
            csv_reader = csv.DictReader(f)
            csv_data = list(csv_reader)

        # JSON
        with open(output_dir / "customers.json", "r") as f:
            json_data = json.load(f)

        # Parquet
        try:
            import pandas as pd

            parquet_df = pd.read_parquet(output_dir / "customers.parquet")
            parquet_data = parquet_df.to_dict("records")
        except ImportError:
            # Skip parquet comparison if pandas not available
            parquet_data = json_data

        # Compare data consistency
        assert len(csv_data) == len(json_data) == len(parquet_data) == 30

        # Compare first few records
        for i in range(min(5, len(csv_data))):
            csv_record = csv_data[i]
            json_record = json_data[i]

            # IDs should match
            assert csv_record["id"] == json_record["id"]
            assert csv_record["name"] == json_record["name"]
            assert csv_record["email"] == json_record["email"]

            # Balance should be close (accounting for string/float conversion)
            csv_balance = float(csv_record["balance"])
            json_balance = float(json_record["balance"])
            assert abs(csv_balance - json_balance) < 0.01

    def test_schema_modification_changes_output(self, tmp_path: Path):
        """Test that schema modifications produce different outputs."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()

        # Original schema
        original_schema = """
system:
  name: "modification-test"
  version: "1.0.0"
  seed: 777
  output:
    format: ["csv"]
    path: "."

entities:
  items:
    count: 25
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
"""

        # Modified schema (different count)
        modified_schema = """
system:
  name: "modification-test"
  version: "1.0.0"
  seed: 777
  output:
    format: ["csv"]
    path: "."

entities:
  items:
    count: 50
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
"""

        schema_file = schema_dir / "modification-test.yaml"

        def generate_with_schema(schema_content, output_dir):
            schema_file.write_text(schema_content.strip())

            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=777)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            csv_writer = CSVWriter()
            csv_writer.write(generated_system.entities, output_dir)

            return generated_system

        # Generate with original schema
        result1 = generate_with_schema(original_schema, output_dir1)

        # Generate with modified schema
        result2 = generate_with_schema(modified_schema, output_dir2)

        # Results should be different
        assert len(result1.entities["items"]) == 25
        assert len(result2.entities["items"]) == 50

        # File contents should be different
        csv_content1 = (output_dir1 / "items.csv").read_text()
        csv_content2 = (output_dir2 / "items.csv").read_text()

        assert csv_content1 != csv_content2

        # Line counts should be different
        lines1 = csv_content1.strip().split("\n")
        lines2 = csv_content2.strip().split("\n")

        assert len(lines1) == 26  # Header + 25 items
        assert len(lines2) == 51  # Header + 50 items

    def test_metadata_consistency(self, tmp_path: Path):
        """Test that generation metadata is consistent across runs."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema_content = """
system:
  name: "metadata-test"
  version: "1.0.0"
  seed: 888
  output:
    format: ["csv"]
    path: "."

entities:
  records:
    count: 40
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      value:
        type: "integer"
        required: true
        constraints:
          min_value: 1
          max_value: 100
"""

        schema_file = schema_dir / "metadata-test.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_and_get_metadata():
            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=888)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])
            return generated_system.metadata

        # Generate metadata multiple times
        metadata1 = generate_and_get_metadata()
        metadata2 = generate_and_get_metadata()
        metadata3 = generate_and_get_metadata()

        # Metadata should be consistent
        assert metadata1.seed_used == metadata2.seed_used == metadata3.seed_used == 888
        assert (
            metadata1.total_records
            == metadata2.total_records
            == metadata3.total_records
            == 40
        )
        assert (
            metadata1.entity_counts
            == metadata2.entity_counts
            == metadata3.entity_counts
        )

        # Schema hashes should be identical
        assert metadata1.schema_hash == metadata2.schema_hash == metadata3.schema_hash

    def test_idempotency_with_multiple_output_formats(self, tmp_path: Path):
        """Test idempotency across multiple output formats simultaneously."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()

        schema_content = """
system:
  name: "multi-format-idempotency"
  version: "1.0.0"
  seed: 555
  output:
    format: ["csv", "json", "parquet"]
    path: "."

entities:
  items:
    count: 50
    attributes:
      id:
        type: "integer"
        unique: true
        required: true
        constraints:
          min_value: 1
          max_value: 100000
      name:
        type: "text.word"
        required: true
      price:
        type: "decimal"
        required: true
        constraints:
          min_value: 1.0
          max_value: 100.0
      created_at:
        type: "datetime.datetime"
        required: true
"""

        schema_file = schema_dir / "multi-format.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_all_formats(output_dir):
            # Fresh imports and instances to ensure clean state
            from jafgen.generation.data_generator import DataGenerator
            from jafgen.generation.link_resolver import LinkResolver
            from jafgen.generation.mimesis_engine import MimesisEngine
            from jafgen.output.csv_writer import CSVWriter
            from jafgen.output.json_writer import JSONWriter
            from jafgen.output.parquet_writer import ParquetWriter
            from jafgen.schema.discovery import SchemaDiscoveryEngine

            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            # Use the schema's seed for proper idempotency
            schema_seed = schemas[0].seed or 555
            mimesis_engine = MimesisEngine(seed=schema_seed)
            mimesis_engine.reset_unique_values()  # Reset for fresh generation
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            # Write to all formats
            csv_writer = CSVWriter()
            json_writer = JSONWriter()
            parquet_writer = ParquetWriter()

            csv_writer.write(generated_system.entities, output_dir)
            json_writer.write(generated_system.entities, output_dir)
            parquet_writer.write(generated_system.entities, output_dir)

            return generated_system

        # Generate twice
        system1 = generate_all_formats(output_dir1)
        system2 = generate_all_formats(output_dir2)

        # Data should be identical
        assert len(system1.entities["items"]) == len(system2.entities["items"])

        for i in range(len(system1.entities["items"])):
            item1 = system1.entities["items"][i]
            item2 = system2.entities["items"][i]
            assert item1["id"] == item2["id"]
            assert item1["name"] == item2["name"]
            assert item1["price"] == item2["price"]
            assert item1["created_at"] == item2["created_at"]

        # All output files should be identical
        for format_ext in ["csv", "json", "parquet"]:
            file1 = output_dir1 / f"items.{format_ext}"
            file2 = output_dir2 / f"items.{format_ext}"

            assert file1.exists()
            assert file2.exists()

            # Compare file hashes
            hash1 = self.calculate_file_hash(file1)
            hash2 = self.calculate_file_hash(file2)
            assert hash1 == hash2, f"{format_ext} files should be identical"

    def test_idempotency_with_complex_relationships(self, tmp_path: Path):
        """Test idempotency with complex entity relationships."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()

        schema_content = """
system:
  name: "complex-relationships"
  version: "1.0.0"
  seed: 999
  output:
    format: ["csv"]
    path: "."

entities:
  categories:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true

  products:
    count: 50
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      category_id:
        type: "link"
        link_to: "complex-relationships.categories.id"
        required: true
      price:
        type: "decimal"
        required: true
        constraints:
          min_value: 1.0
          max_value: 100.0

  customers:
    count: 30
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true

  orders:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "complex-relationships.customers.id"
        required: true
      product_id:
        type: "link"
        link_to: "complex-relationships.products.id"
        required: true
      quantity:
        type: "integer"
        required: true
        constraints:
          min_value: 1
          max_value: 10
"""

        schema_file = schema_dir / "complex-relationships.yaml"
        schema_file.write_text(schema_content.strip())

        def generate_complex_data(output_dir):
            # Fresh imports to ensure clean state
            from jafgen.generation.data_generator import DataGenerator
            from jafgen.generation.link_resolver import LinkResolver
            from jafgen.generation.mimesis_engine import MimesisEngine
            from jafgen.output.csv_writer import CSVWriter
            from jafgen.schema.discovery import SchemaDiscoveryEngine

            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            # Use the schema's seed for proper idempotency
            schema_seed = schemas[0].seed or 999
            mimesis_engine = MimesisEngine(seed=schema_seed)
            mimesis_engine.reset_unique_values()  # Reset for fresh generation
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            csv_writer = CSVWriter()
            csv_writer.write(generated_system.entities, output_dir)

            return generated_system

        # Generate twice
        system1 = generate_complex_data(output_dir1)
        system2 = generate_complex_data(output_dir2)

        # Verify identical entity counts
        for entity_name in ["categories", "products", "customers", "orders"]:
            assert len(system1.entities[entity_name]) == len(
                system2.entities[entity_name]
            )

        # Verify identical relationships
        # Categories should be identical
        for i in range(len(system1.entities["categories"])):
            cat1 = system1.entities["categories"][i]
            cat2 = system2.entities["categories"][i]
            assert cat1["id"] == cat2["id"]
            assert cat1["name"] == cat2["name"]

        # Products should have identical category links
        for i in range(len(system1.entities["products"])):
            prod1 = system1.entities["products"][i]
            prod2 = system2.entities["products"][i]
            assert prod1["id"] == prod2["id"]
            assert prod1["category_id"] == prod2["category_id"]

        # Orders should have identical customer and product links
        for i in range(len(system1.entities["orders"])):
            order1 = system1.entities["orders"][i]
            order2 = system2.entities["orders"][i]
            assert order1["id"] == order2["id"]
            assert order1["customer_id"] == order2["customer_id"]
            assert order1["product_id"] == order2["product_id"]

        # Verify file-level idempotency
        for entity_name in ["categories", "products", "customers", "orders"]:
            file1 = output_dir1 / f"{entity_name}.csv"
            file2 = output_dir2 / f"{entity_name}.csv"

            hash1 = self.calculate_file_hash(file1)
            hash2 = self.calculate_file_hash(file2)
            assert hash1 == hash2, f"{entity_name}.csv files should be identical"

    def test_idempotency_across_process_restarts(self, tmp_path: Path):
        """Test idempotency simulation across process restarts."""
        schema_dir = tmp_path / "schemas"
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"

        schema_dir.mkdir()
        output_dir1.mkdir()
        output_dir2.mkdir()

        schema_content = """
system:
  name: "process-restart-test"
  version: "1.0.0"
  seed: 12345
  output:
    format: ["csv", "json"]
    path: "."

entities:
  users:
    count: 40
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
      created_at:
        type: "datetime.datetime"
        required: true
"""

        schema_file = schema_dir / "process-restart.yaml"
        schema_file.write_text(schema_content.strip())

        def simulate_process_run(output_dir):
            """Simulate a complete process run with fresh imports."""
            # Fresh imports simulate process restart
            from jafgen.generation.data_generator import DataGenerator
            from jafgen.generation.link_resolver import LinkResolver
            from jafgen.generation.mimesis_engine import MimesisEngine
            from jafgen.output.csv_writer import CSVWriter
            from jafgen.output.json_writer import JSONWriter
            from jafgen.schema.discovery import SchemaDiscoveryEngine

            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)

            mimesis_engine = MimesisEngine(seed=12345)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)

            generated_system = data_generator.generate_system(schemas[0])

            csv_writer = CSVWriter()
            json_writer = JSONWriter()

            csv_writer.write(generated_system.entities, output_dir)
            json_writer.write(generated_system.entities, output_dir)

            return generated_system

        # Simulate two separate process runs
        system1 = simulate_process_run(output_dir1)
        system2 = simulate_process_run(output_dir2)

        # Results should be identical
        assert len(system1.entities["users"]) == len(system2.entities["users"])

        # Compare data
        for i in range(len(system1.entities["users"])):
            user1 = system1.entities["users"][i]
            user2 = system2.entities["users"][i]
            assert user1["id"] == user2["id"]
            assert user1["name"] == user2["name"]
            assert user1["email"] == user2["email"]
            assert user1["created_at"] == user2["created_at"]

        # Compare output files
        for format_ext in ["csv", "json"]:
            file1 = output_dir1 / f"users.{format_ext}"
            file2 = output_dir2 / f"users.{format_ext}"

            content1 = file1.read_text()
            content2 = file2.read_text()
            assert (
                content1 == content2
            ), f"users.{format_ext} should be identical across process runs"
