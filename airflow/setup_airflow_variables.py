#!/usr/bin/env python3
"""
Setup script for Airflow Variables required by Jaffle Shop Generator DAGs.

Run this script after setting up Airflow to configure the necessary variables.
"""

import json
import subprocess
import sys
from pathlib import Path

# Default Airflow Variables for Jaffle Shop Generator
AIRFLOW_VARIABLES = {
    # Base configuration
    "jafgen_base_path": "/opt/airflow/jafgen",
    "jafgen_output_path": "/opt/airflow/data", 
    "jafgen_schema_path": "/opt/airflow/schemas",
    
    # Generation settings
    "jafgen_default_seed": "42",
    "jafgen_retention_days": "7",  # Daily DAGs
    "jafgen_weekly_retention_days": "30",  # Weekly DAGs
    
    # Output configuration
    "jafgen_default_formats": '["csv", "json"]',
    "jafgen_enable_parquet": "true",
    
    # Performance settings
    "jafgen_max_records_per_entity": "10000",
    "jafgen_parallel_generation": "true",
    
    # Notification settings
    "jafgen_notification_email": "data-team@company.com",
    "jafgen_slack_webhook": "",  # Optional Slack integration
    
    # Cloud storage (optional)
    "jafgen_s3_bucket": "",  # S3 bucket for data storage
    "jafgen_gcs_bucket": "",  # GCS bucket for data storage
    
    # Database connection (optional)
    "jafgen_db_url": "",  # Database URL for direct loading
}

def run_airflow_command(command: list) -> tuple[int, str, str]:
    """
    Run an Airflow CLI command and return the result.
    
    Args:
        command: List of command arguments
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def check_airflow_available() -> bool:
    """Check if Airflow CLI is available."""
    code, _, _ = run_airflow_command(["airflow", "version"])
    return code == 0

def set_airflow_variable(key: str, value: str) -> bool:
    """
    Set an Airflow variable.
    
    Args:
        key: Variable key
        value: Variable value
        
    Returns:
        True if successful, False otherwise
    """
    command = ["airflow", "variables", "set", key, value]
    code, stdout, stderr = run_airflow_command(command)
    
    if code == 0:
        print(f"✅ Set variable: {key}")
        return True
    else:
        print(f"❌ Failed to set variable {key}: {stderr}")
        return False

def get_airflow_variable(key: str) -> str:
    """
    Get an Airflow variable value.
    
    Args:
        key: Variable key
        
    Returns:
        Variable value or empty string if not found
    """
    command = ["airflow", "variables", "get", key]
    code, stdout, stderr = run_airflow_command(command)
    
    if code == 0:
        return stdout.strip()
    else:
        return ""

def setup_variables(force: bool = False) -> None:
    """
    Setup all Airflow variables for Jaffle Shop Generator.
    
    Args:
        force: If True, overwrite existing variables
    """
    print("🚀 Setting up Airflow Variables for Jaffle Shop Generator")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for key, value in AIRFLOW_VARIABLES.items():
        # Check if variable already exists
        existing_value = get_airflow_variable(key)
        
        if existing_value and not force:
            print(f"⏭️  Skipping existing variable: {key} = {existing_value}")
            skip_count += 1
            continue
        
        # Set the variable
        if set_airflow_variable(key, value):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Setup Summary:")
    print(f"   ✅ Variables set: {success_count}")
    print(f"   ⏭️  Variables skipped: {skip_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if error_count > 0:
        print(f"\n⚠️  {error_count} variables failed to set. Check Airflow connectivity.")
        sys.exit(1)
    else:
        print(f"\n🎉 All variables configured successfully!")

def list_variables() -> None:
    """List all Jaffle Shop Generator variables."""
    print("📋 Current Jaffle Shop Generator Variables:")
    print("=" * 50)
    
    for key in AIRFLOW_VARIABLES.keys():
        value = get_airflow_variable(key)
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value or 'NOT SET'}")

def validate_setup() -> bool:
    """
    Validate that the Airflow setup is correct for Jaffle Shop Generator.
    
    Returns:
        True if setup is valid, False otherwise
    """
    print("🔍 Validating Airflow Setup for Jaffle Shop Generator")
    print("=" * 55)
    
    issues = []
    
    # Check required variables
    required_vars = ["jafgen_base_path", "jafgen_output_path", "jafgen_schema_path"]
    for var in required_vars:
        value = get_airflow_variable(var)
        if not value:
            issues.append(f"Missing required variable: {var}")
        else:
            print(f"✅ {var}: {value}")
    
    # Check if paths exist (if running locally)
    base_path = get_airflow_variable("jafgen_base_path")
    if base_path and Path(base_path).exists():
        print(f"✅ Base path exists: {base_path}")
    elif base_path:
        issues.append(f"Base path does not exist: {base_path}")
    
    # Check DAG files
    dag_files = [
        "jafgen_stripe_daily.py",
        "jafgen_multi_api_weekly.py", 
        "jafgen_airbyte_import.py"
    ]
    
    dags_dir = Path("dags")
    if dags_dir.exists():
        for dag_file in dag_files:
            if (dags_dir / dag_file).exists():
                print(f"✅ DAG file found: {dag_file}")
            else:
                issues.append(f"Missing DAG file: {dag_file}")
    else:
        issues.append("DAGs directory not found")
    
    if issues:
        print(f"\n❌ Validation Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"\n🎉 Validation passed! Setup is ready for Jaffle Shop Generator.")
        return True

def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup Airflow Variables for Jaffle Shop Generator"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Overwrite existing variables"
    )
    parser.add_argument(
        "--list",
        action="store_true", 
        help="List current variables"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate setup"
    )
    
    args = parser.parse_args()
    
    # Check Airflow availability
    if not check_airflow_available():
        print("❌ Airflow CLI not available. Make sure Airflow is installed and configured.")
        print("   Try: pip install apache-airflow")
        sys.exit(1)
    
    if args.list:
        list_variables()
    elif args.validate:
        if not validate_setup():
            sys.exit(1)
    else:
        setup_variables(force=args.force)
        
        # Run validation after setup
        print("\n" + "=" * 60)
        if not validate_setup():
            sys.exit(1)

if __name__ == "__main__":
    main()