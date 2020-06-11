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

- Construct a pyquil program as follows:
```
original_circuit = Program()
original_circuit.inst(CNOT(0, 1))
original_circuit.inst(CNOT(2, 3))
original_circuit.inst(CNOT(1, 3))
original_circuit.inst(CNOT(1, 2))
original_circuit.inst(CNOT(2, 3))
original_circuit.inst(CNOT(0, 3))
```
