"""Output writer components for jafgen."""

from .interfaces import OutputWriter
from .csv_writer import CSVWriter

__all__ = ["OutputWriter", "CSVWriter"]