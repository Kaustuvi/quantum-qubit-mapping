from networkx import DiGraph
import numpy as np
from pyquil.gates import Gate

def heuristic_function(F = list(), circuit_dag = DiGraph, initial_mapping = dict(), distance_matrix = np.matrix, swap_gate = Gate, decay_parameter = list()):
    E = create_extended_successor_set(F, circuit_dag)
    min_score_swap_qubits = list(swap_gate.get_qubits())
    size_E = len(E)
    size_F = len(F)
    W = 0.5
    max_decay = max(decay_parameter[min_score_swap_qubits[0]], decay_parameter[min_score_swap_qubits[1]])
    f_distance = 0
    e_distance = 0
    for gate_details in F:
        f_gate = gate_details[0]
        f_qubits = list(f_gate.get_qubits())
        f_distance += distance_matrix[initial_mapping.get(f_qubits[0]), initial_mapping.get(f_qubits[1])]
    
    for gate_details in E:
        e_gate = gate_details[0]
        e_qubits = list(e_gate.get_qubits())
        e_distance += distance_matrix[initial_mapping.get(e_qubits[0]), initial_mapping.get(e_qubits[1])]

    f_distance = f_distance / size_F
    e_distance = W * (e_distance / size_E)
    H = max_decay * (f_distance + e_distance)
    return H

def create_extended_successor_set(F, circuit_dag):
    E = list()
    for gate in  F:
        for gate_successor in circuit_dag.successors(gate):
            if len(E) <= 20:
                E.append(gate_successor)
    return E