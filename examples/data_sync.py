"""Client-server data sync — send deltas instead of full documents.

Demonstrates computing a delta on the client side and applying it
on the server side, minimizing data transfer.
"""

import copy
import json

from json_delta import apply_delta, diff_delta, validate_delta

# --- Server state ---
server_state = {
    "users": [
        {"id": "u1", "name": "Alice", "role": "viewer"},
        {"id": "u2", "name": "Bob", "role": "viewer"},
    ]
}

# --- Client makes local changes ---
client_state = copy.deepcopy(server_state)
# Promote Alice to admin
client_state["users"][0]["role"] = "admin"
# Add a new user
client_state["users"].append({"id": "u3", "name": "Charlie", "role": "viewer"})

# Client computes a delta (small payload to send)
delta = diff_delta(server_state, client_state, array_keys={"users": "id"})

print("=== Delta payload (what the client sends) ===")
print(json.dumps(delta, indent=2))

# --- Server receives and validates the delta ---
validation = validate_delta(delta)
if not validation.valid:
    print(f"Invalid delta: {validation.errors}")
else:
    print(f"\n=== Delta validated ({len(delta['operations'])} operations) ===")

    # Server applies the delta
    server_state = apply_delta(server_state, delta)

    print("\n=== Server state after sync ===")
    for user in server_state["users"]:
        print(f"  {user['id']}: {user['name']} ({user['role']})")

    assert server_state == client_state
    print("\nSync successful — server matches client!")
