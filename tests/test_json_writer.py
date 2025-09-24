"""Tests for JSON output writer."""

import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from jafgen.output.json_writer import JSONWriter


class TestJSONWriter:
    """Test cases for JSONWriter."""
    
    def test_write_simple_data(self, tmp_path: Path):
        """Test writing simple data to JSON."""
        writer = JSONWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ]
        }
        
        writer.write(data, tmp_path)
        
        # Verify file was created
        json_file = tmp_path / "customers.json"
        assert json_file.exists()
        
        # Verify content
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        assert len(loaded_data) == 2
        assert loaded_data[0]["id"] == 1
        assert loaded_data[0]["name"] == "John Doe"
        assert loaded_data[0]["email"] == "john@example.com"
        assert loaded_data[1]["id"] == 2
        assert loaded_data[1]["name"] == "Jane Smith"
        assert loaded_data[1]["email"] == "jane@example.com"
    
    def test_write_multiple_entities(self, tmp_path: Path):
        """Test writing multiple entities to separate JSON files."""
        writer = JSONWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John Doe"}
            ],
            "orders": [
                {"id": 101, "customer_id": 1, "total": 25.50}
            ]
        }
        
        writer.write(data, tmp_path)
        
        # Verify both files were created
        customers_file = tmp_path / "customers.json"
        orders_file = tmp_path / "orders.json"
        
        assert customers_file.exists()
        assert orders_file.exists()
        
        # Verify customers content
        with open(customers_file, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        
        assert len(customers) == 1
        assert customers[0]["id"] == 1
        assert customers[0]["name"] == "John Doe"
        
        # Verify orders content
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        assert len(orders) == 1
        assert orders[0]["id"] == 101
        assert orders[0]["customer_id"] == 1
        assert orders[0]["total"] == 25.5
    
    def test_write_with_datetime_objects(self, tmp_path: Path):
        """Test writing data with datetime objects."""
        writer = JSONWriter()
        
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
        
        json_file = tmp_path / "events.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == 1
        event = loaded_data[0]
        assert event["id"] == 1
        assert event["created_at"] == "2024-01-15T10:30:45"
        assert event["event_date"] == "2024-01-15"
        assert event["name"] == "Test Event"
    
    def test_write_with_uuid_objects(self, tmp_path: Path):
        """Test writing data with UUID objects."""
        writer = JSONWriter()
        
        test_uuid = uuid4()
        
        data = {
            "users": [
                {
                    "id": test_uuid,
                    "name": "John Doe",
                    "external_id": str(test_uuid)
                }
            ]
        }
        
        writer.write(data, tmp_path)
        
        json_file = tmp_path / "users.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == 1
        user = loaded_data[0]
        assert user["id"] == str(test_uuid)
        assert user["name"] == "John Doe"
        assert user["external_id"] == str(test_uuid)
    
    def test_write_with_nested_objects(self, tmp_path: Path):
        """Test writing data with nested objects and lists."""
        writer = JSONWriter()
        
        data = {
            "products": [
                {
                    "id": 1,
                    "name": "Widget",
                    "metadata": {
                        "color": "blue",
                        "dimensions": {"width": 10, "height": 5}
                    },
                    "tags": ["electronics", "gadget", "blue"]
                }
            ]
        }
        
        writer.write(data, tmp_path)
        
        json_file = tmp_path / "products.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == 1
        product = loaded_data[0]
        assert product["id"] == 1
        assert product["name"] == "Widget"
        assert product["metadata"]["color"] == "blue"
        assert product["metadata"]["dimensions"]["width"] == 10
        assert product["metadata"]["dimensions"]["height"] == 5
        assert product["tags"] == ["electronics", "gadget", "blue"]
    
    def test_write_empty_entity_list(self, tmp_path: Path):
        """Test writing data with empty entity lists."""
        writer = JSONWriter()
        
        data = {
            "customers": [
                {"id": 1, "name": "John"}
            ],
            "orders": []  # Empty list
        }
        
        writer.write(data, tmp_path)
        
        # Only customers file should be created
        customers_file = tmp_path / "customers.json"
        orders_file = tmp_path / "orders.json"
        
        assert customers_file.exists()
        assert not orders_file.exists()
    
    def test_write_creates_directory(self, tmp_path: Path):
        """Test that writer creates output directory if it doesn't exist."""
        writer = JSONWriter()
        
        # Use a nested path that doesn't exist
        output_path = tmp_path / "nested" / "output"
        
        data = {
            "test": [{"id": 1, "value": "test"}]
        }
        
        writer.write(data, output_path)
        
        # Directory should be created
        assert output_path.exists()
        assert output_path.is_dir()
        
        # File should be created in the directory
        test_file = output_path / "test.json"
        assert test_file.exists()
    
    def test_custom_formatting_options(self, tmp_path: Path):
        """Test JSON writer with custom formatting options."""
        writer = JSONWriter(indent=4, ensure_ascii=True)
        
        data = {
            "users": [
                {"id": 1, "name": "José", "city": "São Paulo"}
            ]
        }
        
        writer.write(data, tmp_path)
        
        json_file = tmp_path / "users.json"
        
        # Read raw content to check formatting
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have 4-space indentation
        assert "    " in content
        # Should escape non-ASCII characters
        assert "Jos\\u00e9" in content or "S\\u00e3o Paulo" in content
    
    def test_write_with_none_values(self, tmp_path: Path):
        """Test writing data with None values."""
        writer = JSONWriter()
        
        data = {
            "users": [
                {"id": 1, "name": "John", "middle_name": None, "email": "john@example.com"},
                {"id": 2, "name": "Jane", "middle_name": "Marie", "email": None}
            ]
        }
        
        writer.write(data, tmp_path)
        
        json_file = tmp_path / "users.json"
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == 2
        assert loaded_data[0]["middle_name"] is None
        assert loaded_data[1]["email"] is None