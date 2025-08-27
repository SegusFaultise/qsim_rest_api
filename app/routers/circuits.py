# app/routers/circuits.py

import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import Circuit, CircuitCreate, User
from ..security import get_current_user
from ..data import FAKE_CIRCUITS_DB

router = APIRouter(
    prefix="/circuits",
    tags=["Circuits"],
    dependencies=[Depends(get_current_user)] # All routes here require authentication
)

@router.post("/", response_model=Circuit, status_code=status.HTTP_201_CREATED)
async def create_circuit(
    circuit: CircuitCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    if circuit.qubits > current_user.max_qubits:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Number of qubits ({circuit.qubits}) exceeds plan limit ({current_user.max_qubits})."
        )
    
    circuit_id = f"ckt_{uuid.uuid4().hex[:8]}"
    new_circuit = Circuit(
        id=circuit_id,
        owner=current_user.username,
        **circuit.model_dump()
    )
    FAKE_CIRCUITS_DB[circuit_id] = new_circuit
    return new_circuit

@router.get("/", response_model=List[Circuit])
async def get_user_circuits(current_user: Annotated[User, Depends(get_current_user)]):
    user_circuits = [
        c for c in FAKE_CIRCUITS_DB.values() if c.owner == current_user.username
    ]
    return user_circuits

@router.get("/{circuit_id}", response_model=Circuit)
async def get_circuit_by_id(
    circuit_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not circuit or circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    return circuit
