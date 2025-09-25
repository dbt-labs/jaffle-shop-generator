"""CSV output writer implementation."""

import csv
from pathlib import Path
from typing import Any, Dict, List

from .interfaces import OutputWriter


class CSVWriter(OutputWriter):
    """CSV output writer that handles proper formatting and encoding."""
    
    def __init__(self, encoding: str = "utf-8"):
        """Initialize CSV writer with specified encoding.
        
        Args:
            encoding: Character encoding for output files (default: utf-8)
        """
        self.encoding = encoding
    
    def write(self, data: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
        """Write generated data to CSV files.
        
        Args:
            data: Dictionary mapping entity names to lists of records
            output_path: Base directory path for output files
            
        Raises:
            OSError: If directory creation or file writing fails
            ValueError: If data contains unsupported types for CSV
        """
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        for entity_name, records in data.items():
            if not records:
                continue
                
            csv_file_path = output_path / f"{entity_name}.csv"
            
            # Get fieldnames from first record
            fieldnames = list(records[0].keys())
            
            # Always overwrite existing files for idempotency
            with open(csv_file_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in records:
                    # Convert any non-string values to strings for CSV compatibility
                    csv_record = {}
                    for key, value in record.items():
                        if value is None:
                            csv_record[key] = ""
                        elif isinstance(value, (list, dict)):
                            # Convert complex types to string representation
                            csv_record[key] = str(value)
                        else:
                            csv_record[key] = value
                    
                    writer.writerow(csv_record)