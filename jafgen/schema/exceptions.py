"""Exceptions for schema management."""


class SchemaError(Exception):
    """Base exception for schema-related errors."""

    pass


class SchemaValidationError(SchemaError):
    """Exception raised when schema validation fails."""

    pass


class SchemaLoadError(SchemaError):
    """Exception raised when schema loading fails."""

    pass


class CircularDependencyError(SchemaError):
    """Exception raised when circular dependencies are detected."""

    pass
