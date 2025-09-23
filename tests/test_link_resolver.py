"""Tests for LinkResolver functionality."""

import pytest
from unittest.mock import patch

from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.exceptions import LinkResolutionError
from jafgen.generation.models import DependencyGraph
from jafgen.schema.models import (
    SystemSchema, EntityConfig, AttributeConfig, OutputConfig
)


class TestLinkResolver:
    """Test cases for LinkResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = LinkResolver()
    
    def test_register_entity(self):
        """Test registering entity data."""
        data = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ]
        
        self.resolver.register_entity("test_schema", "users", data)
        
        # Verify data is stored correctly
        assert "test_schema" in self.resolver._entity_data
        assert "users" in self.resolver._entity_data["test_schema"]
        assert self.resolver._entity_data["test_schema"]["users"] == data
    
    def test_register_multiple_entities(self):
        """Test registering multiple entities across schemas."""
        users_data = [{"id": 1, "name": "John"}]
        orders_data = [{"id": 101, "user_id": 1}]
        
        self.resolver.register_entity("schema1", "users", users_data)
        self.resolver.register_entity("schema2", "orders", orders_data)
        
        assert len(self.resolver._entity_data) == 2
        assert "schema1" in self.resolver._entity_data
        assert "schema2" in self.resolver._entity_data
    
    @patch('random.choice')
    def test_resolve_link_success(self, mock_choice):
        """Test successful link resolution."""
        mock_choice.return_value = 1
        
        data = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ]
        self.resolver.register_entity("test_schema", "users", data)
        
        result = self.resolver.resolve_link("test_schema.users.id")
        
        assert result == 1
        mock_choice.assert_called_once_with([1, 2])
    
    def test_resolve_link_invalid_format(self):
        """Test link resolution with invalid format."""
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.resolve_link("invalid.format")
        
        assert "Invalid link specification format" in str(exc_info.value)
        assert "Expected format: 'schema.entity.attribute'" in str(exc_info.value)
    
    def test_resolve_link_schema_not_found(self):
        """Test link resolution when schema doesn't exist."""
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.resolve_link("nonexistent.users.id")
        
        assert "Schema 'nonexistent' not found" in str(exc_info.value)
    
    def test_resolve_link_entity_not_found(self):
        """Test link resolution when entity doesn't exist."""
        self.resolver.register_entity("test_schema", "users", [{"id": 1}])
        
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.resolve_link("test_schema.nonexistent.id")
        
        assert "Entity 'nonexistent' not found in schema 'test_schema'" in str(exc_info.value)
    
    def test_resolve_link_empty_data(self):
        """Test link resolution when entity has no data."""
        self.resolver.register_entity("test_schema", "users", [])
        
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.resolve_link("test_schema.users.id")
        
        assert "No data available for entity 'test_schema.users'" in str(exc_info.value)
    
    def test_resolve_link_attribute_not_found(self):
        """Test link resolution when attribute doesn't exist."""
        data = [{"id": 1, "name": "John"}]
        self.resolver.register_entity("test_schema", "users", data)
        
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.resolve_link("test_schema.users.nonexistent")
        
        assert "Attribute 'nonexistent' not found" in str(exc_info.value)
    
    def test_build_dependency_graph_simple(self):
        """Test building dependency graph with simple relationships."""
        # Create schemas with dependencies
        users_schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.name")
                    }
                ),
                "orders": EntityConfig(
                    name="orders", 
                    count=20,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(type="link", link_to="app.users.id")
                    }
                )
            }
        )
        
        graph = self.resolver.build_dependency_graph([users_schema])
        
        assert "app.users" in graph.nodes
        assert "app.orders" in graph.nodes
        assert "app.orders" in graph.edges
        assert "app.users" in graph.edges["app.orders"]
    
    def test_build_dependency_graph_multiple_schemas(self):
        """Test building dependency graph across multiple schemas."""
        schema1 = SystemSchema(
            name="schema1",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True)
                    }
                )
            }
        )
        
        schema2 = SystemSchema(
            name="schema2", 
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(type="link", link_to="schema1.users.id")
                    }
                )
            }
        )
        
        graph = self.resolver.build_dependency_graph([schema1, schema2])
        
        assert "schema1.users" in graph.nodes
        assert "schema2.orders" in graph.nodes
        assert "schema2.orders" in graph.edges
        assert "schema1.users" in graph.edges["schema2.orders"]
    
    def test_build_dependency_graph_invalid_link(self):
        """Test building dependency graph with invalid link reference."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="nonexistent.users.id")
                    }
                )
            }
        )
        
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.build_dependency_graph([schema])
        
        assert "Link target 'nonexistent.users' not found" in str(exc_info.value)
    
    def test_build_dependency_graph_invalid_format(self):
        """Test building dependency graph with invalid link format."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="invalid.format")
                    }
                )
            }
        )
        
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.build_dependency_graph([schema])
        
        assert "Invalid link specification" in str(exc_info.value)
    
    def test_get_generation_order(self):
        """Test getting generation order from dependency graph."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="app.users.id")
                    }
                )
            }
        )
        
        self.resolver.build_dependency_graph([schema])
        order = self.resolver.get_generation_order()
        
        # Users should come before orders
        users_index = order.index("app.users")
        orders_index = order.index("app.orders")
        assert users_index < orders_index
    
    def test_get_generation_order_no_graph(self):
        """Test getting generation order when no graph is built."""
        with pytest.raises(LinkResolutionError) as exc_info:
            self.resolver.get_generation_order()
        
        assert "Dependency graph not built" in str(exc_info.value)
    
    def test_validate_all_links_success(self):
        """Test validating all links when they are valid."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.name")
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="app.users.id")
                    }
                )
            }
        )
        
        errors = self.resolver.validate_all_links([schema])
        assert errors == []
    
    def test_validate_all_links_invalid_format(self):
        """Test validating links with invalid format."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="invalid.format")
                    }
                )
            }
        )
        
        errors = self.resolver.validate_all_links([schema])
        assert len(errors) == 1
        assert "Invalid link format" in errors[0]
    
    def test_validate_all_links_missing_entity(self):
        """Test validating links with missing target entity."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="app.nonexistent.id")
                    }
                )
            }
        )
        
        errors = self.resolver.validate_all_links([schema])
        assert len(errors) == 1
        assert "Link target entity 'app.nonexistent' not found" in errors[0]
    
    def test_validate_all_links_missing_attribute(self):
        """Test validating links with missing target attribute."""
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True)
                    }
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=20,
                    attributes={
                        "user_id": AttributeConfig(type="link", link_to="app.users.nonexistent")
                    }
                )
            }
        )
        
        errors = self.resolver.validate_all_links([schema])
        assert len(errors) == 1
        assert "Link target attribute 'nonexistent' not found" in errors[0]
    
    def test_clear_registered_data(self):
        """Test clearing registered data."""
        data = [{"id": 1, "name": "John"}]
        self.resolver.register_entity("test_schema", "users", data)
        
        # Build a graph to test it gets cleared too
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=10,
                    attributes={"id": AttributeConfig(type="uuid")}
                )
            }
        )
        self.resolver.build_dependency_graph([schema])
        
        # Clear data
        self.resolver.clear_registered_data()
        
        assert len(self.resolver._entity_data) == 0
        assert self.resolver._dependency_graph is None


class TestDependencyGraphCircularDependency:
    """Test cases for circular dependency detection."""
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        resolver = LinkResolver()
        
        # Create schemas with circular dependency
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "entity_a": EntityConfig(
                    name="entity_a",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "b_ref": AttributeConfig(type="link", link_to="app.entity_b.id")
                    }
                ),
                "entity_b": EntityConfig(
                    name="entity_b",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "a_ref": AttributeConfig(type="link", link_to="app.entity_a.id")
                    }
                )
            }
        )
        
        with pytest.raises(LinkResolutionError) as exc_info:
            resolver.build_dependency_graph([schema])
        
        assert "Circular dependency detected" in str(exc_info.value)
    
    def test_complex_circular_dependency(self):
        """Test detection of complex circular dependencies (A -> B -> C -> A)."""
        resolver = LinkResolver()
        
        schema = SystemSchema(
            name="app",
            version="1.0",
            entities={
                "entity_a": EntityConfig(
                    name="entity_a",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "b_ref": AttributeConfig(type="link", link_to="app.entity_b.id")
                    }
                ),
                "entity_b": EntityConfig(
                    name="entity_b",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "c_ref": AttributeConfig(type="link", link_to="app.entity_c.id")
                    }
                ),
                "entity_c": EntityConfig(
                    name="entity_c",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "a_ref": AttributeConfig(type="link", link_to="app.entity_a.id")
                    }
                )
            }
        )
        
        with pytest.raises(LinkResolutionError) as exc_info:
            resolver.build_dependency_graph([schema])
        
        assert "Circular dependency detected" in str(exc_info.value)


class TestDependencyGraphTopologicalSort:
    """Test cases for topological sorting in dependency graphs."""
    
    def test_simple_topological_sort(self):
        """Test simple topological sorting."""
        graph = DependencyGraph()
        graph.add_dependency("B", "A")  # B depends on A
        graph.add_dependency("C", "B")  # C depends on B
        
        order = graph.get_generation_order()
        
        # A should come first, then B, then C
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")
    
    def test_complex_topological_sort(self):
        """Test complex topological sorting with multiple dependencies."""
        graph = DependencyGraph()
        graph.add_dependency("D", "A")  # D depends on A
        graph.add_dependency("D", "B")  # D depends on B
        graph.add_dependency("C", "A")  # C depends on A
        graph.add_dependency("E", "D")  # E depends on D
        
        order = graph.get_generation_order()
        
        # A and B should come before C and D
        # D should come before E
        # C can be anywhere after A
        assert order.index("A") < order.index("D")
        assert order.index("B") < order.index("D")
        assert order.index("A") < order.index("C")
        assert order.index("D") < order.index("E")
    
    def test_no_dependencies(self):
        """Test topological sort with no dependencies."""
        graph = DependencyGraph()
        graph.nodes = ["A", "B", "C"]
        
        order = graph.get_generation_order()
        
        # All nodes should be present
        assert set(order) == {"A", "B", "C"}
        assert len(order) == 3