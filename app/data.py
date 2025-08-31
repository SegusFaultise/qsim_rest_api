import json
from .schemas import UserInDB, Circuit

def load_users_from_json():
    """
    <summary>
    Loads user data from a 'users.json' file. This serves as a simple, persistent
    data store for user information, replacing a hardcoded dictionary.
    </summary>
    <returns type="dict">
    A dictionary containing the user data loaded from the JSON file.
    Returns an empty dictionary if the file is not found.
    </returns>
    """
    try:
        with open("app/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# --- User Data ---
"""
<summary>
A dictionary that acts as an in-memory database for users. It is populated
by loading data from 'users.json' when the application starts.
</summary>
"""
FAKE_USERS_DB = load_users_from_json()

def get_user(username: str) -> UserInDB | None:
    """
    <summary>
    Retrieves a user's data from the FAKE_USERS_DB dictionary.
    </summary>
    <param name="username" type="str">The username of the user to retrieve.</param>
    <returns type="UserInDB | None">
    A UserInDB Pydantic model instance if the user is found, otherwise None.
    </returns>
    """
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return UserInDB(**user_dict)
    return None

# --- Circuit Data (remains in-memory) ---
"""
<summary>
An in-memory dictionary that serves as a temporary database for storing quantum circuits.
The keys are circuit IDs, and the values are Circuit Pydantic models.
</summary>
"""
FAKE_CIRCUITS_DB: dict[str, Circuit] = {}

# --- Simulation Job Data (remains in-memory) ---
"""
<summary>
An in-memory dictionary to track the state of simulation jobs.
The keys are job IDs, and the values are dictionaries containing the job's status and results.
</summary>
"""
FAKE_SIMULATION_RESULTS_DB: dict = {}
