"""json-delta: Python implementation of the JSON Delta v0 specification.

Compute, apply, validate, and invert JSON deltas with support for
key-based, index-based, and value-based array identity models.
"""

from json_delta._identity import IdentityResolver
from json_delta.apply import apply_delta
from json_delta.compare import compare
from json_delta.diff import diff_delta, squash_deltas
from json_delta.errors import (
    ApplyError,
    DiffError,
    InvertError,
    JsonDeltaError,
    PathError,
    ValidationError,
)
from json_delta.invert import invert_delta, revert_delta
from json_delta.json_patch import from_json_patch, to_json_patch
from json_delta.models import (
    ChangeType,
    ComparisonNode,
    Delta,
    IndexSegment,
    KeyFilterSegment,
    Operation,
    OpType,
    PathSegment,
    PropertySegment,
    RootSegment,
    ValidationResult,
    ValueFilterSegment,
)
from json_delta.path import build_path, describe_path, parse_path, resolve_path
from json_delta.validate import validate_delta

__all__ = [
    "ApplyError",
    "ChangeType",
    "ComparisonNode",
    "Delta",
    "DiffError",
    "IdentityResolver",
    "IndexSegment",
    "InvertError",
    "JsonDeltaError",
    "KeyFilterSegment",
    "OpType",
    "Operation",
    "PathError",
    "PathSegment",
    "PropertySegment",
    "RootSegment",
    "ValidationError",
    "ValidationResult",
    "ValueFilterSegment",
    "apply_delta",
    "build_path",
    "compare",
    "describe_path",
    "diff_delta",
    "from_json_patch",
    "invert_delta",
    "parse_path",
    "resolve_path",
    "revert_delta",
    "squash_deltas",
    "to_json_patch",
    "validate_delta",
]
