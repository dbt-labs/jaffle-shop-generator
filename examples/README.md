# Jafgen Examples

This directory contains example YAML schemas demonstrating various features of jafgen's schema-driven data generation.

## Basic Examples

### Simple Entity
- **File**: `simple-users.yaml`
- **Features**: Basic entity with common attribute types
- **Use Case**: Getting started with schema-driven generation

### Linked Entities  
- **File**: `e-commerce.yaml`
- **Features**: Multiple entities with foreign key relationships
- **Use Case**: Relational data modeling

### Multiple Output Formats
- **File**: `multi-format.yaml` 
- **Features**: Generate data in CSV, JSON, Parquet, and DuckDB formats
- **Use Case**: Supporting different downstream systems

## Advanced Examples

### Complex Relationships
- **File**: `social-network.yaml`
- **Features**: Many-to-many relationships, self-referencing entities
- **Use Case**: Complex data modeling scenarios

### Time Series Data
- **File**: `iot-sensors.yaml`
- **Features**: Time-based data with constraints and patterns
- **Use Case**: IoT and monitoring data

### Financial Data
- **File**: `banking.yaml`
- **Features**: Decimal precision, date ranges, business rules
- **Use Case**: Financial and accounting systems

## Running Examples

1. **Copy examples to your schemas directory:**
   ```bash
   cp examples/*.yaml ./schemas/
   ```

2. **Generate data:**
   ```bash
   jafgen generate --schema-dir ./schemas --output-dir ./output
   ```

3. **Validate schemas:**
   ```bash
   jafgen validate-schema --schema-dir ./schemas
   ```

## Customization Tips

- Adjust `count` values to generate more or fewer records
- Modify `constraints` to fit your data requirements  
- Change `seed` values for different data variations
- Update `output.format` to generate different file types
- Add or remove `link_to` attributes to change relationships

## SaaS Templates

For production-ready schemas, check out the SaaS templates in `schemas/saas-templates/`:
- HubSpot (CRM)
- Salesforce (CRM) 
- Xero (Accounting)
- Huntr (Job Tracking)