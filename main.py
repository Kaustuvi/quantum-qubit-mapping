from pyquil import Program
from pyquil.gates import CNOT, Gate, H, SWAP
import networkx as nx
from networkx.algorithms.shortest_paths import floyd_warshall_numpy
import matplotlib.pyplot as plt
import random

from heuristic_function import heuristic_function
from sabre import sabre

#inputs
original_circuit = Program()
original_circuit.inst(CNOT(0, 1))
original_circuit.inst(CNOT(2, 3))
original_circuit.inst(CNOT(1, 3))
original_circuit.inst(CNOT(1, 2))
original_circuit.inst(CNOT(2, 3))
original_circuit.inst(CNOT(0, 3)) #logical qubits

coupling_graph = nx.Graph()
coupling_graph.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)]) #nodes are physical qubits

physical_qubits = list(coupling_graph.nodes())
logical_qubits = list(original_circuit.get_qubits())

#pre-processing - distance matrix
distance_matrix = floyd_warshall_numpy(coupling_graph)

# pre-processing - circuit DAG
circuit_dag_mapping = dict()
circuit_dag = nx.DiGraph()
circuit_instructions = original_circuit.instructions
for curr_gate_index, curr_gate in enumerate(circuit_instructions):
    curr_gate_qubits = list(curr_gate.get_qubits())
    if len(curr_gate_qubits) == 2:
        for curr_gate_qubit in curr_gate_qubits:
            for prev_gate_index, prev_gate in enumerate(circuit_instructions[:curr_gate_index]):
                prev_gate_qubits = list(prev_gate.get_qubits())
                if curr_gate_qubit in prev_gate_qubits:
                    circuit_dag_mapping.update({(curr_gate_qubit, curr_gate_index, curr_gate): (prev_gate_index, prev_gate)})
                    

for mapping in circuit_dag_mapping.keys():
    v_index = mapping[1]
    v = mapping[2]
    u_index = circuit_dag_mapping.get(mapping)[0]
    u = circuit_dag_mapping.get(mapping)[1]
    circuit_dag.add_edge((u, u_index), (v, v_index))

# nx.draw_networkx(circuit_dag, with_labels=True)
# plt.show()

#preprocessing - front layer initialization
F = list()
for node in circuit_dag.nodes():
    if circuit_dag.in_degree(node) == 0:
        F.append(node)

# preprocessing - initial mapping
initial_mapping = dict()
random.shuffle(physical_qubits)
for l_qubit, p_qubit in zip(logical_qubits, physical_qubits):
    initial_mapping.update({l_qubit: p_qubit})

# heuristic_function(F=F, circuit_dag=circuit_dag, initial_mapping=initial_mapping, distance_matrix=distance_matrix, swap_gate=SWAP(0,1))
final_program = sabre(F = F, initial_mapping = initial_mapping, distance_matrix = distance_matrix, circuit_dag = circuit_dag, coupling_graph = coupling_graph)
print(final_program)



