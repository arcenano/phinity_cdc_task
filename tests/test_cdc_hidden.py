import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Global knobs
MAX_SRC_CYCLES = 20000000
MAX_DST_CYCLES = 20000000

random.seed(1234)

async def apply_reset(dut, duration_ns=50):
    """Asynchronous reset for both clock domains."""
    dut.reset_s.value = 1
    dut.reset_d.value = 1

    await Timer(duration_ns, unit="ns")

    dut.reset_s.value = 0
    dut.reset_d.value = 0

    # Let both domains see at least one edge after reset
    await RisingEdge(dut.clk_s)
    await RisingEdge(dut.clk_d)

async def src_driver(
    dut,
    expected_out,
    num_words: int,
    valid_mode: str = "always",
    toggle_period: int = 4,
    random_prob: float = 0.5,
):
    """
    Drive the source-side valid/data interface and record accepted transfers.

    Handshake condition (source domain):
        transfer occurs when valid_s == 1 and ready_s == 1 on a rising edge of clk_s.

    valid_mode:
        "always"   : valid_s = 1 every cycle
        "never"    : valid_s = 0 every cycle
        "toggleN"  : valid_s = 1 for N cycles, then 0 for N cycles, repeating
        "random"   : valid_s = 1 with probability random_prob each cycle

    For each handshake, the value of data_s is appended to expected_out.
    """
    width = len(dut.data_s)
    mask = (1 << width) - 1

    dut.valid_s.value = 0
    dut.data_s.value = 0

    count = 0
    cycle_count = 0

    while count < num_words:
        cycle_count += 1

        if cycle_count > MAX_SRC_CYCLES:
            raise AssertionError(
                f"src_driver timeout: sent={count}, cycles={cycle_count}, ack_s={int(dut.ack_s.value)}"
            )

        # Drive valid_s for the upcoming cycle
        if valid_mode == "always":
            valid_state = 1
        elif valid_mode == "never":
            valid_state = 0
        elif valid_mode == "toggleN":
            phase = (cycle_count - 1) // toggle_period
            valid_state = 1 if (phase % 2 == 0) else 0
        elif valid_mode == "random":
            valid_state = 1 if random.random() < random_prob else 0
        else:
            raise ValueError(f"Unknown valid_mode='{valid_mode}'")

        # Always drive data
        data_val = random.getrandbits(width) & mask

        dut.data_s.value = data_val

        dut.valid_s.value = valid_state

        # Source-domain edge: DUT samples valid_s/data_s, and ready_s participates in handshake
        await RisingEdge(dut.clk_s)

        if int(dut.valid_s.value) and int(dut.ready_s.value) and not int(dut.reset_s.value):
            val = data_val
            expected_out.append(val)
            count += 1
            dut._log.info(f"[SRC] Sent {count}/{num_words}, data={val}")

    # Stop asserting valid once the requested number of transfers have been accepted
    dut.valid_s.value = 0
    dut._log.info(f"[SRC] DONE: sent {count} transactions")

async def dst_driver(
    dut,
    received_out,
    num_expected: int,
    ready_mode: str = "always",
    toggle_period: int = 4,
    random_prob: float = 0.5,
):
    """
    Drive the destination-side ready signal and record completed transfers.

    Handshake condition (destination domain):
        transfer occurs when valid_d == 1 and ready_d == 1 on a rising edge of clk_d.

    ready_mode:
        "always"   : ready_d = 1 every cycle
        "never"    : ready_d = 0 every cycle
        "toggleN"  : ready_d = 1 for N cycles, then 0 for N cycles, repeating
        "random"   : ready_d = 1 with probability random_prob each cycle

    For each handshake, the value of data_d is appended to received_out.
    """
    dut.ready_d.value = 0

    count = 0
    cycle_count = 0

    while count < num_expected:
        cycle_count += 1

        if cycle_count > MAX_DST_CYCLES:
            raise AssertionError(
                f"dst_driver timeout: received={count}, cycles={cycle_count}, ack_s={int(dut.ack_s.value)}"
            )

        # Drive ready_d for the upcoming cycle
        if ready_mode == "always":
            ready_state = 1
        elif ready_mode == "never":
            ready_state = 0
        elif ready_mode == "toggleN":
            phase = (cycle_count - 1) // toggle_period
            ready_state = 1 if (phase % 2 == 0) else 0
        elif ready_mode == "random":
            ready_state = 1 if random.random() < random_prob else 0
        else:
            raise ValueError(f"Unknown ready_mode='{ready_mode}'")

        dut.ready_d.value = ready_state

        # Destination-domain edge: DUT presents valid_d/data_d and consumes ready_d
        await RisingEdge(dut.clk_d)

        if int(dut.valid_d.value) and ready_state and not int(dut.reset_d.value):
            val = int(dut.data_d.value)
            received_out.append(val)
            count += 1
            dut._log.info(f"[DST] Got word {count}/{num_expected}, data={val}")

    dut.ready_d.value = 0
    dut._log.info(f"[DST] DONE: received {count} transactions")

@cocotb.test()
async def test1_always_valid_always_ready(dut):
    dut._log.info("TEST 1: valid always high, ready always high")

    T = 10
    cocotb.start_soon(Clock(dut.clk_s, T, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, T, "ns").start())

    await apply_reset(dut)

    NUM = 50
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(dut, expected, NUM, valid_mode="always"))
    dst = cocotb.start_soon(dst_driver(dut, received, NUM, ready_mode="always"))

    await dst
    await src

    assert expected == received

@cocotb.test()
async def test2_valid_never(dut):
    dut._log.info("TEST 2: valid always low, ready toggles")

    T = 10
    cocotb.start_soon(Clock(dut.clk_s, T, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, T, "ns").start())

    await apply_reset(dut)

    NUM = 30
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="never"
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="toggleN", toggle_period=4
    ))

    # Wait some time then kill tasks since no transfers will happen
    await Timer(1000, units="ns")
    src.cancel()
    dst.cancel()

    assert len(expected) == 0
    assert len(received) == 0

@cocotb.test()
async def test3_backpressure_always_valid(dut):
    dut._log.info("TEST 3: valid always high, ready toggles for backpressure")

    T = 10
    cocotb.start_soon(Clock(dut.clk_s, T, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, T, "ns").start())

    await apply_reset(dut)

    NUM = 50
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="always"
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="toggleN", toggle_period=7
    ))

    await dst
    await src

    assert expected == received

@cocotb.test()
async def test4_toggle_valid_ready_never(dut):
    dut._log.info("TEST 4: valid toggleN, ready always low")

    T = 10
    cocotb.start_soon(Clock(dut.clk_s, T, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, T, "ns").start())

    await apply_reset(dut)

    NUM = 40
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="toggleN", toggle_period=5
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="never"
    ))

    await Timer(1000, units="ns")
    src.cancel()
    dst.cancel()

    assert len(expected) <= 1 # This makes sure the model didn't cheat and use a FIFO
    assert len(received) == 0

@cocotb.test()
async def test5_toggle_valid_ready_always(dut):
    dut._log.info("TEST 5: valid toggleN, ready always high")

    T = 10
    cocotb.start_soon(Clock(dut.clk_s, T, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, T, "ns").start())

    await apply_reset(dut)

    NUM = 60
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="toggleN", toggle_period=4
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="always"
    ))

    await dst
    await src

    assert expected == received

@cocotb.test()
async def test6_random_equal(dut):
    dut._log.info("TEST 6A: random valid & ready, equal clocks")

    cocotb.start_soon(Clock(dut.clk_s, 10, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, 10, "ns").start())

    await apply_reset(dut)

    NUM = 100
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="random", random_prob=0.5
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="random", random_prob=0.5
    ))

    await dst
    await src

    assert expected == received

@cocotb.test()
async def test6_random_src_faster(dut):
    dut._log.info("TEST 6B: random valid & ready, src faster")

    cocotb.start_soon(Clock(dut.clk_s, 7, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, 13, "ns").start())

    await apply_reset(dut)

    NUM = 10000
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="random", random_prob=0.5
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="random", random_prob=0.5
    ))

    # Ensure reset doesn't affect tb model
    while len(expected) > len(received):
        await RisingEdge(dut.clk_s)
        
    await apply_reset(dut)

    await dst
    await src

    assert expected == received

@cocotb.test()
async def test6_random_dst_faster(dut):
    dut._log.info("TEST 6C: random valid & ready, dst faster")

    cocotb.start_soon(Clock(dut.clk_s, 17, "ns").start())
    cocotb.start_soon(Clock(dut.clk_d, 5, "ns").start())

    await apply_reset(dut)

    NUM = 10000
    expected = []
    received = []

    src = cocotb.start_soon(src_driver(
        dut, expected, NUM,
        valid_mode="random", random_prob=0.5
    ))

    dst = cocotb.start_soon(dst_driver(
        dut, received, NUM,
        ready_mode="random", random_prob=0.5
    ))

    # Ensure reset doesn't affect tb model
    while len(expected) > len(received):
      await RisingEdge(dut.clk_s)
    
    await apply_reset(dut)

    await dst
    await src

    assert expected == received


# -------------------------------------------------------------------------
#  pytest wrapper (unchanged pattern)
# -------------------------------------------------------------------------
def test_cdc_hidden_runner():
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "sources/cdc.sv", proj_path / "sources/sync_bit.sv" ]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="cdc",
        always=True,
    )
    runner.test(
        hdl_toplevel="cdc",
        test_module="test_cdc_hidden",  # this filename (without .py)
    )
