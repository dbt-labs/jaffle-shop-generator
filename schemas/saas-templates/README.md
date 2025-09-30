# SaaS System Schema Templates

This directory contains pre-built YAML schema templates for popular SaaS systems, allowing you to quickly generate realistic test data for common integrations and use cases.

## Available Templates

### HubSpot CRM
- **contacts.yaml** - HubSpot contact records with lead scoring, lifecycle stages, and marketing attribution
- **companies.yaml** - Company records with industry classification, revenue data, and relationship tracking  
- **deals.yaml** - Sales opportunity records with pipeline stages, amounts, and forecasting data

### Salesforce CRM
- **accounts.yaml** - Salesforce account records with industry classification, revenue, and address data
- **contacts.yaml** - Contact records with professional information, relationships, and communication preferences
- **opportunities.yaml** - Sales opportunity records with stages, amounts, forecasting, and competitive tracking

### Xero Accounting
- **customers.yaml** - Customer/contact records with financial details, tax information, and address data
- **invoices.yaml** - Invoice records with line items, tax calculations, payment status, and currency handling
- **payments.yaml** - Payment records with bank details, reconciliation status, and allocation tracking

### Huntr Job Tracking
- **jobs.yaml** - Job opportunity records with application status, salary ranges, and company information
- **activities.yaml** - Job application activities including interviews, follow-ups, and networking events
- **contacts.yaml** - Professional networking contacts with relationship tracking and communication history

## Usage Examples

### Generate HubSpot Test Data

```bash
# Generate HubSpot contacts data
jafgen generate --schema-dir schemas/saas-templates/hubspot --output-dir output/hubspot

# Generate specific entity
jafgen generate --schema schemas/saas-templates/hubspot/contacts.yaml
```

### Generate Xero Financial Data

```bash
# Generate complete Xero dataset
jafgen generate --schema-dir schemas/saas-templates/xero --output-dir output/xero

# Generate invoices with relationships to customers
jafgen generate --schema schemas/saas-templates/xero/customers.yaml schemas/saas-templates/xero/invoices.yaml
```

### Generate Job Search Data

```bash
# Generate Huntr job tracking data
jafgen generate --schema-dir schemas/saas-templates/huntr --output-dir output/huntr
```

## Customization

Each template can be customized by:

1. **Adjusting record counts** - Modify the `count` field for each entity
2. **Changing output formats** - Update the `output.format` array (csv, json, parquet, duckdb)
3. **Modifying constraints** - Adjust min/max values, date ranges, and choice options
4. **Adding relationships** - Use `link_to` attributes to create cross-entity relationships

### Example Customization

```yaml
# Increase contact count and add custom constraints
entities:
  contacts:
    count: 5000  # Generate more records
    attributes:
      hubspotscore:
        type: "integer"
        constraints:
          min_value: 50  # Only high-scoring leads
          max_value: 100
```

## Relationships Between Entities

The templates are designed with realistic relationships:

### HubSpot
- Deals reference Contacts and Companies via ID fields
- Contacts can be associated with Companies
- All entities share common owner and lifecycle tracking

### Salesforce  
- Contacts belong to Accounts
- Opportunities are linked to Accounts and primary Contacts
- Hierarchical account relationships supported

### Xero
- Invoices reference Customers
- Payments are allocated to specific Invoices
- Multi-currency support with exchange rates

### Huntr
- Activities are linked to specific Jobs
- Contacts can be associated with multiple Jobs
- Application timeline tracking across entities

## Data Quality Features

All templates include:

- **Realistic constraints** - Appropriate value ranges and formats
- **Unique identifiers** - UUIDs and unique business keys
- **Temporal consistency** - Logical date relationships
- **Industry-standard formats** - Email addresses, phone numbers, currencies
- **Deterministic generation** - Reproducible datasets with seeding

## Integration Testing

These templates are ideal for:

- **API integration testing** - Generate data matching real system schemas
- **Data pipeline testing** - Test ETL processes with realistic volumes
- **Performance testing** - Generate large datasets for load testing
- **Demo environments** - Populate systems with believable sample data
- **Training and documentation** - Provide realistic examples for user guides

## Contributing

To add new SaaS templates:

1. Research the target system's data model and API documentation
2. Create YAML schemas following the established patterns
3. Include comprehensive attribute coverage with realistic constraints
4. Add relationship modeling where appropriate
5. Write tests to verify schema validity and data generation
6. Update this README with usage examples