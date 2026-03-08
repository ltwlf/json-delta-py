# json-delta-py

[![CI](https://github.com/ltwlf/json-delta-py/actions/workflows/ci.yml/badge.svg)](https://github.com/ltwlf/json-delta-py/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/json-delta-py.svg)](https://pypi.org/project/json-delta-py/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Deterministic JSON state transitions for Python.** Compute, apply, validate, and revert JSON Delta documents with stable array identity and reversible operations. Built for audit logs, undo/redo systems, data synchronization, and agent/workflow state tracking.

Zero dependencies. Fully typed. Python 3.12+.

> **Ecosystem note:** This project implements the [JSON Delta specification](https://github.com/ltwlf/json-delta-format). It is unrelated to the older `json-delta` package on PyPI.

```text
json-delta-format  (specification)
    ├── json-diff-ts      (TypeScript implementation)
    └── json-delta-py     (Python implementation)  ← this package
```

The specification defines the wire format. Each language implementation produces and consumes compatible deltas. A TypeScript implementation is also available: [json-diff-ts](https://github.com/ltwlf/json-diff-ts).

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

# Apply it
result = apply_delta(copy.deepcopy(source), delta)
assert result == target

# Revert it
recovered = revert_delta(copy.deepcopy(target), delta)
assert recovered == source
```

The delta is a plain JSON-serializable dict you can store in a database, send over HTTP, or consume in any language:

```json
{
  "format": "json-delta",
  "version": 1,
  "operations": [
    { "op": "replace", "path": "$.user.role", "value": "admin", "oldValue": "viewer" }
  ]
}
```

## What Is JSON Delta

[JSON Delta](https://github.com/ltwlf/json-delta-format) is a format for describing deterministic state transitions between JSON documents. A delta captures the exact set of changes — adds, removes, and replacements — needed to transform a source document into a target. Deltas are plain JSON: they can be applied, stored, transmitted, replayed, and inverted in any language.

## Why JSON Delta Exists

Most JSON diff libraries track array changes by position. Insert one element at the start and every path shifts:

```text
Remove /items/0  ← was actually "Widget"
Add    /items/0  ← now it's "NewItem"
Update /items/1  ← this used to be /items/0
```

This makes diffs fragile. You can't store them, replay them reliably, or build audit logs on top of them. This is the fundamental problem with index-based formats like JSON Patch (RFC 6902): paths like `/items/0` are positional, so any insertion, deletion, or reorder invalidates every subsequent path.

**JSON Delta solves this with key-based identity.** Array elements are matched by a stable key, and paths use JSONPath filter expressions that survive insertions, deletions, and reordering:

- **Key-based array identity** — paths like `$.items[?(@.id==42)]` stay valid regardless of array order
- **Built-in reversibility** — `oldValue` fields let you invert any delta without external state
- **Self-describing** — the `format` field and path expressions make deltas discoverable without external context

## What JSON Delta Is Useful For

- **Audit logs** — record exactly what changed, revert any change on demand
- **Undo/redo** — invert deltas to move backward and forward through state history
- **Data synchronization** — send compact deltas instead of full documents
- **Configuration history** — track config changes with stable references across deployments
- **Agent and workflow state** — track state transitions in AI agent loops or workflow engines

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

## JSON Delta vs JSON Patch

| Feature | JSON Delta | JSON Patch (RFC 6902) |
| --- | --- | --- |
| Path syntax | JSONPath (`$.items[?(@.id==1)]`) | JSON Pointer (`/items/0`) |
| Array identity | Key-based — survives reorder | Index-based — breaks on insert/delete |
| Reversibility | Built-in via `oldValue` | Not supported |
| Self-describing | `format` field in envelope | No envelope |
| Extensions | `x_`-prefixed properties preserved | Not supported |
| Specification | [json-delta-format](https://github.com/ltwlf/json-delta-format) | [RFC 6902](https://tools.ietf.org/html/rfc6902) |

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
