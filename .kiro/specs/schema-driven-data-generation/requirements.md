# Requirements Document

## Introduction

This feature transforms the jaffle-shop-generator from its current hardcoded approach to a flexible, schema-driven data generation system. The new system will use YAML configuration files to define data schemas, support multiple output formats, integrate with external system definitions (like Airbyte manifests), and provide deterministic, reproducible fake data generation using the Mimesis library.

## Requirements

### Requirement 1

**User Story:** As a data engineer, I want to define data schemas using YAML files, so that I can generate fake data without writing code for each new entity type.

#### Acceptance Criteria

1. WHEN a user places YAML schema files in the ./schemas directory THEN the system SHALL discover and load all valid schema files
2. WHEN a schema defines system-level configuration (name, version, seed, output) THEN the system SHALL apply these settings to the data generation process
3. WHEN a schema defines entities with attributes THEN the system SHALL generate fake data matching the specified types and constraints
4. IF an attribute is marked as unique THEN the system SHALL ensure no duplicate values are generated for that attribute
5. IF an attribute is marked as required THEN the system SHALL never generate null or empty values for that attribute

### Requirement 2

**User Story:** As a data engineer, I want to link entities across different schemas, so that I can maintain referential integrity in my generated datasets.

#### Acceptance Criteria

1. WHEN a schema defines a link_to attribute referencing another entity THEN the system SHALL create valid foreign key relationships
2. WHEN generating linked data THEN the system SHALL ensure referenced entities exist before creating dependent records
3. WHEN multiple schemas reference the same entity THEN the system SHALL maintain consistent linking across all schemas
4. IF a link_to reference cannot be resolved THEN the system SHALL provide a clear error message indicating the missing dependency

### Requirement 3

**User Story:** As a data engineer, I want deterministic data generation with seeding, so that I can reproduce the same datasets for testing and development.

#### Acceptance Criteria

1. WHEN a seed value is specified in the schema THEN the system SHALL generate identical data across multiple runs
2. WHEN no seed is specified THEN the system SHALL use a default seed for reproducibility
3. WHEN different seeds are used THEN the system SHALL generate different but valid datasets
4. WHEN the same seed is used with identical schemas THEN the system SHALL produce byte-for-byte identical output files

### Requirement 4

**User Story:** As a data engineer, I want to output generated data in multiple formats, so that I can integrate with different downstream systems and tools.

#### Acceptance Criteria

1. WHEN generating data THEN the system SHALL support CSV output format
2. WHEN generating data THEN the system SHALL support JSON output format  
3. WHEN generating data THEN the system SHALL support Parquet output format
4. WHEN generating data THEN the system SHALL support DuckDB output format
5. WHEN output format is specified in schema THEN the system SHALL use the specified format
6. WHEN output path is specified in schema THEN the system SHALL write files to the specified location

### Requirement 5

**User Story:** As a data engineer, I want idempotent data generation, so that running the generator multiple times doesn't create duplicate or inconsistent data.

#### Acceptance Criteria

1. WHEN the generator is run multiple times with the same configuration THEN the system SHALL produce identical output files
2. WHEN output files already exist THEN the system SHALL overwrite them with fresh data rather than append
3. WHEN generating linked data THEN the system SHALL maintain consistent relationships across multiple runs
4. IF the schema or seed changes THEN the system SHALL generate new data reflecting the changes

### Requirement 6

**User Story:** As a data engineer, I want CLI commands to manage schemas and generate data, so that I can integrate the tool into automated workflows.

#### Acceptance Criteria

1. WHEN I run the generate command THEN the system SHALL process all schemas and generate data files
2. WHEN I run the validate-schema command THEN the system SHALL check all schemas for syntax and logical errors
3. WHEN I run the list-schemas command THEN the system SHALL display all discovered schemas with their basic information
4. IF a command encounters an error THEN the system SHALL provide clear error messages and appropriate exit codes
5. WHEN using CLI commands THEN the system SHALL support standard help and version flags

### Requirement 7

**User Story:** As a data engineer, I want to import Airbyte source manifest.yaml files, so that I can generate test data matching real API schemas without manual translation.

#### Acceptance Criteria

1. WHEN provided with an Airbyte source manifest.yaml file THEN the system SHALL parse the stream definitions
2. WHEN translating Airbyte manifests THEN the system SHALL convert stream schemas to jafgen-compatible YAML format
3. WHEN Airbyte manifest defines relationships THEN the system SHALL preserve these as link_to attributes
4. IF an Airbyte manifest contains unsupported features THEN the system SHALL provide warnings and skip unsupported elements
5. WHEN importing manifests THEN the system SHALL validate the resulting schemas before saving

### Requirement 8

**User Story:** As a data engineer, I want to use predefined schemas for popular SaaS systems, so that I can quickly generate realistic test data for common integrations.

#### Acceptance Criteria

1. WHEN using HubSpot schema definitions THEN the system SHALL generate data matching HubSpot API structures and relationships
2. WHEN using Xero schema definitions THEN the system SHALL generate data matching Xero API structures and relationships  
3. WHEN using Huntr schema definitions THEN the system SHALL generate data matching Huntr API structures and relationships
4. WHEN using Salesforce schema definitions THEN the system SHALL generate data matching Salesforce API structures and relationships
5. WHEN SaaS schemas define cross-entity relationships THEN the system SHALL maintain referential integrity across related entities

### Requirement 9

**User Story:** As a developer, I want comprehensive test coverage, so that I can confidently modify and extend the system without breaking existing functionality.

#### Acceptance Criteria

1. WHEN running unit tests THEN the system SHALL achieve at least 90% code coverage
2. WHEN testing schema loading THEN the system SHALL validate correct parsing of all YAML features
3. WHEN testing data generation THEN the system SHALL verify deterministic output with seeding
4. WHEN testing output formats THEN the system SHALL validate correct file generation for CSV, JSON, Parquet, and DuckDB
5. WHEN testing integration scenarios THEN the system SHALL verify end-to-end workflows including Airbyte manifest processing

### Requirement 10

**User Story:** As a developer, I want the system to use modern Python tooling and practices, so that the codebase is maintainable and follows industry standards.

#### Acceptance Criteria

1. WHEN code is committed THEN the system SHALL pass black formatting checks
2. WHEN code is committed THEN the system SHALL pass isort import sorting checks
3. WHEN code is committed THEN the system SHALL pass mypy type checking
4. WHEN tests are run THEN the system SHALL generate coverage reports
5. WHEN using external libraries THEN the system SHALL use Mimesis for fake data generation and Typer for CLI framework