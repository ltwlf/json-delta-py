"""json-delta: Python implementation of the JSON Delta v0 specification.

Compute, apply, validate, and invert JSON deltas with support for
key-based, index-based, and value-based array identity models.
"""

from json_delta.apply import apply_delta
from json_delta.diff import diff_delta
from json_delta.errors import (
    ApplyError,
    DiffError,
    InvertError,
    JsonDeltaError,
    PathError,
    ValidationError,
)
from json_delta.invert import invert_delta, revert_delta
from json_delta.models import (
    IndexSegment,
    KeyFilterSegment,
    PathSegment,
    PropertySegment,
    RootSegment,
    ValidationResult,
    ValueFilterSegment,
)
from json_delta.path import build_path, parse_path
from json_delta.validate import validate_delta

__all__ = [
    "ApplyError",
    "DiffError",
    "IndexSegment",
    "InvertError",
    "JsonDeltaError",
    "KeyFilterSegment",
    "PathError",
    "PathSegment",
    "PropertySegment",
    "RootSegment",
    "ValidationError",
    "ValidationResult",
    "ValueFilterSegment",
    "apply_delta",
    "build_path",
    "diff_delta",
    "invert_delta",
    "parse_path",
    "revert_delta",
    "validate_delta",
]
