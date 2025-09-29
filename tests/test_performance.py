"""Performance tests for data generation and memory usage."""

import time
import tempfile
from pathlib import Path
import os

import pytest

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter


class TestPerformance:
    """Performance and memory usage tests."""
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        if not HAS_PSUTIL:
            return 0.0  # Return 0 if psutil not available
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_large_dataset_generation_performance(self, tmp_path: Path):
        """Test performance with large datasets."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Create schema for large dataset
        large_schema = """
system:
  name: "performance-test"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
    path: "."

entities:
  users:
    count: 10000
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
        type: "integer"
        required: true
        constraints:
          min_value: 18
          max_value: 80
      created_at:
        type: "datetime.datetime"
        required: true
  
  orders:
    count: 50000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      user_id:
        type: "link"
        link_to: "performance-test.users.id"
        required: true
      total:
        type: "decimal"
        required: true
        constraints:
          min_value: 5.0
          max_value: 500.0
"""
        
        schema_file = schema_dir / "performance-test.yaml"
        schema_file.write_text(large_schema.strip())
        
        # Measure memory before
        memory_before = self.get_memory_usage()
        
        # Time the complete workflow
        start_time = time.time()
        
        # Schema discovery
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(schema_dir)
        
        assert validation_result.is_valid
        
        # Data generation
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        generated_system = data_generator.generate_system(schemas[0])
        
        generation_time = time.time() - start_time
        memory_after_generation = self.get_memory_usage()
        
        # Verify data was generated correctly
        assert len(generated_system.entities["users"]) == 10000
        assert len(generated_system.entities["orders"]) == 50000
        
        # Performance assertions
        assert generation_time < 30.0  # Should complete within 30 seconds
        
        memory_used = memory_after_generation - memory_before
        if HAS_PSUTIL:
            assert memory_used < 500  # Should use less than 500MB
        
        print(f"Generated 60,000 records in {generation_time:.2f} seconds")
        if HAS_PSUTIL:
            print(f"Memory usage: {memory_used:.2f} MB")
        else:
            print("Memory usage: Not available (psutil not installed)")
        
        # Test output writing performance
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        write_start = time.time()
        csv_writer = CSVWriter()
        csv_writer.write(generated_system.entities, output_dir)
        write_time = time.time() - write_start
        
        assert write_time < 10.0  # CSV writing should be fast
        
        # Verify files were created and have correct size
        users_csv = output_dir / "users.csv"
        orders_csv = output_dir / "orders.csv"
        
        assert users_csv.exists()
        assert orders_csv.exists()
        
        # Check file sizes are reasonable
        users_size = users_csv.stat().st_size
        orders_size = orders_csv.stat().st_size
        
        assert users_size > 100000  # Should be substantial files
        assert orders_size > 500000
        
        print(f"CSV writing took {write_time:.2f} seconds")
        print(f"Users CSV: {users_size / 1024:.1f} KB")
        print(f"Orders CSV: {orders_size / 1024:.1f} KB")
    
    def test_memory_usage_with_unique_constraints(self, tmp_path: Path):
        """Test memory usage when generating many unique values."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Schema with many unique fields
        unique_schema = """
system:
  name: "unique-test"
  version: "1.0.0"
  seed: 42

entities:
  users:
    count: 5000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      email:
        type: "person.email"
        unique: true
        required: true
      username:
        type: "text.word"
        unique: true
        required: true
      phone:
        type: "person.phone_number"
        unique: true
        required: true
"""
        
        schema_file = schema_dir / "unique-test.yaml"
        schema_file.write_text(unique_schema.strip())
        
        memory_before = self.get_memory_usage()
        
        # Generate data
        discovery_engine = SchemaDiscoveryEngine()
        schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)
        
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        start_time = time.time()
        generated_system = data_generator.generate_system(schemas[0])
        generation_time = time.time() - start_time
        
        memory_after = self.get_memory_usage()
        memory_used = memory_after - memory_before
        
        # Verify all values are unique
        users = generated_system.entities["users"]
        emails = [user["email"] for user in users]
        usernames = [user["username"] for user in users]
        
        assert len(set(emails)) == len(emails)  # All emails unique
        assert len(set(usernames)) == len(usernames)  # All usernames unique
        
        # Performance checks
        assert generation_time < 15.0  # Should be reasonably fast
        if HAS_PSUTIL:
            assert memory_used < 200  # Memory usage should be reasonable
        
        print(f"Generated 5,000 users with unique constraints in {generation_time:.2f} seconds")
        if HAS_PSUTIL:
            print(f"Memory usage: {memory_used:.2f} MB")
        else:
            print("Memory usage: Not available (psutil not installed)")
    
    def test_link_resolution_performance(self, tmp_path: Path):
        """Test performance of link resolution with many relationships."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Schema with complex relationships
        complex_schema = """
system:
  name: "complex-links"
  version: "1.0.0"
  seed: 42

entities:
  categories:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
  
  products:
    count: 2000
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
        link_to: "complex-links.categories.id"
        required: true
  
  customers:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
  
  orders:
    count: 5000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "complex-links.customers.id"
        required: true
      product_id:
        type: "link"
        link_to: "complex-links.products.id"
        required: true
"""
        
        schema_file = schema_dir / "complex-links.yaml"
        schema_file.write_text(complex_schema.strip())
        
        start_time = time.time()
        
        # Generate data
        discovery_engine = SchemaDiscoveryEngine()
        schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)
        
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        generated_system = data_generator.generate_system(schemas[0])
        
        total_time = time.time() - start_time
        
        # Verify all links are resolved correctly
        categories = generated_system.entities["categories"]
        products = generated_system.entities["products"]
        customers = generated_system.entities["customers"]
        orders = generated_system.entities["orders"]
        
        category_ids = {cat["id"] for cat in categories}
        product_ids = {prod["id"] for prod in products}
        customer_ids = {cust["id"] for cust in customers}
        
        # Verify referential integrity
        for product in products:
            assert product["category_id"] in category_ids
        
        for order in orders:
            assert order["customer_id"] in customer_ids
            assert order["product_id"] in product_ids
        
        # Performance check
        assert total_time < 20.0  # Should handle complex links efficiently
        
        print(f"Generated complex linked data (8,100 total records) in {total_time:.2f} seconds")
    
    def test_concurrent_generation_simulation(self, tmp_path: Path):
        """Simulate concurrent generation scenarios."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Create multiple small schemas
        for i in range(5):
            schema_content = f"""
system:
  name: "concurrent-test-{i}"
  version: "1.0.0"
  seed: {i * 100}

entities:
  items_{i}:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      value:
        type: "integer"
        required: true
        constraints:
          min_value: 1
          max_value: 1000
"""
            
            schema_file = schema_dir / f"concurrent-{i}.yaml"
            schema_file.write_text(schema_content.strip())
        
        start_time = time.time()
        
        # Process all schemas
        discovery_engine = SchemaDiscoveryEngine()
        schemas, validation_result = discovery_engine.discover_and_load_schemas(schema_dir)
        
        assert len(schemas) == 5
        assert validation_result.is_valid
        
        # Generate data for all schemas
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        generated_systems = []
        for schema in schemas:
            generated_system = data_generator.generate_system(schema)
            generated_systems.append(generated_system)
        
        total_time = time.time() - start_time
        
        # Verify all systems generated correctly
        assert len(generated_systems) == 5
        
        total_records = sum(
            sum(len(entities) for entities in system.entities.values())
            for system in generated_systems
        )
        
        assert total_records == 5000  # 5 schemas * 1000 records each
        
        # Performance check
        assert total_time < 15.0  # Should handle multiple schemas efficiently
        
        records_per_second = total_records / total_time
        print(f"Generated {total_records} records across 5 schemas in {total_time:.2f} seconds")
        print(f"Rate: {records_per_second:.0f} records/second")
    
    @pytest.mark.slow
    def test_stress_test_very_large_dataset(self, tmp_path: Path):
        """Stress test with very large dataset (marked as slow test)."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Very large schema (only run if explicitly requested)
        stress_schema = """
system:
  name: "stress-test"
  version: "1.0.0"
  seed: 42

entities:
  records:
    count: 100000
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
      data:
        type: "text.sentence"
        required: true
"""
        
        schema_file = schema_dir / "stress-test.yaml"
        schema_file.write_text(stress_schema.strip())
        
        memory_before = self.get_memory_usage()
        start_time = time.time()
        
        # Generate data
        discovery_engine = SchemaDiscoveryEngine()
        schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)
        
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        generated_system = data_generator.generate_system(schemas[0])
        
        generation_time = time.time() - start_time
        memory_after = self.get_memory_usage()
        memory_used = memory_after - memory_before
        
        # Verify data
        assert len(generated_system.entities["records"]) == 100000
        
        # Performance assertions (more lenient for stress test)
        assert generation_time < 120.0  # 2 minutes max
        assert memory_used < 1000  # Less than 1GB
        
        print(f"Stress test: Generated 100,000 records in {generation_time:.2f} seconds")
        if HAS_PSUTIL:
            print(f"Memory usage: {memory_used:.2f} MB")
        else:
            print("Memory usage: Not available (psutil not installed)")
        print(f"Rate: {100000 / generation_time:.0f} records/second")
    
    def test_output_format_performance_comparison(self, tmp_path: Path):
        """Compare performance across different output formats."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Schema for format comparison
        format_test_schema = """
system:
  name: "format-performance"
  version: "1.0.0"
  seed: 42

entities:
  records:
    count: 5000
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
      data:
        type: "text.sentence"
        required: true
      value:
        type: "decimal"
        required: true
        constraints:
          min_value: 1.0
          max_value: 1000.0
"""
        
        schema_file = schema_dir / "format-performance.yaml"
        schema_file.write_text(format_test_schema.strip())
        
        # Generate data once
        discovery_engine = SchemaDiscoveryEngine()
        schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)
        
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)
        
        generated_system = data_generator.generate_system(schemas[0])
        
        # Test each output format
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.json_writer import JSONWriter
        from jafgen.output.parquet_writer import ParquetWriter
        from jafgen.output.duckdb_writer import DuckDBWriter
        
        writers = {
            "csv": CSVWriter(),
            "json": JSONWriter(),
            "parquet": ParquetWriter(),
            "duckdb": DuckDBWriter()
        }
        
        performance_results = {}
        
        for format_name, writer in writers.items():
            output_dir = tmp_path / f"output_{format_name}"
            output_dir.mkdir()
            
            start_time = time.time()
            writer.write(generated_system.entities, output_dir)
            write_time = time.time() - start_time
            
            performance_results[format_name] = write_time
            
            # Verify file was created
            if format_name == "duckdb":
                output_file = output_dir / "generated_data.duckdb"
            else:
                output_file = output_dir / f"records.{format_name}"
            
            assert output_file.exists()
            
            print(f"{format_name.upper()} write time: {write_time:.3f} seconds")
        
        # All formats should complete within reasonable time
        for format_name, write_time in performance_results.items():
            assert write_time < 10.0, f"{format_name} took too long: {write_time:.3f}s"
        
        # CSV should generally be fastest for simple data
        assert performance_results["csv"] < 5.0
    
    def test_schema_complexity_performance(self, tmp_path: Path):
        """Test performance with varying schema complexity."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        # Simple schema
        simple_schema = """
system:
  name: "simple-perf"
  version: "1.0.0"
  seed: 42

entities:
  simple:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
"""
        
        # Complex schema with many attributes and constraints
        complex_schema = """
system:
  name: "complex-perf"
  version: "1.0.0"
  seed: 42

entities:
  complex:
    count: 1000
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
        unique: true
        required: true
      address:
        type: "address.address"
        required: true
      birth_date:
        type: "datetime.date"
        required: true
        constraints:
          start_date: "1950-01-01"
          end_date: "2005-12-31"
      salary:
        type: "decimal"
        required: true
        constraints:
          min_value: 30000.0
          max_value: 200000.0
      department:
        type: "text.word"
        required: true
      hire_date:
        type: "datetime.datetime"
        required: true
      is_active:
        type: "development.boolean"
        required: true
"""
        
        schemas_to_test = [
            ("simple", simple_schema),
            ("complex", complex_schema)
        ]
        
        performance_results = {}
        
        for schema_name, schema_content in schemas_to_test:
            schema_file = schema_dir / f"{schema_name}.yaml"
            schema_file.write_text(schema_content.strip())
            
            start_time = time.time()
            
            discovery_engine = SchemaDiscoveryEngine()
            schemas, _ = discovery_engine.discover_and_load_schemas(schema_dir)
            
            # Find the current schema
            current_schema = next(s for s in schemas if s.name.startswith(schema_name))
            
            mimesis_engine = MimesisEngine(seed=42)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)
            
            generated_system = data_generator.generate_system(current_schema)
            
            generation_time = time.time() - start_time
            performance_results[schema_name] = generation_time
            
            # Verify correct number of records
            entity_name = list(generated_system.entities.keys())[0]
            assert len(generated_system.entities[entity_name]) == 1000
            
            print(f"{schema_name.capitalize()} schema generation: {generation_time:.3f} seconds")
            
            # Clean up for next iteration
            schema_file.unlink()
        
        # Both should complete within reasonable time
        assert performance_results["simple"] < 5.0
        assert performance_results["complex"] < 15.0
        
        # Complex schema should take longer but not excessively so
        complexity_ratio = performance_results["complex"] / performance_results["simple"]
        assert complexity_ratio < 10.0  # Complex shouldn't be more than 10x slower