# Airflow Integration Guide

## Running Jaffle Shop Generator as Airflow DAGs

This guide shows how to integrate Jaffle Shop Generator with Apache Airflow for automated, scheduled synthetic data generation. Perfect for maintaining fresh test data, populating development environments, and running regular data pipeline tests.

## Overview

Airflow integration enables:
- **Scheduled Data Generation**: Daily, weekly, or custom schedules
- **Multi-API Workflows**: Generate data for multiple APIs in sequence
- **Data Pipeline Testing**: Automated testing with fresh synthetic data
- **Environment Management**: Keep dev/staging environments populated
- **Monitoring & Alerting**: Track data generation success/failure
- **Scalable Execution**: Distributed generation across Airflow workers

## Prerequisites

### Required Software
- **Apache Airflow** 2.0+ installed and configured
- **Python** 3.8+ with Jaffle Shop Generator installed
- **Database** for Airflow metadata (PostgreSQL recommended)
- **File Storage** for generated data (S3, GCS, or local filesystem)

### Jaffle Shop Installation
```bash
# Install Jaffle Shop Generator in Airflow environment
pip install -e /path/to/jaffle-shop-generator

# Or install from requirements
echo "jafgen" >> requirements.txt
pip install -r requirements.txt
```

## Basic DAG Structure

### Simple Single-API DAG

Create `dags/jafgen_stripe_daily.py`:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from pathlib import Path
import os

# DAG Configuration
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'jafgen_stripe_daily',
    default_args=default_args,
    description='Generate daily Stripe synthetic data',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['jafgen', 'stripe', 'synthetic-data'],
)

def generate_stripe_data(**context):
    """Generate Stripe synthetic data using Jaffle Shop."""
    from jafgen.schema.discovery import SchemaDiscoveryEngine
    from jafgen.generation.data_generator import DataGenerator
    from jafgen.generation.mimesis_engine import MimesisEngine
    from jafgen.generation.link_resolver import LinkResolver
    from jafgen.output.csv_writer import CSVWriter
    from jafgen.output.json_writer import JSONWriter
    
    # Configuration
    schema_path = Path('/opt/airflow/schemas/saas-templates/stripe')
    output_path = Path(f'/opt/airflow/data/stripe/{context["ds"]}')
    seed = int(context['ds_nodash'])  # Use date as seed for reproducibility
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load schemas
    discovery = SchemaDiscoveryEngine()
    schemas, validation = discovery.discover_and_load_schemas(schema_path)
    
    if not validation.is_valid:
        raise ValueError(f"Schema validation failed: {validation.errors}")
    
    # Generate data
    engine = MimesisEngine(seed=seed)
    resolver = LinkResolver()
    generator = DataGenerator(engine, resolver)
    
    results = generator.generate_multiple_systems(schemas)
    
    # Write outputs
    csv_writer = CSVWriter()
    json_writer = JSONWriter()
    
    total_records = 0
    for result in results:
        csv_writer.write(result.entities, output_path / 'csv')
        json_writer.write(result.entities, output_path / 'json')
        
        for entity_name, data in result.entities.items():
            total_records += len(data)
    
    # Log results
    print(f"Generated {total_records} Stripe records for {context['ds']}")
    return total_records

def validate_output(**context):
    """Validate generated data quality."""
    output_path = Path(f'/opt/airflow/data/stripe/{context["ds"]}')
    
    # Check files exist
    csv_files = list((output_path / 'csv').glob('*.csv'))
    json_files = list((output_path / 'json').glob('*.json'))
    
    if not csv_files or not json_files:
        raise ValueError("Generated files not found")
    
    # Basic validation
    for csv_file in csv_files:
        if csv_file.stat().st_size == 0:
            raise ValueError(f"Empty CSV file: {csv_file}")
    
    print(f"Validation passed: {len(csv_files)} CSV files, {len(json_files)} JSON files")
    return True

# Tasks
generate_task = PythonOperator(
    task_id='generate_stripe_data',
    python_callable=generate_stripe_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_output',
    python_callable=validate_output,
    dag=dag,
)

cleanup_task = BashOperator(
    task_id='cleanup_old_data',
    bash_command="""
    # Keep only last 7 days of data
    find /opt/airflow/data/stripe -type d -mtime +7 -exec rm -rf {} +
    """,
    dag=dag,
)

# Task dependencies
generate_task >> validate_task >> cleanup_task
```

## Advanced Multi-API DAG

Create `dags/jafgen_multi_api_weekly.py`:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup
from pathlib import Path

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'jafgen_multi_api_weekly',
    default_args=default_args,
    description='Weekly synthetic data generation for multiple APIs',
    schedule_interval='0 1 * * 0',  # Weekly on Sunday at 1 AM
    catchup=False,
    tags=['jafgen', 'multi-api', 'weekly'],
)

def generate_api_data(api_name, schema_path, record_multiplier=1):
    """Generic function to generate data for any API."""
    def _generate(**context):
        from jafgen.schema.discovery import SchemaDiscoveryEngine
        from jafgen.generation.data_generator import DataGenerator
        from jafgen.generation.mimesis_engine import MimesisEngine
        from jafgen.generation.link_resolver import LinkResolver
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.json_writer import JSONWriter
        from jafgen.output.parquet_writer import ParquetWriter
        
        # Configuration
        output_path = Path(f'/opt/airflow/data/{api_name}/{context["ds"]}')
        seed = int(context['ds_nodash']) + hash(api_name)  # Unique seed per API
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load and generate
        discovery = SchemaDiscoveryEngine()
        schemas, validation = discovery.discover_and_load_schemas(Path(schema_path))
        
        if not validation.is_valid:
            raise ValueError(f"{api_name} schema validation failed")
        
        # Scale record counts for weekly generation
        for schema in schemas:
            for entity in schema.entities.values():
                entity.count = int(entity.count * record_multiplier)
        
        engine = MimesisEngine(seed=seed)
        resolver = LinkResolver()
        generator = DataGenerator(engine, resolver)
        
        results = generator.generate_multiple_systems(schemas)
        
        # Write multiple formats
        csv_writer = CSVWriter()
        json_writer = JSONWriter()
        parquet_writer = ParquetWriter()
        
        total_records = 0
        for result in results:
            csv_writer.write(result.entities, output_path / 'csv')
            json_writer.write(result.entities, output_path / 'json')
            parquet_writer.write(result.entities, output_path / 'parquet')
            
            for entity_name, data in result.entities.items():
                total_records += len(data)
        
        print(f"Generated {total_records} {api_name} records")
        return total_records
    
    return _generate

# API configurations
apis = {
    'stripe': {
        'schema_path': '/opt/airflow/schemas/saas-templates/stripe',
        'multiplier': 2.0,  # 2x records for weekly batch
    },
    'plaid': {
        'schema_path': '/opt/airflow/schemas/saas-templates/plaid',
        'multiplier': 1.5,
    },
    'light': {
        'schema_path': '/opt/airflow/schemas/saas-templates/light',
        'multiplier': 1.8,
    },
}

start = DummyOperator(task_id='start', dag=dag)
end = DummyOperator(task_id='end', dag=dag)

# Create task groups for each API
for api_name, config in apis.items():
    with TaskGroup(group_id=f'{api_name}_generation', dag=dag) as api_group:
        
        generate = PythonOperator(
            task_id=f'generate_{api_name}_data',
            python_callable=generate_api_data(
                api_name, 
                config['schema_path'], 
                config['multiplier']
            ),
        )
        
        validate = PythonOperator(
            task_id=f'validate_{api_name}_data',
            python_callable=lambda **ctx, api=api_name: validate_api_data(api, **ctx),
        )
        
        generate >> validate
    
    start >> api_group >> end

def validate_api_data(api_name, **context):
    """Validate generated API data."""
    output_path = Path(f'/opt/airflow/data/{api_name}/{context["ds"]}')
    
    formats = ['csv', 'json', 'parquet']
    for fmt in formats:
        format_path = output_path / fmt
        if not format_path.exists():
            raise ValueError(f"Missing {fmt} output for {api_name}")
        
        files = list(format_path.glob(f'*.{fmt}'))
        if not files:
            raise ValueError(f"No {fmt} files generated for {api_name}")
    
    return True
```

## Airbyte Integration DAG

Create `dags/jafgen_airbyte_import.py`:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from pathlib import Path

default_args = {
    'owner': 'data-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

dag = DAG(
    'jafgen_airbyte_import',
    default_args=default_args,
    description='Import Airbyte connector and generate data',
    schedule_interval=None,  # Manual trigger
    tags=['jafgen', 'airbyte', 'import'],
)

def import_airbyte_connector(**context):
    """Import Airbyte connector manifest and generate schemas."""
    from jafgen.airbyte.translator import AirbyteTranslator
    
    # Configuration from Airflow Variables or context
    manifest_url = context['dag_run'].conf.get('manifest_url')
    api_name = context['dag_run'].conf.get('api_name', 'imported_api')
    
    if not manifest_url:
        raise ValueError("manifest_url required in DAG run configuration")
    
    # Download manifest
    import requests
    response = requests.get(manifest_url)
    response.raise_for_status()
    
    manifest_path = Path(f'/tmp/{api_name}_manifest.yaml')
    manifest_path.write_text(response.text)
    
    # Translate to jafgen schemas
    translator = AirbyteTranslator()
    schemas = translator.translate_manifest(manifest_path)
    
    # Save schemas
    output_dir = Path(f'/opt/airflow/schemas/imported/{api_name}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from jafgen.schema.yaml_loader import YAMLSchemaLoader
    loader = YAMLSchemaLoader()
    
    for schema in schemas:
        schema_file = output_dir / f'{schema.name}.yaml'
        loader.save_schema(schema, schema_file)
    
    print(f"Imported {len(schemas)} schemas for {api_name}")
    return str(output_dir)

def generate_imported_data(**context):
    """Generate data from imported Airbyte schemas."""
    schema_dir = context['task_instance'].xcom_pull(task_ids='import_connector')
    api_name = context['dag_run'].conf.get('api_name', 'imported_api')
    
    from jafgen.schema.discovery import SchemaDiscoveryEngine
    from jafgen.generation.data_generator import DataGenerator
    from jafgen.generation.mimesis_engine import MimesisEngine
    from jafgen.generation.link_resolver import LinkResolver
    from jafgen.output.csv_writer import CSVWriter
    
    # Generate data
    discovery = SchemaDiscoveryEngine()
    schemas, validation = discovery.discover_and_load_schemas(Path(schema_dir))
    
    if not validation.is_valid:
        raise ValueError("Imported schema validation failed")
    
    engine = MimesisEngine(seed=42)
    resolver = LinkResolver()
    generator = DataGenerator(engine, resolver)
    
    results = generator.generate_multiple_systems(schemas)
    
    # Save output
    output_path = Path(f'/opt/airflow/data/{api_name}/{context["ds"]}')
    output_path.mkdir(parents=True, exist_ok=True)
    
    writer = CSVWriter()
    total_records = 0
    
    for result in results:
        writer.write(result.entities, output_path)
        for entity_name, data in result.entities.items():
            total_records += len(data)
    
    print(f"Generated {total_records} records from imported {api_name} schemas")
    return total_records

# Tasks
import_task = PythonOperator(
    task_id='import_connector',
    python_callable=import_airbyte_connector,
    dag=dag,
)

generate_task = PythonOperator(
    task_id='generate_data',
    python_callable=generate_imported_data,
    dag=dag,
)

import_task >> generate_task
```

## Configuration & Best Practices

### Airflow Variables

Set these in Airflow UI under Admin > Variables:

```json
{
  "jafgen_base_path": "/opt/airflow/jafgen",
  "jafgen_output_path": "/opt/airflow/data",
  "jafgen_schema_path": "/opt/airflow/schemas",
  "jafgen_default_seed": "42",
  "jafgen_retention_days": "30"
}
```

### Environment Setup

Create `docker-compose.override.yml` for Airflow:

```yaml
version: '3.8'
services:
  airflow-webserver:
    volumes:
      - ./jaffle-shop-generator:/opt/airflow/jafgen:ro
      - ./schemas:/opt/airflow/schemas:ro
      - ./data:/opt/airflow/data:rw
    environment:
      - PYTHONPATH=/opt/airflow/jafgen:$PYTHONPATH

  airflow-scheduler:
    volumes:
      - ./jaffle-shop-generator:/opt/airflow/jafgen:ro
      - ./schemas:/opt/airflow/schemas:ro
      - ./data:/opt/airflow/data:rw
    environment:
      - PYTHONPATH=/opt/airflow/jafgen:$PYTHONPATH

  airflow-worker:
    volumes:
      - ./jaffle-shop-generator:/opt/airflow/jafgen:ro
      - ./schemas:/opt/airflow/schemas:ro
      - ./data:/opt/airflow/data:rw
    environment:
      - PYTHONPATH=/opt/airflow/jafgen:$PYTHONPATH
```

### Monitoring & Alerting

Add monitoring tasks:

```python
def check_data_quality(**context):
    """Monitor data quality metrics."""
    from airflow.models import Variable
    import pandas as pd
    
    output_path = Path(f'/opt/airflow/data/stripe/{context["ds"]}')
    
    # Load and analyze data
    customers_df = pd.read_csv(output_path / 'csv' / 'customers.csv')
    
    # Quality checks
    checks = {
        'customer_count': len(customers_df),
        'email_uniqueness': customers_df['email'].nunique() / len(customers_df),
        'null_values': customers_df.isnull().sum().sum(),
    }
    
    # Alert on quality issues
    if checks['email_uniqueness'] < 0.95:
        raise ValueError(f"Email uniqueness too low: {checks['email_uniqueness']}")
    
    if checks['null_values'] > 0:
        raise ValueError(f"Unexpected null values: {checks['null_values']}")
    
    # Store metrics
    Variable.set(f"jafgen_quality_{context['ds']}", str(checks))
    return checks

quality_task = PythonOperator(
    task_id='check_data_quality',
    python_callable=check_data_quality,
    dag=dag,
)
```

## Cloud Storage Integration

### S3 Integration

```python
def upload_to_s3(**context):
    """Upload generated data to S3."""
    import boto3
    from airflow.models import Variable
    
    s3_client = boto3.client('s3')
    bucket = Variable.get('jafgen_s3_bucket')
    
    local_path = Path(f'/opt/airflow/data/stripe/{context["ds"]}')
    s3_prefix = f'synthetic-data/stripe/{context["ds"]}/'
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            s3_key = s3_prefix + str(file_path.relative_to(local_path))
            s3_client.upload_file(str(file_path), bucket, s3_key)
    
    print(f"Uploaded data to s3://{bucket}/{s3_prefix}")

s3_task = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_to_s3,
    dag=dag,
)
```

### Database Loading

```python
def load_to_database(**context):
    """Load generated data to database."""
    import pandas as pd
    from sqlalchemy import create_engine
    from airflow.models import Variable
    
    db_url = Variable.get('jafgen_db_url')
    engine = create_engine(db_url)
    
    data_path = Path(f'/opt/airflow/data/stripe/{context["ds"]}/csv')
    
    for csv_file in data_path.glob('*.csv'):
        table_name = f'synthetic_{csv_file.stem}_{context["ds_nodash"]}'
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Loaded {len(df)} rows to {table_name}")

db_task = PythonOperator(
    task_id='load_to_database',
    python_callable=load_to_database,
    dag=dag,
)
```

## Usage Examples

### Trigger DAG with Configuration

```bash
# Trigger Airbyte import DAG
airflow dags trigger jafgen_airbyte_import \
  --conf '{"manifest_url": "https://example.com/manifest.yaml", "api_name": "custom_api"}'

# Trigger with custom parameters
airflow dags trigger jafgen_stripe_daily \
  --conf '{"record_multiplier": 2.0, "output_format": "parquet"}'
```

### Monitor DAG Runs

```bash
# Check DAG status
airflow dags state jafgen_stripe_daily 2024-01-15

# View task logs
airflow tasks log jafgen_stripe_daily generate_stripe_data 2024-01-15

# List recent runs
airflow dags list-runs -d jafgen_multi_api_weekly --limit 10
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure Jaffle Shop is in Python path
   export PYTHONPATH=/opt/airflow/jafgen:$PYTHONPATH
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod -R 755 /opt/airflow/data
   chown -R airflow:airflow /opt/airflow/data
   ```

3. **Memory Issues**
   ```python
   # Reduce record counts for large datasets
   for schema in schemas:
       for entity in schema.entities.values():
           entity.count = min(entity.count, 1000)
   ```

### Performance Optimization

1. **Parallel Generation**
   ```python
   # Use Airflow's parallel execution
   from airflow.utils.task_group import TaskGroup
   
   with TaskGroup('parallel_apis') as group:
       for api in apis:
           generate_task = PythonOperator(...)
   ```

2. **Incremental Processing**
   ```python
   # Generate only new data
   def incremental_generation(**context):
       last_run = context.get('prev_ds')
       if last_run:
           # Generate only incremental data
           pass
   ```

## Conclusion

This Airflow integration enables:
- **Automated Scheduling**: Regular synthetic data generation
- **Scalable Processing**: Distributed across Airflow workers  
- **Monitoring**: Built-in success/failure tracking
- **Flexibility**: Support for any API schema
- **Cloud Integration**: S3, databases, and other storage systems

The DAGs provide a production-ready foundation for incorporating Jaffle Shop Generator into your data infrastructure and CI/CD pipelines.