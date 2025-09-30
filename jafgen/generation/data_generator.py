"""Concrete implementation of DataGenerator for entity creation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..schema.models import EntityConfig, SystemSchema
from .exceptions import GenerationError
from .interfaces import DataGenerator as DataGeneratorInterface
from .interfaces import (
    LinkResolver,
    MimesisEngine,
)
from .models import GeneratedSystem, GenerationMetadata


class DataGenerator(DataGeneratorInterface):
    """Concrete implementation of data generation for entities."""

    def __init__(
        self,
        mimesis_engine: MimesisEngine,
        link_resolver: Optional[LinkResolver] = None,
    ):
        """Initialize the data generator with required engines."""
        self.mimesis_engine = mimesis_engine
        self.link_resolver = link_resolver

    def generate_system(self, schema: SystemSchema) -> GeneratedSystem:
        """Generate data for an entire system schema."""
        try:
            entities = {}
            total_records = 0
            entity_counts = {}

            # Validate all links before generation if link resolver is available
            if self.link_resolver:
                link_errors = self.link_resolver.validate_all_links([schema])
                if link_errors:
                    raise GenerationError(
                        f"Link validation failed for schema '{schema.name}':\n"
                        + "\n".join(f"  - {error}" for error in link_errors)
                    )

                # Build dependency graph and get generation order
                dependency_graph = self.link_resolver.build_dependency_graph([schema])
                generation_order = dependency_graph.get_generation_order()

                # Filter to only include entities from this schema and map back to entity names
                schema_entity_keys = [
                    f"{schema.name}.{name}" for name in schema.entities.keys()
                ]
                ordered_entity_keys = [
                    key for key in generation_order if key in schema_entity_keys
                ]
                schema_entities = [key.split(".", 1)[1] for key in ordered_entity_keys]
            else:
                # Generate in schema definition order
                schema_entities = list(schema.entities.keys())

            # Generate each entity
            for entity_name in schema_entities:
                if entity_name in schema.entities:
                    entity_config = schema.entities[entity_name]
                    entity_data = self.generate_entity(entity_config)

                    entities[entity_name] = entity_data
                    entity_counts[entity_name] = len(entity_data)
                    total_records += len(entity_data)

                    # Register with link resolver if available
                    if self.link_resolver:
                        self.link_resolver.register_entity(
                            schema.name, entity_name, entity_data
                        )

            # Create metadata
            metadata = GenerationMetadata(
                generated_at=datetime.now(),
                seed_used=schema.seed or getattr(self.mimesis_engine, "seed", 42),
                total_records=total_records,
                entity_counts=entity_counts,
            )

            return GeneratedSystem(schema=schema, entities=entities, metadata=metadata)

        except Exception as e:
            raise GenerationError(
                f"Failed to generate system '{schema.name}': {str(e)}"
            ) from e

    def generate_multiple_systems(
        self, schemas: List[SystemSchema]
    ) -> List[GeneratedSystem]:
        """Generate data for multiple system schemas with cross-schema dependencies.

        Args:
            schemas: List of system schemas to generate

        Returns:
            List of GeneratedSystem objects in dependency order

        Raises:
            GenerationError: If generation fails or dependencies cannot be resolved
        """
        try:
            if not self.link_resolver:
                # Without link resolver, generate each schema independently
                return [self.generate_system(schema) for schema in schemas]

            # Validate all links across all schemas
            link_errors = self.link_resolver.validate_all_links(schemas)
            if link_errors:
                raise GenerationError(
                    f"Link validation failed across schemas:\n"
                    + "\n".join(f"  - {error}" for error in link_errors)
                )

            # Build dependency graph across all schemas
            dependency_graph = self.link_resolver.build_dependency_graph(schemas)
            generation_order = dependency_graph.get_generation_order()

            # Create schema lookup
            schema_lookup = {schema.name: schema for schema in schemas}

            # Track generated systems
            generated_systems = {}

            # Generate entities in dependency order
            for entity_key in generation_order:
                schema_name, entity_name = entity_key.split(".", 1)

                if schema_name not in schema_lookup:
                    continue  # Skip entities not in our schema list

                schema = schema_lookup[schema_name]

                if entity_name not in schema.entities:
                    continue  # Skip entities not in this schema

                # Initialize generated system if not exists
                if schema_name not in generated_systems:
                    generated_systems[schema_name] = GeneratedSystem(
                        schema=schema, entities={}, metadata=None
                    )

                # Generate entity data
                entity_config = schema.entities[entity_name]
                entity_data = self.generate_entity(entity_config)

                # Store in generated system
                generated_systems[schema_name].entities[entity_name] = entity_data

                # Register with link resolver
                self.link_resolver.register_entity(
                    schema_name, entity_name, entity_data
                )

            # Create metadata for each generated system
            result_systems = []
            for schema in schemas:
                if schema.name in generated_systems:
                    generated_system = generated_systems[schema.name]

                    # Calculate metadata
                    total_records = sum(
                        len(data) for data in generated_system.entities.values()
                    )
                    entity_counts = {
                        name: len(data)
                        for name, data in generated_system.entities.items()
                    }

                    generated_system.metadata = GenerationMetadata(
                        generated_at=datetime.now(),
                        seed_used=schema.seed
                        or getattr(self.mimesis_engine, "seed", 42),
                        total_records=total_records,
                        entity_counts=entity_counts,
                    )

                    result_systems.append(generated_system)
                else:
                    # Create empty system for schemas with no entities
                    result_systems.append(
                        GeneratedSystem(
                            schema=schema,
                            entities={},
                            metadata=GenerationMetadata(
                                generated_at=datetime.now(),
                                seed_used=schema.seed
                                or getattr(self.mimesis_engine, "seed", 42),
                                total_records=0,
                                entity_counts={},
                            ),
                        )
                    )

            return result_systems

        except Exception as e:
            raise GenerationError(
                f"Failed to generate multiple systems: {str(e)}"
            ) from e

    def generate_entity(self, entity_config: EntityConfig) -> List[Dict[str, Any]]:
        """Generate data for a single entity."""
        try:
            entity_data = []

            # Generate the specified number of records
            for _ in range(entity_config.count):
                record = {}

                # Generate each attribute
                for attr_name, attr_config in entity_config.attributes.items():
                    value = self.mimesis_engine.generate_value(attr_config)

                    # Resolve links if link resolver is available and value is None (link placeholder)
                    if value is None and attr_config.link_to and self.link_resolver:
                        try:
                            value = self.link_resolver.resolve_link(attr_config.link_to)
                        except Exception as e:
                            if attr_config.required:
                                raise GenerationError(
                                    f"Failed to resolve required link '{attr_config.link_to}' "
                                    f"for attribute '{attr_name}': {str(e)}"
                                ) from e
                            # For non-required links, keep as None

                    # Validate required attributes after link resolution
                    if attr_config.required and self._is_empty_value(value):
                        raise GenerationError(
                            f"Required attribute '{attr_name}' in entity '{entity_config.name}' "
                            f"generated empty value: {value}"
                        )

                    record[attr_name] = value

                entity_data.append(record)

            return entity_data

        except Exception as e:
            raise GenerationError(
                f"Failed to generate entity '{entity_config.name}': {str(e)}"
            ) from e

    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is considered empty for required field validation."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
