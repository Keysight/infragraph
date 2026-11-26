"""Exceptions of schema annotations, free of the schema library dependencies."""


class SchemaAnnotationError(ValueError):
    """Raised when a schema, document, reference or schema filter is invalid."""
