import numpy as np
import networkx as nx
from pyquil import Program
from pyquil.gates import Gate, SWAP
from heuristic_function import heuristic_function

def sabre(F = list(), initial_mapping = dict(), distance_matrix = np.matrix, circuit_dag = nx.DiGraph, coupling_graph = nx.Graph):
    decay_parameter = reset_decay_parameter(initial_mapping)
    final_program = Program()
    while len(F) > 0:
        execute_gate_list = list()
        for gate_details in F:
            if is_gate_executable(gate_details, initial_mapping, coupling_graph):
                execute_gate_list.append(gate_details)
                decay_parameter = reset_decay_parameter(initial_mapping)

        if len(execute_gate_list) > 0:
            for gate_details in execute_gate_list:
                F.remove(gate_details)
                final_program.inst(gate_details[0])
                for successor_details in circuit_dag.successors(gate_details):
                    successor_gate = successor_details[0]
                    successor_qubits = set(successor_gate.get_qubits())
                    dependency_found = False
                    for f_gate_details in F:
                        f_gate = f_gate_details[0]
                        f_qubits = set(f_gate.get_qubits())                
                        if successor_qubits.intersection(f_qubits):
                            dependency_found = True
                            break
                    if not dependency_found:
                        F.append(successor_details)
        else:
            for gate_details in F:
                heuristic_score = dict()
                swap_candidate_list = list()
                f_gate = gate_details[0]
                f_qubits = list(f_gate.get_qubits())
                c_l_qubit, t_l_qubit = f_qubits[0], f_qubits[1]
                c_l_qubit_neighbours, t_l_qubit_neighbours = get_physical_qubit_neighbours(c_l_qubit, t_l_qubit, initial_mapping, coupling_graph)
                for c_l_neighbour in c_l_qubit_neighbours:
                    swap_candidate_list.append(SWAP(c_l_qubit, c_l_neighbour))
                for t_l_qubit_neighbour in t_l_qubit_neighbours:
                    swap_candidate_list.append(SWAP(t_l_qubit, t_l_qubit_neighbour))
                for swap_gate in swap_candidate_list:
                    temp_mapping = update_coupling_graph(swap_gate, initial_mapping, coupling_graph)
                    swap_gate_score = heuristic_function(F, circuit_dag, temp_mapping, distance_matrix, swap_gate, decay_parameter)
                    heuristic_score.update({swap_gate: swap_gate_score})
                all_scores = list(heuristic_score.values())
                min_score = min(all_scores)
                min_score_swap_gate = swap_candidate_list[all_scores.index(min_score)]
                final_program.inst(min_score_swap_gate)
                initial_mapping = update_coupling_graph(min_score_swap_gate, initial_mapping, coupling_graph)
                update_decay_parameter(min_score_swap_gate, decay_parameter)
            # F = [] #needs to be removed
    return final_program, initial_mapping

def is_gate_executable(gate_details = (Gate, int), initial_mapping = dict(), coupling_graph = nx.Graph):
    gate = gate_details[0]
    gate_qubits = list(gate.get_qubits())
    l_qubit1, l_qubit2 = gate_qubits[0], gate_qubits[1]
    p_qubit1, p_qubit2 = initial_mapping.get(l_qubit1), initial_mapping.get(l_qubit2)
    if coupling_graph.has_edge(p_qubit1, p_qubit2):
        return True
    return False

def get_physical_qubit_neighbours(c_l_qubit, t_l_qubit, initial_mapping = dict(), coupling_graph = nx.Graph):
    c_l_qubit_neighbours, t_l_qubit_neighbours = list(), list()
    c_p_qubit, t_p_qubit = initial_mapping.get(c_l_qubit), initial_mapping.get(t_l_qubit)
    c_p_qubit_neighbours, t_p_qubit_neighbours = list(coupling_graph.neighbors(c_p_qubit)), list(coupling_graph.neighbors(t_p_qubit))
    logical_qubits = list(initial_mapping.keys())
    physical_qubits = list(initial_mapping.values())
    for qubit in c_p_qubit_neighbours:
        c_l_qubit_neighbours.append(logical_qubits[physical_qubits.index(qubit)])    
    for qubit in t_p_qubit_neighbours:
        t_l_qubit_neighbours.append(logical_qubits[physical_qubits.index(qubit)])
    return c_l_qubit_neighbours, t_l_qubit_neighbours

def update_coupling_graph(swap_gate = Gate, initial_mapping = dict(), coupling_graph = nx.Graph):
    temp_mapping = initial_mapping.copy()
    swap_qubits = list(swap_gate.get_qubits())
    p_qubit_1, p_qubit_2 = initial_mapping.get(swap_qubits[0]), initial_mapping.get(swap_qubits[1])
    p_qubit_1, p_qubit_2 = p_qubit_2, p_qubit_1
    temp_mapping.update({swap_qubits[0]: p_qubit_1, swap_qubits[1]: p_qubit_2})
    return temp_mapping

def update_decay_parameter(min_score_swap_gate = Gate, decay_parameter = list()):
    min_score_swap_qubits = list(min_score_swap_gate.get_qubits())
    decay_parameter[min_score_swap_qubits[0]] = decay_parameter[min_score_swap_qubits[0]] + 0.001
    decay_parameter[min_score_swap_qubits[1]] = decay_parameter[min_score_swap_qubits[1]] + 0.001

def reset_decay_parameter(initial_mapping: dict):
    return [0.001] * len(list(initial_mapping.keys()))
