"""Exceptions for output writers."""


class OutputError(Exception):
    """Base exception for output-related errors."""
    pass


class OutputWriteError(OutputError):
    """Exception raised when output writing fails."""
    pass


class UnsupportedFormatError(OutputError):
    """Exception raised when an unsupported output format is requested."""
    pass