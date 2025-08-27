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
    assert "probabilities" in result_data["results"]
    # For an H gate on |0>, the result should be a 50/50 superposition
    assert "0" in result_data["results"]["probabilities"]
    assert "1" in result_data["results"]["probabilities"]
