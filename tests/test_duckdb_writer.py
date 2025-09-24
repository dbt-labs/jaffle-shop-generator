"""Tests for DuckDB output writer."""

from datetime import date, datetime
from pathlib import Path

import duckdb
import pytest

from jafgen.output.duckdb_writer import DuckDBWriter


class TestDuckDBWriter:
    """Test cases for DuckDBWriter."""
    
    def test_write_simple_data(self, tmp_path: Path):
        """Test writing simple data to DuckDB."""
        writer = DuckDBWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ]
        }
        
        writer.write(data, tmp_path)
        
        # Verify database file was created
        db_file = tmp_path / "generated_data.duckdb"
        assert db_file.exists()
        
        # Verify content by querying the database
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM customers ORDER BY id").fetchall()
            assert len(result) == 2
            assert result[0] == (1, "John Doe", "john@example.com")
            assert result[1] == (2, "Jane Smith", "jane@example.com")
        finally:
            conn.close()
    
    def test_write_multiple_entities(self, tmp_path: Path):
        """Test writing multiple entities to DuckDB tables."""
        writer = DuckDBWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John Doe"}
            ],
            "orders": [
                {"id": 101, "customer_id": 1, "total": 25.50}
            ]
        }
        
        writer.write(data, tmp_path)
        
        # Verify database file was created
        db_file = tmp_path / "generated_data.duckdb"
        assert db_file.exists()
        
        conn = duckdb.connect(str(db_file))
        try:
            # Verify customers table
            customers = conn.execute("SELECT * FROM customers").fetchall()
            assert len(customers) == 1
            assert customers[0] == (1, "John Doe")
            
            # Verify orders table
            orders = conn.execute("SELECT * FROM orders").fetchall()
            assert len(orders) == 1
            assert orders[0] == (101, 1, 25.5)
        finally:
            conn.close()
    
    def test_write_with_datetime_objects(self, tmp_path: Path):
        """Test writing data with datetime objects."""
        writer = DuckDBWriter()
        
        test_datetime = datetime(2024, 1, 15, 10, 30, 45)
        test_date = date(2024, 1, 15)
        
        data = {
            "events": [
                {
                    "id": 1,
                    "created_at": test_datetime,
                    "event_date": test_date,
                    "name": "Test Event"
                }
            ]
        }
        
        writer.write(data, tmp_path)
        
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM events").fetchall()
            assert len(result) == 1
            event = result[0]
            assert event[0] == 1  # id
            assert event[1] == test_datetime  # created_at
            assert event[2] == test_date  # event_date
            assert event[3] == "Test Event"  # name
        finally:
            conn.close()
    
    def test_write_with_complex_types(self, tmp_path: Path):
        """Test writing data with complex types (lists, dicts)."""
        writer = DuckDBWriter()
        
        data = {
            "products": [
                {
                    "id": 1,
                    "name": "Widget",
                    "metadata": {"color": "blue", "size": "large"},
                    "tags": ["electronics", "gadget"]
                }
            ]
        }
        
        writer.write(data, tmp_path)
        
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM products").fetchall()
            assert len(result) == 1
            product = result[0]
            assert product[0] == 1  # id
            assert product[1] == "Widget"  # name
            # Complex types should be converted to JSON strings
            assert "color" in product[2]  # metadata
            assert "blue" in product[2]
            assert "electronics" in product[3]  # tags
            assert "gadget" in product[3]
        finally:
            conn.close()
    
    def test_write_empty_entity_list(self, tmp_path: Path):
        """Test writing data with empty entity lists."""
        writer = DuckDBWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John"}
            ],
            "orders": []  # Empty list
        }
        
        writer.write(data, tmp_path)
        
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            # Only customers table should exist
            tables = conn.execute("SHOW TABLES").fetchall()
            table_names = [table[0] for table in tables]
            assert "customers" in table_names
            assert "orders" not in table_names
        finally:
            conn.close()
    
    def test_write_creates_directory(self, tmp_path: Path):
        """Test that writer creates output directory if it doesn't exist."""
        writer = DuckDBWriter()
        
        # Use a nested path that doesn't exist
        output_path = tmp_path / "nested" / "output"
        
        data = {
            "test": [{"id": 1, "value": "test"}]
        }
        
        writer.write(data, output_path)
        
        # Directory should be created
        assert output_path.exists()
        assert output_path.is_dir()
        
        # Database file should be created in the directory
        db_file = output_path / "generated_data.duckdb"
        assert db_file.exists()
    
    def test_custom_database_name(self, tmp_path: Path):
        """Test DuckDB writer with custom database name."""
        writer = DuckDBWriter(database_name="custom.duckdb")
        
        data = {
            "users": [
                {"id": 1, "name": "John", "email": "john@example.com"}
            ]
        }
        
        writer.write(data, tmp_path)
        
        # Custom database file should be created
        db_file = tmp_path / "custom.duckdb"
        assert db_file.exists()
        
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM users").fetchall()
            assert len(result) == 1
            assert result[0] == (1, "John", "john@example.com")
        finally:
            conn.close()
    
    def test_write_idempotency(self, tmp_path: Path):
        """Test that multiple writes are idempotent (overwrite existing tables)."""
        writer = DuckDBWriter()
        
        # First write
        data1 = {
            "users": [
                {"id": 1, "name": "John"}
            ]
        }
        writer.write(data1, tmp_path)
        
        # Second write with different data
        data2 = {
            "users": [
                {"id": 2, "name": "Jane"},
                {"id": 3, "name": "Bob"}
            ]
        }
        writer.write(data2, tmp_path)
        
        # Should only have the second write's data
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            assert len(result) == 2
            assert result[0] == (2, "Jane")
            assert result[1] == (3, "Bob")
        finally:
            conn.close()
    
    def test_write_with_none_values(self, tmp_path: Path):
        """Test writing data with None values."""
        writer = DuckDBWriter()
        
        data = {
            "users": [
                {"id": 1, "name": "John", "middle_name": None, "email": "john@example.com"},
                {"id": 2, "name": "Jane", "middle_name": "Marie", "email": None}
            ]
        }
        
        writer.write(data, tmp_path)
        
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            assert len(result) == 2
            # None values should be preserved as NULL in DuckDB
            assert result[0][2] is None  # middle_name
            assert result[1][3] is None  # email
        finally:
            conn.close()
    
    def test_write_various_data_types(self, tmp_path: Path):
        """Test writing various Python data types."""
        writer = DuckDBWriter()
        
        data = {
            "mixed_types": [
                {
                    "string_val": "text",
                    "int_val": 42,
                    "float_val": 3.14,
                    "bool_val": True,
                    "none_val": None
                }
            ]
        }
        
        writer.write(data, tmp_path)
        
        db_file = tmp_path / "generated_data.duckdb"
        conn = duckdb.connect(str(db_file))
        try:
            result = conn.execute("SELECT * FROM mixed_types").fetchall()
            assert len(result) == 1
            row = result[0]
            assert row[0] == "text"
            assert row[1] == 42
            assert row[2] == 3.14
            assert row[3] is True
            assert row[4] is None
        finally:
            conn.close()