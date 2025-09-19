"""Abstract interfaces for data generation."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set

from ..schema.models import AttributeConfig, EntityConfig, SystemSchema


class MimesisEngine(ABC):
    """Abstract base class for Mimesis-based data generation."""
    
    @abstractmethod
    def __init__(self, seed: int = None):
        """Initialize the engine with optional seed."""
        pass
    
    @abstractmethod
    def generate_value(self, attribute_config: AttributeConfig) -> Any:
        """Generate a single value based on attribute configuration."""
        pass
    
    @abstractmethod
    def ensure_unique(self, generator_func: Callable, seen_values: Set) -> Any:
        """Generate a unique value using the given generator function."""
        pass


class LinkResolver(ABC):
    """Abstract base class for resolving entity links."""
    
    @abstractmethod
    def register_entity(self, schema_name: str, entity_name: str, data: List[Dict]) -> None:
        """Register generated entity data for link resolution."""
        pass
    
    @abstractmethod
    def resolve_link(self, link_spec: str) -> Any:
        """Resolve a link specification to an actual value."""
        pass
    
    @abstractmethod
    def build_dependency_graph(self, schemas: List[SystemSchema]) -> "DependencyGraph":
        """Build dependency graph from schemas."""
        pass


class DataGenerator(ABC):
    """Abstract base class for data generation."""
    
    @abstractmethod
    def generate_system(self, schema: SystemSchema) -> "GeneratedSystem":
        """Generate data for an entire system schema."""
        pass
    
    @abstractmethod
    def generate_entity(self, entity_config: EntityConfig) -> List[Dict[str, Any]]:
        """Generate data for a single entity."""
        pass