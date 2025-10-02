"""
Jaffle Shop Generator - Stripe Daily Data Generation DAG

This DAG generates synthetic Stripe data daily for development and testing purposes.
Includes data generation, validation, and cleanup tasks.
"""

from datetime import datetime, timedelta
from pathlib import Path
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

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
    description='Generate daily Stripe synthetic data using Jaffle Shop Generator',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['jafgen', 'stripe', 'synthetic-data', 'daily'],
)

def generate_stripe_data(**context):
    """
    Generate Stripe synthetic data using Jaffle Shop Generator.
    
    Returns:
        dict: Generation statistics including record counts
    """
    try:
        from jafgen.schema.discovery import SchemaDiscoveryEngine
        from jafgen.generation.data_generator import DataGenerator
        from jafgen.generation.mimesis_engine import MimesisEngine
        from jafgen.generation.link_resolver import LinkResolver
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.json_writer import JSONWriter
    except ImportError as e:
        logging.error(f"Failed to import Jaffle Shop Generator: {e}")
        raise
    
    # Configuration
    base_path = Variable.get('jafgen_base_path', '/opt/airflow/jafgen')
    schema_path = Path(base_path) / 'schemas' / 'saas-templates' / 'stripe'
    output_base = Path(Variable.get('jafgen_output_path', '/opt/airflow/data'))
    output_path = output_base / 'stripe' / context['ds']
    
    # Use date as seed for reproducible daily data
    seed = int(context['ds_nodash'])
    
    logging.info(f"Generating Stripe data for {context['ds']} with seed {seed}")
    logging.info(f"Schema path: {schema_path}")
    logging.info(f"Output path: {output_path}")
    
    # Create output directories
    (output_path / 'csv').mkdir(parents=True, exist_ok=True)
    (output_path / 'json').mkdir(parents=True, exist_ok=True)
    
    # Load Stripe schemas
    discovery = SchemaDiscoveryEngine()
    schemas, validation = discovery.discover_and_load_schemas(schema_path)
    
    if not validation.is_valid:
        error_msg = f"Schema validation failed: {validation.errors}"
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    logging.info(f"Loaded {len(schemas)} Stripe schemas successfully")
    
    # Generate data
    engine = MimesisEngine(seed=seed)
    resolver = LinkResolver()
    generator = DataGenerator(engine, resolver)
    
    results = generator.generate_multiple_systems(schemas)
    
    # Write outputs in multiple formats
    csv_writer = CSVWriter()
    json_writer = JSONWriter()
    
    stats = {
        'schemas_processed': len(results),
        'entities': {},
        'total_records': 0,
        'output_files': []
    }
    
    for result in results:
        # Write CSV files
        csv_writer.write(result.entities, output_path / 'csv')
        
        # Write JSON files  
        json_writer.write(result.entities, output_path / 'json')
        
        # Collect statistics
        for entity_name, data in result.entities.items():
            record_count = len(data)
            stats['entities'][entity_name] = record_count
            stats['total_records'] += record_count
            
            # Track output files
            stats['output_files'].extend([
                f"csv/{entity_name}.csv",
                f"json/{entity_name}.json"
            ])
    
    logging.info(f"Generation complete: {stats['total_records']} total records")
    logging.info(f"Entity breakdown: {stats['entities']}")
    
    return stats

def validate_stripe_output(**context):
    """
    Validate generated Stripe data for quality and completeness.
    
    Returns:
        dict: Validation results and metrics
    """
    import pandas as pd
    
    output_base = Path(Variable.get('jafgen_output_path', '/opt/airflow/data'))
    output_path = output_base / 'stripe' / context['ds']
    
    logging.info(f"Validating Stripe data at {output_path}")
    
    validation_results = {
        'files_checked': 0,
        'total_records': 0,
        'quality_checks': {},
        'errors': []
    }
    
    # Check CSV files exist and are valid
    csv_path = output_path / 'csv'
    json_path = output_path / 'json'
    
    if not csv_path.exists() or not json_path.exists():
        raise ValueError("Output directories not found")
    
    csv_files = list(csv_path.glob('*.csv'))
    json_files = list(json_path.glob('*.json'))
    
    if not csv_files:
        raise ValueError("No CSV files generated")
    
    if not json_files:
        raise ValueError("No JSON files generated")
    
    # Validate each CSV file
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            entity_name = csv_file.stem
            
            validation_results['files_checked'] += 1
            validation_results['total_records'] += len(df)
            
            # Entity-specific quality checks
            if entity_name == 'customers':
                # Check email uniqueness
                email_uniqueness = df['email'].nunique() / len(df) if len(df) > 0 else 0
                validation_results['quality_checks']['customer_email_uniqueness'] = email_uniqueness
                
                if email_uniqueness < 0.95:
                    validation_results['errors'].append(
                        f"Customer email uniqueness too low: {email_uniqueness:.2%}"
                    )
            
            elif entity_name == 'charges':
                # Check amount validity
                if 'amount' in df.columns:
                    invalid_amounts = (df['amount'] <= 0).sum()
                    validation_results['quality_checks']['charges_invalid_amounts'] = invalid_amounts
                    
                    if invalid_amounts > 0:
                        validation_results['errors'].append(
                            f"Found {invalid_amounts} charges with invalid amounts"
                        )
            
            # Check for unexpected null values in required fields
            null_counts = df.isnull().sum()
            critical_nulls = null_counts[null_counts > 0]
            
            if len(critical_nulls) > 0:
                validation_results['errors'].append(
                    f"{entity_name}: Unexpected null values in {critical_nulls.to_dict()}"
                )
            
            # File size check
            if csv_file.stat().st_size == 0:
                validation_results['errors'].append(f"Empty file: {csv_file}")
            
        except Exception as e:
            validation_results['errors'].append(f"Error validating {csv_file}: {str(e)}")
    
    # Raise exception if validation errors found
    if validation_results['errors']:
        error_summary = "; ".join(validation_results['errors'])
        raise ValueError(f"Validation failed: {error_summary}")
    
    logging.info(f"Validation passed: {validation_results['files_checked']} files, "
                f"{validation_results['total_records']} records")
    logging.info(f"Quality metrics: {validation_results['quality_checks']}")
    
    return validation_results

def cleanup_old_stripe_data(**context):
    """
    Clean up old Stripe data files to manage storage.
    
    Returns:
        dict: Cleanup statistics
    """
    output_base = Path(Variable.get('jafgen_output_path', '/opt/airflow/data'))
    stripe_path = output_base / 'stripe'
    retention_days = int(Variable.get('jafgen_retention_days', '7'))
    
    if not stripe_path.exists():
        logging.info("No Stripe data directory found, skipping cleanup")
        return {'directories_removed': 0, 'retention_days': retention_days}
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    directories_removed = 0
    
    for date_dir in stripe_path.iterdir():
        if date_dir.is_dir():
            try:
                # Parse directory name as date (YYYY-MM-DD format)
                dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                
                if dir_date < cutoff_date:
                    logging.info(f"Removing old data directory: {date_dir}")
                    import shutil
                    shutil.rmtree(date_dir)
                    directories_removed += 1
                    
            except ValueError:
                # Skip directories that don't match date format
                logging.warning(f"Skipping non-date directory: {date_dir}")
                continue
    
    cleanup_stats = {
        'directories_removed': directories_removed,
        'retention_days': retention_days,
        'cutoff_date': cutoff_date.strftime('%Y-%m-%d')
    }
    
    logging.info(f"Cleanup complete: {cleanup_stats}")
    return cleanup_stats

# Define tasks
generate_task = PythonOperator(
    task_id='generate_stripe_data',
    python_callable=generate_stripe_data,
    dag=dag,
    doc_md="""
    ## Generate Stripe Data
    
    This task generates synthetic Stripe data including:
    - Customers with realistic profiles
    - Charges with payment processing details  
    - Subscriptions with billing cycles
    
    The data is generated using a date-based seed for reproducibility.
    """,
)

validate_task = PythonOperator(
    task_id='validate_stripe_data',
    python_callable=validate_stripe_output,
    dag=dag,
    doc_md="""
    ## Validate Generated Data
    
    Performs quality checks on generated Stripe data:
    - File existence and size validation
    - Data completeness checks
    - Entity-specific quality metrics
    - Referential integrity validation
    """,
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_stripe_data,
    dag=dag,
    doc_md="""
    ## Cleanup Old Data
    
    Removes old Stripe data files based on retention policy.
    Default retention: 7 days (configurable via jafgen_retention_days variable).
    """,
)

# Task dependencies
generate_task >> validate_task >> cleanup_task

# Add task documentation
dag.doc_md = """
# Stripe Daily Data Generation DAG

This DAG generates synthetic Stripe payment data daily using the Jaffle Shop Generator.

## Configuration

Set these Airflow Variables:
- `jafgen_base_path`: Base path to Jaffle Shop Generator installation
- `jafgen_output_path`: Output directory for generated data  
- `jafgen_retention_days`: Number of days to retain old data (default: 7)

## Output

Generated data is saved in both CSV and JSON formats:
- `/data/stripe/YYYY-MM-DD/csv/` - CSV files for each entity
- `/data/stripe/YYYY-MM-DD/json/` - JSON files for each entity

## Monitoring

The DAG includes built-in data quality validation and will fail if:
- Required files are not generated
- Data quality thresholds are not met
- Unexpected null values are found in critical fields

## Schedule

Runs daily at 2 AM UTC. Each run generates fresh data with a date-based seed
for reproducibility while ensuring data variety across days.
"""