"""Exceptions for data generation."""


class GenerationError(Exception):
    """Base exception for generation-related errors."""

    pass


class LinkResolutionError(GenerationError):
    """Exception raised when link resolution fails."""

    pass


class UniqueConstraintError(GenerationError):
    """Exception raised when unique constraint cannot be satisfied."""

    pass


class AttributeGenerationError(GenerationError):
    """Exception raised when attribute value generation fails."""

    pass
