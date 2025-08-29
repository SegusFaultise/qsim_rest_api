# app/core/simulator.py

import numpy as np
from ..schemas import CircuitCreate

# NEW: Helper to create rotation matrices
def create_rotation_matrix(axis: str, theta: float) -> np.ndarray:
    """Creates a rotation matrix for a given axis and angle theta."""
    cos_t = np.cos(theta / 2)
    sin_t = np.sin(theta / 2)
    if axis.upper() == 'X':
        return np.array([[cos_t, -1j * sin_t], [-1j * sin_t, cos_t]])
    elif axis.upper() == 'Y':
        return np.array([[cos_t, -sin_t], [sin_t, cos_t]])
    elif axis.upper() == 'Z':
        return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]])
    raise ValueError("Invalid rotation axis specified.")

def run_simulation(circuit: CircuitCreate) -> dict:
    """
    Runs a quantum circuit simulation.
    This is the CPU-intensive part of the application.
    """
    num_qubits = circuit.qubits
    state_vector = np.zeros(2**num_qubits, dtype=complex)
    state_vector[0] = 1 + 0j

    for gate_info in circuit.gates:
        gate_name = gate_info.gate.upper()
        gate_matrix = None

        # Single-qubit gates
        if gate_name in ["H", "X", "Y", "Z", "S", "T"]:
            if gate_name == "H":
                op_matrix = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
            elif gate_name == "X":
                op_matrix = np.array([[0, 1], [1, 0]])
            elif gate_name == "Y":
                op_matrix = np.array([[0, -1j], [1j, 0]])
            elif gate_name == "Z":
                op_matrix = np.array([[1, 0], [0, -1]])
            elif gate_name == "S":
                op_matrix = np.array([[1, 0], [0, 1j]])
            elif gate_name == "T":
                op_matrix = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])

            # Ensure target is correctly identified
            target = gate_info.targets[0] if gate_info.targets else gate_info.target
            gate_matrix = create_full_gate_matrix(op_matrix, target, num_qubits)

        # NEW: Handle parameterized rotation gates
        elif gate_name in ["RX", "RY", "RZ"]:
            theta = gate_info.parameters.get("theta", 0.0)
            axis = gate_name[-1] # 'X', 'Y', or 'Z'
            op_matrix = create_rotation_matrix(axis, theta)
            target = gate_info.targets[0]
            gate_matrix = create_full_gate_matrix(op_matrix, target, num_qubits)

        # NEW: Handle Measurement gate (currently a no-op in simulation)
        elif gate_name == "MEASURE":
            continue # In this simulator, measurement is implicit at the end

        # Multi-qubit gates (updated for new schema)
        elif gate_name in ["CNOT", "SWAP", "CCNOT"]:
            controls, targets = gate_info.controls, gate_info.targets
            if not targets:
                raise ValueError(f"{gate_name} gate requires at least one target qubit.")

            if gate_name == "CNOT":
                gate_matrix = create_cnot_matrix(controls[0], targets[0], num_qubits)
            elif gate_name == "SWAP":
                # Assuming SWAP acts on the first two targets if specified
                gate_matrix = create_swap_matrix(targets[0], targets[1], num_qubits)
            elif gate_name == "CCNOT":
                gate_matrix = create_ccnot_matrix(controls, targets[0], num_qubits)

        if gate_matrix is not None:
            state_vector = np.dot(gate_matrix, state_vector)

    probabilities = np.abs(state_vector)**2
    results = {}
    for i, prob in enumerate(probabilities):
        if prob > 1e-9:
            state_str = format(i, f'0{num_qubits}b')
            results[state_str] = prob

    return {"states": results}

def create_full_gate_matrix(op_matrix, target_qubit, num_qubits):
    I = np.identity(2, dtype=complex)
    full_matrix = op_matrix if target_qubit == 0 else I
    for qubit in range(1, num_qubits):
        matrix_to_kron = op_matrix if qubit == target_qubit else I
        full_matrix = np.kron(full_matrix, matrix_to_kron)
    return full_matrix

# NEW: Renamed and updated for clarity
def create_controlled_gate_matrix(controls, target, num_qubits, operation_func):
    """Generic helper for creating controlled gates (CNOT, CCNOT, etc.)."""
    size = 2**num_qubits
    matrix = np.zeros((size, size), dtype=complex)
    for i in range(size):
        binary_str = format(i, f'0{num_qubits}b')
        # Check if all control bits are '1'
        if all(binary_str[c] == '1' for c in controls):
            j = operation_func(binary_str, target)
            matrix[j, i] = 1
        else:
            matrix[i, i] = 1
    return matrix

def create_cnot_matrix(control, target, num_qubits):
    def flip_target(binary_str, target_qubit):
        flipped_list = list(binary_str)
        flipped_list[target_qubit] = '0' if binary_str[target_qubit] == '1' else '1'
        return int("".join(flipped_list), 2)
    return create_controlled_gate_matrix([control], target, num_qubits, flip_target)

# NEW: CCNOT implementation
def create_ccnot_matrix(controls, target, num_qubits):
    def flip_target(binary_str, target_qubit):
        flipped_list = list(binary_str)
        flipped_list[target_qubit] = '0' if binary_str[target_qubit] == '1' else '1'
        return int("".join(flipped_list), 2)
    return create_controlled_gate_matrix(controls, target, num_qubits, flip_target)

def create_swap_matrix(qubit1, qubit2, num_qubits):
    size = 2**num_qubits
    swap_matrix = np.zeros((size, size), dtype=complex)
    for i in range(size):
        binary_str = format(i, f'0{num_qubits}b')
        if binary_str[qubit1] != binary_str[qubit2]:
            swapped_list = list(binary_str)
            swapped_list[qubit1], swapped_list[qubit2] = swapped_list[qubit2], swapped_list[qubit1]
            j = int("".join(swapped_list), 2)
            swap_matrix[j, i] = 1
        else:
            swap_matrix[i, i] = 1
    return swap_matrix
