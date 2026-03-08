"""Audit log — store reversible deltas for a complete change history.

Each edit produces a delta with oldValue fields, enabling both
forward replay and backward reversion of any change.
"""

import copy

from json_delta import apply_delta, diff_delta, revert_delta

# Initial document
document = {"title": "Q4 Report", "status": "draft", "author": "Alice"}

# Simulate a series of edits, capturing each delta
audit_log: list[dict] = []


def edit(doc: dict, new_state: dict, editor: str) -> dict:
    """Apply an edit and record the delta in the audit log."""
    delta = diff_delta(doc, new_state, reversible=True)
    # Attach extension metadata (preserved by invert/apply)
    delta["x_editor"] = editor
    audit_log.append(delta)
    return apply_delta(doc, delta)


# Edit 1: Alice updates the status
document = edit(document, {**document, "status": "review"}, "Alice")

# Edit 2: Bob changes the title
document = edit(document, {**document, "title": "Q4 Financial Report"}, "Bob")

# Edit 3: Alice finalizes
document = edit(document, {**document, "status": "final", "approved": True}, "Alice")

print("=== Current Document ===")
print(document)

print("\n=== Audit Log ===")
for i, delta in enumerate(audit_log):
    editor = delta.get("x_editor", "unknown")
    ops = ", ".join(f"{op['op']} {op['path']}" for op in delta["operations"])
    print(f"  [{i}] by {editor}: {ops}")

# Revert the last change
print("\n=== Reverting last edit ===")
document = revert_delta(document, audit_log[-1])
print(document)
assert document == {"title": "Q4 Financial Report", "status": "review", "author": "Alice"}
print("Revert successful!")
