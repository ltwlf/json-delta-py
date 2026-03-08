"""Exception hierarchy for json-delta."""


class JsonDeltaError(Exception):
    """Base exception for all json-delta errors."""


class PathError(JsonDeltaError):
    """Invalid or malformed JSON Delta Path expression."""


class ApplyError(JsonDeltaError):
    """Error during delta application."""


class InvertError(JsonDeltaError):
    """Error during delta inversion (e.g., missing oldValue)."""


class ValidationError(JsonDeltaError):
    """Delta structural validation error."""


class DiffError(JsonDeltaError):
    """Error during diff computation."""
