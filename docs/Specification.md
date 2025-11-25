# CDC Ready/Valid Bridges with Priority Encoding Arbiter — Specification

## Overview

Modern digital systems commonly integrate multiple subsystems operating under **different clock domains**. These subsystems may run at unrelated frequencies, exhibit differing phases, or even start up at different times. When digital data must move between these domains, the transfer cannot be performed through ordinary synchronous logic: doing so risks **metastability**, **data corruption**, lost transactions, and nondeterministic behavior.

To address this problem, designers use **Clock Domain Crossing (CDC)** techniques: specialized hardware structures that safely transfer information between asynchronous or independently clocked parts of a system. 

This CDC bridge acts similarly to a **single-entry FIFO** that safely transports one word at a time across domains, ensuring data integrity through a handshake mechanism. While simple in structure, modules like this are foundational to robust hardware systems, as they enforce strict correctness under unpredictable timing conditions.

Real systems often need to move data from multiple independent sources into a single downstream consumer. A mechanism such as a **priority encoder** is used to **arbitrate** between multiple sources. A simple arbiter implementation can be obtained by cycling through the sources in round robin fashion. 

## Files

- `cdc_arbiter_top.sv`: N-channel CDC and arbiter wrapper
- `priority_arbiter.sv`: destination-domain round-robin arbiter  
- `cdc.sv`: single-channel ready/valid clock-domain-crossing bridge  
- `sync_bit.sv`: single bit X-stage synchronizer 

## Functionality

The **Top module** instantiates N=5 CDC modules and a priority arbiter. 

The **Priority Arbiter** handles transactions between all CDC modules and the external interface. It turns this N channel stream into a single channel. Outgoing ready signals to the CDCs should only be asserted for one cycle. The arbiter is not required to check all channels every cycle, it only asserts ready for the next channel. The arbiter can hold one word at a time. 

The **Clock Domain Crossing (CDC)** module safely transfers data words from a **source clock domain** to a **destination clock domain** using a standard **ready/valid streaming protocol** on each side.The CDC can hold one word at a time. 

The design must support:

- **Independent clocks:** (`clk_s`, `clk_d`) with unrelated frequencies and phases.
- **Order preservation:** data arrives in the destination domain in the same order it was sent.
- **Losslessness:**  no dropped or duplicated words.
- **Backpressure:**  destination can stall transfers using `ready_in = 0`; data must remain stable until accepted.
- **Single-word in-flight buffering:**  the module stores at most one word internally at a time.
- **Clean behavior across resets:** including independent resets for each clock domain.
- **Arbiter Round Robin:** completed in ascending order. 
- **Arbiter Latency:** the cycle after a downstream transfer is completed, ready must be asserted on the next lane (no latency)

## Interfaces Summary

The arbiter has N, WIDTH-wide input data channels with their corresponding ready/valid signals.
- Inputs: `valid_in`, `data_in`
- Output: `ready_out`

It has one output data channel with its corresponding ready/valid interface.

- Inputs: `ready_in`
- Output: `data_out`, `valid_out`

Each CDC has two independent ready/valid interfaces:

### Source clock domain (`clk_s`)
- Inputs: `valid_s`, `data_s`, `clk_s`, `reset_s`
- Output: `ready_s`

A transfer occurs on a rising edge of `clk_s` when both valid_s and ready_s are asserted.

### Destination clock domain (`clk_d`)
- Inputs: `ready_d`, `clk_d`, `reset_d`
- Outputs: `valid_d`, `data_d`

A transfer occurs on a rising edge of `clk_d` when both valid_d and ready_d are asserted.

## Parameters

The widths of `data_s` and `data_out` are determined by the parameter `WIDTH`.

The `DELAY` specifies the number of stages in the synchronization pipeline.

The `N` specifies the number of CDCs.

## Reset Requirements

### Source Reset (`reset_s`)
- After reset:
  - No pre-reset word may appear at the destination.
  - Source must behave as if no data is pending.

### Destination Reset (`reset_d`)
- After reset:
  - No pre-reset word may cause a spurious valid or output.
  - Output must begin in idle state and only assert `valid_d` after a **new** transfer.

