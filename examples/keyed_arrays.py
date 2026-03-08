"""Key-based array identity — track inventory changes by SKU, not position.

Shows how JSON Delta handles arrays where elements have a stable identity
key, producing diffs that survive insertions, deletions, and reordering.
"""

import copy

from json_delta import apply_delta, diff_delta, invert_delta

# Current product inventory
source = {
    "products": [
        {"sku": "LAPTOP-001", "name": "ProBook 14", "price": 999.00, "stock": 45},
        {"sku": "MOUSE-003", "name": "ErgoClick Pro", "price": 49.99, "stock": 200},
        {"sku": "MONITOR-002", "name": "UltraWide 34", "price": 599.00, "stock": 30},
    ]
}

# Updated inventory: price cut, discontinued monitor, new keyboard
target = {
    "products": [
        {"sku": "LAPTOP-001", "name": "ProBook 14", "price": 899.00, "stock": 45},
        {"sku": "MOUSE-003", "name": "ErgoClick Pro", "price": 49.99, "stock": 200},
        {"sku": "KEYBOARD-004", "name": "MechType Ultra", "price": 129.00, "stock": 75},
    ]
}

# Compute a delta using SKU as the identity key
delta = diff_delta(source, target, array_keys={"products": "sku"})

print("=== Inventory Changes ===")
for op in delta["operations"]:
    print(f"  {op['op']:>7s}  {op['path']}")
    if "value" in op:
        print(f"           -> {op['value']}")

# Forward: apply changes to get the new inventory
result = apply_delta(copy.deepcopy(source), delta)
assert result == target, "apply(source, delta) != target"

# Backward: roll back to previous inventory
inverse = invert_delta(delta)
recovered = apply_delta(copy.deepcopy(target), inverse)
assert recovered == source, "apply(target, inverse) != source"

print("\n=== Round-trip verified ===")
print("apply(source, delta) == target")
print("apply(target, inverse(delta)) == source")
