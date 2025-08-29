# app/core/simulator.py

import numpy as np
from ..schemas import CircuitCreate

def run_simulation(circuit: CircuitCreate) -> dict:
    """
    Runs a quantum circuit simulation.
    This is the CPU-intensive part of the application.
    """
    num_qubits = circuit.qubits

    # Initialize state to |00...0>
    state_vector = np.zeros(2**num_qubits, dtype=complex)
    state_vector[0] = 1 + 0j

    # Process each gate
    for gate_info in circuit.gates:
        gate_name = gate_info.gate.upper()

        # Single-qubit gates
        if gate_name in ["H", "X", "Y", "Z", "S", "T"]:
            if gate_name == "H": # Hadamard
                op_matrix = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
            elif gate_name == "X": # Pauli-X (NOT)
                op_matrix = np.array([[0, 1], [1, 0]])
            elif gate_name == "Y": # Pauli-Y
                op_matrix = np.array([[0, -1j], [1j, 0]])
            elif gate_name == "Z": # Pauli-Z
                op_matrix = np.array([[1, 0], [0, -1]])
            elif gate_name == "S": # Phase
                op_matrix = np.array([[1, 0], [0, 1j]])
            elif gate_name == "T": # T-gate
                op_matrix = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])

            gate_matrix = create_full_gate_matrix(op_matrix, gate_info.target, num_qubits)
            state_vector = np.dot(gate_matrix, state_vector)

        # Multi-qubit gates
        elif gate_name in ["CNOT", "SWAP"]:
            if gate_info.control is None:
                raise ValueError(f"{gate_name} gate requires a control qubit.")

            control, target = gate_info.control, gate_info.target

            if gate_name == "CNOT":
                gate_matrix = create_cnot_matrix(control, target, num_qubits)
            elif gate_name == "SWAP":
                gate_matrix = create_swap_matrix(control, target, num_qubits)

            state_vector = np.dot(gate_matrix, state_vector)

    # Calculate probabilities from the final state vector amplitudes
    probabilities = np.abs(state_vector)**2

    # Format results into a dictionary
    results = {}
    for i, prob in enumerate(probabilities):
        if prob > 1e-9: # Only show states with non-negligible probability
            state_str = format(i, f'0{num_qubits}b')
            results[state_str] = prob

    return {"states": results} # Renamed for clarity in the final output

# --- Helper functions for matrix construction ---

def create_full_gate_matrix(op_matrix, target_qubit, num_qubits):
    """Creates the full 2^n x 2^n matrix for a single-qubit gate."""
    I = np.identity(2, dtype=complex)

    # Start with the first matrix
    full_matrix = op_matrix if target_qubit == 0 else I

    # Tensor product to build the full matrix
    for qubit in range(1, num_qubits):
        matrix_to_kron = op_matrix if qubit == target_qubit else I
        full_matrix = np.kron(full_matrix, matrix_to_kron)

    return full_matrix

def create_cnot_matrix(control, target, num_qubits):
    """Creates the full 2^n x 2^n CNOT matrix by permuting basis vectors."""
    size = 2**num_qubits
    cnot_matrix = np.zeros((size, size), dtype=complex)

    for i in range(size):
        binary_str = format(i, f'0{num_qubits}b')

        if binary_str[control] == '1':
            flipped_list = list(binary_str)
            flipped_list[target] = '0' if binary_str[target] == '1' else '1'
            j = int("".join(flipped_list), 2)
            cnot_matrix[j, i] = 1
        else:
            cnot_matrix[i, i] = 1

    return cnot_matrix

def create_swap_matrix(qubit1, qubit2, num_qubits):
    """Creates the full 2^n x 2^n SWAP matrix by permuting basis vectors."""
    size = 2**num_qubits
    swap_matrix = np.zeros((size, size), dtype=complex)

    for i in range(size):
        binary_str = format(i, f'0{num_qubits}b')

        # If bits are different, swap them to find the new position
        if binary_str[qubit1] != binary_str[qubit2]:
            swapped_list = list(binary_str)
            swapped_list[qubit1], swapped_list[qubit2] = swapped_list[qubit2], swapped_list[qubit1]
            j = int("".join(swapped_list), 2)
            swap_matrix[j, i] = 1
        else: # If bits are the same, the state maps to itself
            swap_matrix[i, i] = 1

    return swap_matrix
