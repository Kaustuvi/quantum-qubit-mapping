from pyquil import Program
from networkx import Graph, DiGraph, floyd_warshall_numpy
from typing import Union

import random
import numpy as np

def preprocess_input_circuit(circuit: Program) -> Union[list, DiGraph]:
    """Preprocesses input pyquil circuit to return a directed acyclic graph
    and a list of gates that have no unexecuted predecessors in the DAG

    Args:
        circuit (Program): input pyquil circuit

    Returns:
        Union[list, DiGraph]: list of gates that have no qubit depedency on any other gate
                                and a directed acyclic graph
    """    
    circuit_dag = get_circuit_dag(circuit=circuit)
    front_layer_gates = initialize_front_layer(circuit_dag=circuit_dag)
    return front_layer_gates, circuit_dag

def get_circuit_dag(circuit: Program) -> DiGraph:
    """Scans the input pyquil circuit and returns a directed acyclic 
    graph where each vertex represents a gate in the input circuit and 
    the edges represent the qubit dependencies of a gate on the other

    Args:
        circuit (Program): input pyquil program

    Returns:
        DiGraph: a directed acyclic graph where each vertex represents a gate in
                the input circuit and the edges represent the qubit dependencies of a gate on 
                the other
    """    
    circuit_dag_mapping = get_dag_mapping(circuit.instructions)
    circuit_dag = create_dag(circuit_dag_mapping)
    return circuit_dag

def get_distance_matrix(coupling_graph: Graph) -> np.matrix:
    """Computes the distance matrix from the input qubit coupling graph

    Args:
        coupling_graph (Graph): input graph representing qubit connections

    Returns:
        np.matrix: distance matrix computed from coupling graph using Floyd Warshall Algorithm
    """    
    distance_matrix = floyd_warshall_numpy(coupling_graph)
    return distance_matrix

def get_initial_mapping(circuit: Program, coupling_graph: Graph) -> dict:
    """Computes a random logical to physical qubit mapping using qubits
    in the input pyquil program and coupling graph

    Args:
        circuit (Program): input pyquil program
        coupling_graph (Graph): coupling graph representing qubit connections

    Returns:
        dict: a dictionary containing a random logical to physical qubit mapping
    """    
    initial_mapping = dict()
    physical_qubits = list(coupling_graph.nodes())
    logical_qubits = list(circuit.get_qubits())
    random.shuffle(physical_qubits)
    for logical_qubit, physical_qubit in zip(logical_qubits, physical_qubits):
        initial_mapping.update({logical_qubit: physical_qubit})
    return initial_mapping

def initialize_front_layer(circuit_dag: Graph) -> list:
    """Finds gates that have no unexecuted predecessors in the DAG

    Args:
        circuit_dag (Graph): a directed acyclic graph representing qubit dependencies between
                                gates

    Returns:
        list: returns list of gates that have no unexecuted predecessors in the DAG
    """    
    front_layer_gates = list()
    for node in circuit_dag.nodes():
        if circuit_dag.in_degree(node) == 0:
            front_layer_gates.append(node)
    return front_layer_gates

def get_dag_mapping(instructions: list) -> dict:
    """Scans 2 qubit pyquil gate instructions to compute a mapping between two gates representing 
    qubit dependencies. This mapping is used to construct a directed acyclic graph

    Args:
        instructions (list): pyquil gate instructions

    Returns:
        dict: mapping representing qubit dependencies between two qubit gates
    """    
    circuit_dag_mapping = dict()
    circuit_instructions = enumerate(instructions)
    for curr_gate_index, curr_gate in circuit_instructions:
        curr_gate_qubits = list(curr_gate.get_qubits())
        if len(curr_gate_qubits) == 2:
            for curr_gate_qubit in curr_gate_qubits:
                current_instructions = enumerate(instructions[:curr_gate_index])
                for prev_gate_index, prev_gate in current_instructions:
                    prev_gate_qubits = prev_gate.get_qubits()
                    if curr_gate_qubit in prev_gate_qubits:
                        circuit_dag_mapping.update({(curr_gate_qubit, curr_gate_index, curr_gate): (prev_gate_index, prev_gate)})

    return circuit_dag_mapping

def create_dag(dag_mapping: dict) -> DiGraph:
    """Creates a directed acyclic graph from a mapping between 2 qubit gates that have
    qubit dependencies

    Args:
        dag_mapping (dict): mapping representing qubit dependencies between 2 qubit gates

    Returns:
        DiGraph: a directed acyclic graph that represents qubit dependencies
    """    
    circuit_dag = DiGraph()
    for mapping in dag_mapping.keys():
        v_index = mapping[1]
        v = mapping[2]
        u_index = dag_mapping.get(mapping)[0]
        u = dag_mapping.get(mapping)[1]
        circuit_dag.add_edge((u, u_index), (v, v_index))

    return circuit_dag