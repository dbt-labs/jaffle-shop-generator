"""Tests for Parquet output writer."""

from datetime import date, datetime
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from jafgen.output.parquet_writer import ParquetWriter


class TestParquetWriter:
    """Test cases for ParquetWriter."""

    def test_write_simple_data(self, tmp_path: Path):
        """Test writing simple data to Parquet."""
        writer = ParquetWriter()

        data = {
            "customers": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ]
        }

        writer.write(data, tmp_path)

        # Verify file was created
        parquet_file = tmp_path / "customers.parquet"
        assert parquet_file.exists()

        # Verify content by reading back
        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 2
        assert df.iloc[0]["id"] == 1
        assert df.iloc[0]["name"] == "John Doe"
        assert df.iloc[0]["email"] == "john@example.com"
        assert df.iloc[1]["id"] == 2
        assert df.iloc[1]["name"] == "Jane Smith"
        assert df.iloc[1]["email"] == "jane@example.com"

    def test_write_multiple_entities(self, tmp_path: Path):
        """Test writing multiple entities to separate Parquet files."""
        writer = ParquetWriter()

        data = {
            "customers": [{"id": 1, "name": "John Doe"}],
            "orders": [{"id": 101, "customer_id": 1, "total": 25.50}],
        }

        writer.write(data, tmp_path)

        # Verify both files were created
        customers_file = tmp_path / "customers.parquet"
        orders_file = tmp_path / "orders.parquet"

        assert customers_file.exists()
        assert orders_file.exists()

        # Verify customers content
        customers_table = pq.read_table(customers_file)
        customers_df = customers_table.to_pandas()

        assert len(customers_df) == 1
        assert customers_df.iloc[0]["id"] == 1
        assert customers_df.iloc[0]["name"] == "John Doe"

        # Verify orders content
        orders_table = pq.read_table(orders_file)
        orders_df = orders_table.to_pandas()

        assert len(orders_df) == 1
        assert orders_df.iloc[0]["id"] == 101
        assert orders_df.iloc[0]["customer_id"] == 1
        assert orders_df.iloc[0]["total"] == 25.5

    def test_write_with_datetime_objects(self, tmp_path: Path):
        """Test writing data with datetime objects."""
        writer = ParquetWriter()

        test_datetime = datetime(2024, 1, 15, 10, 30, 45)
        test_date = date(2024, 1, 15)

        data = {
            "events": [
                {
                    "id": 1,
                    "created_at": test_datetime,
                    "event_date": test_date,
                    "name": "Test Event",
                }
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "events.parquet"
        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 1
        event = df.iloc[0]
        assert event["id"] == 1
        # Datetime should be converted to ISO string for Parquet compatibility
        assert (
            str(event["created_at"]) == "2024-01-15T10:30:45"
            or event["created_at"] == test_datetime
        )
        assert (
            str(event["event_date"]) == "2024-01-15" or event["event_date"] == test_date
        )
        assert event["name"] == "Test Event"

    def test_write_with_complex_types(self, tmp_path: Path):
        """Test writing data with complex types (lists, dicts)."""
        writer = ParquetWriter()

        data = {
            "products": [
                {
                    "id": 1,
                    "name": "Widget",
                    "metadata": {"color": "blue", "size": "large"},
                    "tags": ["electronics", "gadget"],
                }
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "products.parquet"
        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 1
        product = df.iloc[0]
        assert product["id"] == 1
        assert product["name"] == "Widget"
        # Complex types should be converted to JSON strings
        metadata_str = str(product["metadata"])
        tags_str = str(product["tags"])
        assert "color" in metadata_str
        assert "blue" in metadata_str
        assert "electronics" in tags_str
        assert "gadget" in tags_str

    def test_write_empty_entity_list(self, tmp_path: Path):
        """Test writing data with empty entity lists."""
        writer = ParquetWriter()

        data = {"customers": [{"id": 1, "name": "John"}], "orders": []}  # Empty list

        writer.write(data, tmp_path)

        # Only customers file should be created
        customers_file = tmp_path / "customers.parquet"
        orders_file = tmp_path / "orders.parquet"

        assert customers_file.exists()
        assert not orders_file.exists()

    def test_write_creates_directory(self, tmp_path: Path):
        """Test that writer creates output directory if it doesn't exist."""
        writer = ParquetWriter()

        # Use a nested path that doesn't exist
        output_path = tmp_path / "nested" / "output"

        data = {"test": [{"id": 1, "value": "test"}]}

        writer.write(data, output_path)

        # Directory should be created
        assert output_path.exists()
        assert output_path.is_dir()

        # File should be created in the directory
        test_file = output_path / "test.parquet"
        assert test_file.exists()

    def test_custom_compression(self, tmp_path: Path):
        """Test Parquet writer with custom compression."""
        writer = ParquetWriter(compression="gzip")

        data = {
            "users": [
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"},
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "users.parquet"
        assert parquet_file.exists()

        # Verify we can read the compressed file
        table = pq.read_table(parquet_file)
        df = table.to_pandas()
        assert len(df) == 2

    def test_write_with_none_values(self, tmp_path: Path):
        """Test writing data with None values."""
        writer = ParquetWriter()

        data = {
            "users": [
                {
                    "id": 1,
                    "name": "John",
                    "middle_name": None,
                    "email": "john@example.com",
                },
                {"id": 2, "name": "Jane", "middle_name": "Marie", "email": None},
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "users.parquet"
        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 2
        # None values should be preserved as NaN/None in Parquet
        assert (
            df.iloc[0]["middle_name"] is None or str(df.iloc[0]["middle_name"]) == "nan"
        )
        assert df.iloc[1]["email"] is None or str(df.iloc[1]["email"]) == "nan"

    def test_write_various_data_types(self, tmp_path: Path):
        """Test writing various Python data types."""
        writer = ParquetWriter()

        data = {
            "mixed_types": [
                {
                    "string_val": "text",
                    "int_val": 42,
                    "float_val": 3.14,
                    "bool_val": True,
                    "none_val": None,
                }
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "mixed_types.parquet"
        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 1
        row = df.iloc[0]
        assert row["string_val"] == "text"
        assert row["int_val"] == 42
        assert row["float_val"] == 3.14
        assert bool(row["bool_val"]) is True
    
    def test_write_with_mixed_column_types_triggers_flattening(self, tmp_path: Path):
        """Test that data with mixed types in a column triggers the flattening logic."""
        writer = ParquetWriter()

        # This data will cause a pyarrow.ArrowTypeError because of mixed types (int and str) in the 'value' column.
        data = {
            "mixed_data": [
                {"id": 1, "value": 100},
                {"id": 2, "value": "a string"},
            ]
        }

        writer.write(data, tmp_path)

        parquet_file = tmp_path / "mixed_data.parquet"
        assert parquet_file.exists()

        table = pq.read_table(parquet_file)
        df = table.to_pandas()

        assert len(df) == 2
        # After flattening, the integer should be converted to a string.
        assert df.iloc[0]["value"] == "100"
        assert df.iloc[1]["value"] == "a string"
