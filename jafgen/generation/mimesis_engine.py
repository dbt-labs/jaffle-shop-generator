"""Concrete implementation of MimesisEngine for deterministic data generation."""

import random
import uuid
from typing import Any, Callable, Optional, Set

from mimesis import Generic
from mimesis.locales import Locale

from ..schema.models import AttributeConfig
from .exceptions import AttributeGenerationError, UniqueConstraintError
from .interfaces import MimesisEngine as MimesisEngineInterface


class MimesisEngine(MimesisEngineInterface):
    """Concrete implementation of Mimesis-based data generation."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the engine with optional seed for reproducibility."""
        self.seed = seed if seed is not None else 42
        self.generic = Generic(locale=Locale.EN, seed=self.seed)
        # Also seed Python's random module for consistency
        random.seed(self.seed)

        # Track unique values per attribute type
        self._unique_values: dict[str, Set[Any]] = {}

        # Maximum retries for unique value generation
        self._max_retries = 1000

    def reset_seed(self, seed: Optional[int] = None) -> None:
        """Reset the engine with a new seed."""
        if seed is not None:
            self.seed = seed
        self.generic = Generic(locale=Locale.EN, seed=self.seed)
        random.seed(self.seed)
        self.reset_unique_values()

    def reset_unique_values(self) -> None:
        """Reset the unique values tracking for fresh generation."""
        self._unique_values.clear()

    def generate_value(self, attribute_config: AttributeConfig) -> Any:
        """Generate a single value based on attribute configuration."""
        try:
            # Handle link_to attributes - these will be resolved by LinkResolver
            if attribute_config.link_to:
                return None  # Placeholder, will be resolved later

            # Get the provider and method from the type string
            provider_method = attribute_config.type

            # Handle constraints
            constraints = attribute_config.constraints or {}

            # Generate the value based on the provider type
            value = self._generate_by_type(provider_method, constraints)

            # Handle unique constraint
            if attribute_config.unique:
                unique_key = f"{provider_method}_{id(attribute_config)}"
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()

                value = self.ensure_unique(
                    lambda: self._generate_by_type(provider_method, constraints),
                    self._unique_values[unique_key],
                )
                self._unique_values[unique_key].add(value)

            return value

        except Exception as e:
            msg = (
                f"Failed to generate value for attribute type "
                f"'{attribute_config.type}': {str(e)}"
            )
            raise AttributeGenerationError(msg) from e

    def ensure_unique(self, generator_func: Callable, seen_values: Set) -> Any:
        """Generate a unique value using the given generator function."""
        for attempt in range(self._max_retries):
            value = generator_func()
            if value not in seen_values:
                return value

        raise UniqueConstraintError(
            f"Could not generate unique value after {self._max_retries} attempts"
        )

    def _generate_by_type(self, provider_method: str, constraints: dict) -> Any:
        """Generate a value based on the provider method string."""
        # Split provider.method format (e.g., "person.full_name")
        if "." in provider_method:
            provider_name, method_name = provider_method.split(".", 1)
        else:
            # Handle simple types
            provider_name = provider_method
            method_name = None

        # Handle special cases and common types
        if provider_name == "uuid":
            # Use seeded random bytes for deterministic UUID generation
            random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
            return str(uuid.UUID(bytes=random_bytes, version=4))
        elif provider_name == "int" or provider_name == "integer":
            min_val = constraints.get("min_value", 1)
            max_val = constraints.get(
                "max_value", 100000
            )  # Increased range for unique IDs
            return self.generic.numeric.integer_number(start=min_val, end=max_val)
        elif provider_name == "float" or provider_name == "decimal":
            min_val = constraints.get("min_value", 0.0)
            max_val = constraints.get("max_value", 1000.0)
            precision = constraints.get("precision", 2)
            value = self.generic.numeric.float_number(start=min_val, end=max_val)
            return round(value, precision)
        elif provider_method == "numeric.decimal":
            # Handle numeric.decimal - mimesis uses 'decimals' not 'decimal'
            min_val = constraints.get("min_value", 0.0)
            max_val = constraints.get("max_value", 1000.0)
            precision = constraints.get("precision", 2)
            value = self.generic.numeric.float_number(start=min_val, end=max_val)
            return round(value, precision)
        elif provider_method == "code.ean13":
            # Handle EAN13 codes - mimesis uses EANFormat enum
            from mimesis.enums import EANFormat

            return self.generic.code.ean(fmt=EANFormat.EAN13)
        elif provider_method == "person.phone":
            # Handle phone numbers - mimesis uses phone_number not phone
            return self.generic.person.phone_number()
        elif provider_method == "address.street_name":
            return self.generic.address.street_name()
        elif provider_method == "address.city":
            return self.generic.address.city()
        elif provider_method == "address.state":
            return self.generic.address.state()
        elif provider_method == "address.postal_code":
            return self.generic.address.postal_code()
        elif provider_method == "address.country_code":
            return self.generic.address.country_code()
        elif provider_method == "internet.url":
            return self.generic.internet.url()
        elif provider_name == "string" or provider_name == "text":
            length = constraints.get("length", 10)
            return self.generic.text.word()[:length]
        elif provider_name == "bool" or provider_name == "boolean":
            return self.generic.development.boolean()
        elif provider_name == "choice":
            choices = constraints.get("choices", ["option1", "option2", "option3"])
            return self.generic.choice(choices)
        elif provider_method == "numeric.integer":
            # Handle numeric.integer specifically
            min_val = constraints.get("min_value", 1)
            max_val = constraints.get(
                "max_value", 100000
            )  # Increased range for unique IDs
            return self.generic.numeric.integer_number(start=min_val, end=max_val)

        # Handle provider.method format
        if method_name:
            try:
                # Get the provider
                provider = getattr(self.generic, provider_name)

                # Get the method
                method = getattr(provider, method_name)

                # Apply constraints as method arguments if applicable
                if constraints:
                    # Filter constraints to only include valid method parameters
                    filtered_constraints = self._filter_method_constraints(
                        method, constraints
                    )
                    return method(**filtered_constraints)
                else:
                    return method()

            except AttributeError as e:
                raise AttributeGenerationError(
                    f"Unknown provider method: {provider_method}"
                ) from e
        else:
            raise AttributeGenerationError(
                f"Invalid provider method format: {provider_method}. "
                f"Expected format: 'provider.method' or recognized simple type"
            )

    def _filter_method_constraints(self, method: Callable, constraints: dict) -> dict:
        """Filter constraints to only include valid method parameters."""
        import inspect

        try:
            # Get method signature
            sig = inspect.signature(method)
            valid_params = set(sig.parameters.keys())

            # Filter constraints to only include valid parameters
            return {k: v for k, v in constraints.items() if k in valid_params}
        except Exception:
            # If we can't inspect the method, return constraints as-is
            return constraints
