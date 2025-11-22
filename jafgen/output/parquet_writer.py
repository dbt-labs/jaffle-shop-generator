"""Parquet output writer implementation."""

from pathlib import Path
from typing import Any, Dict, List

import pyarrow as pa
import pyarrow.parquet as pq

from .interfaces import OutputWriter


class ParquetWriter(OutputWriter):
    """Parquet output writer using PyArrow for efficient columnar storage."""

    def __init__(self, compression: str = "snappy"):
        """Initialize Parquet writer with compression options.

        Args:
        ----
            compression: Compression algorithm (default: snappy)
                        Options: snappy, gzip, brotli, lz4, zstd

        """
        self.compression = compression

    def write(self, data: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
        """Write generated data to Parquet files.

        Args:
        ----
            data: Dictionary mapping entity names to lists of records
            output_path: Base directory path for output files

        Raises:
        ------
            OSError: If directory creation or file writing fails
            ArrowInvalid: If data cannot be converted to Arrow format

        """
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        for entity_name, records in data.items():
            if not records:
                continue

            parquet_file_path = output_path / f"{entity_name}.parquet"

            # Convert records to PyArrow table
            try:
                # Convert list of dicts to PyArrow table
                table = pa.Table.from_pylist(records)

                # Write to Parquet file (overwrites existing file for idempotency)
                pq.write_table(table, parquet_file_path, compression=self.compression)

            except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
                # If direct conversion fails, try with schema inference by flattening all values to strings
                try:
                    flattened_records = [
                        self._flatten_record(record) for record in records
                    ]
                    
                    # Create a schema where all fields are strings
                    fields = [(key, pa.string()) for key in flattened_records[0].keys()]
                    schema = pa.schema(fields)

                    table = pa.Table.from_pylist(flattened_records, schema=schema)
                    pq.write_table(
                        table, parquet_file_path, compression=self.compression
                    )
                except Exception as inner_e:
                    raise ValueError(
                        f"Failed to convert data to Parquet format for entity '{entity_name}': {inner_e}"
                    ) from e

    def _flatten_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten a record by converting all values to strings."""
        flattened: Dict[str, Any] = {}
        for key, value in record.items():
            if value is None:
                flattened[key] = None
            elif isinstance(value, (list, dict)):
                import json
                flattened[key] = json.dumps(value)
            else:
                flattened[key] = str(value)
        return flattened