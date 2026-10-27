"""Exceptions of schema annotations, free of the optional schema dependencies."""


class SchemaAnnotationError(ValueError):
    """Raised when a schema, document, reference or schema filter is invalid."""
