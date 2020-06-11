# Qubit Mapping for NISQ-Era Quantum Devices
### Introduction
The goal of this project was to implement the paper **Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices** by *Gushu Li, Yufei Ding, and Yuan Xie*. 

### Purpose
Due to limited connections between physical qubits, most two-qubit gates cannot be directly implemented on Noisy Intermediate-Scale Quantum (NISQ) devices. A dynamic remapping of logical to physical qubits is needed to enable execution of two qubit gates in a quantum algorithm on a NISQ device. This project implements a **SWAP-based BidiREctional heuristic search algorithm (SABRE)**, proposed in the given paper that is applicable to NISQ devices with arbitrary qubit connections

### Problem Statement
Given an input quantum circuit and the coupling graph of a quantum device, find an **initial mapping** and the intermediate qubit **mapping transition** (by inserting SWAPs) to satisfy all two-qubit constraints and try to minimize the number of additional gates and circuit depth in the final hardware-compliant circuit.

### References
- **Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices** by *Gushu Li, Yufei Ding, and Yuan Xie*. [Click here for pdf](https://arxiv.org/pdf/1809.02573.pdf)
- [Pyquil docs](http://docs.rigetti.com/en/stable/) 

### Usage
An example of how to use this package is illustrated in `example.py`. 

- Construct a pyquil program:
    ```
    from pyquil import Program
    from pyquil.gates import CNOT, Gate, H, SWAP
    original_circuit = Program()
    original_circuit.inst(CNOT(0, 1))
    original_circuit.inst(CNOT(2, 3))
    original_circuit.inst(CNOT(1, 3))
    original_circuit.inst(CNOT(1, 2))
    original_circuit.inst(CNOT(2, 3))
    original_circuit.inst(CNOT(0, 3))
    ```
- Define a coupling graph (the coupling graph can also be a predefined one based on the underlying chip architecture):
    ```
    import networkx as nx
    coupling_graph = nx.Graph()
    coupling_graph.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
    ```
- Apply preprocessing on the circuit and the coupling graph to generate a random initial mapping and a distance matrix:
    ```
    from sabre_tools.circuit_preprocess import preprocess_input_circuit, get_initial_mapping, get_distance_matrix
    initial_mapping = get_initial_mapping(circuit=original_circuit, coupling_graph=coupling_graph)
    distance_matrix = get_distance_matrix(coupling_graph=coupling_graph)
    ```
- Execute the SABRE algorithm on the circuit in forward-backward-forward passes where final mapping output of each pass is provided as the initial mapping of the reverse circuit in the next pass
    ```
    from sabre_tools.sabre import SABRE
    for iteration in range(3):
    front_layer_gates, circuit_dag = preprocess_input_circuit(circuit=temp_circuit)
    final_program, final_mapping = sabre_proc.execute_sabre_algorithm(front_layer_gates = front_layer_gates, qubit_mapping = temp_mapping, circuit_dag = circuit_dag)

    reversed_ins = reversed(temp_circuit.instructions)
    temp_circuit = Program()
    for ins in reversed_ins:
        temp_circuit.inst(ins)
    temp_mapping = final_mapping.copy()
    ```
- To check if SABRE algorithm was able to insert SWAPs in the circuit so that all 2-qubit gates were executed successfully, call the `rewiring_correctness()` function:
    ```
    forbidden_gates = sabre_proc.rewiring_correctness(final_program, final_mapping)
    if forbidden_gates:
        print("", forbidden_gates)
    else:
        print("All gates have been executed")
    ```
    This function scans the logical to physical qubit mapping and the SWAP inserted circuit  to determine if there are gates are not executable and returns the non-executable gate if true, otherwise returns an empty dictionary. This function can also be used to check if the original circuit requires the use of SABRE in the first place
- Count the number of 2 qubit gates in the original or final circuit to determine the circuit depth and number of gates:
    ```
    two_qubit_gate_count = sabre_proc.cnot_count(program)
    ```
### Future Scope
This project has been developed using Rigetti's quantum programming framework Pyquil. A future scope of this project is to make it platform independent so that SABRE can be applied to a quantum program written in any framework.
Another possible scope of research is to implement other algorithms in this field and perform a comparison based on number of gates reduction, scalability, runtime speedup, algorithm performance on large circuits etc. 

### QC Mentorship Program
This project has been initiated and completed as part of the [QC Mentorship Program](https://qosf.org/qc_mentorship/#summary) under [Quantum Open Source Foundation (QOSF)](https://qosf.org/) in collaboration with [Unitary Fund](https://unitary.fund/). 
This work has been completed with constant guidance and motivation by my mentor Petar Korponaić
([LinkedIn](https://www.linkedin.com/in/petar-korponaic/)).