"""Integration tests for DataGenerator with LinkResolver."""


import pytest

from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.exceptions import GenerationError
from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.schema.models import (
    AttributeConfig,
    EntityConfig,
    SystemSchema,
)


class TestDataGeneratorLinkIntegration:
    """Test DataGenerator integration with LinkResolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mimesis_engine = MimesisEngine(seed=42)
        self.link_resolver = LinkResolver()
        self.data_generator = DataGenerator(self.mimesis_engine, self.link_resolver)

    def test_generate_system_with_simple_links(self):
        """Test generating a system with simple entity links."""
        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name"),
                    },
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.users.id"
                        ),
                        "amount": AttributeConfig(type="decimal"),
                    },
                ),
            },
        )

        result = self.data_generator.generate_system(schema)

        # Verify structure
        assert "users" in result.entities
        assert "orders" in result.entities
        assert len(result.entities["users"]) == 5
        assert len(result.entities["orders"]) == 10

        # Verify links are resolved
        user_ids = {user["id"] for user in result.entities["users"]}
        for order in result.entities["orders"]:
            assert order["user_id"] in user_ids
            assert order["user_id"] is not None

        # Verify metadata
        assert result.metadata.total_records == 15
        assert result.metadata.entity_counts["users"] == 5
        assert result.metadata.entity_counts["orders"] == 10

    def test_generate_system_with_complex_dependencies(self):
        """Test generating a system with complex dependency chains."""
        schema = SystemSchema(
            name="ecommerce",
            version="1.0",
            entities={
                "categories": EntityConfig(
                    name="categories",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="text.word"),
                    },
                ),
                "products": EntityConfig(
                    name="products",
                    count=8,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="text.word"),
                        "category_id": AttributeConfig(
                            type="link", link_to="ecommerce.categories.id"
                        ),
                    },
                ),
                "users": EntityConfig(
                    name="users",
                    count=4,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name"),
                    },
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=12,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="ecommerce.users.id"
                        ),
                        "product_id": AttributeConfig(
                            type="link", link_to="ecommerce.products.id"
                        ),
                    },
                ),
            },
        )

        result = self.data_generator.generate_system(schema)

        # Verify all entities generated
        assert len(result.entities) == 4
        assert len(result.entities["categories"]) == 3
        assert len(result.entities["products"]) == 8
        assert len(result.entities["users"]) == 4
        assert len(result.entities["orders"]) == 12

        # Verify dependency chains
        category_ids = {cat["id"] for cat in result.entities["categories"]}
        product_ids = {prod["id"] for prod in result.entities["products"]}
        user_ids = {user["id"] for user in result.entities["users"]}

        # Products should reference valid categories
        for product in result.entities["products"]:
            assert product["category_id"] in category_ids

        # Orders should reference valid users and products
        for order in result.entities["orders"]:
            assert order["user_id"] in user_ids
            assert order["product_id"] in product_ids

    def test_generate_multiple_systems_with_cross_schema_links(self):
        """Test generating multiple systems with cross-schema dependencies."""
        # Schema 1: User management
        users_schema = SystemSchema(
            name="users",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "email": AttributeConfig(type="person.email", unique=True),
                    },
                )
            },
        )

        # Schema 2: Order management (depends on users)
        orders_schema = SystemSchema(
            name="orders",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=8,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="users.users.id"
                        ),
                        "total": AttributeConfig(type="decimal"),
                    },
                )
            },
        )

        results = self.data_generator.generate_multiple_systems(
            [users_schema, orders_schema]
        )

        assert len(results) == 2

        # Find results by schema name
        users_result = next(r for r in results if r.schema.name == "users")
        orders_result = next(r for r in results if r.schema.name == "orders")

        # Verify cross-schema links
        user_ids = {user["id"] for user in users_result.entities["users"]}
        for order in orders_result.entities["orders"]:
            assert order["user_id"] in user_ids

    def test_generate_system_invalid_link_validation(self):
        """Test that invalid links are caught during validation."""
        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.nonexistent.id"
                        ),
                    },
                )
            },
        )

        with pytest.raises(GenerationError) as exc_info:
            self.data_generator.generate_system(schema)

        assert "Link validation failed" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_generate_system_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "entity_a": EntityConfig(
                    name="entity_a",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "b_ref": AttributeConfig(
                            type="link", link_to="test_system.entity_b.id"
                        ),
                    },
                ),
                "entity_b": EntityConfig(
                    name="entity_b",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "a_ref": AttributeConfig(
                            type="link", link_to="test_system.entity_a.id"
                        ),
                    },
                ),
            },
        )

        with pytest.raises(GenerationError) as exc_info:
            self.data_generator.generate_system(schema)

        assert "Circular dependency detected" in str(exc_info.value)

    def test_generate_system_without_link_resolver(self):
        """Test generating system without link resolver (should work but no links)."""
        generator = DataGenerator(self.mimesis_engine)  # No link resolver

        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name"),
                    },
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.users.id", required=False
                        ),
                    },
                ),
            },
        )

        result = generator.generate_system(schema)

        # Should generate entities but links will be None
        assert len(result.entities["users"]) == 3
        assert len(result.entities["orders"]) == 5

        # Links should be None since no resolver
        for order in result.entities["orders"]:
            assert order["user_id"] is None

    def test_generate_system_required_link_fails_without_resolver(self):
        """Test that required links fail without link resolver."""
        generator = DataGenerator(self.mimesis_engine)  # No link resolver

        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.users.id", required=True
                        ),
                    },
                )
            },
        )

        with pytest.raises(GenerationError) as exc_info:
            generator.generate_system(schema)

        assert "Required attribute 'user_id'" in str(exc_info.value)
        assert "generated empty value" in str(exc_info.value)

    def test_generate_entity_with_mixed_attributes(self):
        """Test generating entity with mix of regular and link attributes."""
        # First generate users to link to
        users_config = EntityConfig(
            name="users",
            count=3,
            attributes={
                "id": AttributeConfig(type="uuid", unique=True),
                "name": AttributeConfig(type="person.full_name"),
            },
        )
        users_data = self.data_generator.generate_entity(users_config)
        self.link_resolver.register_entity("test", "users", users_data)

        # Now generate orders that link to users
        orders_config = EntityConfig(
            name="orders",
            count=5,
            attributes={
                "id": AttributeConfig(type="uuid", unique=True),
                "user_id": AttributeConfig(type="link", link_to="test.users.id"),
                "amount": AttributeConfig(type="decimal"),
                "status": AttributeConfig(type="text.word"),
            },
        )

        orders_data = self.data_generator.generate_entity(orders_config)

        assert len(orders_data) == 5
        user_ids = {user["id"] for user in users_data}

        for order in orders_data:
            # Link should be resolved
            assert order["user_id"] in user_ids
            # Regular attributes should be generated
            assert order["id"] is not None
            assert order["amount"] is not None
            assert order["status"] is not None

    def test_deterministic_generation_with_links(self):
        """Test that generation with links maintains referential integrity."""
        schema = SystemSchema(
            name="test_system",
            version="1.0",
            seed=123,
            entities={
                "users": EntityConfig(
                    name="users",
                    count=3,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name"),
                    },
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=5,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.users.id"
                        ),
                    },
                ),
            },
        )

        # Generate data
        result = self.data_generator.generate_system(schema)

        # Verify structure and referential integrity
        assert len(result.entities["users"]) == 3
        assert len(result.entities["orders"]) == 5

        # Verify all user IDs are unique
        user_ids = [user["id"] for user in result.entities["users"]]
        assert len(set(user_ids)) == len(user_ids)

        # Verify all order IDs are unique
        order_ids = [order["id"] for order in result.entities["orders"]]
        assert len(set(order_ids)) == len(order_ids)

        # Verify all order user_ids reference valid users
        user_id_set = set(user_ids)
        for order in result.entities["orders"]:
            assert order["user_id"] in user_id_set


class TestDataGeneratorErrorHandling:
    """Test error handling in DataGenerator with LinkResolver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mimesis_engine = MimesisEngine(seed=42)
        self.link_resolver = LinkResolver()
        self.data_generator = DataGenerator(self.mimesis_engine, self.link_resolver)

    def test_link_resolution_failure_required_attribute(self):
        """Test handling of link resolution failure for required attribute."""
        # Create schema with link to non-existent entity
        schema = SystemSchema(
            name="test_system",
            version="1.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=1,
                    attributes={
                        "user_id": AttributeConfig(
                            type="link", link_to="test_system.users.id", required=True
                        )
                    },
                )
            },
        )

        with pytest.raises(GenerationError) as exc_info:
            self.data_generator.generate_system(schema)

        assert "Link validation failed" in str(exc_info.value)

    def test_multiple_systems_validation_failure(self):
        """Test validation failure in multiple systems generation."""
        schema1 = SystemSchema(
            name="schema1",
            version="1.0",
            entities={
                "entity1": EntityConfig(
                    name="entity1",
                    count=1,
                    attributes={"id": AttributeConfig(type="uuid")},
                )
            },
        )

        schema2 = SystemSchema(
            name="schema2",
            version="1.0",
            entities={
                "entity2": EntityConfig(
                    name="entity2",
                    count=1,
                    attributes={
                        "ref": AttributeConfig(
                            type="link", link_to="nonexistent.entity.id"
                        )
                    },
                )
            },
        )

        with pytest.raises(GenerationError) as exc_info:
            self.data_generator.generate_multiple_systems([schema1, schema2])

        assert "Link validation failed across schemas" in str(exc_info.value)

    def test_empty_schema_list(self):
        """Test generating multiple systems with empty schema list."""
        result = self.data_generator.generate_multiple_systems([])
        assert result == []

    def test_schema_with_no_entities(self):
        """Test generating system with no entities."""
        schema = SystemSchema(name="empty_system", version="1.0", entities={})

        result = self.data_generator.generate_system(schema)

        assert result.entities == {}
        assert result.metadata.total_records == 0
        assert result.metadata.entity_counts == {}
