from networkx import DiGraph
from pyquil.gates import Gate
import numpy as np

def heuristic_function(F: list, circuit_dag: DiGraph, initial_mapping: dict, distance_matrix: np.matrix, swap_gate: Gate, decay_parameter: list) -> float:
    """Computes a heuristic cost function that is used to rate a candidate SWAP to determine whether the SWAP gate can be inserted in a program to resolve
        qubit dependencies

    Args:
        F (list): list of gates that have no unexecuted predecessors in the DAG
        circuit_dag (DiGraph): a directed acyclic graph representing qubit dependencies between
                                gates
        initial_mapping (dict): a dictionary containing logical to physical qubit mapping
        distance_matrix (np.matrix): represents qubit connections from given coupling graph
        swap_gate (Gate): candidate SWAP gate
        decay_parameter (list): decay parameters for each logical qubit in the mapping

    Returns:
        float: heuristic score for the candidate SWAP gate
    """                  
    E = create_extended_successor_set(F, circuit_dag)
    min_score_swap_qubits = list(swap_gate.get_qubits())
    size_E = len(E)
    size_F = len(F)
    W = 0.5
    max_decay = max(decay_parameter[min_score_swap_qubits[0]], decay_parameter[min_score_swap_qubits[1]])
    f_distance = 0
    e_distance = 0
    for gate_details in F:
        f_distance += calculate_distance(gate_details, distance_matrix, initial_mapping)
    
    for gate_details in E:
        e_distance += calculate_distance(gate_details, distance_matrix, initial_mapping)

    f_distance = f_distance / size_F
    e_distance = W * (e_distance / size_E)
    H = max_decay * (f_distance + e_distance)
    return H

def calculate_distance(gate_details: tuple, distance_matrix: np.matrix, initial_mapping: dict) -> float:
    """Obtains the value of the distance matrix for physical qubits corresponding to the logical qubits of the
        given gate

    Args:
        gate_details (tuple): Gate object
        distance_matrix (np.matrix): represents qubit connections from given coupling graph
        initial_mapping (dict): a dictionary containing logical to physical qubit mapping

    Returns:
        float: value of the distance matrix for physical qubits corresponding to the logical qubits of the
                given gate
    """    
    gate = gate_details[0]
    qubits = list(gate.get_qubits())
    return distance_matrix[initial_mapping.get(qubits[0]), initial_mapping.get(qubits[1])]

def create_extended_successor_set(F: list, circuit_dag: DiGraph) -> list:
    """Creates an extended set which contains some closet successors of the gates from F in the DAG

    Args:
        F (list): list of gates that have no unexecuted predecessors in the DAG
        circuit_dag (DiGraph): a directed acyclic graph representing qubit dependencies between
                                gates

    Returns:
        list: an extended set which contains some closet successors of the gates from F in the DAG
    """    
    E = list()
    for gate in  F:
        for gate_successor in circuit_dag.successors(gate):
            if len(E) <= 20:
                E.append(gate_successor)
    return E