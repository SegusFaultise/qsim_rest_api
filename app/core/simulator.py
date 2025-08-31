import numpy as np
from ..schemas import CircuitCreate

def create_rotation_matrix(axis: str, theta: float) -> np.ndarray:
    """
    <summary>
    Creates a 2x2 unitary rotation matrix for a single qubit.
    </summary>
    <param name="axis" type="str">The axis of rotation ('X', 'Y', or 'Z').</param>
    <param name="theta" type="float">The angle of rotation in radians.</param>
    <returns type="np.ndarray">The 2x2 numpy array representing the rotation gate.</returns>
    <exception cref="ValueError">Raised if an invalid axis is specified.</exception>
    """
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
    <summary>
    Runs a full quantum circuit simulation by initializing a state vector and applying
    each gate sequentially. This is the primary CPU-intensive task of the application.
    </summary>
    <param name="circuit" type="CircuitCreate">A Pydantic schema object containing the circuit's qubits and gate definitions.</param>
    <returns type="dict">A dictionary containing the final state probabilities, mapping state strings to their probability.</returns>
    """
    num_qubits = circuit.qubits
    state_vector = np.zeros(2**num_qubits, dtype=complex)
    state_vector[0] = 1 + 0j

    for gate_info in circuit.gates:
        gate_name = gate_info.gate.upper()
        gate_matrix = None

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

            target = gate_info.targets[0] if gate_info.targets else gate_info.target
            gate_matrix = create_full_gate_matrix(op_matrix, target, num_qubits)

        elif gate_name in ["RX", "RY", "RZ"]:
            theta = gate_info.parameters.get("theta", 0.0)
            axis = gate_name[-1]
            op_matrix = create_rotation_matrix(axis, theta)
            target = gate_info.targets[0]
            gate_matrix = create_full_gate_matrix(op_matrix, target, num_qubits)

        elif gate_name == "MEASURE":
            continue

        elif gate_name in ["CNOT", "SWAP", "CCNOT"]:
            controls, targets = gate_info.controls, gate_info.targets
            if not targets:
                raise ValueError(f"{gate_name} gate requires at least one target qubit.")

            if gate_name == "CNOT":
                gate_matrix = create_cnot_matrix(controls[0], targets[0], num_qubits)
            elif gate_name == "SWAP":
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
    """
    <summary>
    Constructs the full gate matrix for a single-qubit operation to be applied to a multi-qubit system.
    It uses the tensor (Kronecker) product to expand the 2x2 operator.
    </summary>
    <param name="op_matrix" type="np.ndarray">The 2x2 matrix of the single-qubit gate.</param>
    <param name="target_qubit" type="int">The index of the qubit the gate acts on.</param>
    <param name="num_qubits" type="int">The total number of qubits in the system.</param>
    <returns type="np.ndarray">The (2^n x 2^n) matrix for the entire system.</returns>
    """
    I = np.identity(2, dtype=complex)
    full_matrix = op_matrix if target_qubit == 0 else I
    for qubit in range(1, num_qubits):
        matrix_to_kron = op_matrix if qubit == target_qubit else I
        full_matrix = np.kron(full_matrix, matrix_to_kron)
    return full_matrix

def create_controlled_gate_matrix(controls, target, num_qubits, operation_func):
    """
    <summary>
    A generic helper function for creating controlled-gate matrices (e.g., CNOT, CCNOT).
    It builds a matrix that applies an operation to a target qubit only if all control qubits are in the |1> state.
    </summary>
    <param name="controls" type="list[int]">A list of control qubit indices.</param>
    <param name="target" type="int">The index of the target qubit.</param>
    <param name="num_qubits" type="int">The total number of qubits in the system.</param>
    <param name="operation_func" type="function">A function that takes a binary string and a target qubit index, and returns the resulting integer state.</param>
    <returns type="np.ndarray">The (2^n x 2^n) matrix for the controlled operation.</returns>
    """
    size = 2**num_qubits
    matrix = np.zeros((size, size), dtype=complex)
    for i in range(size):
        binary_str = format(i, f'0{num_qubits}b')
        if all(binary_str[c] == '1' for c in controls):
            j = operation_func(binary_str, target)
            matrix[j, i] = 1
        else:
            matrix[i, i] = 1
    return matrix

def create_cnot_matrix(control, target, num_qubits):
    """
    <summary>
    Creates the matrix for a CNOT (Controlled-NOT) gate.
    </summary>
    <param name="control" type="int">The index of the control qubit.</param>
    <param name="target" type="int">The index of the target qubit.</param>
    <param name="num_qubits" type="int">The total number of qubits in the system.</param>
    <returns type="np.ndarray">The CNOT gate matrix for the specified system size.</returns>
    """
    def flip_target(binary_str, target_qubit):
        flipped_list = list(binary_str)
        flipped_list[target_qubit] = '0' if binary_str[target_qubit] == '1' else '1'
        return int("".join(flipped_list), 2)
    return create_controlled_gate_matrix([control], target, num_qubits, flip_target)

def create_ccnot_matrix(controls, target, num_qubits):
    """
    <summary>
    Creates the matrix for a CCNOT (Toffoli) gate.
    </summary>
    <param name="controls" type="list[int]">The indices of the two control qubits.</param>
    <param name="target" type="int">The index of the target qubit.</param>
    <param name="num_qubits" type="int">The total number of qubits in the system.</param>
    <returns type="np.ndarray">The CCNOT gate matrix for the specified system size.</returns>
    """
    def flip_target(binary_str, target_qubit):
        flipped_list = list(binary_str)
        flipped_list[target_qubit] = '0' if binary_str[target_qubit] == '1' else '1'
        return int("".join(flipped_list), 2)
    return create_controlled_gate_matrix(controls, target, num_qubits, flip_target)

def create_swap_matrix(qubit1, qubit2, num_qubits):
    """
    <summary>
    Creates the matrix for a SWAP gate, which swaps the states of two qubits.
    </summary>
    <param name="qubit1" type="int">The index of the first qubit to swap.</param>
    <param name="qubit2" type="int">The index of the second qubit to swap.</param>
    <param name="num_qubits" type="int">The total number of qubits in the system.</param>
    <returns type="np.ndarray">The SWAP gate matrix for the specified system size.</returns>
    """
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
