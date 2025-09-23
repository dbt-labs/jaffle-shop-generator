"""Link resolution implementation for entity relationships."""

import random
from typing import Any, Dict, List, Set

from .exceptions import LinkResolutionError
from .interfaces import LinkResolver as LinkResolverInterface
from .models import DependencyGraph
from ..schema.models import SystemSchema


class LinkResolver(LinkResolverInterface):
    """Concrete implementation of link resolution for entity relationships."""
    
    def __init__(self):
        """Initialize the link resolver."""
        self._entity_data: Dict[str, Dict[str, List[Dict]]] = {}
        self._dependency_graph: DependencyGraph = None
    
    def register_entity(self, schema_name: str, entity_name: str, data: List[Dict]) -> None:
        """Register generated entity data for link resolution.
        
        Args:
            schema_name: Name of the schema containing the entity
            entity_name: Name of the entity
            data: List of generated entity records
        """
        if schema_name not in self._entity_data:
            self._entity_data[schema_name] = {}
        
        self._entity_data[schema_name][entity_name] = data
    
    def resolve_link(self, link_spec: str) -> Any:
        """Resolve a link specification to an actual value.
        
        Args:
            link_spec: Link specification in format "schema.entity.attribute"
            
        Returns:
            A random value from the specified entity's attribute
            
        Raises:
            LinkResolutionError: If the link cannot be resolved
        """
        try:
            parts = link_spec.split('.')
            if len(parts) != 3:
                raise LinkResolutionError(
                    f"Invalid link specification format: {link_spec}. "
                    "Expected format: 'schema.entity.attribute'"
                )
            
            schema_name, entity_name, attribute_name = parts
            
            # Check if schema exists
            if schema_name not in self._entity_data:
                raise LinkResolutionError(
                    f"Schema '{schema_name}' not found in registered entities"
                )
            
            # Check if entity exists
            if entity_name not in self._entity_data[schema_name]:
                raise LinkResolutionError(
                    f"Entity '{entity_name}' not found in schema '{schema_name}'"
                )
            
            entity_data = self._entity_data[schema_name][entity_name]
            
            # Check if entity has data
            if not entity_data:
                raise LinkResolutionError(
                    f"No data available for entity '{schema_name}.{entity_name}'"
                )
            
            # Check if attribute exists in the first record (assuming all records have same structure)
            if attribute_name not in entity_data[0]:
                raise LinkResolutionError(
                    f"Attribute '{attribute_name}' not found in entity '{schema_name}.{entity_name}'"
                )
            
            # Return a random value from the specified attribute
            available_values = [record[attribute_name] for record in entity_data]
            return random.choice(available_values)
            
        except Exception as e:
            if isinstance(e, LinkResolutionError):
                raise
            raise LinkResolutionError(f"Failed to resolve link '{link_spec}': {str(e)}")
    
    def build_dependency_graph(self, schemas: List[SystemSchema]) -> DependencyGraph:
        """Build dependency graph from schemas.
        
        Args:
            schemas: List of system schemas to analyze
            
        Returns:
            DependencyGraph with entity dependencies
            
        Raises:
            LinkResolutionError: If circular dependencies are detected
        """
        graph = DependencyGraph()
        
        # First pass: collect all entities
        all_entities = set()
        for schema in schemas:
            for entity_name in schema.entities:
                entity_key = f"{schema.name}.{entity_name}"
                all_entities.add(entity_key)
        
        # Second pass: build dependencies
        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                entity_key = f"{schema.name}.{entity_name}"
                
                # Add entity to graph
                if entity_key not in graph.nodes:
                    graph.nodes.append(entity_key)
                
                # Check each attribute for links
                for attr_name, attr_config in entity_config.attributes.items():
                    if attr_config.link_to:
                        # Parse the link specification
                        link_parts = attr_config.link_to.split('.')
                        if len(link_parts) != 3:
                            raise LinkResolutionError(
                                f"Invalid link specification in {entity_key}.{attr_name}: "
                                f"{attr_config.link_to}. Expected format: 'schema.entity.attribute'"
                            )
                        
                        target_schema, target_entity, target_attribute = link_parts
                        target_entity_key = f"{target_schema}.{target_entity}"
                        
                        # Validate that target entity exists
                        if target_entity_key not in all_entities:
                            raise LinkResolutionError(
                                f"Link target '{target_entity_key}' not found in any schema. "
                                f"Referenced by {entity_key}.{attr_name}"
                            )
                        
                        # Add dependency: entity_key depends on target_entity_key
                        graph.add_dependency(entity_key, target_entity_key)
        
        # Validate no circular dependencies by attempting topological sort
        try:
            graph.get_generation_order()
        except ValueError as e:
            raise LinkResolutionError(f"Circular dependency detected: {str(e)}")
        
        self._dependency_graph = graph
        return graph
    
    def get_generation_order(self) -> List[str]:
        """Get the order in which entities should be generated.
        
        Returns:
            List of entity keys in generation order
            
        Raises:
            LinkResolutionError: If dependency graph hasn't been built
        """
        if self._dependency_graph is None:
            raise LinkResolutionError(
                "Dependency graph not built. Call build_dependency_graph() first."
            )
        
        return self._dependency_graph.get_generation_order()
    
    def validate_all_links(self, schemas: List[SystemSchema]) -> List[str]:
        """Validate that all link specifications in schemas are valid.
        
        Args:
            schemas: List of schemas to validate
            
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        
        # Collect all available entities and their attributes
        available_entities = {}
        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                entity_key = f"{schema.name}.{entity_name}"
                available_entities[entity_key] = set(entity_config.attributes.keys())
        
        # Validate each link
        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                entity_key = f"{schema.name}.{entity_name}"
                
                for attr_name, attr_config in entity_config.attributes.items():
                    if attr_config.link_to:
                        link_parts = attr_config.link_to.split('.')
                        
                        # Check format
                        if len(link_parts) != 3:
                            errors.append(
                                f"Invalid link format in {entity_key}.{attr_name}: "
                                f"{attr_config.link_to}. Expected 'schema.entity.attribute'"
                            )
                            continue
                        
                        target_schema, target_entity, target_attribute = link_parts
                        target_entity_key = f"{target_schema}.{target_entity}"
                        
                        # Check if target entity exists
                        if target_entity_key not in available_entities:
                            errors.append(
                                f"Link target entity '{target_entity_key}' not found. "
                                f"Referenced by {entity_key}.{attr_name}"
                            )
                            continue
                        
                        # Check if target attribute exists
                        if target_attribute not in available_entities[target_entity_key]:
                            errors.append(
                                f"Link target attribute '{target_attribute}' not found in "
                                f"entity '{target_entity_key}'. Referenced by {entity_key}.{attr_name}"
                            )
        
        return errors
    
    def clear_registered_data(self) -> None:
        """Clear all registered entity data."""
        self._entity_data.clear()
        self._dependency_graph = None