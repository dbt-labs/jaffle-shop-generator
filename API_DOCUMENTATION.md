# Jafgen API Documentation

This document provides comprehensive API documentation for programmatic usage of jafgen's schema-driven data generation system.

## Core Components

### Schema Management

#### SchemaDiscoveryEngine

The main entry point for discovering and loading YAML schema files.

```python
from jafgen.schema.discovery import SchemaDiscoveryEngine

# Initialize discovery engine
discovery = SchemaDiscoveryEngine()

# Discover and load schemas from directory
schemas, validation_result = discovery.discover_and_load_schemas(Path("./schemas"))

# Validate schema compatibility
compatibility_result = discovery.validate_schema_compatibility(schemas)

# Get schema summary information
summary = discovery.get_schema_summary(schemas)
```

#### SystemSchema

Data class representing a complete system schema.

```python
from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig

# Create schema programmatically
schema = SystemSchema(
    name="my-system",
    version="1.0.0",
    seed=42,
    output=OutputConfig(
        format=["csv", "json"],
        path="./output"
    ),
    entities={
        "users": EntityConfig(
            name="users",
            count=1000,
            attributes={
                "id": AttributeConfig(
                    type="uuid",
                    unique=True,
                    required=True
                ),
                "name": AttributeConfig(
                    type="person.full_name",
                    required=True
                )
            }
        )
    }
)
```

### Data Generation

#### DataGenerator

Core component for generating synthetic data from schemas.

```python
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver

# Initialize components
mimesis_engine = MimesisEngine(seed=42)
link_resolver = LinkResolver()
generator = DataGenerator(mimesis_engine, link_resolver)

# Generate data for single schema
generated_system = generator.generate_system(schema)

# Generate data for multiple schemas
generated_systems = generator.generate_multiple_systems([schema1, schema2])
```

#### MimesisEngine

Handles fake data generation using the Mimesis library.

```python
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.schema.models import AttributeConfig

engine = MimesisEngine(seed=42)

# Generate single value
attr_config = AttributeConfig(type="person.email", required=True)
email = engine.generate_value(attr_config)

# Generate with constraints
attr_config = AttributeConfig(
    type="numeric.decimal",
    constraints={"min_value": 10.0, "max_value": 100.0, "precision": 2}
)
price = engine.generate_value(attr_config)
```

#### LinkResolver

Manages entity relationships and foreign key resolution.

```python
from jafgen.generation.link_resolver import LinkResolver

resolver = LinkResolver()

# Register generated entity data
resolver.register_entity("system1", "users", user_data)
resolver.register_entity("system1", "orders", order_data)

# Resolve link reference
user_id = resolver.resolve_link("system1.users.id")

# Build dependency graph
dependency_graph = resolver.build_dependency_graph(schemas)
```

### Output Management

#### OutputManager

Coordinates writing data to multiple output formats.

```python
from jafgen.output.output_manager import OutputManager
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter
from jafgen.output.parquet_writer import ParquetWriter
from jafgen.output.duckdb_writer import DuckDBWriter

# Initialize output writers
writers = {
    "csv": CSVWriter(),
    "json": JSONWriter(),
    "parquet": ParquetWriter(),
    "duckdb": DuckDBWriter()
}

manager = OutputManager(writers)

# Write system data
metadata = manager.write_system_data(
    generated_system, 
    output_dir=Path("./output"),
    overwrite=True
)
```

#### Individual Writers

Each output format has its own writer class:

```python
from jafgen.output.csv_writer import CSVWriter

writer = CSVWriter()
writer.write(
    data={"users": [{"id": "123", "name": "John"}]},
    output_path=Path("./output/users.csv")
)
```

### Airbyte Integration

#### AirbyteTranslator

Converts Airbyte source manifests to jafgen schemas.

```python
from jafgen.airbyte.translator import AirbyteTranslator

translator = AirbyteTranslator()

# Translate manifest file
schemas = translator.translate_manifest(Path("manifest.yaml"))

# Detect relationships between entities
schemas_with_relationships = translator.detect_relationships(schemas)

# Get validation results
validation_result = translator.get_validation_result()

# Save schema to file
translator.save_schema(schema, Path("./schemas/converted.yaml"))
```

## Data Models

### Core Schema Models

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union

@dataclass
class AttributeConfig:
    type: str
    unique: bool = False
    required: bool = True
    link_to: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EntityConfig:
    name: str
    count: int
    attributes: Dict[str, AttributeConfig]

@dataclass
class OutputConfig:
    format: Union[str, List[str]]
    path: str

@dataclass
class SystemSchema:
    name: str
    version: str
    seed: Optional[int]
    output: OutputConfig
    entities: Dict[str, EntityConfig]
```

### Generation Models

```python
@dataclass
class GenerationMetadata:
    generated_at: datetime
    seed_used: int
    total_records: int
    entity_counts: Dict[str, int]
    output_formats: List[str]
    generation_time_seconds: float

@dataclass
class GeneratedSystem:
    schema: SystemSchema
    entities: Dict[str, List[Dict[str, Any]]]
    metadata: GenerationMetadata
```

### Validation Models

```python
@dataclass
class ValidationError:
    type: str
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationWarning:
    type: str
    message: str
    location: Optional[str] = None

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
```

## Supported Attribute Types

### Mimesis Provider Types

Jafgen supports all Mimesis provider types with the format `provider.method`:

#### Person
- `person.full_name`
- `person.first_name`
- `person.last_name`
- `person.email`
- `person.phone_number`
- `person.username`
- `person.identifier` (SSN-like)
- `person.occupation`

#### Address
- `address.address`
- `address.city`
- `address.state`
- `address.country`
- `address.zip_code`

#### Datetime
- `datetime.datetime`
- `datetime.date`
- `datetime.time`

#### Numeric
- `numeric.integer`
- `numeric.decimal`

#### Text
- `text.word`
- `text.sentence`
- `text.paragraph`

#### Internet
- `internet.url`
- `internet.domain_name`
- `internet.ip_v4`
- `internet.ip_v6`

#### Development
- `development.boolean`
- `development.version`

#### Code
- `code.ean8`
- `code.ean13`
- `code.isbn`

#### Payment
- `payment.credit_card_number`

#### Company
- `company.company`

#### Special Types
- `uuid` - Generates UUID4 strings
- `choice` - Selects from provided choices
- `link` - References another entity's attribute

### Constraints

Different attribute types support different constraints:

#### Numeric Constraints
```python
constraints = {
    "min_value": 0,
    "max_value": 100,
    "precision": 2  # For decimals
}
```

#### Date/DateTime Constraints
```python
constraints = {
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
}
```

#### Text Constraints
```python
constraints = {
    "nb_words": 10,  # For sentences
    "max_length": 50  # For strings
}
```

#### Choice Constraints
```python
constraints = {
    "choices": ["option1", "option2", "option3"]
}
```

## Error Handling

### Common Exceptions

```python
from jafgen.schema.exceptions import (
    SchemaValidationError,
    SchemaNotFoundError,
    InvalidSchemaFormatError
)

from jafgen.generation.exceptions import (
    DataGenerationError,
    LinkResolutionError,
    UniqueConstraintViolationError
)

from jafgen.output.exceptions import (
    OutputWriteError,
    UnsupportedFormatError
)

try:
    schemas, result = discovery.discover_and_load_schemas(schema_dir)
except SchemaNotFoundError as e:
    print(f"No schemas found: {e}")
except SchemaValidationError as e:
    print(f"Schema validation failed: {e}")
```

## Complete Example

```python
from pathlib import Path
from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver
from jafgen.output.output_manager import OutputManager
from jafgen.output.csv_writer import CSVWriter
from jafgen.output.json_writer import JSONWriter

def generate_data_programmatically():
    # 1. Discover and load schemas
    discovery = SchemaDiscoveryEngine()
    schemas, validation_result = discovery.discover_and_load_schemas(
        Path("./schemas")
    )
    
    if not validation_result.is_valid:
        for error in validation_result.errors:
            print(f"Validation error: {error.message}")
        return
    
    # 2. Initialize generation components
    mimesis_engine = MimesisEngine(seed=42)
    link_resolver = LinkResolver()
    generator = DataGenerator(mimesis_engine, link_resolver)
    
    # 3. Generate data
    generated_systems = generator.generate_multiple_systems(schemas)
    
    # 4. Write output
    writers = {
        "csv": CSVWriter(),
        "json": JSONWriter()
    }
    output_manager = OutputManager(writers)
    
    for generated_system in generated_systems:
        metadata = output_manager.write_system_data(
            generated_system,
            output_dir=Path("./output"),
            overwrite=True
        )
        print(f"Generated {metadata.total_records} records for {generated_system.schema.name}")

if __name__ == "__main__":
    generate_data_programmatically()
```

## Testing

### Unit Testing Components

```python
import pytest
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.schema.models import AttributeConfig

def test_mimesis_engine_deterministic():
    engine1 = MimesisEngine(seed=42)
    engine2 = MimesisEngine(seed=42)
    
    attr_config = AttributeConfig(type="person.email", required=True)
    
    email1 = engine1.generate_value(attr_config)
    email2 = engine2.generate_value(attr_config)
    
    assert email1 == email2  # Same seed = same output

def test_schema_validation():
    from jafgen.schema.discovery import SchemaDiscoveryEngine
    
    discovery = SchemaDiscoveryEngine()
    # Test with invalid schema directory
    schemas, result = discovery.discover_and_load_schemas(Path("./nonexistent"))
    
    assert len(schemas) == 0
    assert not result.is_valid
```

## Performance Considerations

### Memory Usage
- Large entity counts may require significant memory
- Consider generating data in batches for very large datasets
- Use appropriate output formats (Parquet for large datasets)

### Generation Speed
- Seeding adds minimal overhead
- Link resolution can be expensive with many relationships
- Consider simplifying schemas for faster generation

### Output Performance
- CSV is fastest for simple data
- Parquet is most efficient for large datasets
- DuckDB is best for immediate querying

## Best Practices

1. **Schema Design**
   - Keep entity counts reasonable for development
   - Use meaningful attribute names
   - Define constraints that make business sense

2. **Relationships**
   - Avoid circular dependencies
   - Keep relationship depth manageable
   - Use appropriate cardinalities

3. **Output Management**
   - Choose appropriate formats for your use case
   - Use seeds for reproducible testing
   - Validate schemas before generation

4. **Error Handling**
   - Always check validation results
   - Handle exceptions appropriately
   - Provide meaningful error messages

5. **Performance**
   - Start with small datasets for testing
   - Scale up gradually
   - Monitor memory usage with large datasets