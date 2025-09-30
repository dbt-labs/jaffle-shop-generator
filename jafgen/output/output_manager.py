"""Output manager for idempotent file generation and directory management."""

import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..generation.models import GenerationMetadata, calculate_schema_hash
from ..schema.models import FormatConfig, SystemSchema
from .exceptions import OutputError
from .interfaces import OutputWriter


class OutputManager:
    """Manages idempotent output generation with proper directory handling."""

    def __init__(self, output_writers: Dict[str, OutputWriter]):
        """Initialize output manager with available writers.

        Args:
            output_writers: Dictionary mapping format names to writer instances
        """
        self.output_writers = output_writers

    def prepare_output_directory(
        self, output_path: Path, force_recreate: bool = False
    ) -> None:
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
            if os.name != "nt":  # Unix-like systems
                output_path.chmod(
                    stat.S_IRWXU
                    | stat.S_IRGRP
                    | stat.S_IXGRP
                    | stat.S_IROTH
                    | stat.S_IXOTH
                )

        except (OSError, PermissionError) as e:
            raise OutputError(
                f"Failed to prepare output directory '{output_path}': {e}"
            ) from e

    def write_system_data(
        self,
        generated_system: "GeneratedSystem",
        base_output_path: Path,
        overwrite: bool = True,
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

        # Determine output formats and path from schema configuration
        output_formats = (
            schema.output.format
            if isinstance(schema.output.format, list)
            else [schema.output.format]
        )
        schema_output_dir = (
            base_output_path / schema.output.path
            if schema.output.path != "."
            else base_output_path
        )

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
            output_path=str(schema_output_dir),
        )

        # Check for existing metadata to verify idempotency
        existing_metadata = GenerationMetadata.load_from_file(schema_output_dir)
        if existing_metadata and existing_metadata.is_identical_generation(metadata):
            # Skip generation if identical run already exists and files are present
            if self._verify_output_files_exist(
                generated_system.entities, schema_output_dir, output_formats, schema
            ):
                return existing_metadata

        # Write data using schema-driven configuration
        written_formats = []
        for entity_name, entity_data in generated_system.entities.items():
            entity_formats, entity_output_dir = self._get_entity_output_config(
                entity_name, schema, schema_output_dir
            )

            # Prepare entity-specific output directory
            self.prepare_output_directory(entity_output_dir, force_recreate=False)

            for output_format in entity_formats:
                if output_format not in self.output_writers:
                    raise OutputError(f"Unsupported output format: {output_format}")

                try:
                    # Remove existing files for this format if overwrite is True
                    if overwrite:
                        self._remove_existing_files(
                            {entity_name: entity_data}, entity_output_dir, output_format
                        )

                    # Get format-specific configuration
                    format_config = self._get_format_config(
                        output_format, entity_name, schema
                    )

                    # Write the data with format-specific options
                    self._write_with_format_config(
                        {entity_name: entity_data},
                        entity_output_dir,
                        output_format,
                        format_config,
                    )

                    if output_format not in written_formats:
                        written_formats.append(output_format)

                except Exception as e:
                    raise OutputError(
                        f"Failed to write {output_format} format for entity '{entity_name}': {e}"
                    ) from e

        # Update metadata with actually written formats
        metadata.output_formats = written_formats

        # Save metadata for future idempotency checks
        metadata.save_to_file(schema_output_dir)

        return metadata

    def _get_entity_output_config(
        self, entity_name: str, schema: "SystemSchema", default_output_dir: Path
    ) -> tuple[List[str], Path]:
        """Get output configuration for a specific entity.

        Args:
            entity_name: Name of the entity
            schema: System schema containing output configuration
            default_output_dir: Default output directory

        Returns:
            Tuple of (formats, output_directory)
        """
        # Check for entity-specific configuration
        if entity_name in schema.output.per_entity:
            entity_config = schema.output.per_entity[entity_name]

            # Use entity-specific formats if defined, otherwise use schema defaults
            formats = (
                entity_config.format
                if entity_config.format is not None
                else schema.output.format
            )

            # Use entity-specific path if defined, otherwise use schema default
            if entity_config.path is not None:
                output_dir = default_output_dir / entity_config.path
            else:
                output_dir = default_output_dir
        else:
            # Use schema defaults
            formats = schema.output.format
            output_dir = default_output_dir

        # Ensure formats is a list
        if isinstance(formats, str):
            formats = [formats]

        return formats, output_dir

    def _get_format_config(
        self, format_name: str, entity_name: str, schema: "SystemSchema"
    ) -> Optional["FormatConfig"]:
        """Get format-specific configuration for an entity.

        Args:
            format_name: Name of the output format
            entity_name: Name of the entity
            schema: System schema containing format configuration

        Returns:
            FormatConfig if found, None otherwise
        """
        # Check entity-specific format config first
        if entity_name in schema.output.per_entity:
            entity_config = schema.output.per_entity[entity_name]
            if format_name in entity_config.formats:
                return entity_config.formats[format_name]

        # Check schema-level format config
        if format_name in schema.output.formats:
            return schema.output.formats[format_name]

        return None

    def _write_with_format_config(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        output_path: Path,
        format_name: str,
        format_config: Optional["FormatConfig"],
    ) -> None:
        """Write data using format-specific configuration.

        Args:
            data: Entity data to write
            output_path: Output directory path
            format_name: Output format name
            format_config: Format-specific configuration
        """
        writer = self.output_writers[format_name]

        if format_config and format_config.options:
            # Apply format-specific options to the writer
            self._apply_format_options(writer, format_config.options)

        if format_config and format_config.filename_pattern:
            # Use custom filename pattern
            self._write_with_custom_filenames(
                data, output_path, writer, format_config.filename_pattern, format_name
            )
        else:
            # Use default writer behavior
            writer.write(data, output_path)

    def _apply_format_options(
        self, writer: OutputWriter, options: Dict[str, Any]
    ) -> None:
        """Apply format-specific options to a writer.

        Args:
            writer: Output writer instance
            options: Format-specific options to apply
        """
        # Apply options based on writer type
        for option_name, option_value in options.items():
            if hasattr(writer, option_name):
                setattr(writer, option_name, option_value)

    def _write_with_custom_filenames(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        output_path: Path,
        writer: OutputWriter,
        filename_pattern: str,
        format_name: str,
    ) -> None:
        """Write data using custom filename patterns.

        Args:
            data: Entity data to write
            output_path: Output directory path
            writer: Output writer instance
            filename_pattern: Custom filename pattern
            format_name: Output format name for extension
        """
        # Get file extension for format
        extensions = {
            "csv": "csv",
            "json": "json",
            "parquet": "parquet",
            "duckdb": "duckdb",
        }
        ext = extensions.get(format_name, format_name)

        # Write each entity with custom filename
        for entity_name, records in data.items():
            if not records:
                continue

            # Format the filename pattern
            custom_filename = filename_pattern.format(
                entity_name=entity_name, ext=ext, format=format_name
            )

            # Create a temporary single-entity data dict for the writer
            single_entity_data = {entity_name: records}

            # For writers that support custom filenames, we need to handle this differently
            # For now, we'll use a workaround by temporarily changing the output path
            custom_file_path = output_path / custom_filename
            custom_dir = custom_file_path.parent
            custom_dir.mkdir(parents=True, exist_ok=True)

            # Write to a temporary directory and then move the file
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                writer.write(single_entity_data, temp_path)

                # Find the generated file and move it to the custom location
                generated_file = temp_path / f"{entity_name}.{ext}"
                if generated_file.exists():
                    import shutil

                    shutil.move(str(generated_file), str(custom_file_path))

    def _verify_output_files_exist(
        self,
        entities: Dict[str, List[Dict[str, Any]]],
        output_path: Path,
        formats: List[str],
        schema: Optional["SystemSchema"] = None,
    ) -> bool:
        """Verify that all expected output files exist.

        Args:
            entities: Dictionary of entity data
            output_path: Output directory path
            formats: List of output formats to check
            schema: Optional schema for custom filename patterns

        Returns:
            True if all expected files exist, False otherwise
        """
        if schema:
            # Check files using schema-driven configuration
            for entity_name in entities.keys():
                entity_formats, entity_output_dir = self._get_entity_output_config(
                    entity_name, schema, output_path
                )

                for format_name in entity_formats:
                    format_config = self._get_format_config(
                        format_name, entity_name, schema
                    )
                    expected_file = self._get_expected_filename_with_config(
                        entity_name, format_name, entity_output_dir, format_config
                    )
                    if not expected_file.exists():
                        return False
        else:
            # Fallback to simple verification
            for entity_name in entities.keys():
                for format_name in formats:
                    expected_file = self._get_expected_filename(
                        entity_name, format_name, output_path
                    )
                    if not expected_file.exists():
                        return False
        return True

    def _remove_existing_files(
        self,
        entities: Dict[str, List[Dict[str, Any]]],
        output_path: Path,
        format_name: str,
    ) -> None:
        """Remove existing files for a specific format.

        Args:
            entities: Dictionary of entity data
            output_path: Output directory path
            format_name: Format name to remove files for
        """
        for entity_name in entities.keys():
            existing_file = self._get_expected_filename(
                entity_name, format_name, output_path
            )
            if existing_file.exists():
                try:
                    existing_file.unlink()
                except OSError:
                    # Ignore errors when removing files
                    pass

    def _get_expected_filename(
        self, entity_name: str, format_name: str, output_path: Path
    ) -> Path:
        """Get the expected filename for an entity and format.

        Args:
            entity_name: Name of the entity
            format_name: Output format name
            output_path: Output directory path

        Returns:
            Path to the expected file
        """
        extensions = {
            "csv": ".csv",
            "json": ".json",
            "parquet": ".parquet",
            "duckdb": ".duckdb",
        }

        extension = extensions.get(format_name, f".{format_name}")
        return output_path / f"{entity_name}{extension}"

    def _get_expected_filename_with_config(
        self,
        entity_name: str,
        format_name: str,
        output_path: Path,
        format_config: Optional["FormatConfig"],
    ) -> Path:
        """Get the expected filename for an entity with format configuration.

        Args:
            entity_name: Name of the entity
            format_name: Output format name
            output_path: Output directory path
            format_config: Format-specific configuration

        Returns:
            Path to the expected file
        """
        if format_config and format_config.filename_pattern:
            # Use custom filename pattern
            extensions = {
                "csv": "csv",
                "json": "json",
                "parquet": "parquet",
                "duckdb": "duckdb",
            }
            ext = extensions.get(format_name, format_name)

            custom_filename = format_config.filename_pattern.format(
                entity_name=entity_name, ext=ext, format=format_name
            )
            return output_path / custom_filename
        else:
            # Use default filename
            return self._get_expected_filename(entity_name, format_name, output_path)

    def verify_reproducibility(
        self, output_path: Path, expected_metadata: GenerationMetadata
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

    def clean_output_directory(
        self, output_path: Path, keep_metadata: bool = False
    ) -> None:
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
                    if keep_metadata and file_path.name == ".jafgen_metadata.json":
                        continue

                    # Remove generated files
                    if file_path.suffix in [".csv", ".json", ".parquet", ".duckdb"]:
                        file_path.unlink()
                    elif file_path.name == ".jafgen_metadata.json":
                        file_path.unlink()

        except (OSError, PermissionError) as e:
            raise OutputError(
                f"Failed to clean output directory '{output_path}': {e}"
            ) from e
