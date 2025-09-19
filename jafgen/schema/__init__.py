"""Schema management components for jafgen."""

from .models import (
    SystemSchema, EntityConfig, AttributeConfig, OutputConfig,
    ValidationResult, ValidationError, ValidationWarning
)
from .interfaces import SchemaLoader
from .yaml_loader import YAMLSchemaLoader
from .discovery import SchemaDiscoveryEngine
from .exceptions import (
    SchemaError, SchemaValidationError, SchemaLoadError, CircularDependencyError
)

__all__ = [
    'SystemSchema', 'EntityConfig', 'AttributeConfig', 'OutputConfig',
    'ValidationResult', 'ValidationError', 'ValidationWarning',
    'SchemaLoader', 'YAMLSchemaLoader', 'SchemaDiscoveryEngine',
    'SchemaError', 'SchemaValidationError', 'SchemaLoadError', 'CircularDependencyError'
]