"""Data models for the generation process."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from ..schema.models import SystemSchema


@dataclass
class GenerationMetadata:
    """Metadata about a data generation run."""
    
    generated_at: datetime
    seed_used: int
    total_records: int
    entity_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class GeneratedSystem:
    """Result of generating data for a complete system."""
    
    schema: SystemSchema
    entities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    metadata: GenerationMetadata = None


@dataclass
class DependencyGraph:
    """Represents dependencies between entities."""
    
    nodes: List[str] = field(default_factory=list)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_dependency(self, dependent: str, dependency: str) -> None:
        """Add a dependency relationship."""
        if dependent not in self.nodes:
            self.nodes.append(dependent)
        if dependency not in self.nodes:
            self.nodes.append(dependency)
        
        if dependent not in self.edges:
            self.edges[dependent] = []
        self.edges[dependent].append(dependency)
    
    def get_generation_order(self) -> List[str]:
        """Get the order in which entities should be generated (topological sort)."""
        # Simple topological sort implementation
        in_degree = {node: 0 for node in self.nodes}
        
        # Calculate in-degrees
        for node in self.edges:
            for dependency in self.edges[node]:
                in_degree[dependency] += 1
        
        # Find nodes with no incoming edges
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Remove this node and update in-degrees
            if node in self.edges:
                for dependency in self.edges[node]:
                    in_degree[dependency] -= 1
                    if in_degree[dependency] == 0:
                        queue.append(dependency)
        
        if len(result) != len(self.nodes):
            raise ValueError("Circular dependency detected in entity relationships")
        
        return result