"""Abstract interfaces for output writers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class OutputWriter(ABC):
    """Abstract base class for output writers."""
    
    @abstractmethod
    def write(self, data: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
        """Write generated data to the specified output path."""
        pass