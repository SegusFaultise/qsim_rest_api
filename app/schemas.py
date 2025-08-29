# app/schemas.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# --- User Schemas ---
class User(BaseModel):
    username: str
    max_qubits: int

class UserInDB(User):
    hashed_password: str

# --- Circuit Schemas ---
class Gate(BaseModel):
    gate: str
    time: int
    targets: List[int]
    controls: List[int] = []
    parameters: Optional[Dict[str, Any]] = None

class CircuitBase(BaseModel):
    name: str
    qubits: int
    gates: List[Gate]

class CircuitCreate(CircuitBase):
    pass

class Circuit(CircuitBase):
    id: str
    owner: str

# --- Simulation Schemas ---
class SimulationJob(BaseModel):
    job_id: str
    status_url: str

class SimulationResult(BaseModel):
    job_id: str
    status: str
    results: Dict[str, Any] | None = None
    error: str | None = None
