"""Data models for the generation process."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schema.models import SystemSchema


@dataclass
class GenerationMetadata:
    """Metadata about a data generation run."""
    
    generated_at: datetime
    seed_used: int
    total_records: int
    entity_counts: Dict[str, int] = field(default_factory=dict)
    schema_hash: Optional[str] = None
    output_formats: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            'generated_at': self.generated_at.isoformat(),
            'seed_used': self.seed_used,
            'total_records': self.total_records,
            'entity_counts': self.entity_counts,
            'schema_hash': self.schema_hash,
            'output_formats': self.output_formats,
            'output_path': self.output_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationMetadata':
        """Create metadata from dictionary."""
        return cls(
            generated_at=datetime.fromisoformat(data['generated_at']),
            seed_used=data['seed_used'],
            total_records=data['total_records'],
            entity_counts=data.get('entity_counts', {}),
            schema_hash=data.get('schema_hash'),
            output_formats=data.get('output_formats', []),
            output_path=data.get('output_path')
        )
    
    def save_to_file(self, output_path: Path) -> None:
        """Save metadata to a JSON file."""
        metadata_file = output_path / '.jafgen_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, output_path: Path) -> Optional['GenerationMetadata']:
        """Load metadata from a JSON file."""
        metadata_file = output_path / '.jafgen_metadata.json'
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def is_identical_generation(self, other: 'GenerationMetadata') -> bool:
        """Check if this metadata represents an identical generation to another."""
        return (
            self.seed_used == other.seed_used and
            self.schema_hash == other.schema_hash and
            self.total_records == other.total_records and
            self.entity_counts == other.entity_counts and
            self.output_formats == other.output_formats
        )


def calculate_schema_hash(schema: SystemSchema) -> str:
    """Calculate a hash of the schema for reproducibility tracking."""
    # Create a normalized representation of the schema for hashing
    schema_dict = {
        'name': schema.name,
        'version': schema.version,
        'seed': schema.seed,
        'output': {
            'format': sorted(schema.output.format) if isinstance(schema.output.format, list) else [schema.output.format],
            'path': schema.output.path
        },
        'entities': {}
    }
    
    # Add entities in sorted order for consistent hashing
    for entity_name in sorted(schema.entities.keys()):
        entity = schema.entities[entity_name]
        entity_dict = {
            'name': entity.name,
            'count': entity.count,
            'attributes': {}
        }
        
        # Add attributes in sorted order
        for attr_name in sorted(entity.attributes.keys()):
            attr = entity.attributes[attr_name]
            attr_dict = {
                'type': attr.type,
                'unique': attr.unique,
                'required': attr.required,
                'link_to': attr.link_to,
                'constraints': dict(sorted(attr.constraints.items())) if attr.constraints else {}
            }
            entity_dict['attributes'][attr_name] = attr_dict
        
        schema_dict['entities'][entity_name] = entity_dict
    
    # Convert to JSON string and hash
    schema_json = json.dumps(schema_dict, sort_keys=True)
    return hashlib.sha256(schema_json.encode('utf-8')).hexdigest()


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
        # In our edges dict: key depends on values in the list
        # So if edges["B"] = ["A"], it means B depends on A, so A should come first
        
        in_degree = {node: 0 for node in self.nodes}
        
        # Calculate in-degrees: count how many nodes depend on each node
        for dependent in self.edges:
            for dependency in self.edges[dependent]:
                in_degree[dependent] += 1
        
        # Find nodes with no incoming dependencies (no one depends on them)
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Remove this node and update in-degrees of nodes that depend on it
            for dependent in self.edges:
                if node in self.edges[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        if len(result) != len(self.nodes):
            raise ValueError("Circular dependency detected in entity relationships")
        
        return result