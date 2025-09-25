"""Tests for OutputManager functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jafgen.output.output_manager import OutputManager
from jafgen.output.exceptions import OutputError
from jafgen.schema.models import SystemSchema, EntityConfig, AttributeConfig, OutputConfig


class TestOutputManager:
    """Test cases for OutputManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from jafgen.output.csv_writer import CSVWriter
        from jafgen.output.json_writer import JSONWriter
        from jafgen.output.parquet_writer import ParquetWriter
        from jafgen.output.duckdb_writer import DuckDBWriter
        
        writers = {
            "csv": CSVWriter(),
            "json": JSONWriter(),
            "parquet": ParquetWriter(),
            "duckdb": DuckDBWriter()
        }
        self.manager = OutputManager(writers)
    
    def test_init(self):
        """Test OutputManager initialization."""
        assert self.manager is not None
        assert hasattr(self.manager, 'output_writers')
        assert len(self.manager.output_writers) == 4
    
    def test_prepare_output_directory(self, tmp_path: Path):
        """Test preparing output directory."""
        output_path = tmp_path / "test_output"
        
        # Directory doesn't exist yet
        assert not output_path.exists()
        
        self.manager.prepare_output_directory(output_path)
        
        # Directory should be created
        assert output_path.exists()
        assert output_path.is_dir()
    
    def test_prepare_output_directory_existing(self, tmp_path: Path):
        """Test preparing existing output directory."""
        output_path = tmp_path / "existing"
        output_path.mkdir()
        
        # Should not raise error for existing directory
        self.manager.prepare_output_directory(output_path)
        
        assert output_path.exists()
        assert output_path.is_dir()
    
    def test_prepare_output_directory_force_recreate(self, tmp_path: Path):
        """Test force recreating output directory."""
        output_path = tmp_path / "force_recreate"
        output_path.mkdir()
        
        # Create a file in the directory
        test_file = output_path / "test.txt"
        test_file.write_text("test content")
        
        self.manager.prepare_output_directory(output_path, force_recreate=True)
        
        # Directory should still exist but file should be gone
        assert output_path.exists()
        assert output_path.is_dir()
        assert not test_file.exists()
    
    def test_clean_output_directory(self, tmp_path: Path):
        """Test cleaning output directory."""
        output_path = tmp_path / "clean_test"
        output_path.mkdir()
        
        # Create some test files
        (output_path / "test1.csv").write_text("data")
        (output_path / "test2.json").write_text("{}")
        
        self.manager.clean_output_directory(output_path)
        
        # Directory should exist but be empty
        assert output_path.exists()
        assert len(list(output_path.iterdir())) == 0
    
    def test_clean_output_directory_keep_metadata(self, tmp_path: Path):
        """Test cleaning output directory while keeping metadata."""
        output_path = tmp_path / "clean_metadata_test"
        output_path.mkdir()
        
        # Create test files and metadata
        (output_path / "test.csv").write_text("data")
        (output_path / ".jafgen_metadata.json").write_text("{}")
        
        self.manager.clean_output_directory(output_path, keep_metadata=True)
        
        # Data file should be gone, metadata should remain
        assert not (output_path / "test.csv").exists()
        assert (output_path / ".jafgen_metadata.json").exists()
    
    def test_output_writers_access(self):
        """Test accessing output writers."""
        assert "csv" in self.manager.output_writers
        assert "json" in self.manager.output_writers
        assert "parquet" in self.manager.output_writers
        assert "duckdb" in self.manager.output_writers
        
        # Check writer types
        assert self.manager.output_writers["csv"].__class__.__name__ == "CSVWriter"
        assert self.manager.output_writers["json"].__class__.__name__ == "JSONWriter"
        assert self.manager.output_writers["parquet"].__class__.__name__ == "ParquetWriter"
        assert self.manager.output_writers["duckdb"].__class__.__name__ == "DuckDBWriter"