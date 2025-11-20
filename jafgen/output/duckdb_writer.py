"""DuckDB output writer implementation."""

from pathlib import Path
from typing import Any, Dict, List

import duckdb
import pandas as pd

from .interfaces import OutputWriter


class DuckDBWriter(OutputWriter):
    """DuckDB output writer for direct database file creation."""

    def __init__(self, database_name: str = "generated_data.duckdb"):
        """Initialize DuckDB writer with database configuration.

        Args:
        ----
            database_name: Name of the DuckDB database file (default: generated_data.duckdb)

        """
        self.database_name = database_name

    def write(self, data: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
        """Write generated data to DuckDB database file.

        Args:
        ----
            data: Dictionary mapping entity names to lists of records
            output_path: Base directory path for output files

        Raises:
        ------
            OSError: If directory creation or database file creation fails
            duckdb.Error: If database operations fail

        """
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        db_file_path = output_path / self.database_name

        # Remove existing database file for idempotency
        if db_file_path.exists():
            db_file_path.unlink()

        # Connect to DuckDB database (creates new file)
        conn = duckdb.connect(str(db_file_path))

        try:
            for entity_name, records in data.items():
                if not records:
                    continue

                # Drop table if it exists (for idempotency)
                conn.execute(f"DROP TABLE IF EXISTS {entity_name}")

                # Create table from records
                if records:
                    # Prepare records for DuckDB insertion
                    prepared_records = [
                        self._prepare_record(record) for record in records
                    ]

                    # Convert to pandas DataFrame for DuckDB compatibility
                    df = pd.DataFrame(prepared_records)

                    # Use DuckDB's ability to create table from pandas DataFrame
                    conn.register(f"{entity_name}_data", df)
                    conn.execute(
                        f"CREATE TABLE {entity_name} AS SELECT * FROM {entity_name}_data"
                    )
                    conn.unregister(f"{entity_name}_data")

        finally:
            conn.close()

    def _prepare_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a record for DuckDB insertion.

        Args:
        ----
            record: Record dictionary to prepare

        Returns:
        -------
            Prepared record with DuckDB-compatible types

        """
        prepared: Dict[str, Any] = {}

        for key, value in record.items():
            if value is None:
                prepared[key] = None
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON strings
                import json

                prepared[key] = json.dumps(value)
            elif hasattr(value, "isoformat"):
                # Keep datetime objects as-is (DuckDB handles them well)
                prepared[key] = value
            else:
                prepared[key] = value

        return prepared
