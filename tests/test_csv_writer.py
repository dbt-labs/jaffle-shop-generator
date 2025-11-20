"""Tests for CSV output writer."""

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from jafgen.output.csv_writer import CSVWriter


class TestCSVWriter:
    """Test cases for CSVWriter."""

    def test_write_simple_data(self, tmp_path: Path):
        """Test writing simple data to CSV."""
        writer = CSVWriter()

        data = {
            "customers": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ]
        }

        writer.write(data, tmp_path)

        # Verify file was created
        csv_file = tmp_path / "customers.csv"
        assert csv_file.exists()

        # Verify content
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["id"] == "1"
        assert rows[0]["name"] == "John Doe"
        assert rows[0]["email"] == "john@example.com"
        assert rows[1]["id"] == "2"
        assert rows[1]["name"] == "Jane Smith"
        assert rows[1]["email"] == "jane@example.com"

    def test_write_multiple_entities(self, tmp_path: Path):
        """Test writing multiple entities to separate CSV files."""
        writer = CSVWriter()

        data = {
            "customers": [{"id": 1, "name": "John Doe"}],
            "orders": [{"id": 101, "customer_id": 1, "total": 25.50}],
        }

        writer.write(data, tmp_path)

        # Verify both files were created
        customers_file = tmp_path / "customers.csv"
        orders_file = tmp_path / "orders.csv"

        assert customers_file.exists()
        assert orders_file.exists()

        # Verify customers content
        with open(customers_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            customers = list(reader)

        assert len(customers) == 1
        assert customers[0]["id"] == "1"
        assert customers[0]["name"] == "John Doe"

        # Verify orders content
        with open(orders_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            orders = list(reader)

        assert len(orders) == 1
        assert orders[0]["id"] == "101"
        assert orders[0]["customer_id"] == "1"
        assert orders[0]["total"] == "25.5"

    def test_write_with_none_values(self, tmp_path: Path):
        """Test writing data with None values."""
        writer = CSVWriter()

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

        csv_file = tmp_path / "users.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["middle_name"] == ""  # None converted to empty string
        assert rows[1]["email"] == ""  # None converted to empty string

    def test_write_with_complex_types(self, tmp_path: Path):
        """Test writing data with complex types (lists, dicts)."""
        writer = CSVWriter()

        data = {
            "products": [
                {
                    "id": 1,
                    "name": "Widget",
                    "tags": ["electronics", "gadget"],
                    "metadata": {"color": "blue", "size": "large"},
                }
            ]
        }

        writer.write(data, tmp_path)

        csv_file = tmp_path / "products.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["id"] == "1"
        assert rows[0]["name"] == "Widget"
        # Complex types should be converted to string representation
        assert "electronics" in rows[0]["tags"]
        assert "gadget" in rows[0]["tags"]
        assert "color" in rows[0]["metadata"]
        assert "blue" in rows[0]["metadata"]

    def test_write_empty_entity_list(self, tmp_path: Path):
        """Test writing data with empty entity lists."""
        writer = CSVWriter()

        data = {"customers": [{"id": 1, "name": "John"}], "orders": []}  # Empty list

        writer.write(data, tmp_path)

        # Only customers file should be created
        customers_file = tmp_path / "customers.csv"
        orders_file = tmp_path / "orders.csv"

        assert customers_file.exists()
        assert not orders_file.exists()

    def test_write_creates_directory(self, tmp_path: Path):
        """Test that writer creates output directory if it doesn't exist."""
        writer = CSVWriter()

        # Use a nested path that doesn't exist
        output_path = tmp_path / "nested" / "output"

        data = {"test": [{"id": 1, "value": "test"}]}

        writer.write(data, output_path)

        # Directory should be created
        assert output_path.exists()
        assert output_path.is_dir()

        # File should be created in the directory
        test_file = output_path / "test.csv"
        assert test_file.exists()

    def test_custom_encoding(self, tmp_path: Path):
        """Test CSV writer with custom encoding."""
        writer = CSVWriter(encoding="latin1")

        data = {"users": [{"id": 1, "name": "José", "city": "São Paulo"}]}

        writer.write(data, tmp_path)

        csv_file = tmp_path / "users.csv"

        # Read with the same encoding
        with open(csv_file, "r", encoding="latin1") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["name"] == "José"
        assert rows[0]["city"] == "São Paulo"

    def test_write_handles_file_permission_error(self, tmp_path: Path):
        """Test that writer handles file permission errors gracefully."""
        writer = CSVWriter()

        data = {"test": [{"id": 1, "value": "test"}]}

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                writer.write(data, tmp_path)

    def test_write_various_data_types(self, tmp_path: Path):
        """Test writing various Python data types."""
        writer = CSVWriter()

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

        csv_file = tmp_path / "mixed_types.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["string_val"] == "text"
        assert row["int_val"] == "42"
        assert row["float_val"] == "3.14"
        assert row["bool_val"] == "True"
        assert row["none_val"] == ""
