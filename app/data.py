# app/data.py

import json
from .schemas import UserInDB, Circuit

# --- User Data ---
# Load user data from the JSON file instead of a hardcoded dict
def load_users_from_json():
    try:
        with open("app/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

FAKE_USERS_DB = load_users_from_json()

def get_user(username: str) -> UserInDB | None:
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return UserInDB(**user_dict)
    return None

# --- Circuit Data (remains in-memory) ---
FAKE_CIRCUITS_DB: dict[str, Circuit] = {}

# --- Simulation Job Data (remains in-memory) ---
FAKE_SIMULATION_RESULTS_DB: dict = {}
