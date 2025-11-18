from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from jafgen.airbyte.translator import AirbyteTranslator
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.link_resolver import LinkResolver
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.duckdb_writer import DuckDBWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.output_manager import OutputManager
from jafgen.output.parquet_writer import ParquetWriter
from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.simulation import Simulation


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print("jafgen version 0.4.14")
        raise typer.Exit()


app = typer.Typer(
    help="""Jafgen - A flexible synthetic data generator

🥪 Two ways to generate data:

1. [bold]Schema-driven generation[/bold] (recommended):
   • Define entities in YAML files
   • Support multiple output formats (CSV, JSON, Parquet, DuckDB)
   • Deterministic with seeding
   • Link entities with foreign keys
   
   Commands: generate, validate-schema, list-schemas, import-airbyte

2. [bold]Legacy Jaffle Shop simulation[/bold]:
   • Hardcoded entities (customers, orders, products, etc.)
   • CSV output only
   • Time-based simulation
   
   Command: run (deprecated)

For new projects, use schema-driven generation with 'jafgen generate'.
"""
)
console = Console()


# Add version option to the main app
@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version information",
        ),
    ] = None,
):
    """Jafgen - A flexible synthetic data generator

    🚀 Quick start with schema-driven generation:

    1. List available schemas: [bold]jafgen list-schemas[/bold]
    2. Generate data: [bold]jafgen generate[/bold]
    3. Validate schemas: [bold]jafgen validate-schema[/bold]

    📚 For detailed documentation and examples, visit:
    https://github.com/dbt-labs/jaffle-shop-generator
    """
    pass


@app.command()
def run(
    # We set default to 0 here to make sure users don't get confused if they only put in days.
    # If they don't set anything we have years default = 1 later to keep the same functionality.
    years: Annotated[
        int,
        typer.Argument(
            help="Number of years to simulate. If neither days nor years are provided, the default is 1 year."
        ),
    ] = 0,
    days: Annotated[
        int, typer.Option(help="Number of days to simulate. Default is 0.")
    ] = 0,
    pre: Annotated[
        str,
        typer.Option(help="Optional prefix for the output file names."),
    ] = "raw",
) -> None:
    """Generate synthetic data using the legacy Jaffle Shop simulation.

    [yellow]⚠️  DEPRECATION WARNING:[/yellow] The 'run' command uses the legacy hardcoded simulation.
    For more flexible data generation, consider using the new schema-driven approach:

    • [bold]jafgen generate[/bold] - Generate data from YAML schemas
    • [bold]jafgen list-schemas[/bold] - View available schemas
    • [bold]jafgen validate-schema[/bold] - Validate schema files

    See the migration guide: https://github.com/dbt-labs/jaffle-shop-generator#migration-guide
    """
    # Show deprecation warning
    console.print("[yellow]⚠️  Using legacy simulation mode.[/yellow]")
    console.print(
        "[dim]Consider migrating to schema-driven generation with 'jafgen generate'[/dim]"
    )
    console.print(
        "[dim]For help migrating, see: https://github.com/dbt-labs/jaffle-shop-generator#migration-guide[/dim]\n"
    )

    # To keep the default value for backwards compatibility.
    if years == 0 and days == 0:
        years = 1

    sim = Simulation(years, days, pre)
    sim.run_simulation()
    sim.save_results()


@app.command()
def generate(
    schema_dir: Annotated[
        Path,
        typer.Option(
            "--schema-dir", "-s", help="Directory containing YAML schema files"
        ),
    ] = Path("./schemas"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o", help="Directory to write generated data files"
        ),
    ] = Path("./output"),
    seed: Annotated[
        Optional[int],
        typer.Option(
            "--seed",
            help="Seed for deterministic data generation (overrides schema seed)",
        ),
    ] = None,
) -> None:
    """Generate synthetic data from YAML schema definitions."""
    try:
        # Validate input directories
        if not schema_dir.exists():
            console.print(
                f"[red]Error:[/red] Schema directory does not exist: {schema_dir}"
            )
            raise typer.Exit(1)

        if not schema_dir.is_dir():
            console.print(
                f"[red]Error:[/red] Schema path is not a directory: {schema_dir}"
            )
            raise typer.Exit(1)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[blue]Discovering schemas in:[/blue] {schema_dir}")

        # Discover and load schemas
        discovery_engine = SchemaDiscoveryEngine()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading schemas...", total=None)

            schemas, validation_result = discovery_engine.discover_and_load_schemas(
                schema_dir
            )

            progress.update(task, description="Validating schemas...")

            # Check validation results
            if not validation_result.is_valid:
                console.print("[red]Schema validation failed:[/red]")
                for error in validation_result.errors:
                    console.print(f"  [red]•[/red] {error.message}")
                    if error.location:
                        console.print(f"    Location: {error.location}")
                    if error.suggestion:
                        console.print(f"    Suggestion: {error.suggestion}")
                raise typer.Exit(1)

            # Show warnings if any
            if validation_result.warnings:
                console.print("[yellow]Warnings:[/yellow]")
                for warning in validation_result.warnings:
                    console.print(f"  [yellow]•[/yellow] {warning.message}")
                    if warning.location:
                        console.print(f"    Location: {warning.location}")

            if not schemas:
                console.print("[yellow]No schemas found to process.[/yellow]")
                return

            progress.update(task, description=f"Found {len(schemas)} schema(s)")

        console.print(f"[green]Successfully loaded {len(schemas)} schema(s)[/green]")

        # Override seed in schemas if provided via CLI
        if seed is not None:
            for schema in schemas:
                schema.seed = seed

        # Initialize generation components
        mimesis_engine = MimesisEngine(seed=seed)
        link_resolver = LinkResolver()
        data_generator = DataGenerator(mimesis_engine, link_resolver)

        # Initialize output writers and manager
        output_writers = {
            "csv": CSVWriter(),
            "json": JSONWriter(),
            "parquet": ParquetWriter(),
            "duckdb": DuckDBWriter(),
        }
        output_manager = OutputManager(output_writers)

        # Generate data for all schemas
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            generation_task = progress.add_task(
                "Generating data...", total=len(schemas)
            )

            try:
                generated_systems = data_generator.generate_multiple_systems(schemas)

                for i, generated_system in enumerate(generated_systems):
                    schema = generated_system.schema

                    progress.update(
                        generation_task,
                        advance=1,
                        description=f"Generating data for '{schema.name}'...",
                    )

                    # Use output manager for idempotent file generation
                    try:
                        metadata = output_manager.write_system_data(
                            generated_system, output_dir, overwrite=True
                        )

                        # Show success message with formats
                        formats_str = ", ".join(metadata.output_formats)
                        console.print(
                            f"  [green]✓[/green] Generated {formats_str.upper()} files for '{schema.name}'"
                        )

                    except Exception as e:
                        console.print(
                            f"  [red]✗[/red] Failed to write data for '{schema.name}': {e}"
                        )

                progress.update(generation_task, description="Data generation complete")

            except Exception as e:
                console.print(f"[red]Data generation failed:[/red] {e}")
                raise typer.Exit(1)

        # Display summary
        console.print("\n[green]Generation Summary:[/green]")

        summary_table = Table(show_header=True, header_style="bold blue")
        summary_table.add_column("Schema")
        summary_table.add_column("Entities")
        summary_table.add_column("Total Records")
        summary_table.add_column("Output Formats")
        summary_table.add_column("Seed Used")

        for generated_system in generated_systems:
            schema = generated_system.schema
            metadata = generated_system.metadata

            entity_count = len(generated_system.entities)
            total_records = metadata.total_records
            output_formats = ", ".join(
                schema.output.format
                if isinstance(schema.output.format, list)
                else [schema.output.format]
            )
            seed_used = str(metadata.seed_used)

            summary_table.add_row(
                schema.name,
                str(entity_count),
                str(total_records),
                output_formats,
                seed_used,
            )

        console.print(summary_table)
        console.print(f"\n[green]All data written to:[/green] {output_dir}")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def validate_schema(
    schema_dir: Annotated[
        Path,
        typer.Option(
            "--schema-dir",
            "-s",
            help="Directory containing YAML schema files to validate",
        ),
    ] = Path("./schemas"),
) -> None:
    """Validate YAML schema files for syntax and logical errors."""
    try:
        # Validate input directory
        if not schema_dir.exists():
            console.print(
                f"[red]Error:[/red] Schema directory does not exist: {schema_dir}"
            )
            raise typer.Exit(1)

        if not schema_dir.is_dir():
            console.print(
                f"[red]Error:[/red] Schema path is not a directory: {schema_dir}"
            )
            raise typer.Exit(1)

        console.print(f"[blue]Validating schemas in:[/blue] {schema_dir}")

        # Discover and validate schemas
        discovery_engine = SchemaDiscoveryEngine()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering schemas...", total=None)

            schemas, validation_result = discovery_engine.discover_and_load_schemas(
                schema_dir
            )

            progress.update(task, description="Validating schemas...")

            # Additional cross-schema validation
            if schemas:
                compatibility_result = discovery_engine.validate_schema_compatibility(
                    schemas
                )

                # Merge validation results
                validation_result.errors.extend(compatibility_result.errors)
                validation_result.warnings.extend(compatibility_result.warnings)
                validation_result.is_valid = (
                    validation_result.is_valid and compatibility_result.is_valid
                )

            progress.update(task, description="Validation complete")

        # Display results
        if not schemas:
            console.print("[yellow]No schema files found.[/yellow]")
            return

        console.print(
            f"\n[blue]Validation Results for {len(schemas)} schema(s):[/blue]"
        )

        if validation_result.is_valid:
            console.print("[green]✓ All schemas are valid![/green]")
        else:
            console.print("[red]✗ Schema validation failed[/red]")

        # Show errors
        if validation_result.errors:
            console.print(f"\n[red]Errors ({len(validation_result.errors)}):[/red]")
            for i, error in enumerate(validation_result.errors, 1):
                console.print(f"  [red]{i}.[/red] {error.message}")
                if error.location:
                    console.print(f"     [dim]Location:[/dim] {error.location}")
                if error.suggestion:
                    console.print(f"     [dim]Suggestion:[/dim] {error.suggestion}")

        # Show warnings
        if validation_result.warnings:
            console.print(
                f"\n[yellow]Warnings ({len(validation_result.warnings)}):[/yellow]"
            )
            for i, warning in enumerate(validation_result.warnings, 1):
                console.print(f"  [yellow]{i}.[/yellow] {warning.message}")
                if warning.location:
                    console.print(f"     [dim]Location:[/dim] {warning.location}")

        # Show schema summary if valid
        if validation_result.is_valid and schemas:
            console.print("\n[green]Schema Summary:[/green]")

            summary_table = Table(show_header=True, header_style="bold blue")
            summary_table.add_column("Schema")
            summary_table.add_column("Version")
            summary_table.add_column("Entities")
            summary_table.add_column("Total Records")
            summary_table.add_column("Links")
            summary_table.add_column("Output Formats")

            summary = discovery_engine.get_schema_summary(schemas)

            for schema_name, schema_info in summary.items():
                summary_table.add_row(
                    schema_name,
                    schema_info["version"],
                    str(schema_info["entity_count"]),
                    str(schema_info["total_records"]),
                    str(schema_info["link_count"]),
                    ", ".join(schema_info["output_formats"]),
                )

            console.print(summary_table)

        # Exit with error code if validation failed
        if not validation_result.is_valid:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error during validation:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def list_schemas(
    schema_dir: Annotated[
        Path,
        typer.Option(
            "--schema-dir", "-s", help="Directory containing YAML schema files to list"
        ),
    ] = Path("./schemas"),
    detailed: Annotated[
        bool,
        typer.Option(
            "--detailed", "-d", help="Show detailed information about each schema"
        ),
    ] = False,
) -> None:
    """List discovered schema files with basic information."""
    try:
        # Validate input directory
        if not schema_dir.exists():
            console.print(
                f"[red]Error:[/red] Schema directory does not exist: {schema_dir}"
            )
            raise typer.Exit(1)

        if not schema_dir.is_dir():
            console.print(
                f"[red]Error:[/red] Schema path is not a directory: {schema_dir}"
            )
            raise typer.Exit(1)

        console.print(f"[blue]Discovering schemas in:[/blue] {schema_dir}")

        # Discover schemas
        discovery_engine = SchemaDiscoveryEngine()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering schemas...", total=None)

            schemas, validation_result = discovery_engine.discover_and_load_schemas(
                schema_dir
            )

            progress.update(task, description="Processing schema information...")

        if not schemas:
            console.print("[yellow]No schema files found.[/yellow]")
            return

        console.print(f"\n[green]Found {len(schemas)} schema(s):[/green]")

        if detailed:
            # Show detailed information
            for schema in schemas:
                console.print(
                    f"\n[bold blue]{schema.name}[/bold blue] (v{schema.version})"
                )
                console.print(f"  [dim]Seed:[/dim] {schema.seed}")
                console.print(
                    f"  [dim]Output:[/dim] {', '.join(schema.output.format)} → {schema.output.path}"
                )

                if schema.entities:
                    console.print("  [dim]Entities:[/dim]")
                    for entity_name, entity_config in schema.entities.items():
                        link_count = sum(
                            1
                            for attr in entity_config.attributes.values()
                            if attr.link_to
                        )
                        link_info = f" ({link_count} links)" if link_count > 0 else ""
                        console.print(
                            f"    • {entity_name}: {entity_config.count} records, {len(entity_config.attributes)} attributes{link_info}"
                        )
                else:
                    console.print("  [dim]Entities:[/dim] None")
        else:
            # Show summary table
            summary_table = Table(show_header=True, header_style="bold blue")
            summary_table.add_column("Schema")
            summary_table.add_column("Version")
            summary_table.add_column("Entities")
            summary_table.add_column("Total Records")
            summary_table.add_column("Output Formats")
            summary_table.add_column("Status")

            summary = discovery_engine.get_schema_summary(schemas)

            for schema in schemas:
                schema_info = summary[schema.name]

                # Determine status based on validation
                status = "[green]Valid[/green]"
                schema_errors = [
                    e for e in validation_result.errors if schema.name in str(e.message)
                ]
                if schema_errors:
                    status = "[red]Invalid[/red]"
                elif any(
                    schema.name in str(w.message) for w in validation_result.warnings
                ):
                    status = "[yellow]Warnings[/yellow]"

                summary_table.add_row(
                    schema.name,
                    schema_info["version"],
                    str(schema_info["entity_count"]),
                    str(schema_info["total_records"]),
                    ", ".join(schema_info["output_formats"]),
                    status,
                )

            console.print(summary_table)

        # Show validation warnings/errors if any
        if validation_result.warnings or validation_result.errors:
            console.print(
                "\n[yellow]Note:[/yellow] Run 'jafgen validate-schema' for detailed validation information."
            )

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def import_airbyte(
    manifest_file: Annotated[
        Path,
        typer.Option(
            "--manifest-file", "-m", help="Path to Airbyte source manifest.yaml file"
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o", help="Directory to save translated schema files"
        ),
    ] = Path("./schemas"),
    detect_relationships: Annotated[
        bool,
        typer.Option(
            help="Automatically detect and create relationships between entities"
        ),
    ] = True,
    validate: Annotated[
        bool,
        typer.Option(help="Validate translated schemas before saving"),
    ] = True,
) -> None:
    """Import Airbyte source manifest.yaml file and convert to jafgen schemas."""
    try:
        # Validate input file
        if not manifest_file.exists():
            console.print(
                f"[red]Error:[/red] Manifest file does not exist: {manifest_file}"
            )
            raise typer.Exit(1)

        if not manifest_file.is_file():
            console.print(
                f"[red]Error:[/red] Manifest path is not a file: {manifest_file}"
            )
            raise typer.Exit(1)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[blue]Importing Airbyte manifest:[/blue] {manifest_file}")

        # Initialize translator
        translator = AirbyteTranslator()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Translate manifest
            task = progress.add_task("Translating manifest...", total=None)

            try:
                schemas = translator.translate_manifest(manifest_file)

                if not schemas:
                    console.print(
                        "[yellow]No schemas were generated from the manifest.[/yellow]"
                    )
                    return

                progress.update(
                    task, description=f"Translated {len(schemas)} schema(s)"
                )

                # Apply relationship detection if requested
                if detect_relationships:
                    progress.update(task, description="Detecting relationships...")
                    schemas = translator.detect_relationships(schemas)

                # Get translation validation results
                translation_result = translator.get_validation_result()

                # Show translation warnings
                if translation_result.warnings:
                    console.print(
                        f"\n[yellow]Translation Warnings ({len(translation_result.warnings)}):[/yellow]"
                    )
                    for i, warning in enumerate(translation_result.warnings, 1):
                        console.print(f"  [yellow]{i}.[/yellow] {warning.message}")
                        if warning.location:
                            console.print(
                                f"     [dim]Location:[/dim] {warning.location}"
                            )

                # Check for translation errors
                if translation_result.errors:
                    console.print(
                        f"\n[red]Translation Errors ({len(translation_result.errors)}):[/red]"
                    )
                    for i, error in enumerate(translation_result.errors, 1):
                        console.print(f"  [red]{i}.[/red] {error.message}")
                        if error.location:
                            console.print(f"     [dim]Location:[/dim] {error.location}")

                    console.print("[red]Translation failed due to errors.[/red]")
                    raise typer.Exit(1)

                # Validate translated schemas if requested
                if validate:
                    progress.update(
                        task, description="Validating translated schemas..."
                    )

                    discovery_engine = SchemaDiscoveryEngine()
                    validation_result = discovery_engine.validate_schemas(schemas)

                    if not validation_result.is_valid:
                        console.print(
                            f"\n[red]Schema Validation Errors ({len(validation_result.errors)}):[/red]"
                        )
                        for i, error in enumerate(validation_result.errors, 1):
                            console.print(f"  [red]{i}.[/red] {error.message}")
                            if error.location:
                                console.print(
                                    f"     [dim]Location:[/dim] {error.location}"
                                )
                            if error.suggestion:
                                console.print(
                                    f"     [dim]Suggestion:[/dim] {error.suggestion}"
                                )

                        console.print(
                            "[red]Validation failed. Schemas not saved.[/red]"
                        )
                        raise typer.Exit(1)

                    # Show validation warnings
                    if validation_result.warnings:
                        console.print(
                            f"\n[yellow]Schema Validation Warnings ({len(validation_result.warnings)}):[/yellow]"
                        )
                        for i, warning in enumerate(validation_result.warnings, 1):
                            console.print(f"  [yellow]{i}.[/yellow] {warning.message}")
                            if warning.location:
                                console.print(
                                    f"     [dim]Location:[/dim] {warning.location}"
                                )

                # Save schemas
                progress.update(task, description="Saving schema files...")

                saved_files = []
                for schema in schemas:
                    schema_filename = f"{schema.name}.yaml"
                    schema_path = output_dir / schema_filename

                    translator.save_schema(schema, schema_path)
                    saved_files.append(schema_path)

                progress.update(task, description="Import complete")

            except Exception as e:
                console.print(f"[red]Import failed:[/red] {e}")
                raise typer.Exit(1)

        # Display success summary
        console.print("\n[green]Successfully imported Airbyte manifest![/green]")
        console.print(f"[green]Created {len(saved_files)} schema file(s):[/green]")

        for schema_path in saved_files:
            console.print(f"  [green]✓[/green] {schema_path}")

        # Display schema summary
        console.print("\n[blue]Schema Summary:[/blue]")

        summary_table = Table(show_header=True, header_style="bold blue")
        summary_table.add_column("Schema")
        summary_table.add_column("Entities")
        summary_table.add_column("Total Records")
        summary_table.add_column("Links")
        summary_table.add_column("Output Formats")

        for schema in schemas:
            entity_count = len(schema.entities)
            total_records = sum(entity.count for entity in schema.entities.values())
            link_count = sum(
                sum(1 for attr in entity.attributes.values() if attr.link_to)
                for entity in schema.entities.values()
            )
            output_formats = ", ".join(
                schema.output.format
                if isinstance(schema.output.format, list)
                else [schema.output.format]
            )

            summary_table.add_row(
                schema.name,
                str(entity_count),
                str(total_records),
                str(link_count),
                output_formats,
            )

        console.print(summary_table)

        # Show next steps
        console.print("\n[blue]Next Steps:[/blue]")
        console.print(f"  1. Review the generated schema files in: {output_dir}")
        console.print("  2. Adjust entity counts and constraints as needed")
        console.print(
            f"  3. Generate data with: [bold]jafgen generate --schema-dir {output_dir}[/bold]"
        )

        if translation_result.warnings:
            console.print(
                "\n[yellow]Note:[/yellow] Review the translation warnings above and adjust schemas if needed."
            )

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error during import:[/red] {e}")
        raise typer.Exit(1)
