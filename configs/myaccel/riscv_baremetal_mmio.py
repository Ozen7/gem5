#!/usr/bin/env python3
# Minimal RISCV full-system (bare-metal) config with an IO bus + your MMIO device.

import argparse

# Your device
from m5.objects import MyAccel  # from src/dev/testAccel/MyAccel.py
from m5.objects import (
    AddrRange,
    Bridge,
    HiFive,
    IOXBar,
    MemBus,
    PMAChecker,
    RiscvBareMetal,
    RiscvRTC,
    Root,
    SimpleMemory,
    SrcClockDomain,
    System,
    TimingSimpleCPU,
    VoltageDomain,
)
from m5.params import Frequency
from m5.util import addToPath


def build_system(args):
    sys = System()
    sys.clk_domain = SrcClockDomain(
        clock=args.sys_clock, voltage_domain=VoltageDomain()
    )
    sys.mem_mode = "timing"
    sys.mem_ranges = [AddrRange(start=0x80000000, size=args.mem_size)]

    # Workload: bare-metal (no OS). Boot 'kernel' ELF at 0x8000_0000.
    sys.workload = RiscvBareMetal()
    sys.workload.bootloader = args.kernel

    # Buses
    sys.iobus = IOXBar()  # I/O crossbar (MMIO lives here)
    sys.membus = MemBus()  # main memory bus
    sys.system_port = sys.membus.cpu_side_ports

    # Platform similar to the example riscv FS script
    sys.platform = HiFive()
    sys.platform.rtc = RiscvRTC(frequency=Frequency("100MHz"))
    sys.platform.clint.int_pin = sys.platform.rtc.int_pin

    # Bridge between IO bus and mem bus for off-chip ranges
    sys.bridge = Bridge(delay="50ns")
    sys.bridge.mem_side_port = sys.iobus.cpu_side_ports
    sys.bridge.cpu_side_port = sys.membus.mem_side_ports
    sys.bridge.ranges = sys.platform._off_chip_ranges()

    # Attach on/off-chip IO and PLIC; set core count (1)
    sys.platform.attachOnChipIO(sys.membus)
    sys.platform.attachOffChipIO(sys.iobus)
    sys.platform.attachPlic()
    sys.platform.setNumCores(1)

    # CPU
    sys.cpu = [TimingSimpleCPU(cpu_id=0)]
    # Minimal cacheless hookup
    sys.cpu[0].icache_port = sys.membus.cpu_side_ports
    sys.cpu[0].dcache_port = sys.membus.cpu_side_ports

    # PMA checker so uncached MMIO regions behave correctly
    uncacheable = [
        *sys.platform._on_chip_ranges(),
        *sys.platform._off_chip_ranges(),
    ]
    sys.cpu[0].mmu.pma_checker = PMAChecker(uncacheable=uncacheable)

    # Simple DRAM backing
    sys.mem = SimpleMemory(
        range=sys.mem_ranges[0], latency="50ns", bandwidth="16GiB/s"
    )
    sys.mem.port = sys.membus.mem_side_ports

    # Your MMIO device at 0x1000_9000
    sys.myaccel = MyAccel(pio_addr=0x10009000, pio_size=0x1000)
    sys.myaccel.pio = sys.iobus.mem_side_ports  # publish PIO slave onto IO bus

    return sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--kernel",
        required=True,
        help="Path to bare-metal RISCV ELF loaded at 0x80000000",
    )
    p.add_argument("--mem-size", default="3GB")
    p.add_argument("--sys-clock", default="1GHz")
    args = p.parse_args()

    system = build_system(args)
    root = Root(full_system=True, system=system)

    import m5

    m5.instantiate()
    print(">>> Running bare-metal RISCV with MyAccel MMIO @ 0x10009000")
    m5.simulate()


if __name__ == "__main__":
    main()
