"""Schema management components for jafgen."""

from .discovery import SchemaDiscoveryEngine
from .exceptions import (
    CircularDependencyError,
    SchemaError,
    SchemaLoadError,
    SchemaValidationError,
)
from .interfaces import SchemaLoader
from .models import (
    AttributeConfig,
    EntityConfig,
    OutputConfig,
    SystemSchema,
    ValidationError,
    ValidationResult,
    ValidationWarning,
)
from .yaml_loader import YAMLSchemaLoader

__all__ = [
    "SystemSchema",
    "EntityConfig",
    "AttributeConfig",
    "OutputConfig",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "SchemaLoader",
    "YAMLSchemaLoader",
    "SchemaDiscoveryEngine",
    "SchemaError",
    "SchemaValidationError",
    "SchemaLoadError",
    "CircularDependencyError",
]
