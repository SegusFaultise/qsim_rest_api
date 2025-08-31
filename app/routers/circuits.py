import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response

from ..schemas import Circuit, CircuitCreate, User
from ..security import get_current_user
from ..data import FAKE_CIRCUITS_DB

router = APIRouter(
    prefix="/circuits",
    tags=["Circuits"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=Circuit, status_code=status.HTTP_201_CREATED)
async def create_circuit(
    circuit: CircuitCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    <summary>
    Creates a new quantum circuit for the authenticated user.
    </summary>
    <param name="circuit" type="CircuitCreate">The circuit data sent in the request body.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="Circuit">The newly created circuit object, including its generated ID and owner.</returns>
    <exception cref="HTTPException">Raises 403 Forbidden if the number of qubits exceeds the user's plan limit.</exception>
    """
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
    """
    <summary>
    Retrieves a list of all circuits owned by the currently authenticated user.
    </summary>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="List[Circuit]">A list of circuit objects belonging to the user.</returns>
    """
    user_circuits = [
        c for c in FAKE_CIRCUITS_DB.values() if c.owner == current_user.username
    ]
    return user_circuits

@router.get("/{circuit_id}", response_model=Circuit)
async def get_circuit_by_id(
    circuit_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    <summary>
    Retrieves a single circuit by its unique ID, if it exists and is owned by the user.
    </summary>
    <param name="circuit_id" type="str">The unique ID of the circuit to retrieve.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="Circuit">The requested circuit object.</returns>
    <exception cref="HTTPException">Raises 404 Not Found if the circuit does not exist or is not owned by the user.</exception>
    """
    circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not circuit or circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    return circuit

@router.put("/{circuit_id}", response_model=Circuit)
async def update_circuit(
    circuit_id: str,
    circuit_update: CircuitCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    <summary>
    Updates an existing quantum circuit with new data.
    </summary>
    <param name="circuit_id" type="str">The unique ID of the circuit to update.</param>
    <param name="circuit_update" type="CircuitCreate">The new circuit data sent in the request body.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="Circuit">The updated circuit object.</returns>
    <exception cref="HTTPException">
    Raises 404 Not Found if the circuit does not exist or is not owned by the user.
    Raises 403 Forbidden if the number of qubits in the update exceeds the user's plan limit.
    </exception>
    """
    existing_circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not existing_circuit or existing_circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    if circuit_update.qubits > current_user.max_qubits:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Number of qubits ({circuit_update.qubits}) exceeds plan limit ({current_user.max_qubits})."
        )

    updated_circuit = Circuit(
        id=circuit_id,
        owner=current_user.username,
        **circuit_update.model_dump()
    )

    FAKE_CIRCUITS_DB[circuit_id] = updated_circuit
    return updated_circuit

@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_circuit(
    circuit_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    <summary>
    Deletes a specified circuit, if it exists and is owned by the user.
    </summary>
    <param name="circuit_id" type="str">The unique ID of the circuit to delete.</param>
    <param name="current_user" type="User">The authenticated user object, injected by FastAPI.</param>
    <returns type="Response">An empty response with a 204 No Content status code upon successful deletion.</returns>
    <exception cref="HTTPException">Raises 404 Not Found if the circuit does not exist or is not owned by the user.</exception>
    """
    existing_circuit = FAKE_CIRCUITS_DB.get(circuit_id)
    if not existing_circuit or existing_circuit.owner != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")

    del FAKE_CIRCUITS_DB[circuit_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
