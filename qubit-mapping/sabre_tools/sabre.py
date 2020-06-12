from networkx import Graph, DiGraph
from pyquil import Program
from pyquil.gates import Gate, SWAP
from sabre_tools.heuristic_function import heuristic_function
from typing import Union

import numpy as np

class SABRE():
    def __init__(self, distance_matrix: np.matrix, coupling_graph: Graph) -> None:
        """Initialize an instance of SABRE with distance matrix and coupling graph

        Args:
            distance_matrix (np.matrix): represents qubit connections from given coupling graph
            coupling_graph (Graph): represents qubit connections based on the underlying chip architecture
        """             
        self.distance_matrix = distance_matrix
        self.coupling_graph = coupling_graph

    def execute_sabre_algorithm(self, front_layer_gates: list, qubit_mapping: dict, circuit_dag: DiGraph) -> Union[Program, dict]:
        """Applies SABRE algorithm proposed in "Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices"
            by Gushu Li, Yufei Ding, and Yuan Xie (https://arxiv.org/pdf/1809.02573.pdf). This function returns 
            final program with SWAPs inserted and a mapping with qubit dependencies resolved

        Args:
            front_layer_gates (list): list of gates that have no unexecuted predecessors in the DAG
            qubit_mapping (dict): a dictionary containing logical to physical qubit mapping
            circuit_dag (DiGraph): a directed acyclic graph where each vertex represents a gate in the 
                                    input circuit and the edges represent the qubit dependencies of a gate on the other

        Returns:
            Union[Program, dict]: final program with SWAPs inserted and a mapping with qubit dependencies resolved
        """        
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
                        

    def initialize_decay_parameter(self, qubit_mapping: dict) -> list:
        """Initializes decay parameter for each logical qubit present in qubit mapping. This parameter
        is required to determine if a SWAP acting on 2 qubits must be selected to insertion into the program

        Args:
            qubit_mapping (dict): logical to physical qubit mapping

        Returns:
            list: decay parameters for each logical qubit in the mapping
        """        
        return [0.001] * len(list(qubit_mapping.keys()))

    def is_gate_executable(self, gate: Gate, qubit_mapping: dict) -> bool:
        """Determines if a 2 qubut gate is executable, i.e., whether the gate acts on qubits which are connected in
        the coupling graph

        Args:
            gate (Gate): input 2 qubit gate
            qubit_mapping (dict): logical to physical qubit mapping

        Returns:
            bool: True if the input gate acts on connected qubits. False otherwise
        """         
        gate_qubits = list(gate.get_qubits())
        logical_qubit_1, logical_qubit_2 = gate_qubits[0], gate_qubits[1]
        physical_qubit_1, physical_qubit_2 = qubit_mapping.get(logical_qubit_1), qubit_mapping.get(logical_qubit_2)
        return self.coupling_graph.has_edge(physical_qubit_1, physical_qubit_2)

    def is_dependent_on_successors(self, successor_details: tuple, front_layer_gates: list) -> bool:
        """Determines if successors of an executed gate have qubit dependencies with gates in the front layer

        Args:
            successor_details (tuple): successors of an executed gate
            front_layer_gates (list): list of gate that have no unexecuted predecessors in the DAG

        Returns:
            bool: True if there is a gate in the front layer that is applied on qubits of successors of an executed gate.
                    False otherwise
        """        
        successor_gate = successor_details[0]
        successor_qubits = set(successor_gate.get_qubits())
        
        for f_gate_details in front_layer_gates:
            f_gate = f_gate_details[0]
            f_qubits = set(f_gate.get_qubits())          
            if successor_qubits.intersection(f_qubits):
                return True
        return False

    def get_qubit_neighbours(self, control_logical_qubit: int, target_logical_qubit: int, qubit_mapping: dict) -> Union[list, list]:
        """Returns list of neighbours from qubit mapping for input control and target logical qubits whose corresponding 
            physical qubits are connected by an edge in the coupling graph

        Args:
            control_logical_qubit (int): logical control qubit of a 2 qubit gate
            target_logical_qubit (int): logical target qubut of a 2 qubit gate
            qubit_mapping (dict): a dictionary containing logical to physical qubit mapping

        Returns:
            Union[list, list]: list of neighbours for control and target logical qubits whose corresponding physical qubits are 
                                connected by an edge in the coupling graph
        """        
        control_physical_qubit, target_physical_qubit = self.get_physical_qubit(control_logical_qubit, target_logical_qubit, qubit_mapping)
        control_physical_qubit_neighbours, target_physical_qubit_neighbours = self.get_physical_qubit_neighbours(control_physical_qubit, target_physical_qubit)

        control_logical_qubit_neighbours = self.get_logical_qubit_neighbours(control_physical_qubit_neighbours, qubit_mapping)
        target_logical_qubit_neighbours = self.get_logical_qubit_neighbours(target_physical_qubit_neighbours, qubit_mapping)

        return control_logical_qubit_neighbours, target_logical_qubit_neighbours

    def get_physical_qubit(self, control_logical_qubit: int, target_logical_qubit: int, qubit_mapping: dict) -> Union[int, int]:
        """Returns corresponding physical qubits from qubit mapping for input logical qubits of a 2 qubit gate

        Args:
            control_logical_qubit (int): logical control qubit of a 2 qubit gate
            target_logical_qubit (int): logical target qubut of a 2 qubit gate
            qubit_mapping (dict): a dictionary containing logical to physical qubit mapping

        Returns:
            Union[int, int]: corresponding physical qubits for input logical qubits obtained from qubit mapping
        """        
        return qubit_mapping.get(control_logical_qubit), qubit_mapping.get(target_logical_qubit)

    def get_physical_qubit_neighbours(self, control_physical_qubit: int, target_logical_qubit: int) -> Union[list, list]:
        """Returns neighbours from coupling graph for input physical qubits

        Args:
            control_physical_qubit (int): physical control qubit of a 2 qubit gate
            target_logical_qubit (int): physical target qubut of a 2 qubit gate

        Returns:
            Union[list, list]: list of physical qubit neighbours for input physical control and target qubits
        """              
        return self.coupling_graph.neighbors(control_physical_qubit), self.coupling_graph.neighbors(target_logical_qubit)

    def get_logical_qubit_neighbours(self, physical_qubit_neighbours: list, qubit_mapping: dict) -> list:
        """Returns corresponding logical qubits from qubit mapping for input physical qubits

        Args:
            physical_qubit_neighbours (list): physical qubits whose corresponding logical qubits need to be obtained
            qubit_mapping (dict): a dictionary containing logical to physical qubit mapping

        Returns:
            list: list of corresponding logical qubits for input physical qubits obtained from qubit mapping
        """             
        logical_qubits = list(qubit_mapping.keys())
        physical_qubits = list(qubit_mapping.values())
        logical_qubit_neighbours = list()

        for qubit in physical_qubit_neighbours:
            logical_qubit_neighbours.append(logical_qubits[physical_qubits.index(qubit)])
        return logical_qubit_neighbours

    def update_initial_mapping(self, swap_gate: Gate, qubit_mapping: dict) -> dict:
        """Update qubit mapping between logical and physical if a SWAP gate is inserted in the program

        Args:
            swap_gate (Gate): a pyquil SWAP gate
            qubit_mapping (dict): a dictionary containing logical to physical qubit mapping

        Returns:
            dict: updated qubit mapping
        """        
        temp_mapping = qubit_mapping.copy()
        swap_qubits = list(swap_gate.get_qubits())
        p_qubit_1, p_qubit_2 = qubit_mapping.get(swap_qubits[0]), qubit_mapping.get(swap_qubits[1])
        p_qubit_1, p_qubit_2 = p_qubit_2, p_qubit_1
        temp_mapping.update({swap_qubits[0]: p_qubit_1, swap_qubits[1]: p_qubit_2})
        return temp_mapping

    def find_min_score_swap_gate(self, heuristic_score: dict, swap_candidate_list: list) -> Gate:
        """Finds the SWAP gate with the minimum score for the heuristic function

        Args:
            heuristic_score (dict): value of the heuristic function for each possible SWAP gate
            swap_candidate_list (list): list of candidate SWAP gates that can be inserted in the program

        Returns:
            Gate: SWAP gate with minimum score for heuristic function
        """        
        all_scores = list(heuristic_score.values())
        min_score = min(all_scores)
        min_score_swap_gate = swap_candidate_list[all_scores.index(min_score)]
        return min_score_swap_gate

    def update_decay_parameter(self, min_score_swap_gate: Gate, decay_parameter: list) -> list:
        """Updates decay parameters for qubits on which SWAP gate with the minimum heuristic score is applied

        Args:
            min_score_swap_gate (Gate): SWAP gate with the minimum heuristic score
            decay_parameter (list): decay parameter list to be updated

        Returns:
            list: updated decay parameter list
        """        
        min_score_swap_qubits = list(min_score_swap_gate.get_qubits())
        decay_parameter[min_score_swap_qubits[0]] = decay_parameter[min_score_swap_qubits[0]] + 0.001
        decay_parameter[min_score_swap_qubits[1]] = decay_parameter[min_score_swap_qubits[1]] + 0.001
        return decay_parameter

    
    def rewiring_correctness(self, circuit: Program, qubit_mapping: dict) -> dict:
        """Determines if the qubit mapping and SWAP inserted Program obtained from application 
            of SABRE is able to resolve all qubit dependencies. This function can also be used to determine
            if the initial input program requires the use of SABRE

        Args:
            circuit (Program): a pyquil Program
            qubit_mapping (dict): qubit mapping between logical and physical qubits

        Returns:
            dict: an dict object containing the Gate that cannot be executed with the given Program and mapping
                    and the qubits that are not physically connected. An empty dict otherwise. 
        """        
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
            
    def cnot_count(self, circuit: Program) -> int:
        """Counts the number of CNOT gates in the input pyquil Program

        Args:
            circuit (Program): a pyquil Program

        Returns:
            int: number of CNOT gates in the program
        """        
        cnot_count = 0
        for instruction in circuit.instructions:
            if instruction.name == 'CNOT':
                cnot_count = cnot_count + 1
            if instruction.name == 'SWAP':
                cnot_count = cnot_count + 3
        return cnot_count