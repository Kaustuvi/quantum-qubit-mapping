from pyquil import Program
from pyquil.gates import CNOT, Gate, H, SWAP
import networkx as nx
from sabre_tools.sabre import SABRE

from sabre_tools.circuit_preprocess import preprocess_input_circuit, get_initial_mapping, get_distance_matrix
    

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

initial_mapping = get_initial_mapping(circuit=original_circuit, coupling_graph=coupling_graph)
distance_matrix = get_distance_matrix(coupling_graph=coupling_graph)

sabre_proc = SABRE(distance_matrix, coupling_graph)

print("original input circuit:")
print(original_circuit)
print("initial mapping: ", initial_mapping)
forbidden_gates = sabre_proc.rewiring_correctness(original_circuit, initial_mapping)
print("forbidden gates: ", forbidden_gates)
print("number of gates in input circuit: ", sabre_proc.cnot_count(original_circuit))
print()
temp_mapping = initial_mapping.copy()
temp_circuit = original_circuit.copy()

for iteration in range(3):
    front_layer_gates, circuit_dag = preprocess_input_circuit(circuit=temp_circuit)
    final_program, final_mapping = sabre_proc.execute_sabre_algorithm(front_layer_gates = front_layer_gates, qubit_mapping = temp_mapping, circuit_dag = circuit_dag)

    reversed_ins = reversed(temp_circuit.instructions)
    temp_circuit = Program()
    for ins in reversed_ins:
        temp_circuit.inst(ins)

    temp_mapping = final_mapping.copy()

print("final output circuit:")
print(final_program)
print("final mapping after rewiring: ", final_mapping)
forbidden_gates = sabre_proc.rewiring_correctness(final_program, final_mapping)
if forbidden_gates:
    print("", forbidden_gates)
else:
    print("All gates have been executed")
print("number of gates in input circuit: ", sabre_proc.cnot_count(final_program))
