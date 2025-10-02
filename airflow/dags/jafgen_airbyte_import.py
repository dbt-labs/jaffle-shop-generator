"""
Jaffle Shop Generator - Airbyte Connector Import DAG

This DAG imports Airbyte connector manifests and generates synthetic data.
Supports dynamic API import and data generation from Airbyte ecosystem.
"""

from datetime import datetime, timedelta
from pathlib import Path
import logging
import requests
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException

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
    'jafgen_airbyte_import',
    default_args=default_args,
    description='Import Airbyte connector manifests and generate synthetic data',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=['jafgen', 'airbyte', 'import', 'dynamic'],
)

def validate_dag_config(**context):
    """
    Validate DAG run configuration parameters.
    
    Required parameters:
    - manifest_url: URL to Airbyte connector manifest
    - api_name: Name for the imported API
    
    Optional parameters:
    - record_multiplier: Scaling factor for record generation (default: 1.0)
    - output_formats: List of output formats (default: ['csv', 'json'])
    
    Returns:
        dict: Validated configuration
    """
    dag_run_conf = context.get('dag_run', {}).conf or {}
    
    # Required parameters
    manifest_url = dag_run_conf.get('manifest_url')
    api_name = dag_run_conf.get('api_name')
    
    if not manifest_url:
        raise AirflowException(
            "manifest_url is required in DAG run configuration. "
            "Example: {'manifest_url': 'https://example.com/manifest.yaml', 'api_name': 'my_api'}"
        )
    
    if not api_name:
        raise AirflowException(
            "api_name is required in DAG run configuration. "
            "Provide a name for the imported API (e.g., 'shopify', 'salesforce')"
        )
    
    # Validate API name format
    if not api_name.replace('_', '').replace('-', '').isalnum():
        raise AirflowException(
            f"api_name '{api_name}' must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    # Optional parameters with defaults
    config = {
        'manifest_url': manifest_url,
        'api_name': api_name.lower().replace('-', '_'),
        'record_multiplier': float(dag_run_conf.get('record_multiplier', 1.0)),
        'output_formats': dag_run_conf.get('output_formats', ['csv', 'json']),
        'generation_seed': dag_run_conf.get('generation_seed', 42),
    }
    
    # Validate output formats
    valid_formats = ['csv', 'json', 'parquet']
    invalid_formats = set(config['output_formats']) - set(valid_formats)
    if invalid_formats:
        raise AirflowException(
            f"Invalid output formats: {invalid_formats}. Valid formats: {valid_formats}"
        )
    
    logging.info(f"Validated configuration: {config}")
    return config

def download_airbyte_manifest(**context):
    """
    Download Airbyte connector manifest from URL.
    
    Returns:
        dict: Download results including local file path
    """
    config = context['task_instance'].xcom_pull(task_ids='validate_config')
    manifest_url = config['manifest_url']
    api_name = config['api_name']
    
    logging.info(f"Downloading Airbyte manifest from: {manifest_url}")
    
    try:
        # Download manifest with timeout and error handling
        response = requests.get(manifest_url, timeout=30)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('content-type', '').lower()
        if 'yaml' not in content_type and 'text' not in content_type:
            logging.warning(f"Unexpected content type: {content_type}")
        
        # Save to temporary location
        base_path = Path(Variable.get('jafgen_base_path', '/opt/airflow/jafgen'))
        temp_dir = base_path / 'temp' / 'airbyte_imports'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = temp_dir / f'{api_name}_manifest.yaml'
        manifest_path.write_text(response.text, encoding='utf-8')
        
        # Basic validation of manifest content
        manifest_size = len(response.text)
        if manifest_size < 100:
            raise AirflowException(f"Manifest file too small ({manifest_size} bytes), likely invalid")
        
        # Check for basic YAML structure
        if 'streams:' not in response.text and 'entities:' not in response.text:
            logging.warning("Manifest may not contain expected stream/entity definitions")
        
        download_result = {
            'manifest_path': str(manifest_path),
            'manifest_size': manifest_size,
            'content_type': content_type,
            'api_name': api_name,
            'download_url': manifest_url
        }
        
        logging.info(f"Downloaded manifest: {manifest_size} bytes to {manifest_path}")
        return download_result
        
    except requests.exceptions.RequestException as e:
        raise AirflowException(f"Failed to download manifest from {manifest_url}: {str(e)}")
    except Exception as e:
        raise AirflowException(f"Error processing manifest download: {str(e)}")

def import_airbyte_schemas(**context):
    """
    Import Airbyte connector manifest and convert to jafgen schemas.
    
    Returns:
        dict: Import results including schema information
    """
    config = context['task_instance'].xcom_pull(task_ids='validate_config')
    download_result = context['task_instance'].xcom_pull(task_ids='download_manifest')
    
    api_name = config['api_name']
    manifest_path = Path(download_result['manifest_path'])
    
    logging.info(f"Importing Airbyte schemas for {api_name} from {manifest_path}")
    
    try:
        from jafgen.airbyte.translator import AirbyteTranslator
    except ImportError as e:
        raise AirflowException(f"Failed to import Jaffle Shop Generator: {e}")
    
    try:
        # Translate Airbyte manifest to jafgen schemas
        translator = AirbyteTranslator()
        schemas = translator.translate_manifest(manifest_path)
        
        if not schemas:
            raise AirflowException("No schemas generated from Airbyte manifest")
        
        # Save schemas to permanent location
        base_path = Path(Variable.get('jafgen_base_path', '/opt/airflow/jafgen'))
        schema_output_dir = base_path / 'schemas' / 'imported' / api_name
        schema_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each schema as YAML file
        from jafgen.schema.yaml_loader import YAMLSchemaLoader
        loader = YAMLSchemaLoader()
        
        schema_files = []
        total_entities = 0
        total_attributes = 0
        
        for schema in schemas:
            schema_file = schema_output_dir / f'{schema.name}.yaml'
            loader.save_schema(schema, schema_file)
            schema_files.append(str(schema_file))
            
            # Collect statistics
            total_entities += len(schema.entities)
            for entity in schema.entities.values():
                total_attributes += len(entity.attributes)
        
        import_result = {
            'api_name': api_name,
            'schema_output_dir': str(schema_output_dir),
            'schema_files': schema_files,
            'schemas_count': len(schemas),
            'total_entities': total_entities,
            'total_attributes': total_attributes,
            'schema_names': [schema.name for schema in schemas],
            'entity_summary': {
                schema.name: list(schema.entities.keys()) 
                for schema in schemas
            }
        }
        
        logging.info(f"Import successful: {len(schemas)} schemas, {total_entities} entities, {total_attributes} attributes")
        logging.info(f"Schemas saved to: {schema_output_dir}")
        
        return import_result
        
    except Exception as e:
        raise AirflowException(f"Failed to import Airbyte schemas: {str(e)}")

def generate_imported_data(**context):
    """
    Generate synthetic data from imported Airbyte schemas.
    
    Returns:
        dict: Generation results and statistics
    """
    config = context['task_instance'].xcom_pull(task_ids='validate_config')
    import_result = context['task_instance'].xcom_pull(task_ids='import_schemas')
    
    api_name = config['api_name']
    schema_dir = Path(import_result['schema_output_dir'])
    record_multiplier = config['record_multiplier']
    output_formats = config['output_formats']
    generation_seed = config['generation_seed']
    
    logging.info(f"Generating data for imported {api_name} API")
    logging.info(f"Schema directory: {schema_dir}")
    logging.info(f"Record multiplier: {record_multiplier}")
    logging.info(f"Output formats: {output_formats}")
    
    try:
        from jafgen.schema.discovery import SchemaDiscoveryEngine
        from jafgen.generation.data_generator import DataGenerator
        from jafgen.generation.mimesis_engine import MimesisEngine
        from jafgen.generation.link_resolver import LinkResolver
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.json_writer import JSONWriter
        from jafgen.output.parquet_writer import ParquetWriter
    except ImportError as e:
        raise AirflowException(f"Failed to import Jaffle Shop Generator: {e}")
    
    try:
        # Load imported schemas
        discovery = SchemaDiscoveryEngine()
        schemas, validation = discovery.discover_and_load_schemas(schema_dir)
        
        if not validation.is_valid:
            raise AirflowException(f"Schema validation failed: {validation.errors}")
        
        # Apply record multiplier
        if record_multiplier != 1.0:
            for schema in schemas:
                for entity in schema.entities.values():
                    original_count = entity.count
                    entity.count = int(entity.count * record_multiplier)
                    logging.info(f"Scaled {entity.name}: {original_count} -> {entity.count}")
        
        # Generate data
        engine = MimesisEngine(seed=generation_seed)
        resolver = LinkResolver()
        generator = DataGenerator(engine, resolver)
        
        results = generator.generate_multiple_systems(schemas)
        
        # Prepare output directory
        output_base = Path(Variable.get('jafgen_output_path', '/opt/airflow/data'))
        output_path = output_base / 'imported' / api_name / context['ds']
        
        for fmt in output_formats:
            (output_path / fmt).mkdir(parents=True, exist_ok=True)
        
        # Write outputs in requested formats
        writers = {}
        if 'csv' in output_formats:
            writers['csv'] = CSVWriter()
        if 'json' in output_formats:
            writers['json'] = JSONWriter()
        if 'parquet' in output_formats:
            writers['parquet'] = ParquetWriter()
        
        generation_stats = {
            'api_name': api_name,
            'schemas_processed': len(results),
            'entities': {},
            'total_records': 0,
            'output_formats': output_formats,
            'output_path': str(output_path),
            'generation_seed': generation_seed,
            'record_multiplier': record_multiplier
        }
        
        for result in results:
            # Write in all requested formats
            for fmt, writer in writers.items():
                writer.write(result.entities, output_path / fmt)
            
            # Collect statistics
            for entity_name, data in result.entities.items():
                record_count = len(data)
                generation_stats['entities'][entity_name] = record_count
                generation_stats['total_records'] += record_count
        
        logging.info(f"Generation complete: {generation_stats['total_records']} total records")
        logging.info(f"Entity breakdown: {generation_stats['entities']}")
        logging.info(f"Output saved to: {output_path}")
        
        return generation_stats
        
    except Exception as e:
        raise AirflowException(f"Failed to generate data from imported schemas: {str(e)}")

def validate_imported_data(**context):
    """
    Validate generated data from imported schemas.
    
    Returns:
        dict: Validation results
    """
    config = context['task_instance'].xcom_pull(task_ids='validate_config')
    generation_stats = context['task_instance'].xcom_pull(task_ids='generate_data')
    
    api_name = config['api_name']
    output_path = Path(generation_stats['output_path'])
    output_formats = config['output_formats']
    
    logging.info(f"Validating generated {api_name} data at {output_path}")
    
    validation_results = {
        'api_name': api_name,
        'formats_validated': [],
        'entities_validated': [],
        'total_records_validated': 0,
        'errors': []
    }
    
    try:
        # Validate each output format
        for fmt in output_formats:
            format_path = output_path / fmt
            
            if not format_path.exists():
                validation_results['errors'].append(f"Missing {fmt} output directory")
                continue
            
            files = list(format_path.glob(f'*.{fmt}'))
            if not files:
                validation_results['errors'].append(f"No {fmt} files generated")
                continue
            
            validation_results['formats_validated'].append(fmt)
            
            # Validate CSV files for basic data quality
            if fmt == 'csv':
                import pandas as pd
                
                for csv_file in files:
                    entity_name = csv_file.stem
                    validation_results['entities_validated'].append(entity_name)
                    
                    try:
                        df = pd.read_csv(csv_file)
                        record_count = len(df)
                        validation_results['total_records_validated'] += record_count
                        
                        # Basic validation checks
                        if record_count == 0:
                            validation_results['errors'].append(f"{entity_name}: No records generated")
                        
                        if csv_file.stat().st_size == 0:
                            validation_results['errors'].append(f"{entity_name}: Empty file")
                        
                    except Exception as e:
                        validation_results['errors'].append(f"Error validating {csv_file}: {str(e)}")
        
        # Check if validation errors found
        if validation_results['errors']:
            error_summary = "; ".join(validation_results['errors'])
            raise AirflowException(f"{api_name} validation failed: {error_summary}")
        
        logging.info(f"Validation passed: {len(validation_results['entities_validated'])} entities, "
                    f"{validation_results['total_records_validated']} records")
        
        return validation_results
        
    except Exception as e:
        if isinstance(e, AirflowException):
            raise
        raise AirflowException(f"Error during validation: {str(e)}")

def cleanup_temp_files(**context):
    """
    Clean up temporary files created during import process.
    
    Returns:
        dict: Cleanup results
    """
    download_result = context['task_instance'].xcom_pull(task_ids='download_manifest')
    
    cleanup_results = {
        'files_removed': [],
        'errors': []
    }
    
    try:
        # Remove temporary manifest file
        if download_result and 'manifest_path' in download_result:
            manifest_path = Path(download_result['manifest_path'])
            if manifest_path.exists():
                manifest_path.unlink()
                cleanup_results['files_removed'].append(str(manifest_path))
                logging.info(f"Removed temporary manifest: {manifest_path}")
        
        logging.info(f"Cleanup complete: {len(cleanup_results['files_removed'])} files removed")
        return cleanup_results
        
    except Exception as e:
        cleanup_results['errors'].append(str(e))
        logging.warning(f"Cleanup error: {e}")
        return cleanup_results

# Define tasks
start_task = DummyOperator(
    task_id='start_import',
    dag=dag,
)

validate_config_task = PythonOperator(
    task_id='validate_config',
    python_callable=validate_dag_config,
    dag=dag,
)

download_task = PythonOperator(
    task_id='download_manifest',
    python_callable=download_airbyte_manifest,
    dag=dag,
)

import_task = PythonOperator(
    task_id='import_schemas',
    python_callable=import_airbyte_schemas,
    dag=dag,
)

generate_task = PythonOperator(
    task_id='generate_data',
    python_callable=generate_imported_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_imported_data,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_temp_files',
    python_callable=cleanup_temp_files,
    dag=dag,
    trigger_rule='all_done',  # Run even if upstream tasks fail
)

end_task = DummyOperator(
    task_id='end_import',
    dag=dag,
)

# Task dependencies
start_task >> validate_config_task >> download_task >> import_task >> generate_task >> validate_task >> cleanup_task >> end_task

# Add comprehensive DAG documentation
dag.doc_md = """
# Airbyte Connector Import DAG

This DAG dynamically imports Airbyte connector manifests and generates synthetic data.
Enables rapid integration of new APIs from the Airbyte ecosystem.

## Usage

Trigger this DAG manually with configuration parameters:

### Required Parameters
```json
{
  "manifest_url": "https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-stripe/manifest.yaml",
  "api_name": "stripe_imported"
}
```

### Optional Parameters
```json
{
  "record_multiplier": 2.0,
  "output_formats": ["csv", "json", "parquet"],
  "generation_seed": 42
}
```

## Process Flow

1. **Validate Configuration** - Check required parameters
2. **Download Manifest** - Fetch Airbyte connector manifest from URL
3. **Import Schemas** - Convert Airbyte manifest to jafgen schemas
4. **Generate Data** - Create synthetic data using imported schemas
5. **Validate Data** - Verify data quality and completeness
6. **Cleanup** - Remove temporary files

## Output

Generated schemas are saved to:
- `/schemas/imported/{api_name}/` - Converted jafgen schemas

Generated data is saved to:
- `/data/imported/{api_name}/YYYY-MM-DD/` - Synthetic data files

## Supported Airbyte Connectors

This DAG can import any Airbyte connector with a valid manifest.yaml file.
Popular connectors include:
- Stripe, Shopify, WooCommerce (E-commerce)
- Salesforce, HubSpot, Pipedrive (CRM)
- GitHub, GitLab, Jira (Development)
- Slack, Discord, Intercom (Communication)

## Error Handling

The DAG includes comprehensive error handling for:
- Invalid manifest URLs
- Malformed manifest files
- Schema conversion failures
- Data generation errors
- Validation failures

## Examples

### Import Shopify Connector
```bash
airflow dags trigger jafgen_airbyte_import \\
  --conf '{
    "manifest_url": "https://raw.githubusercontent.com/airbytehq/airbyte/master/airbyte-integrations/connectors/source-shopify/manifest.yaml",
    "api_name": "shopify",
    "record_multiplier": 1.5
  }'
```

### Import Custom Connector
```bash
airflow dags trigger jafgen_airbyte_import \\
  --conf '{
    "manifest_url": "https://my-company.com/custom-connector-manifest.yaml",
    "api_name": "custom_api",
    "output_formats": ["csv", "parquet"]
  }'
```

## Monitoring

Monitor the DAG execution through:
- Airflow UI task logs
- XCom values for detailed statistics
- Generated file validation
- Data quality metrics

This DAG enables rapid prototyping and testing with any API supported by Airbyte.
"""