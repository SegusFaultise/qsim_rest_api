# tests/test_api.py

import pytest

pytestmark = pytest.mark.asyncio

async def test_login_success(test_client):
    """Tests successful login and token generation."""
    response = await test_client.post(
        "/auth/login",
        data={"username": "free_user", "password": "password123"}
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

async def test_login_failure(test_client):
    """Tests login with incorrect credentials."""
    response = await test_client.post(
        "/auth/login",
        data={"username": "free_user", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

async def test_create_circuit_unauthorized(test_client):
    """Tests that creating a circuit requires authentication."""
    circuit_data = {
        "name": "Unauthorized Test",
        "qubits": 2,
        "gates": [{"gate": "H", "target": 0}]
    }
    response = await test_client.post("/api/v1/circuits/", json=circuit_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

async def test_create_and_get_circuit_authorized(test_client):
    """Tests creating and then retrieving a circuit with a valid token."""
    # First, log in to get a token
    login_response = await test_client.post(
        "/auth/login",
        data={"username": "pro_user", "password": "password456"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a circuit
    circuit_data = {
        "name": "Bell State Test",
        "qubits": 2,
        "gates": [
            {"gate": "H", "target": 0},
            {"gate": "CNOT", "control": 0, "target": 1}
        ]
    }
    create_response = await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers)
    assert create_response.status_code == 201
    created_circuit = create_response.json()
    assert created_circuit["name"] == "Bell State Test"
    assert "id" in created_circuit

    # Get the list of circuits for this user
    get_response = await test_client.get("/api/v1/circuits/", headers=headers)
    assert get_response.status_code == 200
    circuits_list = get_response.json()
    assert isinstance(circuits_list, list)
    # Note: In a real test suite with a database, you'd check for the specific circuit ID.
    # With our in-memory dict, we just confirm it's a list.

async def test_create_circuit_exceeds_qubit_limit(test_client):
    """Tests that a user cannot create a circuit with more qubits than their plan allows."""
    login_response = await test_client.post(
        "/auth/login",
        data={"username": "free_user", "password": "password123"} # free_user has an 8-qubit limit
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    circuit_data = {
        "name": "Too Big Circuit",
        "qubits": 10, # Exceeds the 8-qubit limit
        "gates": [{"gate": "H", "target": 0}]
    }
    create_response = await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers)
    assert create_response.status_code == 403
    assert "exceeds plan limit" in create_response.json()["detail"]

async def test_simulation_workflow(test_client):
    """Tests the full simulation workflow: create, simulate, and get result."""
    # 1. Login and get token
    login_response = await test_client.post(
        "/auth/login", data={"username": "free_user", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a circuit
    circuit_data = {
        "name": "Simple H Gate", "qubits": 1, "gates": [{"gate": "H", "target": 0}]
    }
    create_response = await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers)
    circuit_id = create_response.json()["id"]

    # 3. Start the simulation
    simulate_response = await test_client.post(f"/api/v1/circuits/{circuit_id}/simulate", headers=headers)
    assert simulate_response.status_code == 202
    job_info = simulate_response.json()
    assert "job_id" in job_info
    assert "status_url" in job_info

    # 4. Get the result
    # Note: Since our background task runs immediately, we can fetch the result right away.
    # In a real async system, you might need to wait/poll.
    result_response = await test_client.get(job_info["status_url"], headers=headers)
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert result_data["status"] == "completed"

    # FIXED: The key was changed from "probabilities" to "states" in the simulator
    assert "states" in result_data["results"]
    # For an H gate on |0>, the result should be a 50/50 superposition
    assert "0" in result_data["results"]["states"]
    assert "1" in result_data["results"]["states"]

async def test_update_circuit(test_client):
    """Tests updating an existing circuit's name and gates."""
    # 1. Login as pro_user and get a token
    login_response = await test_client.post(
        "/auth/login", data={"username": "pro_user", "password": "password456"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create an initial circuit
    initial_data = {"name": "Initial Circuit", "qubits": 1, "gates": [{"gate": "H", "target": 0}]}
    create_response = await test_client.post("/api/v1/circuits/", json=initial_data, headers=headers)
    assert create_response.status_code == 201
    circuit_id = create_response.json()["id"]

    # 3. Define the updated circuit data
    updated_data = {"name": "Updated Circuit", "qubits": 1, "gates": [{"gate": "X", "target": 0}]}
    update_response = await test_client.put(f"/api/v1/circuits/{circuit_id}", json=updated_data, headers=headers)

    # 4. Assert the update was successful
    assert update_response.status_code == 200
    updated_circuit = update_response.json()
    assert updated_circuit["name"] == "Updated Circuit"
    assert updated_circuit["gates"][0]["gate"] == "X"

    # 5. Verify the change by fetching the circuit again
    get_response = await test_client.get(f"/api/v1/circuits/{circuit_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Updated Circuit"

async def test_delete_circuit(test_client):
    """Tests that a circuit can be successfully deleted."""
    # 1. Login and get token
    login_response = await test_client.post(
        "/auth/login", data={"username": "pro_user", "password": "password456"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a circuit to be deleted
    circuit_data = {"name": "To Be Deleted", "qubits": 1, "gates": []}
    create_response = await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers)
    circuit_id = create_response.json()["id"]

    # 3. Delete the circuit
    delete_response = await test_client.delete(f"/api/v1/circuits/{circuit_id}", headers=headers)
    assert delete_response.status_code == 204

    # 4. Verify that the circuit is gone
    get_response = await test_client.get(f"/api/v1/circuits/{circuit_id}", headers=headers)
    assert get_response.status_code == 404

async def test_swap_gate_simulation(test_client):
    """Tests a circuit with a SWAP gate to ensure it produces the correct final state."""
    # 1. Login and get token
    login_response = await test_client.post(
        "/auth/login", data={"username": "free_user", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a circuit that prepares state |01> and then swaps it to |10>
    circuit_data = {
        "name": "SWAP Test",
        "qubits": 2,
        "gates": [
            {"gate": "X", "target": 1},  # Creates state |01>
            {"gate": "SWAP", "control": 0, "target": 1} # Swaps to |10>
        ]
    }
    create_response = await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers)
    circuit_id = create_response.json()["id"]

    # 3. Start simulation
    simulate_response = await test_client.post(f"/api/v1/circuits/{circuit_id}/simulate", headers=headers)
    job_info = simulate_response.json()

    # 4. Get result and verify the final state
    result_response = await test_client.get(job_info["status_url"], headers=headers)
    result_data = result_response.json()

    assert result_data["status"] == "completed"

    # FIXED: The key was changed from "probabilities" to "states"
    final_states = result_data["results"]["states"]

    # The final state should be |10> with ~100% probability
    assert "10" in final_states
    assert final_states["10"] == pytest.approx(1.0)
    assert len(final_states) == 1

async def test_update_circuit_unauthorized_access(test_client):
    """Tests that a user cannot update a circuit belonging to another user."""
    # 1. User A (pro_user) creates a circuit
    login_a_response = await test_client.post("/auth/login", data={"username": "pro_user", "password": "password456"})
    token_a = login_a_response.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    circuit_data = {"name": "User A Circuit", "qubits": 1, "gates": []}
    circuit_id = (await test_client.post("/api/v1/circuits/", json=circuit_data, headers=headers_a)).json()["id"]

    # 2. User B (free_user) tries to update User A's circuit
    login_b_response = await test_client.post("/auth/login", data={"username": "free_user", "password": "password123"})
    token_b = login_b_response.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    updated_data = {"name": "Malicious Update", "qubits": 1, "gates": []}

    update_response = await test_client.put(f"/api/v1/circuits/{circuit_id}", json=updated_data, headers=headers_b)

    # 3. Assert the request is denied
    assert update_response.status_code == 404
