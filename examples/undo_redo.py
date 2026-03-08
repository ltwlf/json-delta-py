"""Undo/redo — reversible configuration editing.

A deployment config editor backed by JSON Delta. Each change
is a reversible delta, enabling multi-step undo and redo.
"""

import copy

from json_delta import apply_delta, diff_delta, invert_delta


class ConfigEditor:
    """Tracks configuration changes with full undo/redo support."""

    def __init__(self, config: dict) -> None:
        self.config = copy.deepcopy(config)
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []

    def update(self, new_config: dict) -> None:
        """Apply a change and push it onto the undo stack."""
        delta = diff_delta(self.config, new_config, reversible=True)
        if not delta["operations"]:
            return
        self.undo_stack.append(delta)
        self.redo_stack.clear()
        self.config = apply_delta(self.config, delta)

    def undo(self) -> bool:
        """Undo the last change. Returns False if nothing to undo."""
        if not self.undo_stack:
            return False
        delta = self.undo_stack.pop()
        self.config = apply_delta(self.config, invert_delta(delta))
        self.redo_stack.append(delta)
        return True

    def redo(self) -> bool:
        """Redo the last undone change. Returns False if nothing to redo."""
        if not self.redo_stack:
            return False
        delta = self.redo_stack.pop()
        self.config = apply_delta(self.config, delta)
        self.undo_stack.append(delta)
        return True


# Editing a service deployment configuration
editor = ConfigEditor({
    "service": "payment-api",
    "replicas": 2,
    "env": "staging",
    "memory": "512Mi",
})
print(f"Initial:    {editor.config}")

# Change 1: scale up for load test
editor.update({**editor.config, "replicas": 5, "memory": "1Gi"})
print(f"Scaled up:  {editor.config}")

# Change 2: promote to production
editor.update({**editor.config, "env": "production"})
print(f"Promoted:   {editor.config}")

# Oops — undo the production promotion
editor.undo()
print(f"After undo: {editor.config}")
assert editor.config["env"] == "staging"

# Undo the scale-up too
editor.undo()
print(f"After undo: {editor.config}")
assert editor.config == {"service": "payment-api", "replicas": 2, "env": "staging", "memory": "512Mi"}

# Redo the scale-up
editor.redo()
print(f"After redo: {editor.config}")
assert editor.config["replicas"] == 5

print("\nUndo/redo verified!")
