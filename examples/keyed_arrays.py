"""Key-based array identity — track changes by element ID, not position.

Demonstrates how JSON Delta handles arrays where elements have a unique
identity key (like "id"), producing stable diffs regardless of element order.
"""

from json_delta import apply_delta, diff_delta, invert_delta

# Source: a product catalog
source = {
    "products": [
        {"id": 1, "name": "Widget", "price": 10.00},
        {"id": 2, "name": "Gadget", "price": 20.00},
        {"id": 3, "name": "Doohickey", "price": 30.00},
    ]
}

# Target: price update, one removal, one addition
target = {
    "products": [
        {"id": 1, "name": "Widget", "price": 12.50},
        {"id": 2, "name": "Gadget", "price": 20.00},
        {"id": 4, "name": "Thingamajig", "price": 40.00},
    ]
}

# Compute a delta using key-based identity on the "products" array
delta = diff_delta(source, target, array_keys={"products": "id"})

print("=== Delta Operations ===")
for op in delta["operations"]:
    print(f"  {op['op']:>7s}  {op['path']}")
    if "value" in op:
        print(f"           value: {op['value']}")

# Apply the delta to verify correctness
import copy

result = apply_delta(copy.deepcopy(source), delta)
assert result == target, "apply(source, delta) != target"

# Compute and apply the inverse to recover the source
inverse = invert_delta(delta)
recovered = apply_delta(copy.deepcopy(target), inverse)
assert recovered == source, "apply(target, inverse) != source"

print("\n=== Round-trip verified ===")
print("apply(source, delta) == target")
print("apply(target, inverse(delta)) == source")
