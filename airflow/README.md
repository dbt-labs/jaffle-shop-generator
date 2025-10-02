# Jaffle Shop Generator - Airflow Integration

This directory contains everything needed to run Jaffle Shop Generator as Airflow DAGs for automated synthetic data generation.

## Quick Start

### 1. Setup Airflow Environment

```bash
# Copy DAG files to your Airflow DAGs directory
cp dags/*.py /path/to/airflow/dags/

# Copy Docker Compose override (if using Docker)
cp docker-compose.override.yml /path/to/airflow/

# Setup Airflow variables
python3 setup_airflow_variables.py
```

### 2. Configure Paths

Update these Airflow Variables in the UI or via CLI:

```bash
# Set base paths
airflow variables set jafgen_base_path "/opt/airflow/jafgen"
airflow variables set jafgen_output_path "/opt/airflow/data"
airflow variables set jafgen_schema_path "/opt/airflow/schemas"

# Set retention policy
airflow variables set jafgen_retention_days "7"
```

### 3. Mount Jaffle Shop Generator

Ensure Jaffle Shop Generator is available in your Airflow environment:

**Docker Setup:**
```yaml
# In docker-compose.yml or override file
volumes:
  - ./jaffle-shop-generator:/opt/airflow/jafgen:ro
  - ./schemas:/opt/airflow/schemas:rw
  - ./data:/opt/airflow/data:rw
```

**Local Setup:**
```bash
# Install Jaffle Shop Generator
pip install -e /path/to/jaffle-shop-generator

# Or add to PYTHONPATH
export PYTHONPATH="/path/to/jaffle-shop-generator:$PYTHONPATH"
```

## Available DAGs

### 1. Daily Stripe Data Generation (`jafgen_stripe_daily`)

**Schedule:** Daily at 2 AM UTC  
**Purpose:** Generate fresh Stripe payment data for development/testing

```bash
# Manual trigger
airflow dags trigger jafgen_stripe_daily

# With custom configuration
airflow dags trigger jafgen_stripe_daily \\
  --conf '{"record_multiplier": 2.0}'
```

**Output:**
- `/data/stripe/YYYY-MM-DD/csv/` - CSV files
- `/data/stripe/YYYY-MM-DD/json/` - JSON files

### 2. Weekly Multi-API Generation (`jafgen_multi_api_weekly`)

**Schedule:** Weekly on Sunday at 1 AM UTC  
**Purpose:** Comprehensive data generation for multiple APIs

**APIs Included:**
- **Stripe** - Payment processing (2x records)
- **Plaid** - Financial services (1.5x records)  
- **Light.inc** - Expense management (1.8x records)

```bash
# Manual trigger
airflow dags trigger jafgen_multi_api_weekly
```

**Output:**
- `/data/stripe/YYYY-MM-DD/` - Stripe data (CSV, JSON, Parquet)
- `/data/plaid/YYYY-MM-DD/` - Plaid data (CSV, JSON, Parquet)
- `/data/light/YYYY-MM-DD/` - Light.inc data (CSV, JSON, Parquet)

### 3. Airbyte Connector Import (`jafgen_airbyte_import`)

**Schedule:** Manual trigger only  
**Purpose:** Import any Airbyte connector and generate data

```bash
# Import Shopify connector
airflow dags trigger jafgen_airbyte_import \\
  --conf '{
    "manifest_url": "https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-shopify/manifest.yaml",
    "api_name": "shopify",
    "record_multiplier": 1.5,
    "output_formats": ["csv", "json", "parquet"]
  }'

# Import custom connector
airflow dags trigger jafgen_airbyte_import \\
  --conf '{
    "manifest_url": "https://my-company.com/custom-manifest.yaml",
    "api_name": "custom_api"
  }'
```

**Output:**
- `/schemas/imported/{api_name}/` - Converted schemas
- `/data/imported/{api_name}/YYYY-MM-DD/` - Generated data

## Configuration

### Airflow Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `jafgen_base_path` | `/opt/airflow/jafgen` | Jaffle Shop installation path |
| `jafgen_output_path` | `/opt/airflow/data` | Data output directory |
| `jafgen_schema_path` | `/opt/airflow/schemas` | Schema files directory |
| `jafgen_retention_days` | `7` | Days to retain generated data |
| `jafgen_default_seed` | `42` | Default generation seed |
| `jafgen_max_records_per_entity` | `10000` | Maximum records per entity |

### DAG Configuration

Each DAG can be configured via `dag_run.conf`:

```json
{
  "record_multiplier": 2.0,
  "output_formats": ["csv", "json", "parquet"],
  "generation_seed": 42,
  "custom_entities": {
    "customers": 5000,
    "transactions": 25000
  }
}
```

## Directory Structure

```
airflow/
├── dags/
│   ├── jafgen_stripe_daily.py          # Daily Stripe generation
│   ├── jafgen_multi_api_weekly.py      # Weekly multi-API generation
│   └── jafgen_airbyte_import.py        # Dynamic Airbyte import
├── docker-compose.override.yml         # Docker configuration
├── setup_airflow_variables.py          # Variable setup script
└── README.md                           # This file

/opt/airflow/
├── jafgen/                             # Jaffle Shop Generator
├── schemas/                            # Schema files
│   ├── saas-templates/                 # Pre-built schemas
│   └── imported/                       # Imported schemas
└── data/                               # Generated data
    ├── stripe/                         # Stripe data by date
    ├── plaid/                          # Plaid data by date
    ├── light/                          # Light.inc data by date
    └── imported/                       # Imported API data
```

## Monitoring & Alerting

### Built-in Monitoring

Each DAG includes:
- **Data Quality Validation** - Automatic quality checks
- **File Existence Verification** - Ensures all files generated
- **Record Count Validation** - Verifies expected data volumes
- **Error Handling** - Comprehensive error reporting

### Custom Alerts

Add Slack/email notifications:

```python
# In DAG default_args
default_args = {
    'email_on_failure': True,
    'email': ['data-team@company.com'],
    'on_failure_callback': slack_failed_task,
}
```

### Metrics Collection

Monitor via Airflow UI:
- Task duration and success rates
- Data generation statistics (via XCom)
- Quality metrics and validation results
- Storage usage and retention

## Cloud Integration

### S3 Storage

```python
# Set S3 bucket variable
airflow variables set jafgen_s3_bucket "my-synthetic-data-bucket"

# Data automatically uploaded after generation
```

### Database Loading

```python
# Set database connection
airflow variables set jafgen_db_url "postgresql://user:pass@host:5432/db"

# Data automatically loaded to timestamped tables
```

### GCS Storage

```python
# Set GCS bucket variable  
airflow variables set jafgen_gcs_bucket "my-synthetic-data-bucket"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check Python path
   airflow config get-value core executor
   
   # Verify Jaffle Shop installation
   python -c "import jafgen; print('OK')"
   ```

2. **Permission Issues**
   ```bash
   # Fix data directory permissions
   chmod -R 755 /opt/airflow/data
   chown -R airflow:airflow /opt/airflow/data
   ```

3. **Memory Issues**
   ```bash
   # Reduce record counts in DAG configuration
   airflow dags trigger jafgen_stripe_daily \\
     --conf '{"record_multiplier": 0.5}'
   ```

### Validation

```bash
# Validate setup
python3 setup_airflow_variables.py --validate

# Check DAG syntax
airflow dags list | grep jafgen

# Test DAG parsing
airflow dags show jafgen_stripe_daily
```

### Logs

```bash
# View task logs
airflow tasks log jafgen_stripe_daily generate_stripe_data 2024-01-15

# View DAG run logs
airflow dags state jafgen_stripe_daily 2024-01-15
```

## Performance Optimization

### Parallel Execution

```python
# Enable parallel API generation
with TaskGroup('parallel_apis') as group:
    for api in apis:
        generate_task = PythonOperator(...)
```

### Resource Management

```yaml
# In docker-compose.yml
services:
  airflow-worker:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
```

### Incremental Processing

```python
# Generate only new/changed data
def incremental_generation(**context):
    last_run = context.get('prev_ds')
    # Generate incremental data only
```

## Best Practices

### 1. Data Retention
- Set appropriate retention policies
- Monitor storage usage
- Archive old data to cold storage

### 2. Quality Assurance
- Always validate generated data
- Monitor quality metrics over time
- Set up alerts for quality degradation

### 3. Resource Management
- Scale record counts based on usage
- Use appropriate output formats
- Monitor memory and CPU usage

### 4. Security
- Use Airflow Connections for sensitive data
- Encrypt data at rest and in transit
- Implement proper access controls

## Support

For issues and questions:
1. Check Airflow logs for detailed error messages
2. Validate configuration with setup script
3. Review DAG documentation in Airflow UI
4. Refer to main Jaffle Shop Generator documentation

## Examples

### Custom API Integration

```python
# Create custom DAG for your API
from airflow import DAG
from jafgen_common import generate_api_data

dag = DAG('my_custom_api_daily', ...)

generate_task = PythonOperator(
    task_id='generate_my_api',
    python_callable=generate_api_data('my_api', {
        'schema_path': 'schemas/custom/my_api',
        'multiplier': 1.0
    })
)
```

### Conditional Generation

```python
# Generate data based on conditions
def conditional_generation(**context):
    if context['ds_nodash'] % 7 == 0:  # Weekly on Sundays
        return generate_large_dataset()
    else:
        return generate_small_dataset()
```

This Airflow integration provides a production-ready foundation for automated synthetic data generation at scale.