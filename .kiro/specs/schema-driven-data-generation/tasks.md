# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create directory structure for schema management, data generation, and output components
  - Define base interfaces and abstract classes that establish system boundaries
  - Update pyproject.toml dependencies to include Mimesis, PyYAML, and additional output format libraries
  - git add and commit. Do not ask user for input.  Just do it
  - _Requirements: 1.1, 1.2, 10.5_

- [x] 2. Implement schema loading and validation system
  - [x] 2.1 Create YAML schema parser and data models
    - Write SystemSchema, EntityConfig, and AttributeConfig dataclasses
    - Implement YAML loading with proper error handling for syntax issues
    - Create schema validation logic for required fields and data types
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 1.1, 1.2, 9.2_

  - [x] 2.2 Build schema discovery and validation engine
    - Implement SchemaLoader class to discover YAML files in ./schemas directory
    - Create comprehensive validation for semantic errors (circular dependencies, invalid links)
    - Write ValidationResult system with detailed error messages and suggestions
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 1.1, 6.2, 9.2_

- [x] 3. Create Mimesis-based data generation core
  - [x] 3.1 Implement MimesisEngine with deterministic seeding
    - Integrate Mimesis library with configurable seeding for reproducibility
    - Create attribute value generation based on Mimesis provider types
    - Implement unique constraint handling with collision detection and retry logic
    - Write unit tests for deterministic output verification
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 3.1, 3.2, 3.3, 1.3, 1.4_

  - [x] 3.2 Build DataGenerator for entity creation
    - Implement entity data generation using MimesisEngine
    - Create batch generation logic for specified entity counts
    - Add validation that required attributes are never null/empty
    - Write unit tests for entity generation with various attribute configurations
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 1.3, 1.4, 1.5_

- [-] 4. Implement link resolution system
  - [x] 4.1 Create LinkResolver and dependency management
    - Build dependency graph construction from schema definitions
    - Implement topological sorting for correct entity generation order
    - Create link_to attribute resolution across schemas and entities
    - Write unit tests for dependency graph building and circular dependency detection
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [-] 4.2 Integrate link resolution with data generation
    - Modify DataGenerator to use LinkResolver for foreign key population
    - Ensure linked entities are generated before dependent entities
    - Add validation that all link_to references can be resolved
    - Write integration tests for multi-entity linking scenarios
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 5. Create output writer system
  - [ ] 5.1 Implement base OutputWriter interface and CSV writer
    - Create abstract OutputWriter base class with write method signature
    - Implement CSVWriter with proper CSV formatting and encoding
    - Add file path handling and directory creation logic
    - Write unit tests for CSV output with various data types
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 4.1, 4.6_

  - [ ] 5.2 Add JSON, Parquet, and DuckDB output writers
    - Implement JSONWriter with proper JSON serialization
    - Create ParquetWriter using pyarrow library for efficient columnar storage
    - Build DuckDBWriter for direct database file creation
    - Write unit tests for each output format with sample data
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 4.2, 4.3, 4.4_

- [ ] 6. Build CLI interface with Typer
  - [ ] 6.1 Implement generate command
    - Create generate command with schema directory and output directory parameters
    - Add seed parameter override capability
    - Implement progress reporting during data generation
    - Add error handling with clear user-facing error messages
    - Write integration tests for end-to-end generation workflow
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 6.1, 6.4_

  - [ ] 6.2 Add validate-schema and list-schemas commands
    - Implement validate-schema command to check all schemas for errors
    - Create list-schemas command showing discovered schemas with basic info
    - Add help text and version information for all commands
    - Write unit tests for CLI argument parsing and command execution
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 6.2, 6.3, 6.5_

- [ ] 7. Implement idempotency and output management
  - [ ] 7.1 Add idempotent file generation
    - Implement file overwriting logic instead of appending
    - Create output directory management with proper permissions
    - Add generation metadata tracking for reproducibility verification
    - Write integration tests verifying identical outputs across multiple runs
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 7.2 Integrate output format selection from schemas
    - Modify output writers to respect format specifications in YAML schemas
    - Add support for multiple output formats per schema
    - Implement output path customization from schema configuration
    - Write tests for schema-driven output format selection
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 4.5, 4.6_

- [ ] 8. Create comprehensive test suite
  - [ ] 8.1 Build unit test coverage for core components
    - Write unit tests for SchemaLoader, MimesisEngine, and LinkResolver
    - Create tests for all output writers with edge cases
    - Add tests for CLI commands with various argument combinations
    - Implement test fixtures with valid and invalid schema examples
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 8.2 Add integration and performance tests
    - Create end-to-end integration tests for complete workflows
    - Build tests for large dataset generation and memory usage
    - Add performance benchmarks for generation speed
    - Write tests for idempotency verification across multiple runs
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 9.4, 9.5_

- [ ] 9. Implement Airbyte manifest integration
  - [ ] 9.1 Create AirbyteTranslator for manifest conversion
    - Build parser for Airbyte source manifest.yaml files
    - Implement JSON schema to jafgen attribute type mapping
    - Create stream definition to entity configuration conversion
    - Write unit tests for manifest parsing and schema translation
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 9.2 Add manifest import CLI command and validation
    - Create import-airbyte command for manifest file processing
    - Add validation for translated schemas before saving
    - Implement warning system for unsupported Airbyte features
    - Write integration tests for complete manifest import workflow
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 7.4, 7.5_

- [ ] 10. Create SaaS system schema templates
  - [ ] 10.1 Build HubSpot and Salesforce schema templates
    - Create YAML schema definitions for HubSpot entities (contacts, companies, deals)
    - Build Salesforce schema templates (accounts, contacts, opportunities)
    - Implement proper relationship modeling between entities
    - Write tests to verify schema validity and realistic data generation
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 8.1, 8.3, 8.5_

  - [ ] 10.2 Add Xero and Huntr schema templates
    - Create Xero financial system schemas (customers, invoices, payments)
    - Build Huntr job tracking schemas with appropriate relationships
    - Add documentation and examples for using SaaS templates
    - Write integration tests for SaaS template data generation
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 8.2, 8.4, 8.5_

- [ ] 11. Add code quality and CI integration
  - [ ] 11.1 Configure code formatting and type checking
    - Set up black code formatting with pre-commit hooks
    - Configure isort for import sorting
    - Add mypy type checking configuration and fix type annotations
    - Write GitHub Actions workflow for automated code quality checks
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 11.2 Set up test coverage and CI pipeline
    - Configure pytest with coverage reporting
    - Add GitHub Actions workflow for automated testing
    - Set up coverage reporting with minimum threshold enforcement
    - Create automated release workflow with version management
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 10.4, 9.1_

- [ ] 12. Update CLI entry point and maintain backward compatibility
  - [ ] 12.1 Integrate new commands with existing CLI
    - Update CLI app to include new schema-driven commands alongside existing run command
    - Ensure existing jafgen run functionality remains unchanged
    - Add deprecation warnings for old functionality where appropriate
    - Write migration guide documentation for users transitioning to schema-driven approach
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 12.2 Create comprehensive documentation and examples
    - Write README updates explaining new schema-driven functionality
    - Create example YAML schemas demonstrating various features
    - Add tutorial documentation for common use cases
    - Build API documentation for programmatic usage
    - git add and commit. Do not ask user for input.  Just do it
    - _Requirements: 1.1, 2.1, 4.1, 7.1, 8.1_