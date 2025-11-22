# CDC Ready/Valid Bridge — Specification

## Overview

Modern digital systems commonly integrate multiple subsystems operating under **different clock domains**. These subsystems may run at unrelated frequencies, exhibit differing phases, or even start up at different times. When digital data must move between these domains, the transfer cannot be performed through ordinary synchronous logic: doing so risks **metastability**, **data corruption**, lost transactions, and nondeterministic behavior.

To address this problem, designers use **Clock Domain Crossing (CDC)** techniques: specialized hardware structures that safely transfer information between asynchronous or independently clocked parts of a system. 

This CDC bridge acts similarly to a **single-entry FIFO** that safely transports one word at a time across domains, ensuring data integrity through a handshake mechanism. While simple in structure, modules like this are foundational to robust hardware systems, as they enforce strict correctness under unpredictable timing conditions.

## Functionality

The **Clock Domain Crossing (CDC)** module  safely transfers data words from a **source clock domain** to a **destination clock domain** using a standard **ready/valid streaming protocol** on each side.

The design must support:

- **Independent clocks:** (`clk_s`, `clk_d`) with unrelated frequencies and phases.
- **Order preservation:** data arrives in the destination domain in the same order it was sent.
- **Losslessness:**  no dropped or duplicated words.
- **Backpressure:**  destination can stall transfers using `ready_d = 0`; data must remain stable until accepted.
- **Single-word in-flight buffering:**  the module stores at most one word internally at a time.
- **Clean behavior across resets:** including independent resets for each clock domain.

This specification provides enough detail for an agent to implement the RTL without needing access to the testbench.



## Interface Summary

The CDC has two independent ready/valid interfaces:

### Source clock domain (`clk_s`)
- Inputs: `valid_s`, `data_s`, `clk_s`, `reset_s`
- Output: `ready_s`

A transfer occurs on a rising edge of `clk_s` when both valid_s and ready_s are asserted.


### Destination clock domain (`clk_d`)
- Inputs: `ready_d`, `clk_d`, `reset_d`
- Outputs: `valid_d`, `data_d`

A transfer occurs on a rising edge of `clk_d` when both valid_d and ready_d are asserted.


## Parameters

The widths of `data_s` and `data_d` are determined by the parameter `WIDTH`.

The `DELAY` specifies the number of stages in the synchronization pipeline.

## Reset Requirements

### Source Reset (`reset_s`)
- After reset:
  - No pre-reset word may appear at the destination.
  - Source must behave as if no data is pending.

### Destination Reset (`reset_d`)
- After reset:
  - No pre-reset word may cause a spurious valid or output.
  - Output must begin in idle state and only assert `valid_d` after a **new** transfer.

