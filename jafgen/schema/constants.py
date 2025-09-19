"""Constants for schema management."""

# Supported Mimesis provider types
SUPPORTED_ATTRIBUTE_TYPES = {
    # Person providers
    "person.full_name",
    "person.first_name", 
    "person.last_name",
    "person.email",
    "person.phone_number",
    "person.age",
    
    # Address providers
    "address.address",
    "address.city",
    "address.state",
    "address.country",
    "address.postal_code",
    
    # Datetime providers
    "datetime.datetime",
    "datetime.date",
    "datetime.time",
    
    # Numeric providers
    "numeric.integer",
    "numeric.float",
    "numeric.decimal",
    
    # Text providers
    "text.word",
    "text.sentence",
    "text.paragraph",
    
    # Internet providers
    "internet.url",
    "internet.domain_name",
    "internet.ip_v4",
    
    # Finance providers
    "finance.currency_code",
    "finance.price",
    
    # Generic providers
    "uuid",
    "boolean",
    "link"  # Special type for entity links
}

# Required schema fields
REQUIRED_SYSTEM_FIELDS = {"name", "version", "entities"}
REQUIRED_ENTITY_FIELDS = {"name", "count", "attributes"}
REQUIRED_ATTRIBUTE_FIELDS = {"type"}

# Supported output formats
SUPPORTED_OUTPUT_FORMATS = {"csv", "json", "parquet", "duckdb"}