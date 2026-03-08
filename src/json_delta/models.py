"""Data models for json-delta path segments and validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RootSegment:
    """The root segment '$'."""


@dataclass(frozen=True, slots=True)
class PropertySegment:
    """A property access segment: .name or ['name']."""

    name: str


@dataclass(frozen=True, slots=True)
class IndexSegment:
    """An array index segment: [0]."""

    index: int


@dataclass(frozen=True, slots=True)
class KeyFilterSegment:
    """A key filter segment: [?(@.key==value)].

    The value field holds the filter literal as a typed Python value:
    str, int, float, bool, or None.
    """

    property: str
    value: Any


@dataclass(frozen=True, slots=True)
class ValueFilterSegment:
    """A value filter segment: [?(@==value)].

    The value field holds the filter literal as a typed Python value:
    str, int, float, bool, or None.
    """

    value: Any


type PathSegment = RootSegment | PropertySegment | IndexSegment | KeyFilterSegment | ValueFilterSegment


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of delta structural validation.

    Attributes:
        valid: Whether the delta document is structurally valid.
        errors: Tuple of error messages (empty if valid).
    """

    valid: bool
    errors: tuple[str, ...]
