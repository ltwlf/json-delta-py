"""Tests for json_delta.models — PathSegment types and ValidationResult."""

from json_delta.models import (
    IndexSegment,
    KeyFilterSegment,
    PropertySegment,
    RootSegment,
    ValidationResult,
    ValueFilterSegment,
)


class TestRootSegment:
    def test_construction(self) -> None:
        seg = RootSegment()
        assert isinstance(seg, RootSegment)

    def test_equality(self) -> None:
        assert RootSegment() == RootSegment()

    def test_hash(self) -> None:
        assert hash(RootSegment()) == hash(RootSegment())

    def test_frozen(self) -> None:
        seg = RootSegment()
        try:
            seg.x = 1  # type: ignore[attr-defined]
            assert False, "Should raise"
        except (AttributeError, TypeError):
            pass


class TestPropertySegment:
    def test_construction(self) -> None:
        seg = PropertySegment(name="user")
        assert seg.name == "user"

    def test_equality(self) -> None:
        assert PropertySegment("name") == PropertySegment("name")
        assert PropertySegment("name") != PropertySegment("other")

    def test_hash(self) -> None:
        assert hash(PropertySegment("x")) == hash(PropertySegment("x"))
        # Different names should (usually) have different hashes
        assert hash(PropertySegment("x")) != hash(PropertySegment("y"))

    def test_frozen(self) -> None:
        seg = PropertySegment("name")
        try:
            seg.name = "other"  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass


class TestIndexSegment:
    def test_construction(self) -> None:
        seg = IndexSegment(index=0)
        assert seg.index == 0

    def test_equality(self) -> None:
        assert IndexSegment(0) == IndexSegment(0)
        assert IndexSegment(0) != IndexSegment(1)

    def test_hash(self) -> None:
        assert hash(IndexSegment(0)) == hash(IndexSegment(0))


class TestKeyFilterSegment:
    def test_construction_with_string_value(self) -> None:
        seg = KeyFilterSegment(property="id", value="42")
        assert seg.property == "id"
        assert seg.value == "42"

    def test_construction_with_int_value(self) -> None:
        seg = KeyFilterSegment(property="id", value=42)
        assert seg.value == 42

    def test_construction_with_bool_value(self) -> None:
        seg = KeyFilterSegment(property="active", value=True)
        assert seg.value is True

    def test_construction_with_null_value(self) -> None:
        seg = KeyFilterSegment(property="status", value=None)
        assert seg.value is None

    def test_equality(self) -> None:
        assert KeyFilterSegment("id", 42) == KeyFilterSegment("id", 42)
        assert KeyFilterSegment("id", 42) != KeyFilterSegment("id", "42")
        assert KeyFilterSegment("id", 42) != KeyFilterSegment("key", 42)

    def test_hash(self) -> None:
        assert hash(KeyFilterSegment("id", 42)) == hash(KeyFilterSegment("id", 42))


class TestValueFilterSegment:
    def test_construction_with_string(self) -> None:
        seg = ValueFilterSegment(value="urgent")
        assert seg.value == "urgent"

    def test_construction_with_number(self) -> None:
        seg = ValueFilterSegment(value=100)
        assert seg.value == 100

    def test_equality(self) -> None:
        assert ValueFilterSegment("urgent") == ValueFilterSegment("urgent")
        assert ValueFilterSegment("urgent") != ValueFilterSegment("other")
        assert ValueFilterSegment(42) != ValueFilterSegment("42")

    def test_hash(self) -> None:
        assert hash(ValueFilterSegment("x")) == hash(ValueFilterSegment("x"))


class TestValidationResult:
    def test_valid(self) -> None:
        result = ValidationResult(valid=True, errors=())
        assert result.valid is True
        assert result.errors == ()

    def test_invalid(self) -> None:
        result = ValidationResult(valid=False, errors=("missing format",))
        assert result.valid is False
        assert result.errors == ("missing format",)

    def test_multiple_errors(self) -> None:
        result = ValidationResult(valid=False, errors=("error 1", "error 2"))
        assert len(result.errors) == 2

    def test_frozen(self) -> None:
        result = ValidationResult(valid=True, errors=())
        try:
            result.valid = False  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass

    def test_equality(self) -> None:
        assert ValidationResult(True, ()) == ValidationResult(True, ())
        assert ValidationResult(False, ("e",)) == ValidationResult(False, ("e",))
        assert ValidationResult(True, ()) != ValidationResult(False, ())
