"""Schema discovery and validation engine."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .interfaces import SchemaLoader
from .models import SystemSchema, ValidationResult, ValidationError, ValidationWarning
from .yaml_loader import YAMLSchemaLoader
from .exceptions import SchemaLoadError, CircularDependencyError


class SchemaDiscoveryEngine:
    """Engine for discovering and validating multiple schemas."""
    
    def __init__(self, loader: Optional[SchemaLoader] = None):
        """Initialize the discovery engine with a schema loader."""
        self.loader = loader or YAMLSchemaLoader()
    
    def discover_and_load_schemas(self, schema_dir: Path) -> Tuple[List[SystemSchema], ValidationResult]:
        """Discover and load all schemas from a directory."""
        schema_paths = self.loader.discover_schemas(schema_dir)
        
        if not schema_paths:
            return [], ValidationResult(
                is_valid=True,
                warnings=[ValidationWarning(
                    type="no_schemas_found",
                    message=f"No schema files found in directory: {schema_dir}",
                    location=str(schema_dir)
                )]
            )
        
        schemas = []
        load_errors = []
        
        # Load each schema
        for schema_path in schema_paths:
            try:
                schema = self.loader.load_schema(schema_path)
                schemas.append(schema)
            except SchemaLoadError as e:
                load_errors.append(ValidationError(
                    type="schema_load_error",
                    message=f"Failed to load schema from {schema_path}: {e}",
                    location=str(schema_path)
                ))
        
        # If we couldn't load any schemas, return early
        if not schemas:
            return [], ValidationResult(
                is_valid=False,
                errors=load_errors
            )
        
        # Validate all schemas together
        if hasattr(self.loader, 'validate_multiple_schemas'):
            validation_result = self.loader.validate_multiple_schemas(schemas)
        else:
            # Fallback to individual validation
            validation_result = self._validate_schemas_individually(schemas)
        
        # Add any load errors to the validation result
        validation_result.errors.extend(load_errors)
        validation_result.is_valid = validation_result.is_valid and len(load_errors) == 0
        
        return schemas, validation_result
    
    def _validate_schemas_individually(self, schemas: List[SystemSchema]) -> ValidationResult:
        """Validate schemas individually when multi-schema validation is not available."""
        all_errors = []
        all_warnings = []
        
        for schema in schemas:
            result = self.loader.validate_schema(schema)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def get_schema_summary(self, schemas: List[SystemSchema]) -> Dict[str, Dict[str, any]]:
        """Get a summary of discovered schemas."""
        summary = {}
        
        for schema in schemas:
            entity_count = len(schema.entities)
            total_attributes = sum(len(entity.attributes) for entity in schema.entities.values())
            total_records = sum(entity.count for entity in schema.entities.values())
            
            # Count link attributes
            link_count = 0
            for entity in schema.entities.values():
                for attr in entity.attributes.values():
                    if attr.link_to:
                        link_count += 1
            
            summary[schema.name] = {
                'version': schema.version,
                'seed': schema.seed,
                'output_formats': schema.output.format,
                'output_path': schema.output.path,
                'entity_count': entity_count,
                'total_attributes': total_attributes,
                'total_records': total_records,
                'link_count': link_count,
                'entities': {
                    entity_name: {
                        'count': entity_config.count,
                        'attributes': len(entity_config.attributes),
                        'links': sum(1 for attr in entity_config.attributes.values() if attr.link_to)
                    }
                    for entity_name, entity_config in schema.entities.items()
                }
            }
        
        return summary
    
    def validate_schema_compatibility(self, schemas: List[SystemSchema]) -> ValidationResult:
        """Validate that schemas are compatible with each other."""
        errors = []
        warnings = []
        
        # Check for duplicate schema names
        schema_names = [schema.name for schema in schemas]
        duplicates = set([name for name in schema_names if schema_names.count(name) > 1])
        
        for duplicate in duplicates:
            errors.append(ValidationError(
                type="duplicate_schema_name",
                message=f"Multiple schemas found with name '{duplicate}'",
                location="schema.name",
                suggestion="Ensure each schema has a unique name"
            ))
        
        # Check for version conflicts
        schema_versions = {}
        for schema in schemas:
            if schema.name in schema_versions:
                if schema_versions[schema.name] != schema.version:
                    warnings.append(ValidationWarning(
                        type="version_mismatch",
                        message=f"Schema '{schema.name}' has multiple versions: {schema_versions[schema.name]}, {schema.version}",
                        location=f"{schema.name}.version"
                    ))
            else:
                schema_versions[schema.name] = schema.version
        
        # Check for conflicting output paths
        output_paths = {}
        for schema in schemas:
            path = schema.output.path
            if path in output_paths:
                warnings.append(ValidationWarning(
                    type="conflicting_output_path",
                    message=f"Multiple schemas writing to same output path: {path}",
                    location="output.path",
                    suggestion="Consider using different output paths for each schema"
                ))
            else:
                output_paths[path] = schema.name
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def build_dependency_graph(self, schemas: List[SystemSchema]) -> Dict[str, List[str]]:
        """Build a dependency graph showing which entities depend on others."""
        dependency_graph = {}
        
        # Build global entity map
        global_entities = {}
        for schema in schemas:
            for entity_name in schema.entities.keys():
                full_entity_name = f"{schema.name}.{entity_name}"
                global_entities[full_entity_name] = schema.name
        
        # Build dependencies
        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                full_entity_name = f"{schema.name}.{entity_name}"
                dependencies = []
                
                for attr_config in entity_config.attributes.values():
                    if attr_config.link_to:
                        # Extract target entity from link_to
                        parts = attr_config.link_to.split('.')
                        if len(parts) >= 2:
                            target_entity = f"{parts[0]}.{parts[1]}"
                            if target_entity in global_entities and target_entity != full_entity_name:
                                dependencies.append(target_entity)
                
                dependency_graph[full_entity_name] = list(set(dependencies))
        
        return dependency_graph
    
    def get_generation_order(self, schemas: List[SystemSchema]) -> List[str]:
        """Get the order in which entities should be generated to satisfy dependencies."""
        dependency_graph = self.build_dependency_graph(schemas)
        
        # Topological sort using Kahn's algorithm
        # in_degree[entity] = number of entities that must be generated before this entity
        in_degree = {entity: 0 for entity in dependency_graph}
        
        # Calculate in-degrees: for each dependency relationship A -> B, B has in_degree + 1
        for entity in dependency_graph:
            for dependency in dependency_graph[entity]:
                if dependency in in_degree:
                    in_degree[entity] += 1
        
        # Start with entities that have no dependencies (in_degree == 0)
        queue = [entity for entity, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Take an entity with no remaining dependencies
            entity = queue.pop(0)
            result.append(entity)
            
            # Find all entities that depend on this entity and reduce their in_degree
            for other_entity in dependency_graph:
                if entity in dependency_graph[other_entity]:
                    in_degree[other_entity] -= 1
                    if in_degree[other_entity] == 0:
                        queue.append(other_entity)
        
        # Check for circular dependencies
        if len(result) != len(dependency_graph):
            remaining = [entity for entity in dependency_graph if entity not in result]
            raise CircularDependencyError(f"Circular dependencies detected among entities: {remaining}")
        
        return result