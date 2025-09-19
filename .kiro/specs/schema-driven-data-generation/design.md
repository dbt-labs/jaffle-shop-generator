# Design Document

## Overview

The schema-driven data generation system transforms jafgen from a hardcoded simulation into a flexible, configuration-driven fake data generator. The new architecture centers around YAML schema definitions that describe entities, their attributes, relationships, and output requirements. The system uses Mimesis for deterministic fake data generation and supports multiple output formats while maintaining referential integrity across linked entities.

## Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Schema Layer   │    │  Output Layer   │
│                 │    │                 │    │                 │
│ • generate      │───▶│ • SchemaLoader  │───▶│ • CSVWriter     │
│ • validate      │    │ • SchemaParser  │    │ • JSONWriter    │
│ • list-schemas  │    │ • Validator     │    │ • ParquetWriter │
└─────────────────┘    └─────────────────┘    │ • DuckDBWriter  │
                                              └─────────────────┘
         │                       │                       ▲
         │                       │                       │
         ▼                       ▼                       │
┌─────────────────┐    ┌─────────────────┐              │
│ Config Manager  │    │ Generation Core │──────────────┘
│                 │    │                 │
│ • SystemConfig  │    │ • DataGenerator │
│ • EntityConfig  │    │ • LinkResolver  │
│ • OutputConfig  │    │ • MimesisEngine │
└─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Schema Discovery**: System scans `./schemas` directory for YAML files
2. **Schema Loading**: Parse and validate YAML schemas into internal config objects
3. **Dependency Resolution**: Build dependency graph for linked entities
4. **Data Generation**: Generate fake data using Mimesis with deterministic seeding
5. **Link Resolution**: Resolve foreign key relationships across entities
6. **Output Writing**: Write data to specified formats (CSV, JSON, Parquet, DuckDB)

## Components and Interfaces

### Schema Management

#### SchemaLoader
```python
class SchemaLoader:
    def discover_schemas(self, schema_dir: Path) -> List[Path]
    def load_schema(self, schema_path: Path) -> SystemSchema
    def validate_schema(self, schema: SystemSchema) -> ValidationResult
```

#### SystemSchema
```python
@dataclass
class SystemSchema:
    name: str
    version: str
    seed: Optional[int]
    output: OutputConfig
    entities: Dict[str, EntityConfig]
```

#### EntityConfig
```python
@dataclass
class EntityConfig:
    name: str
    count: int
    attributes: Dict[str, AttributeConfig]
    
@dataclass
class AttributeConfig:
    type: str  # mimesis provider type
    unique: bool = False
    required: bool = True
    link_to: Optional[str] = None  # "schema.entity.attribute"
    constraints: Dict[str, Any] = field(default_factory=dict)
```

### Data Generation Core

#### DataGenerator
```python
class DataGenerator:
    def __init__(self, mimesis_engine: MimesisEngine, link_resolver: LinkResolver)
    def generate_system(self, schema: SystemSchema) -> GeneratedSystem
    def generate_entity(self, entity_config: EntityConfig) -> List[Dict[str, Any]]
```

#### MimesisEngine
```python
class MimesisEngine:
    def __init__(self, seed: Optional[int] = None)
    def generate_value(self, attribute_config: AttributeConfig) -> Any
    def ensure_unique(self, generator_func: Callable, seen_values: Set) -> Any
```

#### LinkResolver
```python
class LinkResolver:
    def __init__(self)
    def register_entity(self, schema_name: str, entity_name: str, data: List[Dict])
    def resolve_link(self, link_spec: str) -> Any
    def build_dependency_graph(self, schemas: List[SystemSchema]) -> DependencyGraph
```

### Output Management

#### OutputWriter (Abstract Base)
```python
class OutputWriter(ABC):
    @abstractmethod
    def write(self, data: Dict[str, List[Dict]], output_path: Path) -> None
```

#### Concrete Writers
```python
class CSVWriter(OutputWriter): ...
class JSONWriter(OutputWriter): ...  
class ParquetWriter(OutputWriter): ...
class DuckDBWriter(OutputWriter): ...
```

### CLI Interface

#### Command Structure
```python
# Using Typer framework
@app.command()
def generate(
    schema_dir: Path = "./schemas",
    output_dir: Path = "./output",
    seed: Optional[int] = None
) -> None

@app.command() 
def validate_schema(schema_dir: Path = "./schemas") -> None

@app.command()
def list_schemas(schema_dir: Path = "./schemas") -> None
```

## Data Models

### YAML Schema Format

```yaml
# System-level configuration
system:
  name: "jaffle-shop"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "parquet"]
    path: "./output"

# Entity definitions
entities:
  customers:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
      email:
        type: "person.email"
        unique: true
        required: true
      created_at:
        type: "datetime.datetime"
        constraints:
          start_date: "2020-01-01"
          end_date: "2024-12-31"
      
  orders:
    count: 5000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "jaffle-shop.customers.id"
        required: true
      order_date:
        type: "datetime.date"
        required: true
      total_amount:
        type: "numeric.decimal"
        constraints:
          min_value: 5.00
          max_value: 150.00
```

### Internal Data Structures

#### GeneratedSystem
```python
@dataclass
class GeneratedSystem:
    schema: SystemSchema
    entities: Dict[str, List[Dict[str, Any]]]
    metadata: GenerationMetadata

@dataclass
class GenerationMetadata:
    generated_at: datetime
    seed_used: int
    total_records: int
    entity_counts: Dict[str, int]
```

## Error Handling

### Schema Validation Errors
- **Syntax Errors**: Invalid YAML format, missing required fields
- **Semantic Errors**: Invalid attribute types, circular dependencies, broken links
- **Constraint Violations**: Impossible unique constraints, invalid date ranges

### Generation Errors  
- **Link Resolution Failures**: Referenced entity/attribute doesn't exist
- **Unique Constraint Violations**: Cannot generate enough unique values
- **Type Generation Errors**: Invalid Mimesis provider configuration

### Output Errors
- **File System Errors**: Permission issues, disk space, invalid paths
- **Format Errors**: Data incompatible with output format requirements

### Error Response Strategy
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]

@dataclass  
class ValidationError:
    type: ErrorType
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
```

## Testing Strategy

### Unit Tests
- **Schema Loading**: YAML parsing, validation logic, error handling
- **Data Generation**: Mimesis integration, seeding determinism, unique constraints
- **Link Resolution**: Dependency graph building, foreign key resolution
- **Output Writers**: Each format writer with various data types
- **CLI Commands**: Argument parsing, error handling, help text

### Integration Tests
- **End-to-End Workflows**: Schema discovery → generation → output
- **Multi-Schema Scenarios**: Cross-schema linking, dependency resolution
- **Output Format Validation**: Verify generated files are valid and complete
- **Idempotency Testing**: Multiple runs produce identical results
- **Large Dataset Testing**: Performance with high entity counts

### Test Data Fixtures
```
tests/
├── fixtures/
│   ├── schemas/
│   │   ├── valid/
│   │   │   ├── simple-schema.yaml
│   │   │   ├── linked-entities.yaml
│   │   │   └── multi-schema/
│   │   └── invalid/
│   │       ├── syntax-error.yaml
│   │       ├── missing-required.yaml
│   │       └── circular-dependency.yaml
│   └── expected-outputs/
│       ├── simple-schema.csv
│       ├── simple-schema.json
│       └── linked-entities.parquet
```

### Performance Testing
- **Memory Usage**: Large datasets don't cause memory issues
- **Generation Speed**: Acceptable performance for typical use cases
- **File I/O**: Efficient writing for large datasets

## Airbyte Integration

### Manifest Translation
The system will include an `AirbyteTranslator` component that converts Airbyte source manifest.yaml files into jafgen-compatible schemas:

```python
class AirbyteTranslator:
    def translate_manifest(self, manifest_path: Path) -> List[SystemSchema]
    def convert_stream_schema(self, stream: AirbyteStream) -> EntityConfig
    def map_json_schema_types(self, json_schema: Dict) -> Dict[str, AttributeConfig]
```

### SaaS System Schemas
Pre-built schema templates for popular systems:

```
schemas/
├── saas-templates/
│   ├── hubspot/
│   │   ├── contacts.yaml
│   │   ├── companies.yaml
│   │   └── deals.yaml
│   ├── salesforce/
│   │   ├── accounts.yaml
│   │   ├── contacts.yaml
│   │   └── opportunities.yaml
│   └── xero/
│       ├── customers.yaml
│       ├── invoices.yaml
│       └── payments.yaml
```

## Migration Strategy

### Phase 1: Core Infrastructure
- Implement schema loading and validation
- Build Mimesis integration with seeding
- Create basic CSV output writer
- Implement CLI framework

### Phase 2: Advanced Features  
- Add remaining output formats (JSON, Parquet, DuckDB)
- Implement link resolution system
- Add comprehensive error handling
- Build test suite

### Phase 3: External Integrations
- Airbyte manifest translation
- SaaS system schema templates
- Performance optimizations
- Documentation and examples

### Backward Compatibility
The existing CLI interface (`jafgen run`) will be maintained during transition, with the new schema-driven system available via new commands. This allows gradual migration of existing users.