"""Enriched comparison tree for visual diff rendering.

Builds a tree of :class:`ComparisonNode` instances that classifies every value
as unchanged, added, removed, replaced, or container.  Unlike :func:`diff_delta`,
which produces a flat list of operations, :func:`compare` returns the full
document structure — including unchanged values — so you can render side-by-side
diffs, change-highlighted UIs, or detailed audit views.
"""

from __future__ import annotations

from typing import Any

from json_delta._identity import (
    ArrayIdentityKeys,
    _ResolvedIdentity,
    extract_identity,
    resolve_identity,
)
from json_delta._utils import json_equal
from json_delta.models import ChangeType, ComparisonNode


def compare(
    old_obj: Any,
    new_obj: Any,
    *,
    array_identity_keys: ArrayIdentityKeys | None = None,
    exclude_keys: set[str] | None = None,
    exclude_paths: set[str] | None = None,
) -> ComparisonNode:
    """Build an enriched comparison tree showing all values and their change status.

    Unlike :func:`diff_delta` which produces flat operations, ``compare()``
    returns a tree including unchanged values — ideal for rendering
    side-by-side diffs or change-highlighted UIs.

    Args:
        old_obj: The source document.
        new_obj: The target document.
        array_identity_keys: Optional identity key mapping for arrays.
            Accepts the same forms as :func:`diff_delta`: string keys,
            ``(str, Callable)`` tuples, :class:`IdentityResolver` instances,
            and ``re.Pattern`` dict keys.
        exclude_keys: Property names to skip at any depth.
        exclude_paths: Dotted property paths to skip at a specific depth.

    Returns:
        A :class:`ComparisonNode` tree where each node is classified as
        ``unchanged``, ``added``, ``removed``, ``replaced``, or ``container``.

    Example::

        node = compare(
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 30},
        )
        # node.type == ChangeType.CONTAINER
        # node.value["name"].type == ChangeType.REPLACED
        # node.value["age"].type == ChangeType.UNCHANGED
    """
    keys = array_identity_keys or {}
    _exclude: frozenset[str] = frozenset(exclude_keys) if exclude_keys else frozenset()
    _exclude_paths: frozenset[str] = frozenset(exclude_paths) if exclude_paths else frozenset()
    return _compare_values(old_obj, new_obj, [], keys, _exclude, _exclude_paths)


# ---------------------------------------------------------------------------
# Recursive comparison
# ---------------------------------------------------------------------------


def _compare_values(
    old: Any,
    new: Any,
    prop_path: list[str],
    identity_keys: ArrayIdentityKeys,
    exclude: frozenset[str],
    exclude_paths: frozenset[str],
) -> ComparisonNode:
    """Recursively compare two values and produce a ComparisonNode."""
    if json_equal(old, new):
        return _enrich_unchanged(old)

    old_is_dict = isinstance(old, dict) and not isinstance(old, bool)
    new_is_dict = isinstance(new, dict) and not isinstance(new, bool)
    old_is_list = isinstance(old, list)
    new_is_list = isinstance(new, list)

    if old_is_dict and new_is_dict:
        return _compare_objects(old, new, prop_path, identity_keys, exclude, exclude_paths)
    elif old_is_list and new_is_list:
        return _compare_arrays(old, new, prop_path, identity_keys, exclude, exclude_paths)

    # Type change or scalar difference
    return ComparisonNode(type=ChangeType.REPLACED, value=new, old_value=old)


def _enrich_unchanged(value: Any) -> ComparisonNode:
    """Wrap an unchanged value as a ComparisonNode tree.

    Containers get ``ChangeType.CONTAINER`` with per-child nodes.
    Leaves get ``ChangeType.UNCHANGED``.
    """
    if isinstance(value, dict) and not isinstance(value, bool):
        obj_children = {k: _enrich_unchanged(v) for k, v in value.items()}
        return ComparisonNode(type=ChangeType.CONTAINER, value=obj_children)
    if isinstance(value, list):
        arr_children = [_enrich_unchanged(v) for v in value]
        return ComparisonNode(type=ChangeType.CONTAINER, value=arr_children)
    return ComparisonNode(type=ChangeType.UNCHANGED, value=value)


# ---------------------------------------------------------------------------
# Object comparison
# ---------------------------------------------------------------------------


def _compare_objects(
    old: dict[str, Any],
    new: dict[str, Any],
    prop_path: list[str],
    identity_keys: ArrayIdentityKeys,
    exclude: frozenset[str],
    exclude_paths: frozenset[str],
) -> ComparisonNode:
    """Compare two objects and produce a container node with per-key children."""
    children: dict[str, ComparisonNode] = {}
    all_keys = sorted((set(old.keys()) | set(new.keys())) - exclude)

    for key in all_keys:
        if _should_exclude_path(prop_path, key, exclude_paths):
            continue

        if key in old and key not in new:
            children[key] = ComparisonNode(type=ChangeType.REMOVED, old_value=old[key])
        elif key not in old and key in new:
            children[key] = ComparisonNode(type=ChangeType.ADDED, value=new[key])
        else:
            children[key] = _compare_values(
                old[key], new[key], [*prop_path, key], identity_keys, exclude, exclude_paths,
            )

    return ComparisonNode(type=ChangeType.CONTAINER, value=children)


# ---------------------------------------------------------------------------
# Array comparison
# ---------------------------------------------------------------------------


def _compare_arrays(
    old: list[Any],
    new: list[Any],
    prop_path: list[str],
    identity_keys: ArrayIdentityKeys,
    exclude: frozenset[str],
    exclude_paths: frozenset[str],
) -> ComparisonNode:
    """Compare two arrays using the appropriate identity model."""
    identity = resolve_identity(prop_path, identity_keys)

    if identity.mode == "$index":
        return _compare_arrays_index(old, new, prop_path, identity_keys, exclude, exclude_paths)
    elif identity.mode == "$value":
        return _compare_arrays_value(old, new)
    else:
        return _compare_arrays_keyed(old, new, prop_path, identity_keys, exclude, exclude_paths, identity)


def _compare_arrays_index(
    old: list[Any],
    new: list[Any],
    prop_path: list[str],
    identity_keys: ArrayIdentityKeys,
    exclude: frozenset[str],
    exclude_paths: frozenset[str],
) -> ComparisonNode:
    """Compare arrays by positional index."""
    children: list[ComparisonNode] = []
    max_len = max(len(old), len(new))

    for i in range(max_len):
        if i < len(old) and i < len(new):
            children.append(_compare_values(old[i], new[i], prop_path, identity_keys, exclude, exclude_paths))
        elif i >= len(old):
            children.append(ComparisonNode(type=ChangeType.ADDED, value=new[i]))
        else:
            children.append(ComparisonNode(type=ChangeType.REMOVED, old_value=old[i]))

    return ComparisonNode(type=ChangeType.CONTAINER, value=children)


def _compare_arrays_keyed(
    old: list[Any],
    new: list[Any],
    prop_path: list[str],
    identity_keys: ArrayIdentityKeys,
    exclude: frozenset[str],
    exclude_paths: frozenset[str],
    identity: _ResolvedIdentity,
) -> ComparisonNode:
    """Compare arrays by key-based identity."""
    key_property = identity.key_property
    if key_property is None:  # pragma: no cover — guaranteed by resolve_identity for mode="key"
        msg = "key_property must be set for mode='key'"
        raise ValueError(msg)
    resolver = identity.resolver

    # Build lookup maps preserving order
    old_by_key: dict[Any, Any] = {}
    old_order: list[Any] = []
    for elem in old:
        key_val = extract_identity(elem, key_property, resolver)
        hashable_key = _make_hashable(key_val)
        old_by_key[hashable_key] = elem
        old_order.append(hashable_key)

    new_by_key: dict[Any, Any] = {}
    new_order: list[Any] = []
    for elem in new:
        key_val = extract_identity(elem, key_property, resolver)
        hashable_key = _make_hashable(key_val)
        new_by_key[hashable_key] = elem
        new_order.append(hashable_key)

    # Build children list following new order, then appending removed items
    children: list[ComparisonNode] = []

    # Items in new order (matched or added)
    for hashable_key in new_order:
        if hashable_key in old_by_key:
            children.append(
                _compare_values(old_by_key[hashable_key], new_by_key[hashable_key],
                                prop_path, identity_keys, exclude, exclude_paths)
            )
        else:
            children.append(ComparisonNode(type=ChangeType.ADDED, value=new_by_key[hashable_key]))

    # Items removed (in old but not in new)
    for hashable_key in old_order:
        if hashable_key not in new_by_key:
            children.append(ComparisonNode(type=ChangeType.REMOVED, old_value=old_by_key[hashable_key]))

    return ComparisonNode(type=ChangeType.CONTAINER, value=children)


def _compare_arrays_value(
    old: list[Any],
    new: list[Any],
) -> ComparisonNode:
    """Compare arrays by value identity (for primitive arrays)."""
    children: list[ComparisonNode] = []

    # Matched values (in both)
    for new_val in new:
        found = any(json_equal(new_val, old_val) for old_val in old)
        if found:
            children.append(ComparisonNode(type=ChangeType.UNCHANGED, value=new_val))
        else:
            children.append(ComparisonNode(type=ChangeType.ADDED, value=new_val))

    # Removed values (in old but not in new)
    for old_val in old:
        found = any(json_equal(old_val, new_val) for new_val in new)
        if not found:
            children.append(ComparisonNode(type=ChangeType.REMOVED, old_value=old_val))

    return ComparisonNode(type=ChangeType.CONTAINER, value=children)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _should_exclude_path(prop_path: list[str], key: str, exclude_paths: frozenset[str]) -> bool:
    """Check if a key at the current path should be excluded."""
    if not exclude_paths:
        return False
    return ".".join([*prop_path, key]) in exclude_paths


def _make_hashable(value: Any) -> Any:
    """Make a JSON scalar safe for use as a dict key.

    Python considers ``True == 1`` and ``False == 0``, so they collide
    as dict keys.  We wrap bools in a tagged tuple to preserve identity.
    """
    if isinstance(value, bool):
        return ("__bool__", value)
    return value
