#!/usr/bin/env python3
# Full-system platform with an IO bus, a system mem bus, your MMIO device,
# and a TrafficGen master that writes/reads the device registers.

# Import your SimObject (compiled under src/dev/testAccel/)
from m5.objects import (
    AddrRange,
    Bridge,
    IOXBar,
    MyAccel,
    PMAChecker,
    Root,
    SimpleMemory,
    SrcClockDomain,
    System,
    SystemXBar,
    TraceGen,
    TrafficGen,
    VoltageDomain,
)

ACCEL_BASE = 0x10009000  # MMIO window for MyAccel
DRAM_BASE = 0x80000000

# --- System + clocks/memory mode ---
system = System()
system.clk_domain = SrcClockDomain(
    clock="1GHz", voltage_domain=VoltageDomain()
)
system.mem_mode = "timing"
system.mem_ranges = [AddrRange(start=DRAM_BASE, size="256MB")]

# --- Buses ---
system.iobus = IOXBar()  # incoherent I/O crossbar (MMIO)
system.membus = SystemXBar()  # main memory crossbar
system.system_port = system.membus.cpu_side_ports

# --- Bridge IO<->Mem (lets IO masters reach DRAM) ---
system.bridge = Bridge(delay="50ns")
system.bridge.mem_side_port = system.iobus.cpu_side_ports
system.bridge.cpu_side_port = system.membus.mem_side_ports
# Forward any DRAM address range through the bridge
system.bridge.ranges = system.mem_ranges

# --- DRAM backing store ---
system.mem = SimpleMemory(
    range=system.mem_ranges[0], latency="50ns", bandwidth="16GiB/s"
)
system.mem.port = system.membus.mem_side_ports

# --- MMIO device (PIO slave on IO bus) ---
system.myaccel = MyAccel(pio_addr=ACCEL_BASE, pio_size=0x1000)
# PIO (MMIO) ports are slaves on the IO bus (mem_side_ports)
system.myaccel.pio = system.iobus.mem_side_ports

# --- PMA for MMIO semantics (mark MMIO as uncacheable) ---
system.pma = PMAChecker(uncacheable=[AddrRange(ACCEL_BASE, size=0x1000)])

# --- TrafficGen master on the IO bus ---
tgen = TrafficGen()
# Masters plug into the cpu_side_ports of the bus they initiate requests on
tgen.port = system.iobus.cpu_side_ports

# Build a tiny trace: WR SRC, WR DST, WR LEN, WR CMD(start), RD STATUS
trace = TraceGen()
trace.set_addr_size(4)
trace.create(
    [
        (10, True, ACCEL_BASE + 0x00, 4, 0x80010000),  # SRC_LO
        (20, True, ACCEL_BASE + 0x04, 4, 0x80020000),  # DST_LO
        (30, True, ACCEL_BASE + 0x08, 4, 1024),  # LEN
        (40, True, ACCEL_BASE + 0x0C, 4, 1),  # CMD=start
        (60, False, ACCEL_BASE + 0x10, 4),  # STATUS read
    ],
    loop=False,
)
tgen.generator = trace

root = Root(full_system=True, system=system)

import m5

m5.instantiate()
print(">>> TrafficGen→MMIO: writing MyAccel regs then reading STATUS")
m5.simulate()
