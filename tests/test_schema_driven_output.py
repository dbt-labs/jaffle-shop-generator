"""Tests for schema-driven output format selection and configuration."""

import json
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.parquet_writer import ParquetWriter
from jafgen.output.duckdb_writer import DuckDBWriter
from jafgen.output.output_manager import OutputManager
from jafgen.schema.models import (
    AttributeConfig, EntityConfig, OutputConfig, SystemSchema,
    FormatConfig, EntityOutputConfig
)


class TestSchemaDrivenOutput:
    """Test schema-driven output format selection and configuration."""
    
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
    
    @pytest.fixture
    def basic_schema(self) -> SystemSchema:
        """Create a basic schema for testing."""
        return SystemSchema(
            name="test-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],
                path="."
            ),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True),
                        "email": AttributeConfig(type="person.email", unique=True, required=True)
                    }
                )
            }
        )
    
    def test_multiple_output_formats(
        self, 
        basic_schema: SystemSchema, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test generation with multiple output formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(basic_schema)
            metadata = output_manager.write_system_data(generated_system, output_path)
            
            # Verify both formats were written
            assert "csv" in metadata.output_formats
            assert "json" in metadata.output_formats
            
            # Verify files exist
            csv_file = output_path / "users.csv"
            json_file = output_path / "users.json"
            
            assert csv_file.exists()
            assert json_file.exists()
            
            # Verify file contents are valid
            csv_content = csv_file.read_text()
            assert "id,name,email" in csv_content  # CSV header
            
            json_content = json.loads(json_file.read_text())
            assert isinstance(json_content, list)
            assert len(json_content) == 5
    
    def test_custom_output_path(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test custom output path configuration."""
        schema = SystemSchema(
            name="custom-path-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv"],
                path="custom/output/directory"
            ),
            entities={
                "products": EntityConfig(
                    name="products",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify file was written to custom path
            custom_file = output_path / "custom" / "output" / "directory" / "products.csv"
            assert custom_file.exists()
    
    def test_per_entity_output_configuration(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test per-entity output configuration."""
        schema = SystemSchema(
            name="per-entity-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv"],  # Default format
                path=".",
                per_entity={
                    "users": EntityOutputConfig(
                        format=["json", "parquet"],  # Override format for users
                        path="users_data"  # Custom path for users
                    ),
                    "orders": EntityOutputConfig(
                        format=["csv", "duckdb"]  # Different formats for orders
                    )
                }
            ),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "amount": AttributeConfig(type="float", constraints={"min_value": 10.0, "max_value": 100.0}, required=True)
                    }
                ),
                "products": EntityConfig(  # Uses default configuration
                    name="products",
                    count=2,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify users entity files (custom path and formats)
            users_json = output_path / "users_data" / "users.json"
            users_parquet = output_path / "users_data" / "users.parquet"
            assert users_json.exists()
            assert users_parquet.exists()
            
            # Verify orders entity files (default path, custom formats)
            orders_csv = output_path / "orders.csv"
            orders_duckdb = output_path / "generated_data.duckdb"  # DuckDB creates a database file
            assert orders_csv.exists()
            assert orders_duckdb.exists()
            
            # Verify products entity files (default configuration)
            products_csv = output_path / "products.csv"
            assert products_csv.exists()
    
    def test_format_specific_options(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test format-specific options configuration."""
        schema = SystemSchema(
            name="format-options-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],
                path=".",
                formats={
                    "csv": FormatConfig(
                        type="csv",
                        options={"encoding": "utf-8"}
                    ),
                    "json": FormatConfig(
                        type="json",
                        options={"indent": 4, "ensure_ascii": False}
                    )
                }
            ),
            entities={
                "customers": EntityConfig(
                    name="customers",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify files exist
            csv_file = output_path / "customers.csv"
            json_file = output_path / "customers.json"
            
            assert csv_file.exists()
            assert json_file.exists()
            
            # Verify JSON formatting (4-space indentation)
            json_content = json_file.read_text()
            assert "    " in json_content  # Should have 4-space indentation
    
    def test_custom_filename_patterns(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test custom filename patterns."""
        schema = SystemSchema(
            name="filename-pattern-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],
                path=".",
                formats={
                    "csv": FormatConfig(
                        type="csv",
                        filename_pattern="{entity_name}_data.{ext}"
                    ),
                    "json": FormatConfig(
                        type="json",
                        filename_pattern="export_{entity_name}.{ext}"
                    )
                }
            ),
            entities={
                "items": EntityConfig(
                    name="items",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify custom filenames
            csv_file = output_path / "items_data.csv"
            json_file = output_path / "export_items.json"
            
            assert csv_file.exists()
            assert json_file.exists()
            
            # Verify default filenames don't exist
            default_csv = output_path / "items.csv"
            default_json = output_path / "items.json"
            
            assert not default_csv.exists()
            assert not default_json.exists()
    
    def test_entity_specific_format_options(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test entity-specific format options."""
        schema = SystemSchema(
            name="entity-format-options-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["json"],
                path=".",
                formats={
                    "json": FormatConfig(
                        type="json",
                        options={"indent": 2}  # Default 2-space indentation
                    )
                },
                per_entity={
                    "special_items": EntityOutputConfig(
                        formats={
                            "json": FormatConfig(
                                type="json",
                                options={"indent": 8},  # Override with 8-space indentation
                                filename_pattern="special_{entity_name}.{ext}"
                            )
                        }
                    )
                }
            ),
            entities={
                "regular_items": EntityConfig(
                    name="regular_items",
                    count=2,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                ),
                "special_items": EntityConfig(
                    name="special_items",
                    count=2,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify files exist
            regular_file = output_path / "regular_items.json"
            special_file = output_path / "special_special_items.json"
            
            assert regular_file.exists()
            assert special_file.exists()
            
            # Verify different indentation
            regular_content = regular_file.read_text()
            special_content = special_file.read_text()
            
            # Regular should have 2-space indentation
            assert "  " in regular_content and "        " not in regular_content
            
            # Special should have 8-space indentation
            assert "        " in special_content
    
    def test_mixed_configuration_inheritance(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test complex configuration with inheritance and overrides."""
        schema = SystemSchema(
            name="mixed-config-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],  # Default formats
                path="default_output",  # Default path
                formats={
                    "csv": FormatConfig(
                        type="csv",
                        options={"encoding": "utf-8"}
                    )
                },
                per_entity={
                    "users": EntityOutputConfig(
                        format=["json", "parquet"],  # Override formats
                        path="users_special",  # Override path
                        formats={
                            "json": FormatConfig(
                                type="json",
                                options={"indent": 6},
                                filename_pattern="user_export_{entity_name}.{ext}"
                            )
                        }
                    ),
                    "orders": EntityOutputConfig(
                        # Inherit default formats but override path
                        path="orders_data"
                    )
                }
            ),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=2,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "amount": AttributeConfig(type="float", constraints={"min_value": 10.0, "max_value": 100.0}, required=True)
                    }
                ),
                "products": EntityConfig(
                    name="products",
                    count=2,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            output_manager.write_system_data(generated_system, output_path)
            
            # Verify users: custom formats, path, and filename
            users_json = output_path / "default_output" / "users_special" / "user_export_users.json"
            users_parquet = output_path / "default_output" / "users_special" / "users.parquet"
            assert users_json.exists()
            assert users_parquet.exists()
            
            # Verify orders: default formats, custom path
            orders_csv = output_path / "default_output" / "orders_data" / "orders.csv"
            orders_json = output_path / "default_output" / "orders_data" / "orders.json"
            assert orders_csv.exists()
            assert orders_json.exists()
            
            # Verify products: all defaults
            products_csv = output_path / "default_output" / "products.csv"
            products_json = output_path / "default_output" / "products.json"
            assert products_csv.exists()
            assert products_json.exists()
    
    def test_output_format_validation(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test validation of unsupported output formats."""
        schema = SystemSchema(
            name="invalid-format-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "unsupported_format"],
                path="."
            ),
            entities={
                "test_entity": EntityConfig(
                    name="test_entity",
                    count=1,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data
            generated_system = data_generator.generate_system(schema)
            
            # Should raise error for unsupported format
            with pytest.raises(Exception) as exc_info:
                output_manager.write_system_data(generated_system, output_path)
            
            assert "unsupported_format" in str(exc_info.value).lower()
    
    def test_idempotency_with_schema_configuration(
        self, 
        data_generator: DataGenerator,
        output_manager: OutputManager
    ):
        """Test idempotency works with schema-driven configuration."""
        schema = SystemSchema(
            name="idempotency-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(
                format=["csv", "json"],
                path=".",
                per_entity={
                    "items": EntityOutputConfig(
                        path="custom_items",
                        formats={
                            "csv": FormatConfig(
                                type="csv",
                                filename_pattern="custom_{entity_name}.{ext}"
                            )
                        }
                    )
                }
            ),
            entities={
                "items": EntityConfig(
                    name="items",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True, required=True),
                        "name": AttributeConfig(type="text.word", required=True)
                    }
                )
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            
            # Generate data first time
            generated_system1 = data_generator.generate_system(schema)
            metadata1 = output_manager.write_system_data(generated_system1, output_path)
            
            # Read file contents
            csv_file = output_path / "custom_items" / "custom_items.csv"
            json_file = output_path / "custom_items" / "items.json"  # JSON also goes to custom path
            
            assert csv_file.exists()
            assert json_file.exists()
            
            csv_content1 = csv_file.read_text()
            json_content1 = json_file.read_text()
            
            # Generate data second time
            generated_system2 = data_generator.generate_system(schema)
            metadata2 = output_manager.write_system_data(generated_system2, output_path)
            
            # Verify idempotency
            assert metadata1.is_identical_generation(metadata2)
            
            csv_content2 = csv_file.read_text()
            json_content2 = json_file.read_text()
            
            assert csv_content1 == csv_content2
            assert json_content1 == json_content2