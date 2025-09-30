# Jafgen Tutorial: Common Use Cases

This tutorial walks through common use cases for jafgen's schema-driven data generation, from basic examples to advanced scenarios.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Entity Definition](#basic-entity-definition)
3. [Entity Relationships](#entity-relationships)
4. [Multiple Output Formats](#multiple-output-formats)
5. [Working with Constraints](#working-with-constraints)
6. [Time Series Data](#time-series-data)
7. [Financial Data](#financial-data)
8. [Importing from Airbyte](#importing-from-airbyte)
9. [Using SaaS Templates](#using-saas-templates)
10. [Advanced Patterns](#advanced-patterns)

## Getting Started

### Installation

```bash
pip install jafgen
```

### Your First Schema

Create a directory for your schemas and add a simple YAML file:

```bash
mkdir schemas
```

Create `schemas/users.yaml`:

```yaml
system:
  name: "users"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
    path: "./output"

entities:
  users:
    count: 100
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
```

Generate data:

```bash
jafgen generate --schema-dir ./schemas --output-dir ./output
```

## Basic Entity Definition

### Common Attribute Types

```yaml
entities:
  products:
    count: 50
    attributes:
      # Identifiers
      id:
        type: "uuid"
        unique: true
        required: true
      
      # Text fields
      name:
        type: "text.word"
        required: true
      description:
        type: "text.sentence"
        constraints:
          nb_words: 15
      
      # Numbers
      price:
        type: "numeric.decimal"
        constraints:
          min_value: 5.00
          max_value: 500.00
          precision: 2
      quantity:
        type: "numeric.integer"
        constraints:
          min_value: 0
          max_value: 1000
      
      # Dates
      created_at:
        type: "datetime.datetime"
        constraints:
          start_date: "2020-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
      
      # Choices
      category:
        type: "choice"
        constraints:
          choices: ["Electronics", "Clothing", "Books", "Home"]
      
      # Booleans
      is_active:
        type: "development.boolean"
        required: true
```

### Required vs Optional Fields

```yaml
attributes:
  # Required field (default)
  name:
    type: "person.full_name"
    required: true
  
  # Optional field
  middle_name:
    type: "person.first_name"
    required: false
  
  # Required is true by default
  email:
    type: "person.email"
    unique: true
```

## Entity Relationships

### One-to-Many Relationships

```yaml
system:
  name: "blog"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv"]
    path: "./output"

entities:
  authors:
    count: 10
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

  posts:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      author_id:
        type: "link"
        link_to: "blog.authors.id"  # Format: system.entity.attribute
        required: true
      title:
        type: "text.sentence"
        constraints:
          nb_words: 8
      content:
        type: "text.paragraph"
      published_at:
        type: "datetime.datetime"
        constraints:
          start_date: "2020-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
```

### Many-to-Many Relationships

```yaml
entities:
  students:
    count: 200
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true

  courses:
    count: 20
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      credits:
        type: "numeric.integer"
        constraints:
          min_value: 1
          max_value: 6

  enrollments:
    count: 800
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      student_id:
        type: "link"
        link_to: "university.students.id"
        required: true
      course_id:
        type: "link"
        link_to: "university.courses.id"
        required: true
      enrolled_at:
        type: "datetime.date"
        constraints:
          start_date: "2020-01-01"
          end_date: "2024-12-31"
      grade:
        type: "choice"
        required: false
        constraints:
          choices: ["A", "B", "C", "D", "F"]
```

## Multiple Output Formats

### Generate All Formats

```yaml
system:
  name: "multi-format"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "json", "parquet", "duckdb"]
    path: "./output"

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
```

This will generate:
- `output/customers.csv`
- `output/customers.json`
- `output/customers.parquet`
- `output/multi-format.duckdb` (contains customers table)

### Format-Specific Use Cases

- **CSV**: Excel compatibility, simple analysis
- **JSON**: API responses, NoSQL databases
- **Parquet**: Big data analytics, data warehouses
- **DuckDB**: Local SQL analysis, data exploration

## Working with Constraints

### Numeric Constraints

```yaml
attributes:
  # Integer with range
  age:
    type: "numeric.integer"
    constraints:
      min_value: 18
      max_value: 65
  
  # Decimal with precision
  salary:
    type: "numeric.decimal"
    constraints:
      min_value: 30000.00
      max_value: 200000.00
      precision: 2
  
  # Percentage
  discount:
    type: "numeric.decimal"
    constraints:
      min_value: 0.00
      max_value: 1.00
      precision: 4
```

### Date Constraints

```yaml
attributes:
  # Date range
  birth_date:
    type: "datetime.date"
    constraints:
      start_date: "1970-01-01"
      end_date: "2005-12-31"
  
  # DateTime with time
  created_at:
    type: "datetime.datetime"
    constraints:
      start_date: "2020-01-01T00:00:00"
      end_date: "2024-12-31T23:59:59"
  
  # Recent dates only
  last_login:
    type: "datetime.datetime"
    constraints:
      start_date: "2024-01-01T00:00:00"
      end_date: "2024-12-31T23:59:59"
```

### Text Constraints

```yaml
attributes:
  # Short description
  summary:
    type: "text.sentence"
    constraints:
      nb_words: 10
  
  # Long content
  article:
    type: "text.paragraph"
    constraints:
      nb_sentences: 5
  
  # Single word
  tag:
    type: "text.word"
```

### Choice Constraints

```yaml
attributes:
  # Status field
  status:
    type: "choice"
    constraints:
      choices: ["active", "inactive", "pending", "suspended"]
  
  # Priority levels
  priority:
    type: "choice"
    constraints:
      choices: ["low", "medium", "high", "critical"]
  
  # Geographic regions
  region:
    type: "choice"
    constraints:
      choices: ["North", "South", "East", "West", "Central"]
```

## Time Series Data

### IoT Sensor Data

```yaml
system:
  name: "iot-monitoring"
  version: "1.0.0"
  seed: 42
  output:
    format: ["parquet", "duckdb"]
    path: "./output"

entities:
  sensors:
    count: 100
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      location:
        type: "address.city"
        required: true
      sensor_type:
        type: "choice"
        constraints:
          choices: ["temperature", "humidity", "pressure", "motion"]

  readings:
    count: 100000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      sensor_id:
        type: "link"
        link_to: "iot-monitoring.sensors.id"
        required: true
      timestamp:
        type: "datetime.datetime"
        constraints:
          start_date: "2024-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
      value:
        type: "numeric.decimal"
        constraints:
          min_value: -50.0
          max_value: 150.0
          precision: 2
      unit:
        type: "choice"
        constraints:
          choices: ["celsius", "fahrenheit", "percent", "pascal"]
```

### Log Data

```yaml
entities:
  applications:
    count: 10
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "text.word"
        required: true
      version:
        type: "development.version"
        required: true

  log_entries:
    count: 50000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      application_id:
        type: "link"
        link_to: "logging.applications.id"
        required: true
      timestamp:
        type: "datetime.datetime"
        constraints:
          start_date: "2024-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
      level:
        type: "choice"
        constraints:
          choices: ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
      message:
        type: "text.sentence"
        constraints:
          nb_words: 12
      source_file:
        type: "text.word"
        required: true
      line_number:
        type: "numeric.integer"
        constraints:
          min_value: 1
          max_value: 10000
```

## Financial Data

### Banking System

```yaml
system:
  name: "banking"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "duckdb"]
    path: "./output"

entities:
  customers:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_number:
        type: "numeric.integer"
        unique: true
        constraints:
          min_value: 100000
          max_value: 999999
      name:
        type: "person.full_name"
        required: true
      ssn:
        type: "person.identifier"
        unique: true
        required: true
      credit_score:
        type: "numeric.integer"
        constraints:
          min_value: 300
          max_value: 850

  accounts:
    count: 2500
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      account_number:
        type: "numeric.integer"
        unique: true
        constraints:
          min_value: 1000000000
          max_value: 9999999999
      customer_id:
        type: "link"
        link_to: "banking.customers.id"
        required: true
      account_type:
        type: "choice"
        constraints:
          choices: ["checking", "savings", "money_market", "cd"]
      balance:
        type: "numeric.decimal"
        constraints:
          min_value: 0.00
          max_value: 1000000.00
          precision: 2

  transactions:
    count: 50000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      account_id:
        type: "link"
        link_to: "banking.accounts.id"
        required: true
      transaction_date:
        type: "datetime.datetime"
        constraints:
          start_date: "2020-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
      amount:
        type: "numeric.decimal"
        constraints:
          min_value: -10000.00
          max_value: 50000.00
          precision: 2
      transaction_type:
        type: "choice"
        constraints:
          choices: ["deposit", "withdrawal", "transfer", "payment", "fee"]
      description:
        type: "text.sentence"
        constraints:
          nb_words: 6
```

## Importing from Airbyte

### Import a Manifest

```bash
# Import Airbyte source manifest
jafgen import-airbyte \
  --manifest-file ./airbyte-source/manifest.yaml \
  --output-dir ./schemas \
  --detect-relationships \
  --validate
```

### Customize Imported Schemas

After importing, you can customize the generated schemas:

1. **Adjust entity counts**:
   ```yaml
   entities:
     users:
       count: 10000  # Increase from default 1000
   ```

2. **Add constraints**:
   ```yaml
   attributes:
     created_at:
       type: "datetime.datetime"
       constraints:
         start_date: "2020-01-01T00:00:00"
         end_date: "2024-12-31T23:59:59"
   ```

3. **Modify output formats**:
   ```yaml
   system:
     output:
       format: ["csv", "parquet"]  # Add parquet format
   ```

## Using SaaS Templates

### Available Templates

```bash
# List available templates
ls schemas/saas-templates/
# hubspot/  salesforce/  xero/  huntr/
```

### Use HubSpot Template

```bash
# Copy HubSpot schemas
cp -r schemas/saas-templates/hubspot ./my-schemas/

# Generate HubSpot-like data
jafgen generate --schema-dir ./my-schemas --output-dir ./output
```

### Customize Templates

Edit the copied schema files to fit your needs:

```yaml
# my-schemas/contacts.yaml
entities:
  contacts:
    count: 5000  # Increase from default
    attributes:
      # Add custom fields
      lead_source:
        type: "choice"
        constraints:
          choices: ["website", "referral", "social", "email", "phone"]
      
      # Modify existing constraints
      created_at:
        type: "datetime.datetime"
        constraints:
          start_date: "2022-01-01T00:00:00"  # More recent data
          end_date: "2024-12-31T23:59:59"
```

## Advanced Patterns

### Self-Referencing Entities

```yaml
entities:
  employees:
    count: 500
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: true
      manager_id:
        type: "link"
        link_to: "company.employees.id"
        required: false  # CEO has no manager
      department:
        type: "choice"
        constraints:
          choices: ["Engineering", "Sales", "Marketing", "HR"]
```

### Complex Business Rules

```yaml
entities:
  orders:
    count: 10000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "ecommerce.customers.id"
        required: true
      order_date:
        type: "datetime.datetime"
        constraints:
          start_date: "2020-01-01T00:00:00"
          end_date: "2024-12-31T23:59:59"
      
      # Business rule: orders on weekends get different status
      status:
        type: "choice"
        constraints:
          choices: ["pending", "processing", "shipped", "delivered"]
      
      # Seasonal pricing
      total_amount:
        type: "numeric.decimal"
        constraints:
          min_value: 10.00
          max_value: 2000.00
          precision: 2
```

### Multi-Schema Systems

Create separate schema files for different domains:

```bash
schemas/
├── users.yaml          # User management
├── products.yaml       # Product catalog
├── orders.yaml         # Order processing
└── analytics.yaml      # Analytics events
```

Each can reference entities from others:

```yaml
# orders.yaml
entities:
  orders:
    count: 5000
    attributes:
      customer_id:
        type: "link"
        link_to: "users.customers.id"  # Reference users schema
      product_id:
        type: "link"
        link_to: "products.items.id"   # Reference products schema
```

## Best Practices

### 1. Start Small
```yaml
entities:
  users:
    count: 100  # Start with small counts for testing
```

### 2. Use Meaningful Seeds
```yaml
system:
  seed: 42  # Use consistent seeds for reproducible testing
```

### 3. Validate Early
```bash
# Always validate before generating large datasets
jafgen validate-schema --schema-dir ./schemas
```

### 4. Choose Appropriate Formats
- **Development**: CSV for easy inspection
- **Analytics**: Parquet for performance
- **Exploration**: DuckDB for SQL queries

### 5. Document Your Schemas
```yaml
# Add comments to explain business logic
entities:
  orders:
    count: 10000
    attributes:
      # Customer reference - required for all orders
      customer_id:
        type: "link"
        link_to: "ecommerce.customers.id"
        required: true
```

## Troubleshooting

### Common Issues

1. **Schema validation errors**:
   ```bash
   jafgen validate-schema --schema-dir ./schemas
   ```

2. **Link resolution failures**:
   - Check that referenced entities exist
   - Verify link_to format: `system.entity.attribute`

3. **Unique constraint violations**:
   - Reduce entity count or remove unique constraint
   - Use more diverse attribute types

4. **Memory issues with large datasets**:
   - Reduce entity counts
   - Generate data in batches
   - Use appropriate output formats

### Getting Help

- Check the [API Documentation](API_DOCUMENTATION.md)
- Review [examples](examples/)
- Open issues on GitHub

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more patterns
2. **Try SaaS Templates**: Use pre-built schemas for common systems
3. **Build Custom Schemas**: Create schemas for your specific use cases
4. **Integrate with Tools**: Use generated data with dbt, analytics tools, etc.
5. **Contribute**: Share your schemas and improvements with the community