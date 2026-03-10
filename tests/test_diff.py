"""Tests for json_delta.diff — delta computation."""

import pytest

from json_delta.apply import apply_delta
from json_delta.diff import diff_delta
from json_delta.errors import DiffError
from json_delta.invert import invert_delta

from tests.conftest import deep_clone, load_fixture


# ---------------------------------------------------------------------------
# Identical objects
# ---------------------------------------------------------------------------


class TestIdentical:
    def test_identical_objects_empty_ops(self) -> None:
        obj = {"name": "Alice", "age": 30}
        delta = diff_delta(obj, obj)
        assert delta["operations"] == []

    def test_identical_arrays_empty_ops(self) -> None:
        delta = diff_delta([1, 2, 3], [1, 2, 3])
        assert delta["operations"] == []

    def test_identical_scalars_empty_ops(self) -> None:
        delta = diff_delta(42, 42)
        assert delta["operations"] == []

    def test_identical_null_empty_ops(self) -> None:
        delta = diff_delta(None, None)
        assert delta["operations"] == []


# ---------------------------------------------------------------------------
# Simple property operations
# ---------------------------------------------------------------------------


class TestPropertyDiff:
    def test_replace_property(self) -> None:
        old = {"name": "Alice"}
        new = {"name": "Bob"}
        delta = diff_delta(old, new)
        assert len(delta["operations"]) == 1
        op = delta["operations"][0]
        assert op["op"] == "replace"
        assert op["path"] == "$.name"
        assert op["value"] == "Bob"
        assert op["oldValue"] == "Alice"

    def test_add_property(self) -> None:
        old = {"name": "Alice"}
        new = {"name": "Alice", "role": "admin"}
        delta = diff_delta(old, new)
        ops = delta["operations"]
        add_ops = [o for o in ops if o["op"] == "add"]
        assert len(add_ops) == 1
        assert add_ops[0]["path"] == "$.role"
        assert add_ops[0]["value"] == "admin"

    def test_remove_property(self) -> None:
        old = {"name": "Alice", "role": "admin"}
        new = {"name": "Alice"}
        delta = diff_delta(old, new)
        ops = delta["operations"]
        remove_ops = [o for o in ops if o["op"] == "remove"]
        assert len(remove_ops) == 1
        assert remove_ops[0]["path"] == "$.role"
        assert remove_ops[0]["oldValue"] == "admin"

    def test_nested_property_changes(self) -> None:
        old = {"user": {"address": {"city": "Portland"}}}
        new = {"user": {"address": {"city": "Seattle"}}}
        delta = diff_delta(old, new)
        assert len(delta["operations"]) == 1
        assert delta["operations"][0]["path"] == "$.user.address.city"

    def test_replace_with_null(self) -> None:
        old = {"val": "hello"}
        new = {"val": None}
        delta = diff_delta(old, new)
        op = delta["operations"][0]
        assert op["value"] is None
        assert op["oldValue"] == "hello"


# ---------------------------------------------------------------------------
# Type changes
# ---------------------------------------------------------------------------


class TestTypeChanges:
    def test_object_to_array(self) -> None:
        old = {"data": {"key": "val"}}
        new = {"data": [1, 2, 3]}
        delta = diff_delta(old, new)
        ops = [o for o in delta["operations"] if o["path"] == "$.data"]
        assert len(ops) == 1
        assert ops[0]["op"] == "replace"

    def test_array_to_object(self) -> None:
        old = {"data": [1, 2]}
        new = {"data": {"key": "val"}}
        delta = diff_delta(old, new)
        ops = [o for o in delta["operations"] if o["path"] == "$.data"]
        assert len(ops) == 1
        assert ops[0]["op"] == "replace"

    def test_string_to_number(self) -> None:
        old = {"val": "42"}
        new = {"val": 42}
        delta = diff_delta(old, new)
        op = delta["operations"][0]
        assert op["op"] == "replace"
        assert op["value"] == 42
        assert op["oldValue"] == "42"

    def test_null_to_object(self) -> None:
        old = {"data": None}
        new = {"data": {"key": "val"}}
        delta = diff_delta(old, new)
        op = delta["operations"][0]
        assert op["op"] == "replace"


# ---------------------------------------------------------------------------
# Index-based array comparison
# ---------------------------------------------------------------------------


class TestIndexArrays:
    def test_replace_element(self) -> None:
        old = {"tags": ["urgent", "review"]}
        new = {"tags": ["urgent", "approved"]}
        delta = diff_delta(old, new)
        ops = delta["operations"]
        assert len(ops) == 1
        assert ops[0]["path"] == "$.tags[1]"
        assert ops[0]["op"] == "replace"

    def test_different_lengths_add(self) -> None:
        old = {"items": [1, 2]}
        new = {"items": [1, 2, 3]}
        delta = diff_delta(old, new)
        add_ops = [o for o in delta["operations"] if o["op"] == "add"]
        assert len(add_ops) == 1
        assert add_ops[0]["path"] == "$.items[2]"

    def test_different_lengths_remove(self) -> None:
        old = {"items": [1, 2, 3]}
        new = {"items": [1, 2]}
        delta = diff_delta(old, new)
        remove_ops = [o for o in delta["operations"] if o["op"] == "remove"]
        assert len(remove_ops) == 1
        assert remove_ops[0]["path"] == "$.items[2]"

    def test_explicit_index_identity(self) -> None:
        """$index identity mode explicitly set."""
        old = {"items": [1, 2]}
        new = {"items": [1, 3]}
        delta = diff_delta(old, new, array_keys={"items": "$index"})
        assert len(delta["operations"]) == 1
        assert delta["operations"][0]["path"] == "$.items[1]"


# ---------------------------------------------------------------------------
# Key-based array comparison
# ---------------------------------------------------------------------------


class TestKeyedArrays:
    def test_update_element_property(self) -> None:
        old = {"items": [{"id": 1, "name": "Widget", "price": 10}]}
        new = {"items": [{"id": 1, "name": "Widget Pro", "price": 10}]}
        delta = diff_delta(old, new, array_keys={"items": "id"})
        ops = delta["operations"]
        assert len(ops) == 1
        assert ops[0]["path"] == "$.items[?(@.id==1)].name"
        assert ops[0]["value"] == "Widget Pro"

    def test_add_element(self) -> None:
        old = {"items": [{"id": 1, "name": "Widget"}]}
        new = {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}
        delta = diff_delta(old, new, array_keys={"items": "id"})
        add_ops = [o for o in delta["operations"] if o["op"] == "add"]
        assert len(add_ops) == 1
        assert add_ops[0]["value"] == {"id": 2, "name": "Gadget"}

    def test_remove_element(self) -> None:
        old = {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}
        new = {"items": [{"id": 1, "name": "Widget"}]}
        delta = diff_delta(old, new, array_keys={"items": "id"})
        remove_ops = [o for o in delta["operations"] if o["op"] == "remove"]
        assert len(remove_ops) == 1
        assert remove_ops[0]["oldValue"] == {"id": 2, "name": "Gadget"}

    def test_string_id(self) -> None:
        old = {"items": [{"id": "a", "val": 1}]}
        new = {"items": [{"id": "a", "val": 2}]}
        delta = diff_delta(old, new, array_keys={"items": "id"})
        assert delta["operations"][0]["path"] == "$.items[?(@.id=='a')].val"

    def test_numeric_id_typed_filter(self) -> None:
        """Numeric IDs should produce number literals in filter, not string."""
        old = {"items": [{"id": 42, "val": 1}]}
        new = {"items": [{"id": 42, "val": 2}]}
        delta = diff_delta(old, new, array_keys={"items": "id"})
        assert "id==42" in delta["operations"][0]["path"]
        assert "id=='42'" not in delta["operations"][0]["path"]

    def test_missing_identity_key_raises(self) -> None:
        with pytest.raises(DiffError, match="identity key"):
            diff_delta(
                {"items": [{"name": "Widget"}]},
                {"items": [{"name": "Gadget"}]},
                array_keys={"items": "id"},
            )


# ---------------------------------------------------------------------------
# Value-based array comparison
# ---------------------------------------------------------------------------


class TestValueArrays:
    def test_string_values_add(self) -> None:
        old = {"tags": ["urgent"]}
        new = {"tags": ["urgent", "review"]}
        delta = diff_delta(old, new, array_keys={"tags": "$value"})
        add_ops = [o for o in delta["operations"] if o["op"] == "add"]
        assert len(add_ops) == 1
        assert "=='review'" in add_ops[0]["path"]

    def test_string_values_remove(self) -> None:
        old = {"tags": ["urgent", "draft"]}
        new = {"tags": ["urgent"]}
        delta = diff_delta(old, new, array_keys={"tags": "$value"})
        remove_ops = [o for o in delta["operations"] if o["op"] == "remove"]
        assert len(remove_ops) == 1
        assert "=='draft'" in remove_ops[0]["path"]

    def test_number_values(self) -> None:
        old = {"scores": [10, 20]}
        new = {"scores": [10, 30]}
        delta = diff_delta(old, new, array_keys={"scores": "$value"})
        assert len(delta["operations"]) == 2  # remove 20, add 30


# ---------------------------------------------------------------------------
# Reversibility
# ---------------------------------------------------------------------------


class TestReversibility:
    def test_non_reversible_omits_old_value(self) -> None:
        old = {"name": "Alice"}
        new = {"name": "Bob"}
        delta = diff_delta(old, new, reversible=False)
        op = delta["operations"][0]
        assert op["op"] == "replace"
        assert "oldValue" not in op

    def test_non_reversible_remove_omits_old_value(self) -> None:
        old = {"name": "Alice", "role": "admin"}
        new = {"name": "Alice"}
        delta = diff_delta(old, new, reversible=False)
        remove_ops = [o for o in delta["operations"] if o["op"] == "remove"]
        assert "oldValue" not in remove_ops[0]

    def test_reversible_includes_old_value(self) -> None:
        old = {"name": "Alice"}
        new = {"name": "Bob"}
        delta = diff_delta(old, new, reversible=True)
        assert "oldValue" in delta["operations"][0]


# ---------------------------------------------------------------------------
# Special property names
# ---------------------------------------------------------------------------


class TestSpecialPaths:
    def test_property_needing_brackets(self) -> None:
        old = {"a.b": 1}
        new = {"a.b": 2}
        delta = diff_delta(old, new)
        assert delta["operations"][0]["path"] == "$['a.b']"

    def test_digit_starting_property(self) -> None:
        old = {"0key": "old"}
        new = {"0key": "new"}
        delta = diff_delta(old, new)
        assert delta["operations"][0]["path"] == "$['0key']"


# ---------------------------------------------------------------------------
# Nested array keys
# ---------------------------------------------------------------------------


class TestNestedArrayKeys:
    def test_nested_keyed_array(self) -> None:
        old = {"users": [{"id": 1, "contacts": [{"type": "email", "val": "a@b.com"}]}]}
        new = {"users": [{"id": 1, "contacts": [{"type": "email", "val": "new@b.com"}]}]}
        delta = diff_delta(old, new, array_keys={"users": "id", "users.contacts": "type"})
        ops = delta["operations"]
        assert len(ops) == 1
        # Should target the nested property through both filters
        assert "id==1" in ops[0]["path"]
        assert "type=='email'" in ops[0]["path"]
        assert ops[0]["path"].endswith(".val")


# ---------------------------------------------------------------------------
# Delta envelope format
# ---------------------------------------------------------------------------


class TestDeltaFormat:
    def test_envelope_fields(self) -> None:
        delta = diff_delta({"a": 1}, {"a": 2})
        assert delta["format"] == "json-delta"
        assert delta["version"] == 1
        assert isinstance(delta["operations"], list)


# ---------------------------------------------------------------------------
# Error conditions
# ---------------------------------------------------------------------------


class TestDiffErrors:
    def test_non_finite_float_raises(self) -> None:
        with pytest.raises(DiffError, match="Non-finite"):
            diff_delta({"val": float("inf")}, {"val": 1})

    def test_nan_raises(self) -> None:
        with pytest.raises(DiffError, match="Non-finite"):
            diff_delta({"val": float("nan")}, {"val": 1})

    def test_non_json_type_raises(self) -> None:
        with pytest.raises(DiffError, match="non-JSON"):
            diff_delta(set(), {})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Exclude keys
# ---------------------------------------------------------------------------


class TestExcludeKeys:
    def test_excluded_top_level_key_no_ops(self) -> None:
        """Excluded keys produce zero operations even when values differ."""
        old = {"name": "Alice", "metadata": {"updated": "2025-01-01"}}
        new = {"name": "Alice", "metadata": {"updated": "2026-03-10"}}
        delta = diff_delta(old, new, exclude_keys={"metadata"})
        assert delta["operations"] == []

    def test_non_excluded_keys_still_diff(self) -> None:
        """Non-excluded keys diff normally when exclude_keys is set."""
        old = {"name": "Alice", "metadata": "old"}
        new = {"name": "Bob", "metadata": "new"}
        delta = diff_delta(old, new, exclude_keys={"metadata"})
        assert len(delta["operations"]) == 1
        assert delta["operations"][0]["path"] == "$.name"
        assert delta["operations"][0]["value"] == "Bob"

    def test_excluded_key_added_no_ops(self) -> None:
        """Adding an excluded key produces no add operation."""
        old = {"name": "Alice"}
        new = {"name": "Alice", "_internal": True}
        delta = diff_delta(old, new, exclude_keys={"_internal"})
        assert delta["operations"] == []

    def test_excluded_key_removed_no_ops(self) -> None:
        """Removing an excluded key produces no remove operation."""
        old = {"name": "Alice", "_internal": True}
        new = {"name": "Alice"}
        delta = diff_delta(old, new, exclude_keys={"_internal"})
        assert delta["operations"] == []

    def test_exclude_inside_keyed_array_elements(self) -> None:
        """Exclusion works at any depth, including inside keyed array elements."""
        old = {"items": [{"id": 1, "name": "Widget", "metadata": {"v": 1}}]}
        new = {"items": [{"id": 1, "name": "Widget", "metadata": {"v": 2}}]}
        delta = diff_delta(old, new, array_keys={"items": "id"}, exclude_keys={"metadata"})
        assert delta["operations"] == []

    def test_exclude_nested_property(self) -> None:
        """Exclusion applies at any depth in nested objects."""
        old = {"a": {"b": {"skip_me": 1, "keep": "old"}}}
        new = {"a": {"b": {"skip_me": 999, "keep": "new"}}}
        delta = diff_delta(old, new, exclude_keys={"skip_me"})
        assert len(delta["operations"]) == 1
        assert delta["operations"][0]["path"] == "$.a.b.keep"

    def test_empty_exclude_keys_same_as_none(self) -> None:
        """Empty set behaves identically to None."""
        old = {"name": "Alice"}
        new = {"name": "Bob"}
        delta_none = diff_delta(old, new, exclude_keys=None)
        delta_empty = diff_delta(old, new, exclude_keys=set())
        assert len(delta_none["operations"]) == len(delta_empty["operations"])
        assert delta_none["operations"][0]["path"] == delta_empty["operations"][0]["path"]

    def test_dotted_key_treated_as_literal_name(self) -> None:
        """Keys with dots are treated as literal property names, not paths."""
        old = {"a.b": 1, "c": 2}
        new = {"a.b": 99, "c": 3}
        delta = diff_delta(old, new, exclude_keys={"a.b"})
        assert len(delta["operations"]) == 1
        assert delta["operations"][0]["path"] == "$.c"

    def test_multiple_excluded_keys(self) -> None:
        """Multiple keys can be excluded simultaneously."""
        old = {"name": "Alice", "etag": "abc", "updated_at": "2025", "age": 30}
        new = {"name": "Bob", "etag": "def", "updated_at": "2026", "age": 31}
        delta = diff_delta(old, new, exclude_keys={"etag", "updated_at"})
        paths = {op["path"] for op in delta["operations"]}
        assert paths == {"$.name", "$.age"}

    def test_exclude_combined_with_reversible(self) -> None:
        """exclude_keys works correctly with reversible=False."""
        old = {"name": "Alice", "meta": "x"}
        new = {"name": "Bob", "meta": "y"}
        delta = diff_delta(old, new, exclude_keys={"meta"}, reversible=False)
        assert len(delta["operations"]) == 1
        assert "oldValue" not in delta["operations"][0]


# ---------------------------------------------------------------------------
# Conformance: apply(source, diff(source, target)) == target
# ---------------------------------------------------------------------------


class TestDiffConformance:
    def test_basic_replace_apply_roundtrip(self) -> None:
        fixture = load_fixture("basic-replace")
        source = fixture["source"]
        target = fixture["target"]
        delta = diff_delta(source, target)
        result = apply_delta(deep_clone(source), delta)
        assert result == target

    def test_keyed_array_apply_roundtrip(self) -> None:
        fixture = load_fixture("keyed-array-update")
        source = fixture["source"]
        target = fixture["target"]
        hints = fixture.get("computeHints", {})
        array_keys = hints.get("arrayKeys")
        delta = diff_delta(source, target, array_keys=array_keys)
        result = apply_delta(deep_clone(source), delta)
        assert result == target

    def test_keyed_array_invert_roundtrip(self) -> None:
        """diff + invert + apply round-trip: apply(target, invert(diff(source, target))) == source."""
        fixture = load_fixture("keyed-array-update")
        source = fixture["source"]
        target = fixture["target"]
        hints = fixture.get("computeHints", {})
        array_keys = hints.get("arrayKeys")
        delta = diff_delta(source, target, array_keys=array_keys)
        inverse = invert_delta(delta)
        recovered = apply_delta(deep_clone(target), inverse)
        assert recovered == source
