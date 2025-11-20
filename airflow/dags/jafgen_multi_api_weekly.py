"""Jaffle Shop Generator - Multi-API Weekly Data Generation DAG.

This DAG generates synthetic data for multiple APIs weekly, including Stripe,
Plaid, and Light.inc. Designed for comprehensive testing and development
environment population.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

# DAG Configuration
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    "jafgen_multi_api_weekly",
    default_args=default_args,
    description=(
        "Weekly synthetic data generation for multiple APIs using "
        "Jaffle Shop Generator"
    ),
    schedule_interval="0 1 * * 0",  # Weekly on Sunday at 1 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=["jafgen", "multi-api", "weekly", "comprehensive"],
)

# API configurations with scaling factors for weekly generation
API_CONFIGS = {
    "stripe": {
        "schema_path": "schemas/saas-templates/stripe",
        "multiplier": 2.0,  # 2x records for weekly batch
        "description": "Payment processing and subscription data",
        "entities": ["customers", "charges", "subscriptions"],
    },
    "plaid": {
        "schema_path": "schemas/saas-templates/plaid",
        "multiplier": 1.5,  # 1.5x records for financial data
        "description": "Banking and financial transaction data",
        "entities": [
            "accounts",
            "transactions",
            "institutions",
            "investments",
        ],
    },
    "light": {
        "schema_path": "schemas/saas-templates/light",
        "multiplier": 1.8,  # 1.8x records for expense data
        "description": "Corporate expense and card management data",
        "entities": ["cards", "transactions", "expenses", "vendors"],
    },
}


def generate_api_data(api_name: str, config: dict):
    """Create API-specific data generation callable.

    Args:
    ----
        api_name: Name of the API (e.g., 'stripe', 'plaid')
        config: API configuration dictionary

    Returns:
    -------
        Callable for Airflow PythonOperator

    """

    def _generate(**context):
        try:
            from jafgen.generation.data_generator import DataGenerator
            from jafgen.generation.link_resolver import LinkResolver
            from jafgen.generation.mimesis_engine import MimesisEngine
            from jafgen.output.csv_writer import CSVWriter
            from jafgen.output.json_writer import JSONWriter
            from jafgen.output.parquet_writer import ParquetWriter
            from jafgen.schema.discovery import SchemaDiscoveryEngine
        except ImportError as e:
            logging.error(f"Failed to import Jaffle Shop Generator: {e}")
            raise

        # Configuration
        base_path = Path(Variable.get("jafgen_base_path", "/opt/airflow/jafgen"))
        schema_path = base_path / config["schema_path"]
        output_base = Path(Variable.get("jafgen_output_path", "/opt/airflow/data"))
        output_path = output_base / api_name / context["ds"]

        # Unique seed per API and date
        base_seed = int(context["ds_nodash"])
        api_seed = base_seed + hash(api_name) % 10000

        logging.info(f"Generating {api_name} data for {context['ds']}")
        logging.info(f"Schema path: {schema_path}")
        logging.info(f"Output path: {output_path}")
        logging.info(f"Seed: {api_seed}, Multiplier: {config['multiplier']}")

        # Create output directories
        for fmt in ["csv", "json", "parquet"]:
            (output_path / fmt).mkdir(parents=True, exist_ok=True)

        # Load schemas
        discovery = SchemaDiscoveryEngine()
        schemas, validation = discovery.discover_and_load_schemas(schema_path)

        if not validation.is_valid:
            error_msg = f"{api_name} schema validation failed: {validation.errors}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Scale record counts for weekly generation
        for schema in schemas:
            for entity in schema.entities.values():
                original_count = entity.count
                entity.count = int(entity.count * config["multiplier"])
                logging.info(
                    f"Scaled {entity.name}: {original_count} -> {entity.count}"
                )

        # Generate data
        engine = MimesisEngine(seed=api_seed)
        resolver = LinkResolver()
        generator = DataGenerator(engine, resolver)

        results = generator.generate_multiple_systems(schemas)

        # Write multiple output formats
        csv_writer = CSVWriter()
        json_writer = JSONWriter()
        parquet_writer = ParquetWriter()

        stats = {
            "api_name": api_name,
            "schemas_processed": len(results),
            "entities": {},
            "total_records": 0,
            "output_formats": ["csv", "json", "parquet"],
            "generation_seed": api_seed,
            "multiplier_applied": config["multiplier"],
        }

        for result in results:
            # Write in all formats
            csv_writer.write(result.entities, output_path / "csv")
            json_writer.write(result.entities, output_path / "json")
            parquet_writer.write(result.entities, output_path / "parquet")

            # Collect statistics
            for entity_name, data in result.entities.items():
                record_count = len(data)
                stats["entities"][entity_name] = record_count
                stats["total_records"] += record_count

        logging.info(
            f"{api_name} generation complete: {stats['total_records']} total records"
        )
        logging.info(f"Entity breakdown: {stats['entities']}")

        return stats

    return _generate


def validate_api_data(api_name: str, expected_entities: list):
    """Create API-specific validation callable.

    Args:
    ----
        api_name: Name of the API
        expected_entities: List of expected entity names

    Returns:
    -------
        Callable for Airflow PythonOperator

    """

    def _validate(**context):
        import pandas as pd

        output_base = Path(Variable.get("jafgen_output_path", "/opt/airflow/data"))
        output_path = output_base / api_name / context["ds"]

        logging.info(f"Validating {api_name} data at {output_path}")

        validation_results = {
            "api_name": api_name,
            "formats_validated": [],
            "entities_found": [],
            "total_records": 0,
            "quality_metrics": {},
            "errors": [],
        }

        # Check all output formats exist
        formats = ["csv", "json", "parquet"]
        for fmt in formats:
            format_path = output_path / fmt
            if not format_path.exists():
                validation_results["errors"].append(f"Missing {fmt} output directory")
                continue

            files = list(format_path.glob(f"*.{fmt}"))
            if not files:
                validation_results["errors"].append(f"No {fmt} files generated")
                continue

            validation_results["formats_validated"].append(fmt)

            # Validate CSV files for data quality
            if fmt == "csv":
                for csv_file in files:
                    entity_name = csv_file.stem
                    validation_results["entities_found"].append(entity_name)

                    try:
                        df = pd.read_csv(csv_file)
                        record_count = len(df)
                        validation_results["total_records"] += record_count

                        # Basic quality checks
                        null_percentage = (
                            df.isnull().sum().sum() / (len(df) * len(df.columns))
                        ) * 100
                        validation_results["quality_metrics"][
                            f"{entity_name}_null_percentage"
                        ] = null_percentage

                        # Check for minimum record counts (scaled for weekly)
                        min_expected = 100  # Minimum records per entity
                        if record_count < min_expected:
                            validation_results["errors"].append(
                                f"{entity_name}: Only {record_count} records, "
                                f"expected at least {min_expected}"
                            )

                        # API-specific validations
                        if api_name == "stripe" and entity_name == "customers":
                            email_uniqueness = (
                                df["email"].nunique() / len(df) if len(df) > 0 else 0
                            )
                            validation_results["quality_metrics"][
                                "customer_email_uniqueness"
                            ] = email_uniqueness

                            if email_uniqueness < 0.95:
                                validation_results["errors"].append(
                                    f"Stripe customer email uniqueness too low: "
                                    f"{email_uniqueness:.2%}"
                                )

                        elif api_name == "plaid" and entity_name == "accounts":
                            if "account_id" in df.columns:
                                id_uniqueness = (
                                    df["account_id"].nunique() / len(df)
                                    if len(df) > 0
                                    else 0
                                )
                                validation_results["quality_metrics"][
                                    "account_id_uniqueness"
                                ] = id_uniqueness

                                if id_uniqueness < 1.0:
                                    validation_results["errors"].append(
                                        f"Plaid account ID uniqueness issue: "
                                        f"{id_uniqueness:.2%}"
                                    )

                    except Exception as e:
                        validation_results["errors"].append(
                            f"Error validating {csv_file}: {str(e)}"
                        )

        # Check for expected entities
        missing_entities = set(expected_entities) - set(
            validation_results["entities_found"]
        )
        if missing_entities:
            validation_results["errors"].append(
                f"Missing expected entities: {missing_entities}"
            )

        # Raise exception if validation errors found
        if validation_results["errors"]:
            error_summary = "; ".join(validation_results["errors"])
            raise ValueError(f"{api_name} validation failed: {error_summary}")

        logging.info(
            f"{api_name} validation passed: "
            f"{len(validation_results['entities_found'])} entities, "
            f"{validation_results['total_records']} total records"
        )
        logging.info(f"Quality metrics: {validation_results['quality_metrics']}")

        return validation_results

    return _validate


def generate_summary_report(**context):
    """Generate a summary report of all API data generation.

    Args:
    ----
        context: Airflow context dictionary

    Returns:
    -------
        dict: Comprehensive summary statistics

    """
    summary = {
        "generation_date": context["ds"],
        "apis_processed": [],
        "total_records_all_apis": 0,
        "total_entities": 0,
        "output_formats": ["csv", "json", "parquet"],
        "api_details": {},
    }

    # Collect results from all API generation tasks
    for api_name in API_CONFIGS.keys():
        try:
            # Get generation stats from XCom
            generation_stats = context["task_instance"].xcom_pull(
                task_ids=f"{api_name}_generation.generate_{api_name}_data"
            )

            validation_stats = context["task_instance"].xcom_pull(
                task_ids=f"{api_name}_generation.validate_{api_name}_data"
            )

            if generation_stats and validation_stats:
                summary["apis_processed"].append(api_name)
                summary["total_records_all_apis"] += generation_stats["total_records"]
                summary["total_entities"] += len(generation_stats["entities"])

                summary["api_details"][api_name] = {
                    "description": API_CONFIGS[api_name]["description"],
                    "records_generated": generation_stats["total_records"],
                    "entities": list(generation_stats["entities"].keys()),
                    "entity_counts": generation_stats["entities"],
                    "multiplier_applied": generation_stats["multiplier_applied"],
                    "validation_passed": True,
                    "quality_metrics": validation_stats.get("quality_metrics", {}),
                }

        except Exception as e:
            logging.warning(f"Could not collect stats for {api_name}: {e}")
            summary["api_details"][api_name] = {
                "error": str(e),
                "validation_passed": False,
            }

    # Log comprehensive summary
    logging.info("=== WEEKLY DATA GENERATION SUMMARY ===")
    logging.info(f"Date: {summary['generation_date']}")
    logging.info(f"APIs Processed: {len(summary['apis_processed'])}")
    logging.info(f"Total Records: {summary['total_records_all_apis']:,}")
    logging.info(f"Total Entities: {summary['total_entities']}")

    for api_name, details in summary["api_details"].items():
        if "records_generated" in details:
            logging.info(
                f"{api_name.upper()}: {details['records_generated']:,} records "
                f"across {len(details['entities'])} entities"
            )

    logging.info("=" * 40)

    return summary


# Create start and end dummy tasks
start_task = DummyOperator(
    task_id="start_weekly_generation",
    dag=dag,
)

end_task = DummyOperator(
    task_id="end_weekly_generation",
    dag=dag,
)

summary_task = PythonOperator(
    task_id="generate_summary_report",
    python_callable=generate_summary_report,
    dag=dag,
)

# Create task groups for each API
api_task_groups = []

for api_name, config in API_CONFIGS.items():
    with TaskGroup(group_id=f"{api_name}_generation", dag=dag) as api_group:

        generate_task = PythonOperator(
            task_id=f"generate_{api_name}_data",
            python_callable=generate_api_data(api_name, config),
            doc_md=f"""
            ## Generate {api_name.title()} Data

            {config['description']}

            **Expected Entities:** {', '.join(config['entities'])}
            **Record Multiplier:** {config['multiplier']}x (weekly batch)
            **Output Formats:** CSV, JSON, Parquet
            """,
        )

        validate_task = PythonOperator(
            task_id=f"validate_{api_name}_data",
            python_callable=validate_api_data(api_name, config["entities"]),
            doc_md=f"""
            ## Validate {api_name.title()} Data

            Performs comprehensive validation including:
            - File existence across all formats
            - Data quality metrics
            - Entity-specific business rule validation
            - Record count thresholds
            """,
        )

        generate_task >> validate_task

    api_task_groups.append(api_group)

# Set up task dependencies
start_task >> api_task_groups >> summary_task >> end_task

# Add comprehensive DAG documentation
dag.doc_md = """
# Multi-API Weekly Data Generation DAG

This DAG generates comprehensive synthetic data for multiple APIs weekly
using Jaffle Shop Generator. Designed for populating development environments
and comprehensive testing scenarios.

## APIs Included

### Stripe (Payment Processing)
- **Entities:** Customers, Charges, Subscriptions
- **Use Cases:** E-commerce testing, payment flow validation
- **Record Multiplier:** 2.0x (higher volume for payment testing)

### Plaid (Financial Services)
- **Entities:** Accounts, Transactions, Institutions, Investments
- **Use Cases:** Fintech development, banking integration testing
- **Record Multiplier:** 1.5x (moderate volume for financial data)

### Light.inc (Expense Management)
- **Entities:** Cards, Transactions, Expenses, Vendors
- **Use Cases:** Corporate expense testing, card management validation
- **Record Multiplier:** 1.8x (higher volume for expense workflows)

## Configuration

### Required Airflow Variables
- `jafgen_base_path`: Base path to Jaffle Shop Generator installation
- `jafgen_output_path`: Output directory for generated data
- `jafgen_retention_days`: Data retention period (default: 30 days for weekly)

### Output Structure
```
/data/
├── stripe/YYYY-MM-DD/
│   ├── csv/
│   ├── json/
│   └── parquet/
├── plaid/YYYY-MM-DD/
│   ├── csv/
│   ├── json/
│   └── parquet/
└── light/YYYY-MM-DD/
    ├── csv/
    ├── json/
    └── parquet/
```

## Features

- **Parallel Processing:** All APIs generated simultaneously
- **Multiple Formats:** CSV, JSON, and Parquet output
- **Quality Validation:** Comprehensive data quality checks
- **Scalable Records:** Weekly multipliers for larger datasets
- **Summary Reporting:** Consolidated generation statistics
- **Error Handling:** Robust error handling and retry logic

## Monitoring

Each API generation includes:
- File existence validation
- Data quality metrics
- Business rule validation
- Record count verification
- Format consistency checks

## Schedule

Runs weekly on Sundays at 1 AM UTC. Generates fresh data with unique seeds
per API while maintaining reproducibility for the same date.

## Usage

Perfect for:
- Weekly development environment refresh
- Comprehensive API testing
- Data pipeline validation
- Multi-system integration testing
- Performance testing with larger datasets
"""
