"""Data models for schema definitions."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AttributeConfig:
    """Configuration for a single entity attribute."""
    
    type: str  # mimesis provider type
    unique: bool = False
    required: bool = True
    link_to: Optional[str] = None  # "schema.entity.attribute"
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityConfig:
    """Configuration for an entity definition."""
    
    name: str
    count: int
    attributes: Dict[str, AttributeConfig]


@dataclass
class FormatConfig:
    """Configuration for a specific output format."""
    
    type: str  # Format type (csv, json, parquet, duckdb)
    options: Dict[str, Any] = field(default_factory=dict)  # Format-specific options
    filename_pattern: Optional[str] = None  # Custom filename pattern (e.g., "{entity_name}_data.{ext}")


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    
    format: List[str] = field(default_factory=lambda: ["csv"])
    path: str = "./output"
    formats: Dict[str, FormatConfig] = field(default_factory=dict)  # Advanced format configurations
    per_entity: Dict[str, 'EntityOutputConfig'] = field(default_factory=dict)  # Per-entity output overrides


@dataclass
class EntityOutputConfig:
    """Output configuration specific to an entity."""
    
    format: Optional[List[str]] = None  # Override formats for this entity
    path: Optional[str] = None  # Override path for this entity
    formats: Dict[str, FormatConfig] = field(default_factory=dict)  # Entity-specific format configs


@dataclass
class SystemSchema:
    """Complete schema definition for a system."""
    
    name: str
    version: str
    seed: Optional[int] = None
    output: OutputConfig = field(default_factory=OutputConfig)
    entities: Dict[str, EntityConfig] = field(default_factory=dict)


@dataclass
class ValidationError:
    """Represents a validation error in a schema."""
    
    type: str
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationWarning:
    """Represents a validation warning in a schema."""
    
    type: str
    message: str
    location: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of schema validation."""
    
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)