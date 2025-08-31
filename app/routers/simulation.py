import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks

from ..schemas import SimulationJob, SimulationResult, User, Circuit
from ..security import get_current_user
from ..data import FAKE_CIRCUITS_DB, FAKE_SIMULATION_RESULTS_DB
from ..core.simulator import run_simulation

router = APIRouter(
    tags=["Simulation"],
    dependencies=[Depends(get_current_user)]
)

def run_simulation_background(job_id: str, circuit: Circuit):
    """
    <summary>
    A helper function designed to run the CPU-intensive circuit simulation in a background task.
    It updates the job status in the fake database to 'completed' on success or 'failed' on error.
    </summary>
    <param name="job_id" type="str">The unique ID for the simulation job.</param>
    <param name="circuit" type="Circuit">The circuit object to be simulated.</param>
    """
    try:
        simulation_output = run_simulation(circuit)
        job_data = FAKE_SIMULATION_RESULTS_DB.get(job_id, {})
        job_data.update({"status": "completed", "results": simulation_output})
        FAKE_SIMULATION_RESULTS_DB[job_id] = job_data
    except Exception as e:
        job_data = FAKE_SIMULATION_RESULTS_DB.get(job_id, {})
        job_data.update({"status": "failed", "error": str(e), "results": None})
        FAKE_SIMULATION_RESULTS_DB[job_id] = job_data

@router.post("/circuits/{circuit_id}/simulate", response_model=SimulationJob, status_code=status.HTTP_202_ACCEPTED)
async def start_new_simulation(
    circuit_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
):
    """
    <summary>
    Initiates a new quantum circuit simulation as a background task.
    It immediately returns a job ID and a status URL, allowing the client to poll for results.
    </summary>
    <param name="circuit_id" type="str">The ID of the circuit to simulate.</param>
    <param name="background_tasks" type="BackgroundTasks">FastAPI dependency for running tasks after the response is sent.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <param name="request" type="Request">The incoming request object, used to build the status URL.</param>
    <returns type="SimulationJob">An object containing the job_id and the URL to poll for the result.</returns>
    <exception cref="HTTPException">Raises 404 Not Found if the circuit does not exist or is not owned by the user.</exception>
    """
    circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not circuit or circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    FAKE_SIMULATION_RESULTS_DB[job_id] = {
        "status": "pending",
        "results": None,
        "owner": current_user.username
    }

    background_tasks.add_task(run_simulation_background, job_id, circuit)

    status_url = request.url_for('get_simulation_result', job_id=job_id)
    return {"job_id": job_id, "status_url": str(status_url)}

@router.get("/results/{job_id}", response_model=SimulationResult, name="get_simulation_result")
async def get_simulation_result(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    <summary>
    Retrieves the status and results of a previously started simulation job.
    </summary>
    <param name="job_id" type="str">The unique ID of the simulation job to check.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="SimulationResult">An object containing the job's status and the simulation results if completed.</returns>
    <exception cref="HTTPException">Raises 404 Not Found if the job does not exist or is not owned by the user.</exception>
    """
    job = FAKE_SIMULATION_RESULTS_DB.get(job_id)

    if not job or job.get("owner") != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return SimulationResult(job_id=job_id, **job)
