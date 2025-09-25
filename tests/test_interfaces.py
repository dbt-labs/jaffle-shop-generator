"""Tests for interface classes."""

import pytest
from abc import ABC

from jafgen.generation.interfaces import MimesisEngine, LinkResolver, DataGenerator
from jafgen.output.interfaces import OutputWriter
from jafgen.schema.interfaces import SchemaLoader


class TestMimesisEngineInterface:
    """Test cases for MimesisEngine interface."""
    
    def test_is_abstract(self):
        """Test that MimesisEngine is abstract."""
        assert issubclass(MimesisEngine, ABC)
        
        with pytest.raises(TypeError):
            MimesisEngine()
    
    def test_has_required_methods(self):
        """Test that interface defines required methods."""
        assert hasattr(MimesisEngine, 'generate_value')
        assert hasattr(MimesisEngine, 'ensure_unique')


class TestLinkResolverInterface:
    """Test cases for LinkResolver interface."""
    
    def test_is_abstract(self):
        """Test that LinkResolver is abstract."""
        assert issubclass(LinkResolver, ABC)
        
        with pytest.raises(TypeError):
            LinkResolver()
    
    def test_has_required_methods(self):
        """Test that interface defines required methods."""
        assert hasattr(LinkResolver, 'register_entity')
        assert hasattr(LinkResolver, 'resolve_link')
        assert hasattr(LinkResolver, 'build_dependency_graph')


class TestDataGeneratorInterface:
    """Test cases for DataGenerator interface."""
    
    def test_is_abstract(self):
        """Test that DataGenerator is abstract."""
        assert issubclass(DataGenerator, ABC)
        
        with pytest.raises(TypeError):
            DataGenerator()
    
    def test_has_required_methods(self):
        """Test that interface defines required methods."""
        assert hasattr(DataGenerator, 'generate_entity')
        assert hasattr(DataGenerator, 'generate_system')


class TestOutputWriterInterface:
    """Test cases for OutputWriter interface."""
    
    def test_is_abstract(self):
        """Test that OutputWriter is abstract."""
        assert issubclass(OutputWriter, ABC)
        
        with pytest.raises(TypeError):
            OutputWriter()
    
    def test_has_required_methods(self):
        """Test that interface defines required methods."""
        assert hasattr(OutputWriter, 'write')


class TestSchemaLoaderInterface:
    """Test cases for SchemaLoader interface."""
    
    def test_is_abstract(self):
        """Test that SchemaLoader is abstract."""
        assert issubclass(SchemaLoader, ABC)
        
        with pytest.raises(TypeError):
            SchemaLoader()
    
    def test_has_required_methods(self):
        """Test that interface defines required methods."""
        assert hasattr(SchemaLoader, 'discover_schemas')
        assert hasattr(SchemaLoader, 'load_schema')
        assert hasattr(SchemaLoader, 'validate_schema')


class ConcreteMimesisEngine(MimesisEngine):
    """Concrete implementation for testing."""
    
    def __init__(self, seed=None):
        self.seed = seed
    
    def generate_value(self, attribute_config):
        return "test_value"
    
    def ensure_unique(self, generator_func, seen_values):
        return "unique_value"


class ConcreteDataGenerator(DataGenerator):
    """Concrete implementation for testing."""
    
    def generate_entity(self, entity_config):
        return []
    
    def generate_system(self, schema):
        return None


class ConcreteLinkResolver(LinkResolver):
    """Concrete implementation for testing."""
    
    def register_entity(self, schema_name, entity_name, data):
        pass
    
    def resolve_link(self, link_spec):
        return None
    
    def build_dependency_graph(self, schemas):
        return None


class ConcreteOutputWriter(OutputWriter):
    """Concrete implementation for testing."""
    
    def write(self, data, output_path):
        pass


class ConcreteSchemaLoader(SchemaLoader):
    """Concrete implementation for testing."""
    
    def discover_schemas(self, schema_dir):
        return []
    
    def load_schema(self, schema_path):
        return None
    
    def validate_schema(self, schema):
        return None


class TestConcreteImplementations:
    """Test that concrete implementations work."""
    
    def test_concrete_mimesis_engine(self):
        """Test concrete MimesisEngine implementation."""
        engine = ConcreteMimesisEngine(seed=42)
        assert engine is not None
        assert engine.seed == 42
        assert engine.generate_value(None) == "test_value"
        assert engine.ensure_unique(None, set()) == "unique_value"
    
    def test_concrete_data_generator(self):
        """Test concrete DataGenerator implementation."""
        generator = ConcreteDataGenerator()
        assert generator is not None
        assert generator.generate_entity(None) == []
        assert generator.generate_system(None) is None
    
    def test_concrete_link_resolver(self):
        """Test concrete LinkResolver implementation."""
        resolver = ConcreteLinkResolver()
        assert resolver is not None
        resolver.register_entity("test", "entity", [])
        assert resolver.resolve_link("test.entity.id") is None
        assert resolver.build_dependency_graph([]) is None
    
    def test_concrete_output_writer(self):
        """Test concrete OutputWriter implementation."""
        writer = ConcreteOutputWriter()
        assert writer is not None
        writer.write({}, "/tmp")  # Should not raise
    
    def test_concrete_schema_loader(self):
        """Test concrete SchemaLoader implementation."""
        loader = ConcreteSchemaLoader()
        assert loader is not None
        assert loader.discover_schemas("/tmp") == []
        assert loader.load_schema("/tmp/schema.yaml") is None
        assert loader.validate_schema(None) is None