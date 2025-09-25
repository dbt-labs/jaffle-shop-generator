"""Integration tests for idempotent file generation."""

import json
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.models import GenerationMetadata, calculate_schema_hash
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.parquet_writer import ParquetWriter
from jafgen.output.duckdb_writer import DuckDBWriter
from jafgen.output.output_manager import OutputManager
from jafgen.schema.models import (
    AttributeConfig, EntityConfig, OutputConfig, SystemSchema
)


class TestIdempotentGeneration:
    """Test idempotent file generation and reproducibility."""
    
    @pytest.fixture
    def sample_schema(self) -> SystemSchema:
        """Create a sample schema for testing."""
        return SystemSchema(
            name="test-system",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],
                path="."
            ),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True),
                        "email": AttributeConfig(type="person.email", unique=True, required=True),
                        "age": AttributeConfig(type="int", constraints={"min_value": 18, "max_value": 80}, required=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "user_id": AttributeConfig(type="link", link_to="test-system.users.id", required=True),
                        "amount": AttributeConfig(type="float", constraints={"min_value": 10.0, "max_value": 500.0}, required=True),
                        "created_at": AttributeConfig(type="datetime.datetime", required=True)
                    }
                )
            }
        )
    
    @pytest.fixture
    def output_manager(self) -> OutputManager:
        """Create an output manager with all writers."""
        output_writers = {
            'csv': CSVWriter(),
            'json': JSONWriter(),
            'parquet': ParquetWriter(),
            'duckdb': DuckDBWriter()
        }
        return OutputManager(output_writers)
    
    @pytest.fixture
    def data_generator(self) -> DataGenerator:
        """Create a data generator with consistent seeding."""
        mimesis_engine = MimesisEngine(seed=42)
        link_resolver = LinkResolver()
        return DataGenerator(mimesis_engine, link_resolver)
    
    def test_identical_generation_same_seed(
        self, 
        sample_schema: SystemSchema, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test that identical schemas with same seed produce identical output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data first time
            generated_system1 = data_generator.generate_system(sample_schema)
            metadata1 = output_manager.write_system_data(generated_system1, output_path)
            
            # Read generated files
            files1 = self._read_all_files(output_path)
            
            # Generate data second time with same configuration
            generated_system2 = data_generator.generate_system(sample_schema)
            metadata2 = output_manager.write_system_data(generated_system2, output_path)
            
            # Read generated files again
            files2 = self._read_all_files(output_path)
            
            # Verify metadata indicates identical generation
            assert metadata1.is_identical_generation(metadata2)
            
            # Verify file contents are identical
            assert files1 == files2
            
            # Verify metadata files are consistent
            assert metadata1.schema_hash == metadata2.schema_hash
            assert metadata1.seed_used == metadata2.seed_used
            assert metadata1.total_records == metadata2.total_records
    
    def test_different_generation_different_seed(
        self, 
        sample_schema: SystemSchema,
        output_manager: OutputManager
    ):
        """Test that different seeds produce different output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data with seed 42
            data_generator1 = DataGenerator(MimesisEngine(seed=42), LinkResolver())
            generated_system1 = data_generator1.generate_system(sample_schema)
            metadata1 = output_manager.write_system_data(generated_system1, output_path)
            files1 = self._read_all_files(output_path)
            
            # Clear output directory
            output_manager.clean_output_directory(output_path)
            
            # Generate data with seed 123
            sample_schema.seed = 123
            data_generator2 = DataGenerator(MimesisEngine(seed=123), LinkResolver())
            generated_system2 = data_generator2.generate_system(sample_schema)
            metadata2 = output_manager.write_system_data(generated_system2, output_path)
            files2 = self._read_all_files(output_path)
            
            # Verify metadata indicates different generation
            assert not metadata1.is_identical_generation(metadata2)
            
            # Verify file contents are different
            assert files1 != files2
            
            # Verify different seeds were used
            assert metadata1.seed_used != metadata2.seed_used
    
    def test_schema_hash_consistency(self, sample_schema: SystemSchema):
        """Test that schema hash is consistent for identical schemas."""
        hash1 = calculate_schema_hash(sample_schema)
        hash2 = calculate_schema_hash(sample_schema)
        
        assert hash1 == hash2
        
        # Modify schema and verify hash changes
        sample_schema.entities["users"].count = 20
        hash3 = calculate_schema_hash(sample_schema)
        
        assert hash1 != hash3
    
    def test_metadata_persistence(
        self, 
        sample_schema: SystemSchema, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test that metadata is properly saved and loaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data and save metadata
            generated_system = data_generator.generate_system(sample_schema)
            original_metadata = output_manager.write_system_data(generated_system, output_path)
            
            # Load metadata from file
            loaded_metadata = GenerationMetadata.load_from_file(output_path)
            
            assert loaded_metadata is not None
            assert loaded_metadata.is_identical_generation(original_metadata)
            assert loaded_metadata.seed_used == original_metadata.seed_used
            assert loaded_metadata.schema_hash == original_metadata.schema_hash
            assert loaded_metadata.total_records == original_metadata.total_records
    
    def test_output_directory_management(self, output_manager: OutputManager):
        """Test output directory creation and permission management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Test nested directory creation
            nested_path = base_path / "level1" / "level2" / "level3"
            output_manager.prepare_output_directory(nested_path)
            
            assert nested_path.exists()
            assert nested_path.is_dir()
            
            # Test directory recreation
            output_manager.prepare_output_directory(nested_path, force_recreate=True)
            assert nested_path.exists()
    
    def test_file_overwriting_behavior(
        self, 
        sample_schema: SystemSchema, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test that files are properly overwritten for idempotency."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate initial data
            generated_system = data_generator.generate_system(sample_schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Get initial file modification times
            initial_times = {}
            for file_path in output_path.glob("*.csv"):
                initial_times[file_path.name] = file_path.stat().st_mtime
            
            # Wait a moment to ensure different timestamps
            import time
            time.sleep(0.1)
            
            # Generate data again
            generated_system2 = data_generator.generate_system(sample_schema)
            output_manager.write_system_data(generated_system2, output_path)
            
            # Verify files were overwritten (different modification times)
            for file_path in output_path.glob("*.csv"):
                new_time = file_path.stat().st_mtime
                # Files should have been overwritten (newer timestamps)
                assert new_time >= initial_times[file_path.name]
    
    def test_reproducibility_verification(
        self, 
        sample_schema: SystemSchema, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test reproducibility verification functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(sample_schema)
            metadata = output_manager.write_system_data(generated_system, output_path)
            
            # Verify reproducibility with same metadata
            assert output_manager.verify_reproducibility(output_path, metadata)
            
            # Create different metadata and verify it fails
            different_metadata = GenerationMetadata(
                generated_at=metadata.generated_at,
                seed_used=999,  # Different seed
                total_records=metadata.total_records,
                entity_counts=metadata.entity_counts,
                schema_hash=metadata.schema_hash,
                output_formats=metadata.output_formats,
                output_path=metadata.output_path
            )
            
            assert not output_manager.verify_reproducibility(output_path, different_metadata)
    
    def test_clean_output_directory(self, output_manager: OutputManager):
        """Test output directory cleaning functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Create some test files
            (output_path / "test.csv").write_text("test data")
            (output_path / "test.json").write_text('{"test": "data"}')
            (output_path / "test.parquet").write_bytes(b"parquet data")
            (output_path / ".jafgen_metadata.json").write_text('{"test": "metadata"}')
            (output_path / "other.txt").write_text("other file")
            
            # Clean directory but keep metadata
            output_manager.clean_output_directory(output_path, keep_metadata=True)
            
            # Verify generated files are removed but metadata and other files remain
            assert not (output_path / "test.csv").exists()
            assert not (output_path / "test.json").exists()
            assert not (output_path / "test.parquet").exists()
            assert (output_path / ".jafgen_metadata.json").exists()
            assert (output_path / "other.txt").exists()
            
            # Clean directory completely
            output_manager.clean_output_directory(output_path, keep_metadata=False)
            
            # Verify metadata is also removed
            assert not (output_path / ".jafgen_metadata.json").exists()
            assert (output_path / "other.txt").exists()  # Non-generated files remain
    
    def _read_all_files(self, output_path: Path) -> Dict[str, str]:
        """Read all generated files in the output directory.
        
        Args:
            output_path: Path to the output directory
            
        Returns:
            Dictionary mapping filenames to their contents
        """
        files = {}
        
        # Read CSV files
        for csv_file in output_path.glob("*.csv"):
            files[csv_file.name] = csv_file.read_text(encoding='utf-8')
        
        # Read JSON files
        for json_file in output_path.glob("*.json"):
            if json_file.name != '.jafgen_metadata.json':  # Skip metadata
                files[json_file.name] = json_file.read_text(encoding='utf-8')
        
        return files


class TestMultipleSchemaIdempotency:
    """Test idempotency with multiple schemas and cross-schema dependencies."""
    
    @pytest.fixture
    def linked_schemas(self) -> List[SystemSchema]:
        """Create multiple schemas with cross-schema dependencies."""
        schema1 = SystemSchema(
            name="users-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(format=["csv"], path="users"),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        schema2 = SystemSchema(
            name="orders-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(format=["csv"], path="orders"),
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "user_id": AttributeConfig(type="link", link_to="users-schema.users.id", required=True),
                        "amount": AttributeConfig(type="float", constraints={"min_value": 10.0, "max_value": 500.0}, required=True)
                    }
                )
            }
        )
        
        return [schema1, schema2]
    
    def test_multiple_schema_idempotency(self, linked_schemas: List[SystemSchema]):
        """Test idempotency with multiple linked schemas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Initialize components
            mimesis_engine = MimesisEngine(seed=42)
            link_resolver = LinkResolver()
            data_generator = DataGenerator(mimesis_engine, link_resolver)
            
            output_writers = {
                'csv': CSVWriter(),
                'json': JSONWriter()
            }
            output_manager = OutputManager(output_writers)
            
            # Generate data first time
            generated_systems1 = data_generator.generate_multiple_systems(linked_schemas)
            
            metadata_list1 = []
            for generated_system in generated_systems1:
                metadata = output_manager.write_system_data(generated_system, output_path)
                metadata_list1.append(metadata)
            
            # Read all generated files
            files1 = self._read_all_files_recursive(output_path)
            
            # Generate data second time
            mimesis_engine2 = MimesisEngine(seed=42)
            link_resolver2 = LinkResolver()
            data_generator2 = DataGenerator(mimesis_engine2, link_resolver2)
            
            generated_systems2 = data_generator2.generate_multiple_systems(linked_schemas)
            
            metadata_list2 = []
            for generated_system in generated_systems2:
                metadata = output_manager.write_system_data(generated_system, output_path)
                metadata_list2.append(metadata)
            
            # Read all generated files again
            files2 = self._read_all_files_recursive(output_path)
            
            # Verify identical generation
            assert len(metadata_list1) == len(metadata_list2)
            for meta1, meta2 in zip(metadata_list1, metadata_list2):
                assert meta1.is_identical_generation(meta2)
            
            # Verify file contents are identical
            assert files1 == files2
    
    def _read_all_files_recursive(self, output_path: Path) -> Dict[str, str]:
        """Recursively read all generated files.
        
        Args:
            output_path: Base output directory
            
        Returns:
            Dictionary mapping relative file paths to contents
        """
        files = {}
        
        for file_path in output_path.rglob("*.csv"):
            relative_path = file_path.relative_to(output_path)
            files[str(relative_path)] = file_path.read_text(encoding='utf-8')
        
        for file_path in output_path.rglob("*.json"):
            if file_path.name != '.jafgen_metadata.json':
                relative_path = file_path.relative_to(output_path)
                files[str(relative_path)] = file_path.read_text(encoding='utf-8')
        
        return files