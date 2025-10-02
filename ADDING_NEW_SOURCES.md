# Adding New Data Sources to Jaffle Shop Generator

This guide shows you how to add new data sources (like Stripe, Shopify, etc.) to generate realistic synthetic data.

## Two Approaches

### 1. Manual YAML Schema (Recommended)
Create custom schemas with full control over data structure and relationships.

### 2. Airbyte Import (Automated)
Import schemas automatically from Airbyte connector metadata.

---

## Approach 1: Manual YAML Schema

### Step 1: Create Schema Directory
```bash
mkdir -p schemas/saas-templates/your-service
```

### Step 2: Define Entity Schemas

Create YAML files for each entity. Here's a Stripe example:

**schemas/saas-templates/stripe/customers.yaml**
```yaml
system:
  name: "stripe-customers"
  version: "1.0.0"
  seed: 42
  output:
    format: ["csv", "json"]
    path: "stripe"

entities:
  customers:
    count: 1000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      email:
        type: "person.email"
        unique: true
        required: true
      name:
        type: "person.full_name"
        required: false
      # Add more attributes...
```

### Step 3: Add Relationships

Link entities together using `link_to`:

**schemas/saas-templates/stripe/charges.yaml**
```yaml
entities:
  charges:
    count: 5000
    attributes:
      id:
        type: "uuid"
        unique: true
        required: true
      customer_id:
        type: "link"
        link_to: "stripe-customers.customers.id"  # Links to customers
        required: true
      amount:
        type: "integer"
        constraints:
          min_value: 100
          max_value: 100000
```

### Step 4: Available Data Types

| Type | Description | Example |
|------|-------------|---------|
| `uuid` | Unique identifier | `01b4cd0f-ca62-4b0f-8285-f769a4dd36ce` |
| `person.email` | Email address | `user@example.com` |
| `person.full_name` | Full name | `John Smith` |
| `person.phone` | Phone number | `+1-555-123-4567` |
| `integer` | Whole number | `42` |
| `decimal` | Decimal number | `19.99` |
| `datetime.datetime` | Date and time | `2025-01-15 14:30:00` |
| `boolean` | True/false | `true` |
| `choice` | Pick from list | See constraints |
| `text.word` | Single word | `example` |
| `text.sentence` | Full sentence | `This is a sentence.` |
| `address.city` | City name | `New York` |
| `internet.url` | Web URL | `https://example.com` |

### Step 5: Add Constraints

```yaml
attributes:
  amount:
    type: "integer"
    constraints:
      min_value: 100
      max_value: 50000
  
  status:
    type: "choice"
    constraints:
      choices: ["active", "inactive", "pending"]
  
  price:
    type: "decimal"
    constraints:
      min_value: 1.0
      max_value: 999.99
      precision: 2
```

### Step 6: Test Your Schema

```python
from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver
from pathlib import Path

# Load your schemas
discovery = SchemaDiscoveryEngine()
schemas, validation = discovery.discover_and_load_schemas(Path('schemas/saas-templates/your-service'))

# Generate data
engine = MimesisEngine(seed=42)
resolver = LinkResolver()
generator = DataGenerator(engine, resolver)

results = generator.generate_multiple_systems(schemas)

# Check results
for result in results:
    print(f'{result.schema.name}: {len(result.entities)} entities')
```

---

## Approach 2: Airbyte Import

### Step 1: Get Airbyte Connector Spec

Download the connector specification from Airbyte:
```bash
# Example for Stripe
curl -o stripe-spec.json https://connectors.airbyte.com/files/metadata/airbyte/source-stripe/latest/spec.json
```

### Step 2: Import Schema

```bash
jafgen import-airbyte stripe-spec.json --output schemas/stripe-airbyte
```

This automatically creates YAML schemas based on the Airbyte connector metadata.

### Step 3: Customize Generated Schemas

The imported schemas may need tweaking:
- Adjust record counts
- Add realistic constraints
- Modify data types for better realism

---

## Real-World Examples

### Stripe Payment Platform
```
schemas/saas-templates/stripe/
├── customers.yaml      # Customer records
├── charges.yaml        # Payment transactions
├── subscriptions.yaml  # Recurring billing
└── invoices.yaml       # Invoice data
```

### Shopify E-commerce
```
schemas/saas-templates/shopify/
├── customers.yaml      # Customer profiles
├── products.yaml       # Product catalog
├── orders.yaml         # Order transactions
└── inventory.yaml      # Stock levels
```

### Salesforce CRM
```
schemas/saas-templates/salesforce/
├── accounts.yaml       # Company accounts
├── contacts.yaml       # Individual contacts
├── opportunities.yaml  # Sales opportunities
└── activities.yaml     # Sales activities
```

---

## Best Practices

### 1. Realistic Data Volumes
```yaml
entities:
  customers:
    count: 10000        # Large customer base
  orders:
    count: 50000        # 5x more orders than customers
  order_items:
    count: 150000       # 3x more items than orders
```

### 2. Proper Relationships
```yaml
# Always link child entities to parents
order_id:
  type: "link"
  link_to: "orders-schema.orders.id"
  required: true
```

### 3. Business Logic Constraints
```yaml
# Stripe amounts are in cents
amount:
  type: "integer"
  constraints:
    min_value: 50      # $0.50 minimum
    max_value: 100000  # $1,000 maximum

# Realistic subscription intervals
interval:
  type: "choice"
  constraints:
    choices: ["month", "year", "quarter"]
```

### 4. Consistent Naming
- Use service prefix: `stripe-customers`, `shopify-products`
- Follow API field names when possible
- Use snake_case for attributes

---

## Testing Your Schema

Create a test file:

**tests/test_your_service.py**
```python
import pytest
from pathlib import Path
from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver

def test_your_service_schemas():
    """Test that your service schemas work correctly."""
    discovery = SchemaDiscoveryEngine()
    schemas, validation = discovery.discover_and_load_schemas(
        Path('schemas/saas-templates/your-service')
    )
    
    assert validation.is_valid
    assert len(schemas) > 0
    
    # Test data generation
    engine = MimesisEngine(seed=42)
    resolver = LinkResolver()
    generator = DataGenerator(engine, resolver)
    
    results = generator.generate_multiple_systems(schemas)
    
    # Verify relationships work
    for result in results:
        for entity_name, data in result.entities.items():
            assert len(data) > 0
            # Add specific assertions for your data
```

---

## Need Help?

1. **Check existing examples** in `schemas/saas-templates/`
2. **Review data types** in the mimesis documentation
3. **Test incrementally** - start with one entity, then add relationships
4. **Use realistic constraints** based on the actual service's API

The manual YAML approach gives you the most control and is recommended for most use cases. Use Airbyte import when you want to quickly bootstrap from existing connector metadata.