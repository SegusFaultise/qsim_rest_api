import asyncio
import httpx
import time
import itertools
from datetime import datetime


DEV_API_BASE_URL = "http://localhost:8000"
PROD_API_BASE_URL = "http://13.211.138.90:8080"
API_BASE_URL = PROD_API_BASE_URL
USERNAME = "free_user"
PASSWORD = "password123"

TEST_DURATION_SECONDS = 300
MAX_CONCURRENT_WORKERS = 4
QUBITS_FOR_TEST = 9
TEST_CIRCUIT_DATA = {
    "name": "Sustained Heavy Load Test",
    "qubits": QUBITS_FOR_TEST,
    "gates": [
        {"gate": "h", "time": 0, "targets": [i], "controls": []}
        for i in range(QUBITS_FOR_TEST)
    ],
}

async def login_and_get_token(client: httpx.AsyncClient) -> str:
    """
    <summary>
    Logs in to the API to get an authentication token.
    </summary>
    <param name="client" type="httpx.AsyncClient">An active httpx client instance.</param>
    <returns type="str">The JWT access token for authentication.</returns>
    """
    print(f"[{datetime.now():%H:%M:%S}] Attempting to log in...")
    response = await client.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print(f"[{datetime.now():%H:%M:%S}] Login successful.")
    return token

async def create_test_circuit(client: httpx.AsyncClient, token: str) -> str:
    """
    <summary>
    Creates a single, reusable, and CPU-intensive circuit for all simulation requests.
    </summary>
    <param name="client" type="httpx.AsyncClient">An active httpx client instance.</param>
    <param name="token" type="str">A valid JWT access token.</param>
    <returns type="str">The unique ID of the newly created circuit.</returns>
    """
    print(f"[{datetime.now():%H:%M:%S}] Creating a single, {QUBITS_FOR_TEST}-qubit test circuit...")
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        f"{API_BASE_URL}/api/v1/circuits/",
        json=TEST_CIRCUIT_DATA,
        headers=headers
    )
    response.raise_for_status()
    circuit_id = response.json()["id"]
    print(f"[{datetime.now():%H:%M:%S}] Test circuit created with ID: {circuit_id}")
    return circuit_id

async def run_simulation(semaphore: asyncio.Semaphore, client: httpx.AsyncClient, token: str, circuit_id: str, request_num: int) -> bool:
    """
    <summary>
    Sends a single POST request to the simulation endpoint, managed by a semaphore.
    </summary>
    <param name="semaphore" type="asyncio.Semaphore">The semaphore to control concurrency.</param>
    <param name="client" type="httpx.AsyncClient">An active httpx client instance.</param>
    <param name="token" type="str">A valid JWT access token.</param>
    <param name="circuit_id" type="str">The ID of the circuit to simulate.</param>
    <param name="request_num" type="int">The sequential number of this request for logging.</param>
    <returns type="bool">True for success, False for failure.</returns>
    """
    async with semaphore:
        log_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{log_time}] -> Starting simulation request #{request_num}...")
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/circuits/{circuit_id}/simulate",
                headers=headers,
                timeout=90.0
            )
            response.raise_for_status()
            job_id = response.json()["job_id"]
            print(f"[{log_time}] Success #{request_num}: Job {job_id} started.")
            return True
        except httpx.HTTPStatusError as e:
            print(f"[{log_time}] Error #{request_num}: HTTP {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"[{log_time}] Error #{request_num}: Request failed: {e}")
            return False

async def main():
    """
    <summary>
    Orchestrates the load test: logs in, creates the circuit, and then continuously
    sends simulation requests for a fixed duration to sustain high CPU load.
    </summary>
    """
    async with httpx.AsyncClient() as client:
        try:
            token = await login_and_get_token(client)
            circuit_id = await create_test_circuit(client, token)

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)
            start_time = time.time()
            end_time = start_time + TEST_DURATION_SECONDS

            print(f"\n Starting sustained load test for {TEST_DURATION_SECONDS} seconds...")

            tasks = []
            for i in itertools.count(1):
                if time.time() >= end_time:
                    break
                task = asyncio.create_task(run_simulation(semaphore, client, token, circuit_id, i))
                tasks.append(task)
                await asyncio.sleep(0.1)

            results = await asyncio.gather(*tasks)

            success_count = sum(1 for r in results if r)
            failure_count = len(results) - success_count

            print("\n--- Load Test Summary ---")
            print(f"Total Requests Sent: {len(results)}")
            print(f"Successful Requests: {success_count}")
            print(f"Failed Requests:     {failure_count}")
            print(f"Total Duration:      {time.time() - start_time:.2f} seconds.")

        except httpx.HTTPStatusError as e:
            print(f"\nCRITICAL SETUP ERROR: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"\nCRITICAL SETUP ERROR: Could not connect to the API at {e.request.url}.")

if __name__ == "__main__":
    asyncio.run(main())
