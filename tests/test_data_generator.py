"""Tests for DataGenerator implementation."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.exceptions import GenerationError
from jafgen.generation.models import DependencyGraph
from jafgen.schema.models import AttributeConfig, EntityConfig, SystemSchema, OutputConfig


class TestDataGenerator:
    """Test cases for DataGenerator."""
    
    def test_init(self):
        """Test DataGenerator initialization."""
        mimesis_engine = Mock()
        link_resolver = Mock()
        
        generator = DataGenerator(mimesis_engine, link_resolver)
        
        assert generator.mimesis_engine == mimesis_engine
        assert generator.link_resolver == link_resolver
    
    def test_init_without_link_resolver(self):
        """Test DataGenerator initialization without link resolver."""
        mimesis_engine = Mock()
        
        generator = DataGenerator(mimesis_engine)
        
        assert generator.mimesis_engine == mimesis_engine
        assert generator.link_resolver is None
    
    def test_generate_entity_simple(self):
        """Test generating a simple entity without links."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = ["John Doe", "john@example.com", 25]
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=1,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True),
                "email": AttributeConfig(type="person.email", required=True),
                "age": AttributeConfig(type="int", required=False)
            }
        )
        
        result = generator.generate_entity(entity_config)
        
        assert len(result) == 1
        assert result[0]["name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"
        assert result[0]["age"] == 25
        
        # Verify mimesis_engine was called for each attribute
        assert mimesis_engine.generate_value.call_count == 3
    
    def test_generate_entity_multiple_records(self):
        """Test generating multiple records for an entity."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = [
            "John Doe", "john@example.com",  # Record 1
            "Jane Smith", "jane@example.com"  # Record 2
        ]
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=2,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True),
                "email": AttributeConfig(type="person.email", required=True)
            }
        )
        
        result = generator.generate_entity(entity_config)
        
        assert len(result) == 2
        assert result[0]["name"] == "John Doe"
        assert result[0]["email"] == "john@example.com"
        assert result[1]["name"] == "Jane Smith"
        assert result[1]["email"] == "jane@example.com"
    
    def test_generate_entity_with_required_validation(self):
        """Test that required attributes are validated."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.return_value = None  # Empty value
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=1,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True)
            }
        )
        
        with pytest.raises(GenerationError) as exc_info:
            generator.generate_entity(entity_config)
        
        assert "Required attribute 'name'" in str(exc_info.value)
        assert "generated empty value" in str(exc_info.value)
    
    def test_generate_entity_with_empty_string_validation(self):
        """Test that empty strings are caught for required attributes."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.return_value = "   "  # Whitespace only
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=1,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True)
            }
        )
        
        with pytest.raises(GenerationError) as exc_info:
            generator.generate_entity(entity_config)
        
        assert "Required attribute 'name'" in str(exc_info.value)
    
    def test_generate_entity_non_required_empty_values_allowed(self):
        """Test that non-required attributes can have empty values."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = ["John Doe", None]  # Second value is None
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=1,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True),
                "nickname": AttributeConfig(type="person.first_name", required=False)
            }
        )
        
        result = generator.generate_entity(entity_config)
        
        assert len(result) == 1
        assert result[0]["name"] == "John Doe"
        assert result[0]["nickname"] is None
    
    def test_generate_entity_with_link_resolution(self):
        """Test generating entity with link resolution."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = ["Order 1", None]  # None for link_to
        
        link_resolver = Mock()
        link_resolver.resolve_link.return_value = "user-123"
        
        generator = DataGenerator(mimesis_engine, link_resolver)
        
        entity_config = EntityConfig(
            name="orders",
            count=1,
            attributes={
                "name": AttributeConfig(type="text", required=True),
                "user_id": AttributeConfig(
                    type="uuid", 
                    required=True, 
                    link_to="users.id"
                )
            }
        )
        
        result = generator.generate_entity(entity_config)
        
        assert len(result) == 1
        assert result[0]["name"] == "Order 1"
        assert result[0]["user_id"] == "user-123"
        
        link_resolver.resolve_link.assert_called_once_with("users.id")
    
    def test_generate_entity_link_resolution_failure_required(self):
        """Test that link resolution failure raises error for required attributes."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.return_value = None  # Link placeholder
        
        link_resolver = Mock()
        link_resolver.resolve_link.side_effect = Exception("Link not found")
        
        generator = DataGenerator(mimesis_engine, link_resolver)
        
        entity_config = EntityConfig(
            name="orders",
            count=1,
            attributes={
                "user_id": AttributeConfig(
                    type="uuid", 
                    required=True, 
                    link_to="users.id"
                )
            }
        )
        
        with pytest.raises(GenerationError) as exc_info:
            generator.generate_entity(entity_config)
        
        assert "Failed to resolve required link" in str(exc_info.value)
        assert "users.id" in str(exc_info.value)
    
    def test_generate_entity_link_resolution_failure_non_required(self):
        """Test that link resolution failure is handled gracefully for non-required attributes."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = ["Order 1", None]  # None for link_to
        
        link_resolver = Mock()
        link_resolver.resolve_link.side_effect = Exception("Link not found")
        
        generator = DataGenerator(mimesis_engine, link_resolver)
        
        entity_config = EntityConfig(
            name="orders",
            count=1,
            attributes={
                "name": AttributeConfig(type="text", required=True),
                "user_id": AttributeConfig(
                    type="uuid", 
                    required=False, 
                    link_to="users.id"
                )
            }
        )
        
        result = generator.generate_entity(entity_config)
        
        assert len(result) == 1
        assert result[0]["name"] == "Order 1"
        assert result[0]["user_id"] is None
    
    def test_generate_system_simple(self):
        """Test generating a simple system without dependencies."""
        mimesis_engine = Mock()
        mimesis_engine.seed = 42
        mimesis_engine.generate_value.side_effect = ["John Doe", "john@example.com"]
        
        generator = DataGenerator(mimesis_engine)
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            seed=42,
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="person.full_name", required=True),
                        "email": AttributeConfig(type="person.email", required=True)
                    }
                )
            }
        )
        
        result = generator.generate_system(schema)
        
        assert result.schema == schema
        assert len(result.entities) == 1
        assert "users" in result.entities
        assert len(result.entities["users"]) == 1
        assert result.entities["users"][0]["name"] == "John Doe"
        assert result.entities["users"][0]["email"] == "john@example.com"
        
        # Check metadata
        assert result.metadata.seed_used == 42
        assert result.metadata.total_records == 1
        assert result.metadata.entity_counts["users"] == 1
        assert isinstance(result.metadata.generated_at, datetime)
    
    def test_generate_system_with_dependencies(self):
        """Test generating a system with entity dependencies."""
        mimesis_engine = Mock()
        mimesis_engine.seed = 42
        mimesis_engine.generate_value.side_effect = [
            "John Doe", "john@example.com",  # User
            "Order 1", None  # Order (None for link_to)
        ]
        
        link_resolver = Mock()
        link_resolver.resolve_link.return_value = "user-123"
        link_resolver.validate_all_links.return_value = []  # No validation errors
        
        # Mock dependency graph
        dependency_graph = Mock()
        dependency_graph.get_generation_order.return_value = ["test_system.users", "test_system.orders"]
        link_resolver.build_dependency_graph.return_value = dependency_graph
        
        generator = DataGenerator(mimesis_engine, link_resolver)
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            seed=42,
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="person.full_name", required=True),
                        "email": AttributeConfig(type="person.email", required=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="text", required=True),
                        "user_id": AttributeConfig(
                            type="uuid", 
                            required=True, 
                            link_to="users.id"
                        )
                    }
                )
            }
        )
        
        result = generator.generate_system(schema)
        
        assert len(result.entities) == 2
        assert "users" in result.entities
        assert "orders" in result.entities
        assert result.metadata.total_records == 2
        
        # Verify link resolver was used
        link_resolver.build_dependency_graph.assert_called_once_with([schema])
        link_resolver.register_entity.assert_any_call("test_system", "users", result.entities["users"])
        link_resolver.register_entity.assert_any_call("test_system", "orders", result.entities["orders"])
    
    def test_generate_system_uses_schema_seed(self):
        """Test that system generation uses schema seed when available."""
        mimesis_engine = Mock()
        mimesis_engine.seed = 999  # Different from schema seed
        mimesis_engine.generate_value.return_value = "test"
        
        generator = DataGenerator(mimesis_engine)
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            seed=123,  # Schema-specific seed
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        result = generator.generate_system(schema)
        
        assert result.metadata.seed_used == 123  # Should use schema seed
    
    def test_generate_system_uses_engine_seed_when_schema_none(self):
        """Test that system generation uses engine seed when schema seed is None."""
        mimesis_engine = Mock()
        mimesis_engine.seed = 999
        mimesis_engine.generate_value.return_value = "test"
        
        generator = DataGenerator(mimesis_engine)
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            seed=None,  # No schema seed
            output=OutputConfig(),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        result = generator.generate_system(schema)
        
        assert result.metadata.seed_used == 999  # Should use engine seed
    
    def test_is_empty_value(self):
        """Test the _is_empty_value helper method."""
        mimesis_engine = Mock()
        generator = DataGenerator(mimesis_engine)
        
        # Test None
        assert generator._is_empty_value(None) is True
        
        # Test empty string
        assert generator._is_empty_value("") is True
        assert generator._is_empty_value("   ") is True
        
        # Test empty collections
        assert generator._is_empty_value([]) is True
        assert generator._is_empty_value({}) is True
        
        # Test non-empty values
        assert generator._is_empty_value("hello") is False
        assert generator._is_empty_value(0) is False
        assert generator._is_empty_value(False) is False
        assert generator._is_empty_value([1, 2, 3]) is False
        assert generator._is_empty_value({"key": "value"}) is False
    
    def test_generate_entity_exception_handling(self):
        """Test that entity generation exceptions are properly wrapped."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = Exception("Mimesis error")
        
        generator = DataGenerator(mimesis_engine)
        
        entity_config = EntityConfig(
            name="users",
            count=1,
            attributes={
                "name": AttributeConfig(type="person.full_name", required=True)
            }
        )
        
        with pytest.raises(GenerationError) as exc_info:
            generator.generate_entity(entity_config)
        
        assert "Failed to generate entity 'users'" in str(exc_info.value)
        assert "Mimesis error" in str(exc_info.value)
    
    def test_generate_system_exception_handling(self):
        """Test that system generation exceptions are properly wrapped."""
        mimesis_engine = Mock()
        mimesis_engine.generate_value.side_effect = Exception("Generation error")
        
        generator = DataGenerator(mimesis_engine)
        
        schema = SystemSchema(
            name="test_system",
            version="1.0.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=1,
                    attributes={
                        "name": AttributeConfig(type="person.full_name", required=True)
                    }
                )
            }
        )
        
        with pytest.raises(GenerationError) as exc_info:
            generator.generate_system(schema)
        
        assert "Failed to generate system 'test_system'" in str(exc_info.value)