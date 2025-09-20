"""Concrete implementation of DataGenerator for entity creation."""

from datetime import datetime
from typing import Any, Dict, List

from .exceptions import GenerationError
from .interfaces import DataGenerator as DataGeneratorInterface, LinkResolver, MimesisEngine
from .models import GeneratedSystem, GenerationMetadata
from ..schema.models import EntityConfig, SystemSchema


class DataGenerator(DataGeneratorInterface):
    """Concrete implementation of data generation for entities."""
    
    def __init__(self, mimesis_engine: MimesisEngine, link_resolver: LinkResolver = None):
        """Initialize the data generator with required engines."""
        self.mimesis_engine = mimesis_engine
        self.link_resolver = link_resolver
    
    def generate_system(self, schema: SystemSchema) -> GeneratedSystem:
        """Generate data for an entire system schema."""
        try:
            entities = {}
            total_records = 0
            entity_counts = {}
            
            # Generate entities in dependency order if link resolver is available
            if self.link_resolver:
                # Build dependency graph and get generation order
                dependency_graph = self.link_resolver.build_dependency_graph([schema])
                generation_order = dependency_graph.get_generation_order()
                
                # Filter to only include entities from this schema
                schema_entities = [name for name in generation_order if name in schema.entities]
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
                        self.link_resolver.register_entity(schema.name, entity_name, entity_data)
            
            # Create metadata
            metadata = GenerationMetadata(
                generated_at=datetime.now(),
                seed_used=schema.seed or self.mimesis_engine.seed,
                total_records=total_records,
                entity_counts=entity_counts
            )
            
            return GeneratedSystem(
                schema=schema,
                entities=entities,
                metadata=metadata
            )
            
        except Exception as e:
            raise GenerationError(f"Failed to generate system '{schema.name}': {str(e)}") from e
    
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