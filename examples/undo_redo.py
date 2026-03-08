"""Undo/redo stack — use deltas as the foundation for undo/redo.

Each user action produces a reversible delta. Undo inverts and applies
the delta; redo re-applies the original delta.
"""

import copy

from json_delta import apply_delta, diff_delta, invert_delta


class UndoRedoStack:
    def __init__(self, initial_state: dict) -> None:
        self.state = copy.deepcopy(initial_state)
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []

    def apply_change(self, new_state: dict) -> None:
        """Record a change and clear the redo stack."""
        delta = diff_delta(self.state, new_state, reversible=True)
        if not delta["operations"]:
            return  # No change
        self.undo_stack.append(delta)
        self.redo_stack.clear()
        self.state = apply_delta(self.state, delta)

    def undo(self) -> None:
        """Undo the last change."""
        if not self.undo_stack:
            print("  Nothing to undo")
            return
        delta = self.undo_stack.pop()
        inverse = invert_delta(delta)
        self.state = apply_delta(self.state, inverse)
        self.redo_stack.append(delta)

    def redo(self) -> None:
        """Redo the last undone change."""
        if not self.redo_stack:
            print("  Nothing to redo")
            return
        delta = self.redo_stack.pop()
        self.state = apply_delta(self.state, delta)
        self.undo_stack.append(delta)


# Demo
stack = UndoRedoStack({"name": "Alice", "score": 0})
print(f"Initial: {stack.state}")

stack.apply_change({"name": "Alice", "score": 10})
print(f"After +10: {stack.state}")

stack.apply_change({"name": "Alice", "score": 25})
print(f"After +15: {stack.state}")

stack.undo()
print(f"After undo: {stack.state}")
assert stack.state == {"name": "Alice", "score": 10}

stack.undo()
print(f"After undo: {stack.state}")
assert stack.state == {"name": "Alice", "score": 0}

stack.redo()
print(f"After redo: {stack.state}")
assert stack.state == {"name": "Alice", "score": 10}

print("\nUndo/redo verified!")
