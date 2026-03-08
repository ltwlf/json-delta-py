"""Audit log — complete change history with point-in-time recovery.

Records every edit as a reversible delta with metadata (who, when).
The full audit trail enables compliance reporting, replay, and revert.
"""

import copy
from datetime import datetime, timezone

from json_delta import apply_delta, diff_delta, revert_delta

# Initial document
initial = {"title": "Q4 Report", "status": "draft", "author": "Alice"}
document = copy.deepcopy(initial)

# Audit log stores every delta with extension metadata
audit_log: list[dict] = []


def edit(doc: dict, new_state: dict, editor: str) -> dict:
    """Apply an edit and record the delta with metadata."""
    delta = diff_delta(doc, new_state, reversible=True)
    delta["x_editor"] = editor
    delta["x_timestamp"] = datetime.now(timezone.utc).isoformat()
    audit_log.append(delta)
    return apply_delta(doc, delta)


# Document workflow: draft → review → final
document = edit(document, {**document, "status": "review"}, "Alice")
document = edit(document, {**document, "title": "Q4 Financial Report"}, "Bob")
document = edit(document, {**document, "status": "final", "approved": True}, "Alice")

print("=== Current Document ===")
print(document)

print("\n=== Audit Trail ===")
for i, delta in enumerate(audit_log):
    editor = delta["x_editor"]
    ops = ", ".join(f"{op['op']} {op['path']}" for op in delta["operations"])
    print(f"  [{i}] {editor}: {ops}")

# Replay: rebuild the document from scratch using the audit log
replayed = copy.deepcopy(initial)
for delta in audit_log:
    replayed = apply_delta(replayed, delta)
assert replayed == document, "Replay should reproduce the current document"

# Revert: undo the last edit (e.g., premature finalization)
document = revert_delta(document, audit_log[-1])
assert document == {"title": "Q4 Financial Report", "status": "review", "author": "Alice"}

print("\n=== After reverting last edit ===")
print(document)

print("\nAudit log with replay and revert verified!")
