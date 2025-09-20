"""Tests for MimesisEngine implementation."""

import pytest
from unittest.mock import Mock

from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.exceptions import AttributeGenerationError, UniqueConstraintError
from jafgen.schema.models import AttributeConfig


class TestMimesisEngine:
    """Test cases for MimesisEngine."""
    
    def test_init_with_seed(self):
        """Test engine initialization with seed."""
        engine = MimesisEngine(seed=123)
        assert engine.seed == 123
        assert engine.generic is not None
    
    def test_init_without_seed_uses_default(self):
        """Test engine initialization without seed uses default."""
        engine = MimesisEngine()
        assert engine.seed == 42
    
    def test_deterministic_generation_with_same_seed(self):
        """Test that same seed produces identical results."""
        config = AttributeConfig(type="person.full_name")
        
        engine1 = MimesisEngine(seed=123)
        engine2 = MimesisEngine(seed=123)
        
        value1 = engine1.generate_value(config)
        value2 = engine2.generate_value(config)
        
        assert value1 == value2
        assert isinstance(value1, str)
        assert len(value1) > 0
    
    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        config = AttributeConfig(type="person.full_name")
        
        engine1 = MimesisEngine(seed=123)
        engine2 = MimesisEngine(seed=456)
        
        # Generate multiple values to reduce chance of coincidental match
        values1 = [engine1.generate_value(config) for _ in range(10)]
        values2 = [engine2.generate_value(config) for _ in range(10)]
        
        # At least some values should be different
        assert values1 != values2
    
    def test_generate_person_full_name(self):
        """Test generating person full name."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="person.full_name")
        
        value = engine.generate_value(config)
        
        assert isinstance(value, str)
        assert len(value) > 0
        assert ' ' in value  # Should contain space between names
    
    def test_generate_person_email(self):
        """Test generating person email."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="person.email")
        
        value = engine.generate_value(config)
        
        assert isinstance(value, str)
        assert '@' in value
        assert '.' in value
    
    def test_generate_uuid(self):
        """Test generating UUID."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="uuid")
        
        value = engine.generate_value(config)
        
        assert isinstance(value, str)
        assert len(value) == 36  # Standard UUID length
        assert value.count('-') == 4  # Standard UUID format
    
    def test_generate_integer_with_constraints(self):
        """Test generating integer with min/max constraints."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="int",
            constraints={"min_value": 10, "max_value": 20}
        )
        
        value = engine.generate_value(config)
        
        assert isinstance(value, int)
        assert 10 <= value <= 20
    
    def test_generate_float_with_constraints(self):
        """Test generating float with constraints."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="float",
            constraints={"min_value": 1.0, "max_value": 10.0, "precision": 2}
        )
        
        value = engine.generate_value(config)
        
        assert isinstance(value, float)
        assert 1.0 <= value <= 10.0
        # Check precision (2 decimal places)
        assert len(str(value).split('.')[-1]) <= 2
    
    def test_generate_boolean(self):
        """Test generating boolean value."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="bool")
        
        value = engine.generate_value(config)
        
        assert isinstance(value, bool)
    
    def test_generate_datetime_with_constraints(self):
        """Test generating datetime with date constraints."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="datetime.datetime",
            constraints={"start": 2020, "end": 2024}
        )
        
        value = engine.generate_value(config)
        
        # Should return a datetime object or string
        assert value is not None
    
    def test_unique_constraint_generates_different_values(self):
        """Test that unique constraint generates different values."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="person.full_name", unique=True)
        
        values = []
        for _ in range(10):
            value = engine.generate_value(config)
            values.append(value)
        
        # All values should be unique
        assert len(values) == len(set(values))
    
    def test_unique_constraint_failure_raises_exception(self):
        """Test that unique constraint failure raises exception."""
        engine = MimesisEngine(seed=123)
        engine._max_retries = 5  # Reduce retries for faster test
        
        # Mock the generator to always return the same value
        def mock_generator():
            return "same_value"
        
        seen_values = set()
        
        # First call should succeed
        value = engine.ensure_unique(mock_generator, seen_values)
        seen_values.add(value)
        
        # Second call should fail after retries
        with pytest.raises(UniqueConstraintError):
            engine.ensure_unique(mock_generator, seen_values)
    
    def test_link_to_attribute_returns_none(self):
        """Test that link_to attributes return None (to be resolved later)."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="uuid",
            link_to="other_schema.entity.id"
        )
        
        value = engine.generate_value(config)
        
        assert value is None
    
    def test_invalid_provider_method_raises_exception(self):
        """Test that invalid provider method raises exception."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="invalid.method")
        
        with pytest.raises(AttributeGenerationError) as exc_info:
            engine.generate_value(config)
        
        assert "Unknown provider method" in str(exc_info.value)
    
    def test_invalid_format_raises_exception(self):
        """Test that invalid format raises exception."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="invalid_format")
        
        with pytest.raises(AttributeGenerationError) as exc_info:
            engine.generate_value(config)
        
        assert "Invalid provider method format" in str(exc_info.value)
    
    def test_required_attribute_never_returns_none_or_empty(self):
        """Test that required attributes never return None or empty values."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(type="person.full_name", required=True)
        
        for _ in range(20):  # Test multiple generations
            value = engine.generate_value(config)
            assert value is not None
            assert value != ""
            assert len(str(value).strip()) > 0
    
    def test_numeric_decimal_type(self):
        """Test generating numeric decimal values."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="decimal",
            constraints={"min_value": 5.0, "max_value": 100.0, "precision": 2}
        )
        
        value = engine.generate_value(config)
        
        assert isinstance(value, float)
        assert 5.0 <= value <= 100.0
    
    def test_text_type_with_length_constraint(self):
        """Test generating text with length constraint."""
        engine = MimesisEngine(seed=123)
        config = AttributeConfig(
            type="text",
            constraints={"length": 5}
        )
        
        value = engine.generate_value(config)
        
        assert isinstance(value, str)
        assert len(value) <= 5
    
    def test_multiple_engines_with_same_seed_produce_same_sequence(self):
        """Test that multiple engines with same seed produce identical sequences."""
        config = AttributeConfig(type="person.full_name")
        
        engine1 = MimesisEngine(seed=999)
        engine2 = MimesisEngine(seed=999)
        
        sequence1 = [engine1.generate_value(config) for _ in range(5)]
        sequence2 = [engine2.generate_value(config) for _ in range(5)]
        
        assert sequence1 == sequence2