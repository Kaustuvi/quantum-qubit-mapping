from pyquil import Program
from pyquil.gates import CNOT, Gate, H
import networkx as nx
from networkx.algorithms.shortest_paths import floyd_warshall_numpy
import matplotlib.pyplot as plt
import random

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
qubit_dependencies = dict()
gate_mapping = dict()
circuit_dag = nx.DiGraph()
circuit_instructions = original_circuit.instructions
for index, curr_gate in enumerate(circuit_instructions):
    if len(curr_gate.qubits) == 2:
        gate_mapping.update({curr_gate: "g"+str(index)})
        for curr_gate_qubit in curr_gate.qubits:
            for prev_gate in circuit_instructions[:index]:
                if curr_gate_qubit in prev_gate.qubits:
                    v = gate_mapping.get(curr_gate)
                    u = gate_mapping.get(prev_gate)
                    qubit_dependencies.update({(curr_gate_qubit, v): u})
                    
for qubit_mapping in qubit_dependencies.keys():
    v = qubit_mapping[1]
    u = qubit_dependencies.get(qubit_mapping)
    # print("For q" + str(qubit_mapping[0]) + " " + str(v) + " -> " + str(u))
    circuit_dag.add_edge(u, v)

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



