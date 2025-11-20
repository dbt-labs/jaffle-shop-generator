"""Tests for schema discovery and validation engine."""

import tempfile
from pathlib import Path

import pytest

from jafgen.schema import (
    CircularDependencyError,
    SchemaDiscoveryEngine,
)
from jafgen.schema.models import (
    AttributeConfig,
    EntityConfig,
    OutputConfig,
    SystemSchema,
)


class TestSchemaDiscoveryEngine:
    """Test cases for SchemaDiscoveryEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = SchemaDiscoveryEngine()

    def test_discover_empty_directory(self):
        """Test discovery in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schemas, result = self.engine.discover_and_load_schemas(Path(temp_dir))

            assert schemas == []
            assert result.is_valid is True
            assert len(result.warnings) == 1
            assert result.warnings[0].type == "no_schemas_found"

    def test_discover_and_load_valid_schemas(self):
        """Test discovery and loading of valid schemas."""
        schema1_content = """
system:
  name: "users-schema"
  version: "1.0.0"
  seed: 42

entities:
  users:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
      name:
        type: "person.full_name"
"""

        schema2_content = """
system:
  name: "orders-schema"
  version: "1.0.0"
  seed: 42

entities:
  orders:
    count: 200
    attributes:
      id:
        type: "uuid"
        unique: true
      user_id:
        type: "link"
        link_to: "users-schema.users.id"
      total:
        type: "numeric.decimal"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)

            (schema_dir / "users.yaml").write_text(schema1_content)
            (schema_dir / "orders.yaml").write_text(schema2_content)

            schemas, result = self.engine.discover_and_load_schemas(schema_dir)

            assert len(schemas) == 2
            assert result.is_valid is True

            schema_names = [s.name for s in schemas]
            assert "users-schema" in schema_names
            assert "orders-schema" in schema_names

    def test_discover_with_invalid_schema(self):
        """Test discovery with one invalid schema."""
        valid_schema = """
system:
  name: "valid-schema"
  version: "1.0.0"

entities:
  users:
    count: 100
    attributes:
      id:
        type: "uuid"
"""

        invalid_schema = """
system:
  name: "invalid-schema"
  # Missing version
entities:
  users:
    count: 100
    attributes:
      id:
        type: "uuid"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)

            (schema_dir / "valid.yaml").write_text(valid_schema)
            (schema_dir / "invalid.yaml").write_text(invalid_schema)

            schemas, result = self.engine.discover_and_load_schemas(schema_dir)

            assert (
                len(schemas) == 2
            )  # Both should load, but validation will catch issues
            assert result.is_valid is False
            assert any(error.type == "missing_field" for error in result.errors)

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        schema_content = """
system:
  name: "circular-schema"
  version: "1.0.0"

entities:
  entity_a:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
      b_ref:
        type: "link"
        link_to: "circular-schema.entity_b.id"

  entity_b:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
      a_ref:
        type: "link"
        link_to: "circular-schema.entity_a.id"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            (schema_dir / "circular.yaml").write_text(schema_content)

            schemas, result = self.engine.discover_and_load_schemas(schema_dir)

            assert len(schemas) == 1
            assert result.is_valid is False
            assert any(error.type == "circular_dependency" for error in result.errors)

    def test_get_schema_summary(self):
        """Test schema summary generation."""
        schema = SystemSchema(
            name="test-schema",
            version="1.0.0",
            seed=42,
            output=OutputConfig(format=["csv", "json"], path="./output"),
            entities={
                "users": EntityConfig(
                    name="users",
                    count=100,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "name": AttributeConfig(type="person.full_name"),
                        "email": AttributeConfig(type="person.email", unique=True),
                    },
                ),
                "orders": EntityConfig(
                    name="orders",
                    count=200,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="test-schema.users.id"
                        ),
                    },
                ),
            },
        )

        summary = self.engine.get_schema_summary([schema])

        assert "test-schema" in summary
        schema_summary = summary["test-schema"]

        assert schema_summary["version"] == "1.0.0"
        assert schema_summary["seed"] == 42
        assert schema_summary["output_formats"] == ["csv", "json"]
        assert schema_summary["entity_count"] == 2
        assert schema_summary["total_attributes"] == 5
        assert schema_summary["total_records"] == 300
        assert schema_summary["link_count"] == 1

        assert "users" in schema_summary["entities"]
        assert "orders" in schema_summary["entities"]
        assert schema_summary["entities"]["users"]["count"] == 100
        assert schema_summary["entities"]["orders"]["links"] == 1

    def test_validate_schema_compatibility(self):
        """Test schema compatibility validation."""
        schema1 = SystemSchema(
            name="duplicate-name",
            version="1.0.0",
            output=OutputConfig(path="./output1"),
        )

        schema2 = SystemSchema(
            name="duplicate-name",  # Same name
            version="2.0.0",
            output=OutputConfig(path="./output1"),  # Same output path
        )

        result = self.engine.validate_schema_compatibility([schema1, schema2])

        assert result.is_valid is False
        assert any(error.type == "duplicate_schema_name" for error in result.errors)
        assert any(
            warning.type == "conflicting_output_path" for warning in result.warnings
        )

    def test_build_dependency_graph(self):
        """Test dependency graph building."""
        schema1 = SystemSchema(
            name="schema1",
            version="1.0.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=100,
                    attributes={"id": AttributeConfig(type="uuid", unique=True)},
                )
            },
        )

        schema2 = SystemSchema(
            name="schema2",
            version="1.0.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=200,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="schema1.users.id"
                        ),
                    },
                )
            },
        )

        dependency_graph = self.engine.build_dependency_graph([schema1, schema2])

        assert "schema1.users" in dependency_graph
        assert "schema2.orders" in dependency_graph
        assert "schema1.users" in dependency_graph["schema2.orders"]
        assert len(dependency_graph["schema1.users"]) == 0  # No dependencies

    def test_get_generation_order(self):
        """Test generation order calculation."""
        schema1 = SystemSchema(
            name="schema1",
            version="1.0.0",
            entities={
                "users": EntityConfig(
                    name="users",
                    count=100,
                    attributes={"id": AttributeConfig(type="uuid", unique=True)},
                )
            },
        )

        schema2 = SystemSchema(
            name="schema2",
            version="1.0.0",
            entities={
                "orders": EntityConfig(
                    name="orders",
                    count=200,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "user_id": AttributeConfig(
                            type="link", link_to="schema1.users.id"
                        ),
                    },
                )
            },
        )

        order = self.engine.get_generation_order([schema1, schema2])

        # Users should come before orders
        users_index = order.index("schema1.users")
        orders_index = order.index("schema2.orders")
        assert users_index < orders_index

    def test_get_generation_order_circular_dependency(self):
        """Test generation order with circular dependencies."""
        schema = SystemSchema(
            name="circular",
            version="1.0.0",
            entities={
                "entity_a": EntityConfig(
                    name="entity_a",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "b_ref": AttributeConfig(
                            type="link", link_to="circular.entity_b.id"
                        ),
                    },
                ),
                "entity_b": EntityConfig(
                    name="entity_b",
                    count=10,
                    attributes={
                        "id": AttributeConfig(type="uuid", unique=True),
                        "a_ref": AttributeConfig(
                            type="link", link_to="circular.entity_a.id"
                        ),
                    },
                ),
            },
        )

        with pytest.raises(CircularDependencyError):
            self.engine.get_generation_order([schema])
