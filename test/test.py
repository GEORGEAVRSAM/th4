# SPDX-FileCopyrightText: © 2026 George Avrsam
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge

# Values the self-test program (see tb.v) must write to the output port, in order.
EXPECTED = [8, 4, 10, 12, 2, 6, 10, 7, 9]
PORT_IN = 10  # value on the input port uio[3:0]


@cocotb.test()
async def test_th4_selftest(dut):
    dut._log.info("Start")
    clock = Clock(dut.clk, 1, unit="us")  # 1 MHz
    cocotb.start_soon(clock.start())

    dut._log.info("Reset")
    dut.ena.value = 1
    dut.uio_in.value = PORT_IN
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Run the self-test program")
    seen, when, last, cycle = [], [], 0, 0
    for _ in range(2400):
        await FallingEdge(dut.clk)
        cycle += 1
        out = int(dut.uio_out.value) >> 4  # output port = uio[7:4]
        if out != last:
            seen.append(out)
            when.append(cycle)
            last = out
            dut._log.info(f"cycle {cycle}: output port = {out}")

    assert int(dut.uio_oe.value) == 0xF0, "uio[7:4] must be outputs, uio[3:0] inputs"
    assert 15 not in seen, f"self-test reached 'fail': {seen}"
    assert seen == EXPECTED, f"output sequence {seen}, expected {EXPECTED}"

    # Two WAIT 1 (1026 cycles each) plus LOAD 9 and OUT between outputs 7 and 9
    gap = when[8] - when[7]
    assert gap == 2054, f"timer: WAIT 1 + WAIT 1 took {gap} cycles, expected 2054"
