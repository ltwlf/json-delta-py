"""Client-server sync — send deltas instead of full documents.

Computes a delta on the client and applies it on the server.
Only the changes are transmitted, reducing payload size.
"""

import copy
import json

from json_delta import apply_delta, diff_delta, validate_delta

# Server holds the current team directory
server_state = {
    "users": [
        {"id": "u1", "name": "Alice Chen", "role": "viewer", "department": "Engineering"},
        {"id": "u2", "name": "Bob Martinez", "role": "viewer", "department": "Engineering"},
        {"id": "u3", "name": "Carol Park", "role": "admin", "department": "Security"},
        {"id": "u4", "name": "Dan Wilson", "role": "viewer", "department": "Marketing"},
        {"id": "u5", "name": "Eva Santos", "role": "viewer", "department": "Design"},
    ]
}

# Client makes local changes: promote Alice, add a new hire
client_state = copy.deepcopy(server_state)
client_state["users"][0]["role"] = "admin"
client_state["users"].append(
    {"id": "u6", "name": "Frank Okafor", "role": "viewer", "department": "Engineering"}
)

# Compute delta (what the client sends instead of the full document)
delta = diff_delta(server_state, client_state, array_keys={"users": "id"})

# Compare payload sizes
full_size = len(json.dumps(client_state))
delta_size = len(json.dumps(delta))
print(f"Full document: {full_size} bytes")
print(f"Delta payload: {delta_size} bytes ({delta_size * 100 // full_size}% of full)")

print(f"\n=== Delta ({len(delta['operations'])} operations) ===")
print(json.dumps(delta, indent=2))

# Server validates and applies the delta
validation = validate_delta(delta)
assert validation.valid, f"Invalid delta: {validation.errors}"

server_state = apply_delta(server_state, delta)

print("\n=== Server state after sync ===")
for user in server_state["users"]:
    print(f"  {user['id']}: {user['name']} ({user['role']}, {user['department']})")

assert server_state == client_state
print("\nSync verified — server matches client!")
