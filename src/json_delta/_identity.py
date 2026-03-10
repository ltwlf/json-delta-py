"""Internal identity resolution for array comparison.

Determines how array elements are matched during diff and compare:
by key, by value, by index, or by custom callable.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from json_delta.errors import DiffError


@dataclass(frozen=True, slots=True)
class IdentityResolver:
    """Custom identity resolution for array elements.

    The ``property`` name appears in filter paths: ``[?(@.{property}==...)]``.
    The ``resolve`` callable extracts the identity value from an element.

    Example::

        # Composite key: combine type + region into a single identity
        IdentityResolver("type", lambda e: f"{e['type']}-{e['region']}")

        # Computed identity from nested structure
        IdentityResolver("id", lambda e: e["meta"]["uuid"])
    """

    property: str
    resolve: Callable[[Any], Any]


# All valid forms for specifying an identity key
type IdentityKey = str | IdentityResolver | tuple[str, Callable[[Any], Any]]

# Full mapping: path (exact or regex) → identity key
type ArrayIdentityKeys = dict[str | re.Pattern[str], IdentityKey]


@dataclass(frozen=True, slots=True)
class _ResolvedIdentity:
    """The resolved identity model for a specific array.

    Internal type — not part of the public API.
    """

    mode: Literal["$index", "$value", "key"]
    key_property: str | None = None
    resolver: Callable[[Any], Any] | None = None


def resolve_identity(
    prop_path: list[str],
    array_identity_keys: ArrayIdentityKeys,
) -> _ResolvedIdentity:
    """Determine the identity model for an array at the given property path.

    Matches against exact string keys first, then regex patterns
    (in dict insertion order). Falls back to ``$index`` if no match.
    """
    path_str = ".".join(prop_path)

    # 1. Try exact string matches first
    for key, value in array_identity_keys.items():
        if isinstance(key, str) and key == path_str:
            return _normalize_identity_value(value)

    # 2. Try regex pattern matches (insertion order)
    for key, value in array_identity_keys.items():
        if isinstance(key, re.Pattern) and key.search(path_str):
            return _normalize_identity_value(value)

    # 3. Default: index-based
    return _ResolvedIdentity(mode="$index")


def _normalize_identity_value(value: IdentityKey) -> _ResolvedIdentity:
    """Normalize the various forms of identity key values."""
    if isinstance(value, str):
        if value == "$index":
            return _ResolvedIdentity(mode="$index")
        if value == "$value":
            return _ResolvedIdentity(mode="$value")
        return _ResolvedIdentity(mode="key", key_property=value)

    if isinstance(value, IdentityResolver):
        return _ResolvedIdentity(
            mode="key",
            key_property=value.property,
            resolver=value.resolve,
        )

    if isinstance(value, tuple) and len(value) == 2:
        prop_name, resolver_fn = value
        if not isinstance(prop_name, str) or not callable(resolver_fn):
            raise DiffError(
                f"Tuple identity key must be (str, Callable), "
                f"got ({type(prop_name).__name__}, {type(resolver_fn).__name__})"
            )
        return _ResolvedIdentity(
            mode="key",
            key_property=prop_name,
            resolver=resolver_fn,
        )

    raise DiffError(
        f"Invalid identity key value: {value!r}. "
        f"Expected str, (str, Callable), or IdentityResolver."
    )


def extract_identity(
    elem: Any,
    key_property: str,
    resolver: Callable[[Any], Any] | None,
) -> Any:
    """Extract the identity value from an array element.

    Uses the custom resolver if provided, otherwise reads the key property
    directly from the element dict.
    """
    if resolver is not None:
        return resolver(elem)
    if not isinstance(elem, dict) or key_property not in elem:
        raise DiffError(f"Array element missing identity key '{key_property}': {elem!r}")
    return elem[key_property]
