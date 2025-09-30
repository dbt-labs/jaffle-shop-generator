# Migration Guide: From Legacy to Schema-Driven Generation

This guide helps you migrate from the legacy `jafgen run` command to the new schema-driven approach using `jafgen generate`.

## Overview

Jafgen now supports two approaches for data generation:

1. **Schema-driven generation** (recommended) - Flexible, configurable data generation using YAML schemas
2. **Legacy simulation** (deprecated) - The original hardcoded Jaffle Shop simulation

## Why Migrate?

The new schema-driven approach offers several advantages:

- **Flexibility**: Define any entities and attributes you need
- **Multiple formats**: Output to CSV, JSON, Parquet, or DuckDB
- **Deterministic**: Reproducible data with seeding
- **Relationships**: Link entities with foreign keys
- **Validation**: Built-in schema validation
- **Extensibility**: Import from Airbyte manifests, use SaaS templates

## Quick Migration

### Before (Legacy)
```bash
# Generate 2 years of Jaffle Shop data
jafgen run 2 --pre my_data
```

### After (Schema-driven)
```bash
# Generate data from schemas (includes Jaffle Shop equivalent)
jafgen generate --schema-dir ./schemas --output-dir ./output --seed 42
```

## Step-by-Step Migration

### 1. Understand Your Current Data

The legacy `jafgen run` command generates these entities:
- Customers
- Orders  
- Products
- Order Items
- Supplies
- Stores
- Tweets

### 2. Use Equivalent Schemas

We provide pre-built schemas that replicate the legacy Jaffle Shop data structure. These are available in the `schemas/saas-templates/` directory.

### 3. Migration Commands

#### List available schemas
```bash
jafgen list-schemas
```

#### Validate schemas before generation
```bash
jafgen validate-schema --schema-dir ./schemas
```

#### Generate data with specific seed for reproducibility
```bash
jafgen generate --schema-dir ./schemas --output-dir ./output --seed 42
```

### 4. Customize Your Schemas

Create your own YAML schema files in the `./schemas` directory:

```yaml
# schemas/my-system.yaml
system:
  name: "my-system"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "parquet"]
    path: "./output"

entities:
  users:
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
```

## Command Mapping

| Legacy Command | New Command | Description |
|----------------|-------------|-------------|
| `jafgen run` | `jafgen generate` | Generate data |
| N/A | `jafgen list-schemas` | List available schemas |
| N/A | `jafgen validate-schema` | Validate schema files |
| N/A | `jafgen import-airbyte` | Import Airbyte manifests |

## Key Differences

### Output Formats
- **Legacy**: CSV only
- **Schema-driven**: CSV, JSON, Parquet, DuckDB

### Reproducibility
- **Legacy**: Non-deterministic (different data each run)
- **Schema-driven**: Deterministic with seeding (same data with same seed)

### Customization
- **Legacy**: Hardcoded entities and attributes
- **Schema-driven**: Fully customizable via YAML

### File Organization
- **Legacy**: Files prefixed with `--pre` option
- **Schema-driven**: Organized by schema name and entity

## Advanced Features

### Import from Airbyte
Convert Airbyte source manifests to jafgen schemas:

```bash
jafgen import-airbyte --manifest-file source_manifest.yaml --output-dir ./schemas
```

### Use SaaS Templates
Pre-built schemas for popular systems:

```bash
# Copy templates to your schemas directory
cp -r schemas/saas-templates/hubspot ./schemas/
jafgen generate --schema-dir ./schemas
```

### Multiple Output Formats
Generate data in multiple formats simultaneously:

```yaml
system:
  output:
    format: ["csv", "json", "parquet", "duckdb"]
    path: "./output"
```

## Troubleshooting

### Schema Validation Errors
```bash
# Check for schema issues
jafgen validate-schema --schema-dir ./schemas
```

### Missing Dependencies
Ensure you have the latest version with all dependencies:
```bash
pip install --upgrade jafgen
```

### Legacy Data Compatibility
If you need the exact same data structure as the legacy command, use the provided Jaffle Shop schema templates.

## Getting Help

- **Documentation**: https://github.com/dbt-labs/jaffle-shop-generator
- **Examples**: Check the `schemas/saas-templates/` directory
- **Issues**: Report bugs on GitHub

## Timeline

- **Current**: Both approaches are supported
- **Future**: Legacy `run` command will be removed in a future major version
- **Recommendation**: Migrate to schema-driven generation for new projects

The legacy `run` command will continue to work but shows deprecation warnings. We recommend migrating to the schema-driven approach for all new projects.