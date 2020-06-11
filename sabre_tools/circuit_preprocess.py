from pyquil import Program
from networkx import Graph, DiGraph, floyd_warshall_numpy

import random

def preprocess_input_circuit(circuit: Program):
    circuit_dag = get_circuit_dag(circuit=circuit)
    front_layer_gates = initialize_front_layer(circuit_dag=circuit_dag)
    return front_layer_gates, circuit_dag

def get_circuit_dag(circuit: Program):
    circuit_dag_mapping = get_dag_mapping(circuit.instructions)
    circuit_dag = create_dag(circuit_dag_mapping)
    return circuit_dag

def get_distance_matrix(coupling_graph: Graph):
    distance_matrix = floyd_warshall_numpy(coupling_graph)
    return distance_matrix

def get_initial_mapping(circuit: Program, coupling_graph: Graph):
    initial_mapping = dict()
    physical_qubits = list(coupling_graph.nodes())
    logical_qubits = list(circuit.get_qubits())
    random.shuffle(physical_qubits)
    for logical_qubit, physical_qubit in zip(logical_qubits, physical_qubits):
        initial_mapping.update({logical_qubit: physical_qubit})
    return initial_mapping

def initialize_front_layer(circuit_dag: Graph):
    front_layer_gates = list()
    for node in circuit_dag.nodes():
        if circuit_dag.in_degree(node) == 0:
            front_layer_gates.append(node)
    return front_layer_gates

def get_dag_mapping(instructions):
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

def create_dag(dag_mapping: dict):
    circuit_dag = DiGraph()
    for mapping in dag_mapping.keys():
        v_index = mapping[1]
        v = mapping[2]
        u_index = dag_mapping.get(mapping)[0]
        u = dag_mapping.get(mapping)[1]
        circuit_dag.add_edge((u, u_index), (v, v_index))

    return circuit_dag