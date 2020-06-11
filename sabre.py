import numpy as np
from networkx import Graph, DiGraph
from pyquil import Program
from pyquil.gates import Gate, SWAP
from heuristic_function import heuristic_function

class SABRE():
    def __init__(self, distance_matrix: np.matrix, coupling_graph: Graph):
        self.distance_matrix = distance_matrix
        self.coupling_graph = coupling_graph

    def execute_sabre_algorithm(self, front_layer_gates = list, qubit_mapping = dict, circuit_dag = DiGraph):
        decay_parameter = self.initialize_decay_parameter(qubit_mapping)
        final_circuit = Program()

        while len(front_layer_gates) > 0:
            execute_gate_list = list()
            for gate_details in front_layer_gates:
                if self.is_gate_executable(gate_details[0], qubit_mapping):
                    execute_gate_list.append(gate_details)
                    decay_parameter = self.initialize_decay_parameter(qubit_mapping)

            if len(execute_gate_list) > 0:
                for gate_details in execute_gate_list:
                    front_layer_gates.remove(gate_details)
                    final_circuit.inst(gate_details[0])
                    for successor_details in circuit_dag.successors(gate_details):
                        dependency_found = self.is_dependent_on_successors(successor_details, front_layer_gates)
                        if not dependency_found:
                            front_layer_gates.append(successor_details)
            else:
                for gate_details in front_layer_gates:
                    heuristic_score = dict()
                    swap_candidate_list = list()
                    f_gate = gate_details[0]
                    f_qubits = list(f_gate.get_qubits())
                    control_logical_qubit, target_logical_qubit = f_qubits[0], f_qubits[1]
                    control_logical_qubit_neighbours, target_logical_qubit_neighbours = self.get_qubit_neighbours(control_logical_qubit, target_logical_qubit, qubit_mapping)
                    for control_logical_qubit_neighbour in control_logical_qubit_neighbours:
                        swap_candidate_list.append(SWAP(control_logical_qubit, control_logical_qubit_neighbour))
                    for target_logical_qubit_neighbour in target_logical_qubit_neighbours:
                        swap_candidate_list.append(SWAP(target_logical_qubit, target_logical_qubit_neighbour))
                    for swap_gate in swap_candidate_list:
                        temp_mapping = self.update_initial_mapping(swap_gate, qubit_mapping)
                        swap_gate_score = heuristic_function(front_layer_gates, circuit_dag, temp_mapping, self.distance_matrix, swap_gate, decay_parameter)
                        heuristic_score.update({swap_gate: swap_gate_score})
                    min_score_swap_gate = self.find_min_score_swap_gate(heuristic_score, swap_candidate_list)
                    final_circuit.inst(min_score_swap_gate)
                    qubit_mapping = self.update_initial_mapping(min_score_swap_gate, qubit_mapping)
                    decay_parameter = self.update_decay_parameter(min_score_swap_gate, decay_parameter)
        return final_circuit, qubit_mapping
                        

    def initialize_decay_parameter(self, qubit_mapping: dict):
        return [0.001] * len(list(qubit_mapping.keys()))

    def is_gate_executable(self, gate = Gate, qubit_mapping = dict()):
        gate_qubits = list(gate.get_qubits())
        logical_qubit_1, logical_qubit_2 = gate_qubits[0], gate_qubits[1]
        physical_qubit_1, physical_qubit_2 = qubit_mapping.get(logical_qubit_1), qubit_mapping.get(logical_qubit_2)
        return self.coupling_graph.has_edge(physical_qubit_1, physical_qubit_2)

    def is_dependent_on_successors(self, successor_details: tuple, front_layer_gates: list):
        successor_gate = successor_details[0]
        successor_qubits = set(successor_gate.get_qubits())
        
        for f_gate_details in front_layer_gates:
            f_gate = f_gate_details[0]
            f_qubits = set(f_gate.get_qubits())          
            if successor_qubits.intersection(f_qubits):
                return True
        return False

    def get_qubit_neighbours(self, control_logical_qubit, target_logical_qubit, qubit_mapping = dict):
        control_physical_qubit, target_physical_qubit = self.get_physical_qubit(control_logical_qubit, target_logical_qubit, qubit_mapping)
        control_physical_qubit_neighbours, target_physical_qubit_neighbours = self.get_physical_qubit_neighbours(control_physical_qubit, target_physical_qubit)

        control_logical_qubit_neighbours = self.get_logical_qubit_neighbours(control_physical_qubit_neighbours, qubit_mapping)
        target_logical_qubit_neighbours = self.get_logical_qubit_neighbours(target_physical_qubit_neighbours, qubit_mapping)

        return control_logical_qubit_neighbours, target_logical_qubit_neighbours

    def get_physical_qubit(self, control_logical_qubit, target_logical_qubit, qubit_mapping = dict):
        return qubit_mapping.get(control_logical_qubit), qubit_mapping.get(target_logical_qubit)

    def get_physical_qubit_neighbours(self, control_physical_qubit, target_logical_qubit):
        return self.coupling_graph.neighbors(control_physical_qubit), self.coupling_graph.neighbors(target_logical_qubit)

    def get_logical_qubit_neighbours(self, physical_qubit_neighbours, qubit_mapping: dict):
        logical_qubits = list(qubit_mapping.keys())
        physical_qubits = list(qubit_mapping.values())
        logical_qubit_neighbours = list()

        for qubit in physical_qubit_neighbours:
            logical_qubit_neighbours.append(logical_qubits[physical_qubits.index(qubit)])
        return logical_qubit_neighbours

    def update_initial_mapping(self, swap_gate = Gate, qubit_mapping = dict()):
        temp_mapping = qubit_mapping.copy()
        swap_qubits = list(swap_gate.get_qubits())
        p_qubit_1, p_qubit_2 = qubit_mapping.get(swap_qubits[0]), qubit_mapping.get(swap_qubits[1])
        p_qubit_1, p_qubit_2 = p_qubit_2, p_qubit_1
        temp_mapping.update({swap_qubits[0]: p_qubit_1, swap_qubits[1]: p_qubit_2})
        return temp_mapping

    def find_min_score_swap_gate(self, heuristic_score, swap_candidate_list):
        all_scores = list(heuristic_score.values())
        min_score = min(all_scores)
        min_score_swap_gate = swap_candidate_list[all_scores.index(min_score)]
        return min_score_swap_gate

    def update_decay_parameter(self, min_score_swap_gate = Gate, decay_parameter = list()):
        min_score_swap_qubits = list(min_score_swap_gate.get_qubits())
        decay_parameter[min_score_swap_qubits[0]] = decay_parameter[min_score_swap_qubits[0]] + 0.001
        decay_parameter[min_score_swap_qubits[1]] = decay_parameter[min_score_swap_qubits[1]] + 0.001
        return decay_parameter

    
    def rewiring_correctness(self, circuit: Program, qubit_mapping: dict):
        forbidden_gate = dict()
        temp_mapping = qubit_mapping.copy()
        for instruction in circuit.instructions:
            if instruction.name == 'SWAP':
                temp_mapping = self.update_initial_mapping(instruction, temp_mapping)
            if not self.is_gate_executable(instruction, temp_mapping):
                gate_qubits = list(instruction.get_qubits())
                logical_qubit1, logical_qubit2 = gate_qubits[0], gate_qubits[1]
                p_qubit1, p_qubit2 = temp_mapping.get(logical_qubit1), temp_mapping.get(logical_qubit2)
                forbidden_gate.update({instruction: (p_qubit1, p_qubit2)})

        return forbidden_gate
            
    def cnot_count(self, circuit: Program):
        cnot_count = 0
        for instruction in circuit.instructions:
            if instruction.name == 'CNOT':
                cnot_count = cnot_count + 1
            if instruction.name == 'SWAP':
                cnot_count = cnot_count + 3
        return cnot_count

        

                    

# def sabre(front_layer_gates = list(), qubit_mapping = dict(), distance_matrix = np.matrix, circuit_dag = nx.DiGraph, coupling_graph = nx.Graph):
    
#         else:
#             for gate_details in front_layer_gates:
#                 heuristic_score = dict()
#                 swap_candidate_list = list()
#                 f_gate = gate_details[0]
#                 f_qubits = list(f_gate.get_qubits())
#                 c_l_qubit, t_l_qubit = f_qubits[0], f_qubits[1]
#                 c_l_qubit_neighbours, t_l_qubit_neighbours = get_physical_qubit_neighbours(c_l_qubit, t_l_qubit, qubit_mapping, coupling_graph)
#                 for c_l_neighbour in c_l_qubit_neighbours:
#                     swap_candidate_list.append(SWAP(c_l_qubit, c_l_neighbour))
#                 for t_l_qubit_neighbour in t_l_qubit_neighbours:
#                     swap_candidate_list.append(SWAP(t_l_qubit, t_l_qubit_neighbour))
#                 for swap_gate in swap_candidate_list:
#                     temp_mapping = update_initial_mapping(swap_gate, qubit_mapping, coupling_graph)
#                     swap_gate_score = heuristic_function(front_layer_gates, circuit_dag, temp_mapping, distance_matrix, swap_gate, decay_parameter)
#                     heuristic_score.update({swap_gate: swap_gate_score})
#                 all_scores = list(heuristic_score.values())
#                 min_score = min(all_scores)
#                 min_score_swap_gate = swap_candidate_list[all_scores.index(min_score)]
#                 final_circuit.inst(min_score_swap_gate)
#                 qubit_mapping = update_initial_mapping(min_score_swap_gate, qubit_mapping, coupling_graph)
#                 update_decay_parameter(min_score_swap_gate, decay_parameter)
#     return final_circuit, qubit_mapping

# def update_decay_parameter(min_score_swap_gate = Gate, decay_parameter = list()):
#     min_score_swap_qubits = list(min_score_swap_gate.get_qubits())
#     decay_parameter[min_score_swap_qubits[0]] = decay_parameter[min_score_swap_qubits[0]] + 0.001
#     decay_parameter[min_score_swap_qubits[1]] = decay_parameter[min_score_swap_qubits[1]] + 0.001