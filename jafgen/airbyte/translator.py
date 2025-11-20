"""Airbyte manifest translator for converting Airbyte source manifests to jafgen schemas."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from jafgen.schema.models import (
    AttributeConfig,
    EntityConfig,
    OutputConfig,
    SystemSchema,
    ValidationError,
    ValidationResult,
    ValidationWarning,
)


class AirbyteTranslator:
    """Translates Airbyte source manifest.yaml files to jafgen schema format."""

    # JSON Schema type to Mimesis provider mapping
    TYPE_MAPPINGS = {
        # String types with formats
        ("string", "email"): "person.email",
        ("string", "date-time"): "datetime.datetime",
        ("string", "date"): "datetime.date",
        ("string", "time"): "datetime.time",
        ("string", "uri"): "internet.url",
        ("string", "uuid"): "cryptographic.uuid",
        ("string", "hostname"): "internet.domain_name",
        ("string", "ipv4"): "internet.ip_v4",
        ("string", "ipv6"): "internet.ip_v6",
        # Numeric types - use simple types that MimesisEngine handles specially
        ("integer", None): "integer",
        ("number", None): "decimal",
        # Boolean type
        ("boolean", None): "development.boolean",
        # Default string type
        ("string", None): "text.word",
    }

    def __init__(self) -> None:
        """Initialize the Airbyte translator."""
        self.warnings: List[ValidationWarning] = []
        self.errors: List[ValidationError] = []

    def translate_manifest(self, manifest_path: Path) -> List[SystemSchema]:
        """Translate an Airbyte source manifest.yaml file to jafgen schemas.

        Args:
        ----
            manifest_path: Path to the Airbyte manifest.yaml file

        Returns:
        -------
            List of SystemSchema objects (typically one)

        Raises:
        ------
            FileNotFoundError: If manifest file doesn't exist
            yaml.YAMLError: If manifest file has invalid YAML syntax
            ValueError: If manifest structure is invalid

        """
        self.warnings.clear()
        self.errors.clear()

        if not manifest_path.exists():
            raise FileNotFoundError(f"Airbyte manifest file not found: {manifest_path}")

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in manifest file: {e}")

        if not isinstance(manifest_data, dict):
            raise ValueError("Manifest file must contain a YAML object")

        return self._convert_manifest_to_schemas(manifest_data, manifest_path.stem)

    def _convert_manifest_to_schemas(
        self, manifest_data: Dict[str, Any], base_name: str
    ) -> List[SystemSchema]:
        """Convert manifest data to SystemSchema objects."""
        streams = manifest_data.get("streams", [])

        if not streams:
            self.warnings.append(
                ValidationWarning(
                    type="no_streams",
                    message="No streams found in Airbyte manifest",
                    location="manifest.streams",
                )
            )
            return []

        # Create a single system schema containing all streams as entities
        entities = {}

        for stream in streams:
            try:
                entity_config = self._convert_stream_to_entity(stream)
                entities[entity_config.name] = entity_config
            except Exception as e:
                self.errors.append(
                    ValidationError(
                        type="stream_conversion_error",
                        message=f"Failed to convert stream '{stream.get('name', 'unknown')}': {str(e)}",
                        location=f"streams.{stream.get('name', 'unknown')}",
                    )
                )

        if not entities:
            raise ValueError("No valid entities could be created from Airbyte streams")

        # Create system schema
        system_schema = SystemSchema(
            name=base_name,
            version="1.0.0",
            seed=42,  # Default seed for reproducibility
            output=OutputConfig(format=["csv", "json"], path="./output"),
            entities=entities,
        )

        return [system_schema]

    def _convert_stream_to_entity(self, stream: Dict[str, Any]) -> EntityConfig:
        """Convert an Airbyte stream definition to an EntityConfig."""
        stream_name = stream.get("name")
        if not stream_name:
            raise ValueError("Stream must have a name")

        json_schema = stream.get("json_schema", {})
        if not json_schema:
            raise ValueError(f"Stream '{stream_name}' must have a json_schema")

        properties = json_schema.get("properties", {})
        required_fields = set(json_schema.get("required", []))

        attributes = {}

        for field_name, field_schema in properties.items():
            try:
                attribute_config = self._convert_json_schema_field(
                    field_name, field_schema, is_required=field_name in required_fields
                )
                attributes[field_name] = attribute_config
            except Exception as e:
                self.warnings.append(
                    ValidationWarning(
                        type="field_conversion_warning",
                        message=f"Could not convert field '{field_name}' in stream '{stream_name}': {str(e)}",
                        location=f"streams.{stream_name}.json_schema.properties.{field_name}",
                    )
                )

        if not attributes:
            raise ValueError(
                f"No valid attributes could be created for stream '{stream_name}'"
            )

        # Default entity count - can be overridden in the generated schema
        entity_count = 1000

        return EntityConfig(name=stream_name, count=entity_count, attributes=attributes)

    def _convert_json_schema_field(
        self, field_name: str, field_schema: Dict[str, Any], is_required: bool = True
    ) -> AttributeConfig:
        """Convert a JSON Schema field definition to an AttributeConfig."""
        field_type = field_schema.get("type")
        field_format = field_schema.get("format")

        if not field_type:
            # Handle complex types that might not have a simple type
            if (
                "oneOf" in field_schema
                or "anyOf" in field_schema
                or "allOf" in field_schema
            ):
                self.warnings.append(
                    ValidationWarning(
                        type="unsupported_schema_feature",
                        message=f"Complex schema features (oneOf/anyOf/allOf) not supported for field '{field_name}', using default string type",
                        location=f"field.{field_name}",
                    )
                )
                field_type = "string"
            elif "enum" in field_schema:
                # Handle enum as string with constraints
                field_type = "string"
            else:
                raise ValueError(f"Field '{field_name}' has no type information")

        # Map JSON Schema type to Mimesis provider
        mimesis_type = self._map_json_schema_type(
            field_type, field_format, field_schema
        )

        # Determine if field should be unique (typically for ID fields)
        is_unique = (
            field_name.lower() in ["id", "uuid", "identifier"]
            or field_name.lower().endswith("_id")
            or field_format == "uuid"
        )

        # Build constraints from JSON Schema validation rules
        constraints = self._extract_constraints(field_schema)

        return AttributeConfig(
            type=mimesis_type,
            unique=is_unique,
            required=is_required,
            constraints=constraints,
        )

    def _map_json_schema_type(
        self, json_type: str, json_format: Optional[str], field_schema: Dict[str, Any]
    ) -> str:
        """Map JSON Schema type and format to Mimesis provider type."""
        # Check for enum values
        if "enum" in field_schema:
            enum_values = field_schema["enum"]
            if all(isinstance(v, str) for v in enum_values):
                return "choice"  # Will use constraints to specify choices
            else:
                self.warnings.append(
                    ValidationWarning(
                        type="enum_type_warning",
                        message=f"Mixed-type enum not fully supported, using default type for {json_type}",
                    )
                )

        # Use type mapping
        mapping_key = (json_type, json_format)
        if mapping_key in self.TYPE_MAPPINGS:
            return self.TYPE_MAPPINGS[mapping_key]

        # Fallback to type without format
        fallback_key = (json_type, None)
        if fallback_key in self.TYPE_MAPPINGS:
            if json_format:
                self.warnings.append(
                    ValidationWarning(
                        type="unsupported_format",
                        message=f"Format '{json_format}' not supported for type '{json_type}', using default {json_type} mapping",
                    )
                )
            return self.TYPE_MAPPINGS[fallback_key]

        # Handle unsupported types
        if json_type == "array":
            self.warnings.append(
                ValidationWarning(
                    type="unsupported_type",
                    message="Array types not supported, using text.word as fallback",
                )
            )
            return "text.word"
        elif json_type == "object":
            self.warnings.append(
                ValidationWarning(
                    type="unsupported_type",
                    message="Object types not supported, using text.word as fallback",
                )
            )
            return "text.word"
        else:
            self.warnings.append(
                ValidationWarning(
                    type="unknown_type",
                    message=f"Unknown JSON Schema type '{json_type}', using text.word as fallback",
                )
            )
            return "text.word"

    def _extract_constraints(self, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract validation constraints from JSON Schema field definition."""
        constraints = {}

        # Numeric constraints
        if "minimum" in field_schema:
            constraints["min_value"] = field_schema["minimum"]
        if "maximum" in field_schema:
            constraints["max_value"] = field_schema["maximum"]
        if "exclusiveMinimum" in field_schema:
            constraints["min_value"] = field_schema["exclusiveMinimum"] + 1
        if "exclusiveMaximum" in field_schema:
            constraints["max_value"] = field_schema["exclusiveMaximum"] - 1

        # String constraints
        if "minLength" in field_schema:
            constraints["min_length"] = field_schema["minLength"]
        if "maxLength" in field_schema:
            constraints["max_length"] = field_schema["maxLength"]
        if "pattern" in field_schema:
            constraints["pattern"] = field_schema["pattern"]

        # Enum constraints
        if "enum" in field_schema:
            constraints["choices"] = field_schema["enum"]

        # Array constraints
        if "minItems" in field_schema:
            constraints["min_items"] = field_schema["minItems"]
        if "maxItems" in field_schema:
            constraints["max_items"] = field_schema["maxItems"]

        return constraints

    def detect_relationships(self, schemas: List[SystemSchema]) -> List[SystemSchema]:
        """Detect and create relationships between entities based on naming conventions.

        This method analyzes field names to detect foreign key relationships
        and updates the schemas with link_to attributes.

        Args:
        ----
            schemas: List of SystemSchema objects to analyze

        Returns:
        -------
            Updated list of SystemSchema objects with relationships

        """
        if not schemas:
            return schemas

        # Build a map of all entities and their ID fields
        entity_id_map = {}

        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                # Look for ID fields in this entity
                id_fields = []
                for attr_name, attr_config in entity_config.attributes.items():
                    if (
                        attr_name.lower() in ["id", "uuid", "identifier"]
                        or attr_config.unique
                        and attr_name.lower().endswith("id")
                    ):
                        id_fields.append(attr_name)

                if id_fields:
                    entity_id_map[entity_name] = {
                        "schema": schema.name,
                        "entity": entity_name,
                        "id_fields": id_fields,
                    }

        # Now look for foreign key relationships
        for schema in schemas:
            for entity_name, entity_config in schema.entities.items():
                for attr_name, attr_config in entity_config.attributes.items():
                    # Check if this looks like a foreign key
                    if (
                        attr_name.lower().endswith("_id")
                        and attr_name.lower() != "id"
                        and not attr_config.link_to
                    ):  # Don't override existing links

                        # Extract the referenced entity name
                        potential_entity = attr_name[:-3]  # Remove "_id" suffix

                        # Handle plural/singular variations
                        potential_entities = [
                            potential_entity,
                            potential_entity + "s",  # singular -> plural
                            (
                                potential_entity[:-1]
                                if potential_entity.endswith("s")
                                else None
                            ),  # plural -> singular
                        ]
                        potential_entities = [e for e in potential_entities if e]

                        # Look for matching entity
                        for potential in potential_entities:
                            if potential in entity_id_map:
                                target_info = entity_id_map[potential]
                                # Use the first ID field (usually "id")
                                target_id_field = target_info["id_fields"][0]

                                # Create link_to reference
                                link_to = f"{target_info['schema']}.{target_info['entity']}.{target_id_field}"
                                attr_config.link_to = link_to

                                # Update the attribute type to match the target
                                target_entity = schemas[0].entities[
                                    potential
                                ]  # Assuming single schema for now
                                target_attr = target_entity.attributes[target_id_field]
                                attr_config.type = target_attr.type
                                attr_config.unique = (
                                    False  # Foreign keys are not unique
                                )

                                break

        return schemas

    def save_schema(self, schema: SystemSchema, output_path: Path) -> None:
        """Save a SystemSchema to a YAML file.

        Args:
        ----
            schema: SystemSchema to save
            output_path: Path where to save the schema file

        """
        # Convert schema to dictionary format suitable for YAML
        schema_dict = {
            "system": {
                "name": schema.name,
                "version": schema.version,
                "seed": schema.seed,
                "output": {"format": schema.output.format, "path": schema.output.path},
            },
            "entities": {},
        }

        for entity_name, entity_config in schema.entities.items():
            entity_dict = {"count": entity_config.count, "attributes": {}}

            for attr_name, attr_config in entity_config.attributes.items():
                attr_dict = {
                    "type": attr_config.type,
                    "unique": attr_config.unique,
                    "required": attr_config.required,
                }

                if attr_config.link_to:
                    attr_dict["link_to"] = attr_config.link_to

                if attr_config.constraints:
                    attr_dict["constraints"] = attr_config.constraints

                entity_dict["attributes"][attr_name] = attr_dict  # type: ignore[index]

            schema_dict["entities"][entity_name] = entity_dict  # type: ignore[assignment]

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML file
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                schema_dict, f, default_flow_style=False, sort_keys=False, indent=2
            )

    def get_validation_result(self) -> ValidationResult:
        """Get the validation result from the last translation operation.

        Returns
        -------
            ValidationResult containing any errors and warnings

        """
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
        )
