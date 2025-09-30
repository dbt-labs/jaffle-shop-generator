# 🥪 Jaffle Shop Generator 🏭

> [!NOTE]
> This is not an official dbt Labs project. It is maintained on a volunteer basis by dbt Labs employees who are passionate about analytics engineering, the dbt Community, and jaffles, and feel that generating datasets for learning and practicing is important. Please understand it's a work in progress and not supported in the same way as dbt itself.

The Jaffle Shop Generator or `jafgen` is a flexible command line tool for generating synthetic datasets suitable for analytics engineering practice or demonstrations. 

## 🚀 Two Approaches to Data Generation

### Schema-Driven Generation (Recommended)

Define your data structure using YAML configuration files and generate realistic synthetic data with full control over entities, attributes, relationships, and output formats.

**Features:**
- 📝 **YAML Configuration**: Define entities and attributes declaratively
- 🔗 **Entity Relationships**: Link entities with foreign keys
- 📊 **Multiple Formats**: Output to CSV, JSON, Parquet, or DuckDB
- 🎯 **Deterministic**: Reproducible data with seeding
- ✅ **Validation**: Built-in schema validation
- 🔌 **Integrations**: Import from Airbyte manifests
- 📚 **Templates**: Pre-built schemas for popular SaaS systems

### Legacy Jaffle Shop Simulation

The original hardcoded simulation that generates data for a fictional coffee shop with predefined entities:

- Customers (who place Orders)
- Orders (from those Customers)
- Products (the food and beverages the Orders contain)
- Order Items (of those Products)
- Supplies (needed for making those Products)
- Stores (where the Orders are placed and fulfilled)
- Tweets (Customers sometimes issue Tweets after placing an Order)

It uses some straightforward math to create seasonality and trends in the data, for instance weekends being less busy than weekdays, customers having certain preferences, and new store locations opening over time.

## Installation

_Requires Python 3.10 or higher_.

If you have [pipx](https://pypa.github.io/pipx/installation/) installed, `jafgen` is an ideal tool to use via pipx. You can generate data without installing anything in the local workspace using the following:

```shell
pipx run jafgen [options]
```

You can also install `jafgen` into your project or workspace, ideally in a virtual environment.

```shell
pip install jafgen
```

## Quick Start

### Schema-Driven Generation (Recommended)

1. **List available schemas:**
   ```shell
   jafgen list-schemas
   ```

2. **Generate data from schemas:**
   ```shell
   jafgen generate --schema-dir ./schemas --output-dir ./output
   ```

3. **Validate your schemas:**
   ```shell
   jafgen validate-schema --schema-dir ./schemas
   ```

### Create Your Own Schema

Create a YAML file in the `./schemas` directory:

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
  
  orders:
    count: 5000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      user_id:
        type: "link"
        link_to: "my-system.users.id"
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

### Legacy Jaffle Shop Simulation

> ⚠️ **Deprecated**: The `run` command is deprecated. Consider migrating to schema-driven generation.

Generate legacy Jaffle Shop data:

```shell
# Generate 1 year of data (default)
jafgen run

# Generate 3 years of data with custom prefix
jafgen run 3 --pre cool --days 30
```

**Options:**
- `[int]` Years to generate data for (default: 1)
- `--days [int]` Additional days to generate
- `--pre [string]` Prefix for output files (default: "raw")

## Documentation

### Getting Started
- **[Tutorial](TUTORIAL.md)** - Step-by-step guide with common use cases
- **[Examples](examples/)** - Ready-to-use schema examples
- **[Migration Guide](MIGRATION_GUIDE.md)** - Migrate from legacy to schema-driven generation

### Reference
- **[API Documentation](API_DOCUMENTATION.md)** - Programmatic usage and API reference
- **[Command Reference](#command-reference)** - Complete CLI command documentation

### Templates
- **[SaaS Templates](schemas/saas-templates/)** - Pre-built schemas for popular systems

## Advanced Features

### Import from Airbyte

Convert Airbyte source manifests to jafgen schemas:

```shell
jafgen import-airbyte --manifest-file source_manifest.yaml --output-dir ./schemas
```

### SaaS System Templates

Use pre-built schemas for popular systems:

```shell
# List available templates
ls schemas/saas-templates/

# Generate HubSpot-like data
jafgen generate --schema-dir ./schemas/saas-templates/hubspot

# Generate Salesforce-like data  
jafgen generate --schema-dir ./schemas/saas-templates/salesforce
```

Available templates:
- **HubSpot**: Contacts, Companies, Deals
- **Salesforce**: Accounts, Contacts, Opportunities  
- **Xero**: Customers, Invoices, Payments
- **Huntr**: Jobs, Contacts, Activities

### Multiple Output Formats

Generate data in multiple formats simultaneously:

```yaml
system:
  output:
    format: ["csv", "json", "parquet", "duckdb"]
    path: "./output"
```

### Deterministic Generation

Use seeds for reproducible data:

```shell
# Same seed = same data
jafgen generate --seed 42
jafgen generate --seed 42  # Identical output

# Different seed = different data
jafgen generate --seed 123  # Different output
```

## Purpose

Finding a good data set to practice, learn, or teach analytics engineering with can be difficult. Most open datasets are great for machine learning -- they offer single wide tables that you can manipulate and analyze. Full, real relational databases on the other hand are generally protected by private companies. Not only that, but they're a bit _too_ real. To get to a state that a beginner or intermediate person can understand, there needs to be an advanced amount of analytics engineering transformation applied.

To that end, this project generates relatively simple, clean (but importantly, not _perfect_) data for a variety of entities in discrete tables, which can be transformed and combined into analytical building blocks. There are even trends (like seasonality) and personas (like buying patterns) that can be sussed out through data modeling!

## Approach

The great [@drewbanin](https://github.com/drewbanin) watched the movie [Synecdoche, New York](https://en.wikipedia.org/wiki/Synecdoche,_New_York), and was inspired by the idea of creating a complete simulation of a world. Rather than using discrete rules to generate synthetic data, instead setting up entities with behavior patterns and letting them loose to interact with each other. This was the birth of the Jaffle Shop Generator. There are customers, stores, products, and more, all with their own behaviors and interactions as time passes. These combine to create unique and realistic datasets on every run.

An important caveat is that `jafgen` is _not_ idempotent. By design, it generates new data every time you run it based on the simulation's interactions. This is intended behavior, as it allows for more realistic and interesting data generation. Certain aspects are hard coded, like stores opening at certain times, but the output data is always unique.

We hope over time to add more complex behaviors and trends to the simulation!

## Command Reference

### Schema-Driven Commands

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate data from YAML schemas | `jafgen generate --schema-dir ./schemas` |
| `list-schemas` | List discovered schemas | `jafgen list-schemas --detailed` |
| `validate-schema` | Validate schema files | `jafgen validate-schema --schema-dir ./schemas` |
| `import-airbyte` | Import Airbyte manifests | `jafgen import-airbyte --manifest-file manifest.yaml` |

### Legacy Commands

| Command | Description | Example |
|---------|-------------|---------|
| `run` | Legacy Jaffle Shop simulation (deprecated) | `jafgen run 2 --pre my_data` |

### Global Options

| Option | Description |
|--------|-------------|
| `--version, -v` | Show version information |
| `--help` | Show help message |

## Examples

### Basic Schema-Driven Generation

```shell
# Generate data from all schemas in ./schemas directory
jafgen generate

# Generate with custom directories and seed
jafgen generate --schema-dir ./my-schemas --output-dir ./data --seed 42

# Validate schemas before generation
jafgen validate-schema && jafgen generate
```

### Working with Templates

```shell
# Copy a template to your schemas directory
cp -r schemas/saas-templates/hubspot ./my-schemas/

# Customize the schema files as needed
# Then generate data
jafgen generate --schema-dir ./my-schemas
```

### Airbyte Integration

```shell
# Import an Airbyte manifest
jafgen import-airbyte --manifest-file airbyte_source/manifest.yaml --output-dir ./schemas

# Generate data from imported schemas
jafgen generate --schema-dir ./schemas
```

## Contribution

We welcome contribution to the project! It's relatively simple to get started, just clone the repo, spin up a virtual environment, and install the dependencies:

```shell
gh repo clone dbt-labs/jaffle-shop-generator
python3 -m venv .venv
# Install the package requirements
pip install -r requirements.txt
# Install the dev tooling (ruff and pytest)
pip install -r dev-requirements.txt
# Install the package in editable mode
pip install -e .
```

Working out from the `jafgen` command, you can see the main entrypoint in `jafgen/cli.py`. For schema-driven generation, the core logic is in the `jafgen/schema/`, `jafgen/generation/`, and `jafgen/output/` modules. The legacy simulation is found in `jafgen/simulation.py`.

We recommend installing our githook scripts locally. To do that, install [Lefthook](https://github.com/evilmartians/lefthook) and run
```
lefthook install
```
