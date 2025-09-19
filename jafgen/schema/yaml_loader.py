"""YAML-based schema loader implementation."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interfaces import SchemaLoader
from .models import (
    SystemSchema, EntityConfig, AttributeConfig, OutputConfig,
    ValidationResult, ValidationError, ValidationWarning
)
from .exceptions import SchemaLoadError, SchemaValidationError


class YAMLSchemaLoader(SchemaLoader):
    """YAML-based implementation of SchemaLoader."""
    
    def discover_schemas(self, schema_dir: Path) -> List[Path]:
        """Discover YAML schema files in the given directory."""
        if not schema_dir.exists():
            return []
        
        if not schema_dir.is_dir():
            raise SchemaLoadError(f"Schema path {schema_dir} is not a directory")
        
        # Find all .yaml and .yml files
        yaml_files = []
        for pattern in ["*.yaml", "*.yml"]:
            yaml_files.extend(schema_dir.glob(pattern))
        
        return sorted(yaml_files)
    
    def load_schema(self, schema_path: Path) -> SystemSchema:
        """Load a schema from a YAML file."""
        try:
            with open(schema_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise SchemaLoadError(f"Invalid YAML syntax in {schema_path}: {e}")
        except FileNotFoundError:
            raise SchemaLoadError(f"Schema file not found: {schema_path}")
        except Exception as e:
            raise SchemaLoadError(f"Error reading schema file {schema_path}: {e}")
        
        if not isinstance(data, dict):
            raise SchemaLoadError(f"Schema file {schema_path} must contain a YAML object")
        
        return self._parse_schema_data(data, schema_path)
    
    def validate_schema(self, schema: SystemSchema) -> ValidationResult:
        """Validate a loaded schema for semantic correctness."""
        errors = []
        warnings = []
        
        # Validate system-level configuration
        if not schema.name:
            errors.append(ValidationError(
                type="missing_field",
                message="System name is required",
                location="system.name"
            ))
        
        if not schema.version:
            errors.append(ValidationError(
                type="missing_field", 
                message="System version is required",
                location="system.version"
            ))
        
        # Validate entities
        if not schema.entities:
            warnings.append(ValidationWarning(
                type="empty_entities",
                message="No entities defined in schema",
                location="entities"
            ))
        
        for entity_name, entity_config in schema.entities.items():
            self._validate_entity(entity_name, entity_config, errors, warnings)
        
        # Validate cross-entity links
        self._validate_links(schema, errors, warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _parse_schema_data(self, data: Dict[str, Any], schema_path: Path) -> SystemSchema:
        """Parse raw YAML data into SystemSchema object."""
        try:
            # Parse system configuration
            system_data = data.get('system', {})
            if not isinstance(system_data, dict):
                raise SchemaLoadError("'system' section must be an object")
            
            name = system_data.get('name', '')
            version = system_data.get('version', '')
            seed = system_data.get('seed')
            
            # Parse output configuration
            output_data = system_data.get('output', {})
            if not isinstance(output_data, dict):
                raise SchemaLoadError("'output' section must be an object")
            
            output_config = OutputConfig(
                format=output_data.get('format', ['csv']),
                path=output_data.get('path', './output')
            )
            
            # Parse entities
            entities_data = data.get('entities', {})
            if not isinstance(entities_data, dict):
                raise SchemaLoadError("'entities' section must be an object")
            
            entities = {}
            for entity_name, entity_data in entities_data.items():
                entities[entity_name] = self._parse_entity(entity_name, entity_data)
            
            return SystemSchema(
                name=name,
                version=version,
                seed=seed,
                output=output_config,
                entities=entities
            )
            
        except Exception as e:
            if isinstance(e, SchemaLoadError):
                raise
            raise SchemaLoadError(f"Error parsing schema {schema_path}: {e}")
    
    def _parse_entity(self, entity_name: str, entity_data: Dict[str, Any]) -> EntityConfig:
        """Parse entity configuration from YAML data."""
        if not isinstance(entity_data, dict):
            raise SchemaLoadError(f"Entity '{entity_name}' must be an object")
        
        count = entity_data.get('count', 0)
        if not isinstance(count, int) or count < 0:
            raise SchemaLoadError(f"Entity '{entity_name}' count must be a non-negative integer")
        
        attributes_data = entity_data.get('attributes', {})
        if not isinstance(attributes_data, dict):
            raise SchemaLoadError(f"Entity '{entity_name}' attributes must be an object")
        
        attributes = {}
        for attr_name, attr_data in attributes_data.items():
            attributes[attr_name] = self._parse_attribute(entity_name, attr_name, attr_data)
        
        return EntityConfig(
            name=entity_name,
            count=count,
            attributes=attributes
        )
    
    def _parse_attribute(self, entity_name: str, attr_name: str, attr_data: Dict[str, Any]) -> AttributeConfig:
        """Parse attribute configuration from YAML data."""
        if not isinstance(attr_data, dict):
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' must be an object")
        
        attr_type = attr_data.get('type', '')
        if not attr_type:
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' must have a type")
        
        unique = attr_data.get('unique', False)
        required = attr_data.get('required', True)
        link_to = attr_data.get('link_to')
        constraints = attr_data.get('constraints', {})
        
        if not isinstance(unique, bool):
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' unique must be boolean")
        
        if not isinstance(required, bool):
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' required must be boolean")
        
        if link_to is not None and not isinstance(link_to, str):
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' link_to must be a string")
        
        if not isinstance(constraints, dict):
            raise SchemaLoadError(f"Attribute '{entity_name}.{attr_name}' constraints must be an object")
        
        return AttributeConfig(
            type=attr_type,
            unique=unique,
            required=required,
            link_to=link_to,
            constraints=constraints
        )
    
    def _validate_entity(self, entity_name: str, entity_config: EntityConfig, 
                        errors: List[ValidationError], warnings: List[ValidationWarning]) -> None:
        """Validate a single entity configuration."""
        if entity_config.count <= 0:
            errors.append(ValidationError(
                type="invalid_count",
                message=f"Entity '{entity_name}' count must be greater than 0",
                location=f"entities.{entity_name}.count"
            ))
        
        if not entity_config.attributes:
            warnings.append(ValidationWarning(
                type="empty_attributes",
                message=f"Entity '{entity_name}' has no attributes defined",
                location=f"entities.{entity_name}.attributes"
            ))
        
        # Validate attributes
        for attr_name, attr_config in entity_config.attributes.items():
            self._validate_attribute(entity_name, attr_name, attr_config, errors, warnings)
    
    def _validate_attribute(self, entity_name: str, attr_name: str, attr_config: AttributeConfig,
                           errors: List[ValidationError], warnings: List[ValidationWarning]) -> None:
        """Validate a single attribute configuration."""
        # Check for valid attribute types (basic validation)
        valid_types = {
            'uuid', 'person.full_name', 'person.email', 'person.first_name', 'person.last_name',
            'datetime.datetime', 'datetime.date', 'datetime.time', 'numeric.decimal', 'numeric.integer',
            'text.word', 'text.sentence', 'text.paragraph', 'address.address', 'address.city',
            'address.state', 'address.country', 'internet.url', 'internet.domain_name',
            'finance.currency_code', 'link'
        }
        
        if attr_config.type not in valid_types:
            warnings.append(ValidationWarning(
                type="unknown_type",
                message=f"Unknown attribute type '{attr_config.type}' for {entity_name}.{attr_name}",
                location=f"entities.{entity_name}.attributes.{attr_name}.type",
            ))
        
        # Validate link_to format if present
        if attr_config.link_to:
            if attr_config.type != 'link':
                warnings.append(ValidationWarning(
                    type="link_type_mismatch",
                    message=f"Attribute {entity_name}.{attr_name} has link_to but type is not 'link'",
                    location=f"entities.{entity_name}.attributes.{attr_name}"
                ))
            
            # Basic link_to format validation (schema.entity.attribute)
            parts = attr_config.link_to.split('.')
            if len(parts) != 3:
                errors.append(ValidationError(
                    type="invalid_link_format",
                    message=f"Invalid link_to format '{attr_config.link_to}' for {entity_name}.{attr_name}. Expected format: 'schema.entity.attribute'",
                    location=f"entities.{entity_name}.attributes.{attr_name}.link_to",
                    suggestion="Use format: 'schema.entity.attribute'"
                ))
    
    def _validate_links(self, schema: SystemSchema, errors: List[ValidationError], 
                       warnings: List[ValidationWarning]) -> None:
        """Validate cross-entity links within the schema."""
        # Build a map of available entities and attributes
        available_targets = {}
        for entity_name, entity_config in schema.entities.items():
            for attr_name in entity_config.attributes.keys():
                target_key = f"{schema.name}.{entity_name}.{attr_name}"
                available_targets[target_key] = (entity_name, attr_name)
        
        # Check all link_to references
        for entity_name, entity_config in schema.entities.items():
            for attr_name, attr_config in entity_config.attributes.items():
                if attr_config.link_to:
                    if attr_config.link_to not in available_targets:
                        # Check if it's a reference to another schema (external link)
                        parts = attr_config.link_to.split('.')
                        if len(parts) == 3 and parts[0] != schema.name:
                            warnings.append(ValidationWarning(
                                type="external_link",
                                message=f"External link '{attr_config.link_to}' in {entity_name}.{attr_name} cannot be validated",
                                location=f"entities.{entity_name}.attributes.{attr_name}.link_to"
                            ))
                        else:
                            errors.append(ValidationError(
                                type="broken_link",
                                message=f"Link target '{attr_config.link_to}' not found for {entity_name}.{attr_name}",
                                location=f"entities.{entity_name}.attributes.{attr_name}.link_to",
                                suggestion=f"Available targets: {', '.join(sorted(available_targets.keys()))}"
                            ))