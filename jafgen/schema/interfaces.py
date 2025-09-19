"""Abstract interfaces for schema management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .models import SystemSchema, ValidationResult


class SchemaLoader(ABC):
    """Abstract base class for schema loading."""
    
    @abstractmethod
    def discover_schemas(self, schema_dir: Path) -> List[Path]:
        """Discover schema files in the given directory."""
        pass
    
    @abstractmethod
    def load_schema(self, schema_path: Path) -> SystemSchema:
        """Load a schema from the given path."""
        pass
    
    @abstractmethod
    def validate_schema(self, schema: SystemSchema) -> ValidationResult:
        """Validate a loaded schema."""
        pass