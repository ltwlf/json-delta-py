"""State transitions — track agent or workflow state changes as deltas.

Useful for AI agent loops, workflow engines, or any system where
you need to record exactly what changed between steps.
"""

import copy

from json_delta import apply_delta, diff_delta

# An AI agent's state evolving over multiple steps
states = [
    # Step 0: initial state
    {
        "task": "Research competitors",
        "status": "in_progress",
        "findings": [],
        "confidence": 0.0,
    },
    # Step 1: first finding
    {
        "task": "Research competitors",
        "status": "in_progress",
        "findings": [{"company": "Acme", "strength": "pricing"}],
        "confidence": 0.3,
    },
    # Step 2: second finding + confidence update
    {
        "task": "Research competitors",
        "status": "in_progress",
        "findings": [
            {"company": "Acme", "strength": "pricing"},
            {"company": "Globex", "strength": "technology"},
        ],
        "confidence": 0.7,
    },
    # Step 3: task complete
    {
        "task": "Research competitors",
        "status": "completed",
        "findings": [
            {"company": "Acme", "strength": "pricing"},
            {"company": "Globex", "strength": "technology"},
        ],
        "confidence": 1.0,
        "summary": "Two main competitors identified.",
    },
]

print("=== State Transition Log ===")
for i in range(1, len(states)):
    delta = diff_delta(
        states[i - 1],
        states[i],
        array_keys={"findings": "company"},
        reversible=False,
    )
    print(f"\nStep {i - 1} -> {i}:")
    for op in delta["operations"]:
        print(f"  {op['op']:>7s}  {op['path']}  =  {op.get('value', '(removed)')}")

# Verify each transition produces the correct next state
for i in range(1, len(states)):
    delta = diff_delta(states[i - 1], states[i], array_keys={"findings": "company"})
    result = apply_delta(copy.deepcopy(states[i - 1]), delta)
    assert result == states[i], f"Transition {i - 1}->{i} failed"

print("\nAll state transitions verified!")
