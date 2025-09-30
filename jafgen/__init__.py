"""A synthetic data generator CLI for a fictional Jaffle Shop."""

# Schema-driven components
from .generation.interfaces import DataGenerator, LinkResolver, MimesisEngine
from .generation.models import DependencyGraph, GeneratedSystem, GenerationMetadata
from .output.interfaces import OutputWriter
from .schema.interfaces import SchemaLoader
from .schema.models import (
    AttributeConfig,
    EntityConfig,
    OutputConfig,
    SystemSchema,
    ValidationError,
    ValidationResult,
    ValidationWarning,
)

__all__ = [
    # Schema models
    "AttributeConfig",
    "EntityConfig",
    "OutputConfig",
    "SystemSchema",
    "ValidationError",
    "ValidationResult",
    "ValidationWarning",
    # Interfaces
    "SchemaLoader",
    "DataGenerator",
    "LinkResolver",
    "MimesisEngine",
    "OutputWriter",
    # Generation models
    "DependencyGraph",
    "GeneratedSystem",
    "GenerationMetadata",
]
