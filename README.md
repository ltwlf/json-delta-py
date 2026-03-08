# json-delta-py

Deterministic JSON state transitions for Python.
Compute, apply, validate, and revert JSON Delta documents with stable array identity and reversible operations.

> **Ecosystem note:** This project implements the JSON Delta specification defined in the [`json-delta-format`](https://github.com/ltwlf/json-delta-format) repository. It is unrelated to the older `json-delta` package published on PyPI.

```text
json-delta-format  (specification)
    ├── json-diff-ts      (TypeScript implementation)
    └── json-delta-py     (Python implementation)  <-- this package
```

If this project is useful to you, please consider starring the repository.

## Installation

```bash
pip install json-delta-py
```

## Quick Start

```python
import copy
from json_delta import diff_delta, apply_delta, revert_delta

source = {"user": {"name": "Alice", "role": "viewer"}}
target = {"user": {"name": "Alice", "role": "admin"}}

# Compute a delta
delta = diff_delta(source, target)
# {'format': 'json-delta', 'version': 1, 'operations': [
#   {'op': 'replace', 'path': '$.user.role', 'value': 'admin', 'oldValue': 'viewer'}
# ]}

# Apply it
result = apply_delta(copy.deepcopy(source), delta)
assert result == target

# Revert it
recovered = revert_delta(copy.deepcopy(target), delta)
assert recovered == source
```

## Why This Exists

JSON Patch (RFC 6902) uses index-based array paths (`/items/0`). When arrays reorder, insert, or delete concurrently, indices silently point to the wrong elements. JSON Delta solves this:

- **Key-based array identity** — paths like `$.items[?(@.id==42)]` stay valid regardless of array order
- **Built-in reversibility** — `oldValue` fields let you invert any delta without external state
- **Self-describing paths** — array identity is embedded in the path, no external schema needed

This makes JSON Delta a reliable foundation for:

- **Audit logs** — record exactly what changed, revert any change
- **Undo/redo** — invert deltas to move backward and forward through history
- **Data synchronization** — send compact deltas instead of full documents
- **Agent and workflow state** — track state transitions with stable references

## API Reference

| Function | Description |
| --- | --- |
| `diff_delta(old, new, *, array_keys=None, reversible=True)` | Compute a delta between two objects |
| `apply_delta(obj, delta)` | Apply a delta to an object (mutates in place, use return value) |
| `validate_delta(delta)` | Validate delta structure, returns `ValidationResult` |
| `invert_delta(delta)` | Compute the inverse of a reversible delta |
| `revert_delta(obj, delta)` | Revert a delta (shorthand for `apply(obj, invert(delta))`) |
| `parse_path(path)` | Parse a JSON Delta Path string into typed segments |
| `build_path(segments)` | Build a canonical path string from segments |

## Array Identity Models

JSON Delta supports three ways to identify array elements:

```python
from json_delta import diff_delta

old = {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}
new = {"items": [{"id": 1, "name": "Widget Pro"}, {"id": 2, "name": "Gadget"}]}

# Key-based: track elements by a property value
delta = diff_delta(old, new, array_keys={"items": "id"})
# Path: $.items[?(@.id==1)].name — stable across reordering

# Value-based: for primitive arrays
old_tags = {"tags": ["urgent", "draft"]}
new_tags = {"tags": ["urgent", "review"]}
delta = diff_delta(old_tags, new_tags, array_keys={"tags": "$value"})
# Paths: $.tags[?(@=='draft')] (remove), $.tags[?(@=='review')] (add)

# Index-based (default): track elements by position
delta = diff_delta(old, new)
# Path: $.items[0].name — positional, fragile across concurrent changes
```

## JSON Delta vs JSON Patch

| Feature | JSON Delta | JSON Patch (RFC 6902) |
| --- | --- | --- |
| Array identity | Key-based, value-based, index-based | Index-based only |
| Reversibility | Built-in via `oldValue` | Not supported |
| Path syntax | JSONPath subset (`$.user.name`) | JSON Pointer (`/user/name`) |
| Operations | add, remove, replace | add, remove, replace, move, copy, test |
| Extensions | `x_`-prefixed properties preserved | Not supported |

## Examples

See the [`examples/`](examples/) directory for runnable demos:

- **[keyed_arrays.py](examples/keyed_arrays.py)** — key-based array identity with round-trip verification
- **[audit_log.py](examples/audit_log.py)** — audit trail with reversible deltas and extension metadata
- **[undo_redo.py](examples/undo_redo.py)** — undo/redo stack built on delta inversion
- **[data_sync.py](examples/data_sync.py)** — client-server sync sending deltas instead of full documents
- **[state_transitions.py](examples/state_transitions.py)** — tracking agent/workflow state changes

## Specification

This library implements the [JSON Delta v0 specification](https://github.com/ltwlf/json-delta-format/blob/main/spec/v0.md). It passes all Level 1 (Apply) and Level 2 (Reversible) conformance fixtures.

## Requirements

- Python 3.12+
- Zero runtime dependencies

## License

MIT
