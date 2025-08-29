# app/routers/simulation.py

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
    """Helper function to run the simulation in the background."""
    try:
        simulation_output = run_simulation(circuit)
        # Update status and add results, keeping owner info
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
    circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not circuit or circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    # Store initial job status with ownership information
    FAKE_SIMULATION_RESULTS_DB[job_id] = {
        "status": "pending",
        "results": None,
        "owner": current_user.username
    }

    # Add the long-running simulation to the background
    background_tasks.add_task(run_simulation_background, job_id, circuit)

    status_url = request.url_for('get_simulation_result', job_id=job_id)
    return {"job_id": job_id, "status_url": str(status_url)}

@router.get("/results/{job_id}", response_model=SimulationResult, name="get_simulation_result")
async def get_simulation_result(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    job = FAKE_SIMULATION_RESULTS_DB.get(job_id)

    # Securely check if the job exists and belongs to the current user
    if not job or job.get("owner") != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return SimulationResult(job_id=job_id, **job)
