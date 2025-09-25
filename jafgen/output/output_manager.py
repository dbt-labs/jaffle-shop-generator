"""Output manager for idempotent file generation and directory management."""

import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import OutputError
from .interfaces import OutputWriter
from ..generation.models import GenerationMetadata, calculate_schema_hash
from ..schema.models import SystemSchema


class OutputManager:
    """Manages idempotent output generation with proper directory handling."""
    
    def __init__(self, output_writers: Dict[str, OutputWriter]):
        """Initialize output manager with available writers.
        
        Args:
            output_writers: Dictionary mapping format names to writer instances
        """
        self.output_writers = output_writers
    
    def prepare_output_directory(self, output_path: Path, force_recreate: bool = False) -> None:
        """Prepare output directory with proper permissions.
        
        Args:
            output_path: Path to the output directory
            force_recreate: Whether to recreate the directory if it exists
            
        Raises:
            OutputError: If directory creation or permission setting fails
        """
        try:
            if force_recreate and output_path.exists():
                # Remove existing directory and contents
                import shutil
                shutil.rmtree(output_path)
            
            # Create directory with parents if needed
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Set appropriate permissions (readable/writable by owner, readable by group/others)
            if os.name != 'nt':  # Unix-like systems
                output_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            
        except (OSError, PermissionError) as e:
            raise OutputError(f"Failed to prepare output directory '{output_path}': {e}") from e
    
    def write_system_data(
        self, 
        generated_system: 'GeneratedSystem', 
        base_output_path: Path,
        overwrite: bool = True
    ) -> GenerationMetadata:
        """Write system data with idempotent behavior.
        
        Args:
            generated_system: The generated system data to write
            base_output_path: Base output directory path
            overwrite: Whether to overwrite existing files (default: True for idempotency)
            
        Returns:
            GenerationMetadata: Metadata about the generation run
            
        Raises:
            OutputError: If writing fails or format is unsupported
        """
        schema = generated_system.schema
        
        # Determine output formats and path
        output_formats = schema.output.format if isinstance(schema.output.format, list) else [schema.output.format]
        schema_output_dir = base_output_path / schema.output.path if schema.output.path != "." else base_output_path
        
        # Prepare output directory
        self.prepare_output_directory(schema_output_dir, force_recreate=False)
        
        # Calculate schema hash for reproducibility tracking
        schema_hash = calculate_schema_hash(schema)
        
        # Create enhanced metadata
        metadata = GenerationMetadata(
            generated_at=generated_system.metadata.generated_at,
            seed_used=generated_system.metadata.seed_used,
            total_records=generated_system.metadata.total_records,
            entity_counts=generated_system.metadata.entity_counts,
            schema_hash=schema_hash,
            output_formats=output_formats,
            output_path=str(schema_output_dir)
        )
        
        # Check for existing metadata to verify idempotency
        existing_metadata = GenerationMetadata.load_from_file(schema_output_dir)
        if existing_metadata and existing_metadata.is_identical_generation(metadata):
            # Skip generation if identical run already exists and files are present
            if self._verify_output_files_exist(generated_system.entities, schema_output_dir, output_formats):
                return existing_metadata
        
        # Write data in each requested format
        written_formats = []
        for output_format in output_formats:
            if output_format not in self.output_writers:
                raise OutputError(f"Unsupported output format: {output_format}")
            
            try:
                # Remove existing files for this format if overwrite is True
                if overwrite:
                    self._remove_existing_files(generated_system.entities, schema_output_dir, output_format)
                
                # Write the data
                self.output_writers[output_format].write(generated_system.entities, schema_output_dir)
                written_formats.append(output_format)
                
            except Exception as e:
                raise OutputError(f"Failed to write {output_format} format for schema '{schema.name}': {e}") from e
        
        # Update metadata with actually written formats
        metadata.output_formats = written_formats
        
        # Save metadata for future idempotency checks
        metadata.save_to_file(schema_output_dir)
        
        return metadata
    
    def _verify_output_files_exist(
        self, 
        entities: Dict[str, List[Dict[str, Any]]], 
        output_path: Path, 
        formats: List[str]
    ) -> bool:
        """Verify that all expected output files exist.
        
        Args:
            entities: Dictionary of entity data
            output_path: Output directory path
            formats: List of output formats to check
            
        Returns:
            True if all expected files exist, False otherwise
        """
        for entity_name in entities.keys():
            for format_name in formats:
                expected_file = self._get_expected_filename(entity_name, format_name, output_path)
                if not expected_file.exists():
                    return False
        return True
    
    def _remove_existing_files(
        self, 
        entities: Dict[str, List[Dict[str, Any]]], 
        output_path: Path, 
        format_name: str
    ) -> None:
        """Remove existing files for a specific format.
        
        Args:
            entities: Dictionary of entity data
            output_path: Output directory path
            format_name: Format name to remove files for
        """
        for entity_name in entities.keys():
            existing_file = self._get_expected_filename(entity_name, format_name, output_path)
            if existing_file.exists():
                try:
                    existing_file.unlink()
                except OSError:
                    # Ignore errors when removing files
                    pass
    
    def _get_expected_filename(self, entity_name: str, format_name: str, output_path: Path) -> Path:
        """Get the expected filename for an entity and format.
        
        Args:
            entity_name: Name of the entity
            format_name: Output format name
            output_path: Output directory path
            
        Returns:
            Path to the expected file
        """
        extensions = {
            'csv': '.csv',
            'json': '.json',
            'parquet': '.parquet',
            'duckdb': '.duckdb'
        }
        
        extension = extensions.get(format_name, f'.{format_name}')
        return output_path / f"{entity_name}{extension}"
    
    def verify_reproducibility(
        self, 
        output_path: Path, 
        expected_metadata: GenerationMetadata
    ) -> bool:
        """Verify that output matches expected metadata for reproducibility.
        
        Args:
            output_path: Path to check for output files
            expected_metadata: Expected metadata to compare against
            
        Returns:
            True if output is reproducible, False otherwise
        """
        # Load existing metadata
        existing_metadata = GenerationMetadata.load_from_file(output_path)
        if not existing_metadata:
            return False
        
        # Check if generations are identical
        return existing_metadata.is_identical_generation(expected_metadata)
    
    def clean_output_directory(self, output_path: Path, keep_metadata: bool = False) -> None:
        """Clean output directory of generated files.
        
        Args:
            output_path: Path to clean
            keep_metadata: Whether to keep metadata files (default: False)
            
        Raises:
            OutputError: If cleaning fails
        """
        try:
            if not output_path.exists():
                return
            
            for file_path in output_path.iterdir():
                if file_path.is_file():
                    # Skip metadata file if requested
                    if keep_metadata and file_path.name == '.jafgen_metadata.json':
                        continue
                    
                    # Remove generated files
                    if file_path.suffix in ['.csv', '.json', '.parquet', '.duckdb']:
                        file_path.unlink()
                    elif file_path.name == '.jafgen_metadata.json':
                        file_path.unlink()
                        
        except (OSError, PermissionError) as e:
            raise OutputError(f"Failed to clean output directory '{output_path}': {e}") from e