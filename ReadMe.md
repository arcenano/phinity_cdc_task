# Clock Domain Crossing Channels with Arbitration

## Industry Relevance

Modern digital systems commonly integrate multiple subsystems operating under **different clock domains**. These subsystems may run at unrelated frequencies, exhibit differing phases, or even start up at different times. When digital data must move between these domains, the transfer cannot be performed through ordinary synchronous logic: doing so risks **metastability**, **data corruption**, lost transactions, and nondeterministic behavior.

To address this problem, designers use **Clock Domain Crossing (CDC)** techniques: specialized hardware structures that safely transfer information between asynchronous or independently clocked parts of a system. 

Real systems often need to move data from multiple independent sources into a single downstream consumer. A mechanism such as a **priority encoder** is used to **arbitrate** between multiple sources. A simple arbiter implementation can be obtained by cycling through the sources in round robin fashion. 

## Task Selection

This task was selected because it contains very fundamental logic blocks that are utilized across many use cases. These designs are simple, and don't require expertise in a specific field. Additionally, many examples of these kind of blocks are available online; there is plenty of similar data to have trained the model on. 

## Context Codebase

The model is provided a specifications document and top level file that contains the interface definition for the system. 

## Results

Average Reward: 40%

https://www.hud.ai/jobs/ef0d191f-3903-45fe-bbd6-3a0e31d20ae2

# Verification and Golden Solution (File 1)

## Tests

Tests 4,6,7 are where most of the verification happens, the rest are very useful for debugging. 

Tests are evaluated by keeping track of send words and comparing them to received words. 

### Test 1.  Same clocks, single channel simple.
  - Valid always high  on a single channel and ready always high.

### Test 2.  Same clocks, single channel, no transactions (src).
  - Valid always low on every channel, toggle ready deterministically (every N cycles).

### Test 3.  Same clocks, single channel backpressure.
  - Valid always high on a single channel, toggle ready deterministically (every N cycles).

### Test 4.  Same clocks, single channel no transactions (dst).
  - Toggle valid deterministically (# cycles) on a single channel, ready always low.
  - Ensure CDC and Arbiter hold only one word each (assert len(expected) <= 2).

### Test 5.  Same clocks, single channel intermittent data.
  - Toggle valid deterministically (N cycles), ready high.

### Test 6.  Stochastic Stimulus, same clocks.
  - Toggle both valid and ready randomly.

### Test 6a. Stochastic Stimulus, CDC.
  - Toggle both valid and ready randomly.
  - Src clk frequency is higher than dst clk.

### Test 6B. Stochastic Stimulus, CDC.
  - Toggle both valid and ready randomly.
  - Src clk frequency is lower than dst clk.

### Test 7: Verify arbiter round-robin over all N channels.
  - Each source channel i sends exactly one word with value i.
  - All valids are asserted together, and test waits until each channel handshakes.
  - Destination applies backpressure deterministically, for a given number of cycles at a time (toggleN).
  - Verify that outputs are a cyclic rotation of [0,1,2,...,N-1]. (order is mantained).
  - Verify that ready is asserted with no latency after a downstream handshake.

## Solution

To pass all of these tests the solution must comply with the specifications detailed in Specifications.md. 

### Arbiter
  - Only holds one word at a time (single data_latch).
  - Downstream Interface only transacts when ready and valid.
  - CDC Interface only transacts when ready(sel) and valid(sel).
  - No latency after transaction (next ready gets toggled when ready_in).

### CDC
  - Both src and dst interface only transact when corresponding ready and valid are asserted.
  - A handshake is completed to transfer stable data across clock domains.
  - Only one word at a time is held (single data_latch). 


# Arbiter Failure Analysis Report (File 2)

Analyzed trace https://www.hud.ai/trace/842a0cf4-daac-437a-a83f-1e573f60be55 with focus on faulty `priority_arbiter` implementation. 

---

## A. Symptoms

The following incorrect behaviors were observed during simulation:

### 1. **Incorrect round-robin ordering (Test 7)**
The sequence of output words was not a cyclic rotation of `[0, 1, 2, ... N−1]`, as required. 

**Test output**:
base expected = [0, 1, 2, 3, 4]
received      = [0, 2, 4, 1, 3]

This test ensures that the data transfers from the CDCs to the arbiter happen in order.
Data was scrambled, so the transfers didn't happen in order. Data can be cyclically shifted but not scrambled.

### 2. **Arbiter bubbles  (Test 7)**
The testbench detected cycles where:

- `valid_out && ready_in` (downstream accepted a word),
- but **on the next cycle**, no `ready_out[i]` was asserted.

This violates the specification that the arbiter must resume scanning channels **with zero-cycle latency** following an output transfer.

The testbench raised `Arbiter order mismatch` assertions.

## B. Root Cause

The failures come from two tightly related RTL mistakes in the arbiter:

1. **Channel pointer advanced twice per transfer**  
   In the `always_ff` block, `current_channel` is updated using `next_channel(next_channel(current_channel))` in the same clock cycle.  
   This effectively skips a channel on each transfer (0 → 2 → 4 → 1 → 3 for N=5).  

2. **Ready output signal is driven by data_valid**  
    The statement that drives the ready_out:

    if (!data_valid) begin ready_out[current_channel] = 1'b1; end

    Depends on the data_valid output, it should also depend on ready in. Otherwise, if a transfer happens this cycle, we won't have a ready on the next cycle. This is the "bubble" the testbench complains about. 

The model wrote logic inconsistent with the specification. 