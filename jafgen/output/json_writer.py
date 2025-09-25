"""JSON output writer implementation."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from .interfaces import OutputWriter


class JSONWriter(OutputWriter):
    """JSON output writer with proper serialization handling."""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """Initialize JSON writer with formatting options.
        
        Args:
            indent: Number of spaces for indentation (default: 2)
            ensure_ascii: Whether to escape non-ASCII characters (default: False)
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
    
    def write(self, data: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
        """Write generated data to JSON files.
        
        Args:
            data: Dictionary mapping entity names to lists of records
            output_path: Base directory path for output files
            
        Raises:
            OSError: If directory creation or file writing fails
            TypeError: If data contains non-serializable types
        """
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        for entity_name, records in data.items():
            if not records:
                continue
                
            json_file_path = output_path / f"{entity_name}.json"
            
            # Convert records to JSON-serializable format
            serializable_records = [
                self._make_serializable(record) for record in records
            ]
            
            # Always overwrite existing files for idempotency
            with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(
                    serializable_records,
                    jsonfile,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii,
                    default=self._json_serializer
                )
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable representation of the object
        """
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return self._make_serializable(obj.__dict__)
        else:
            return obj
    
    def _json_serializer(self, obj: Any) -> Any:
        """Default JSON serializer for non-standard types.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable representation
            
        Raises:
            TypeError: If object is not serializable
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")