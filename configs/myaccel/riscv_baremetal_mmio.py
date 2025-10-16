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
    PMAChecker,
    RiscvBareMetal,
    RiscvISA,
    RiscvRTC,
    Root,
    SimpleMemory,
    SrcClockDomain,
    System,
    SystemXBar,
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
    sys.membus = SystemXBar()  # main memory bus
    sys.system_port = sys.membus.cpu_side_ports

    # Platform
    sys.platform = HiFive()

    # Buses and bridge first (same as you have)
    sys.bridge = Bridge(delay="50ns")
    sys.bridge.mem_side_port = sys.iobus.cpu_side_ports
    sys.bridge.cpu_side_port = sys.membus.mem_side_ports
    sys.bridge.ranges = sys.platform._off_chip_ranges()

    # RTC/CLINT
    sys.platform.rtc = RiscvRTC(frequency=Frequency("100MHz"))
    sys.platform.clint.int_pin = sys.platform.rtc.int_pin

    # (Defer PCI + attach* calls until AFTER CPU + IRQ controllers exist)

    # CPU
    sys.cpu = [TimingSimpleCPU(cpu_id=0)]

    # ISA → threads → IRQ controller
    sys.cpu[0].isa = [RiscvISA()]
    sys.cpu[0].createThreads()
    sys.cpu[0].createInterruptController()

    # Minimal cacheless hookup
    sys.cpu[0].icache_port = sys.membus.cpu_side_ports
    sys.cpu[0].dcache_port = sys.membus.cpu_side_ports

    # Now that CPUs + interrupt controllers exist, wire platform
    if hasattr(sys.platform, "pci_host"):
        sys.platform.pci_host.pio = sys.iobus.mem_side_ports
        if hasattr(sys.platform.pci_host, "dma"):
            sys.platform.pci_host.dma = sys.membus.mem_side_ports

    sys.platform.attachOnChipIO(sys.membus)
    sys.platform.attachOffChipIO(sys.iobus)
    sys.platform.setNumCores(len(sys.cpu))
    sys.platform.attachPlic()

    # Simple DRAM backing
    sys.mem = SimpleMemory(
        range=sys.mem_ranges[0], latency="50ns", bandwidth="16GiB/s"
    )
    sys.mem.port = sys.membus.mem_side_ports

    # Define MyAccel window once
    MYACCEL_BASE = 0x10009000
    MYACCEL_SIZE = 0x1000
    myaccel_range = AddrRange(MYACCEL_BASE, size=MYACCEL_SIZE)

    sys.myaccel = MyAccel(
        pio_addr=MYACCEL_BASE,
        pio_size=MYACCEL_SIZE,
        pio_latency="50ns",
    )
    # For bring-up: hang directly off the main memory bus
    sys.myaccel.pio = sys.membus.mem_side_ports

    # (Optional) You can leave bridge.ranges as-is or drop the extra range now.
    # When you later move back to IOXBar, re-add: + [myaccel_range]

    # Make MMIO uncacheable for the CPU (PMA)
    try:
        from m5.objects import PMAChecker

        pma_cls = PMAChecker
    except ImportError:
        from m5.objects import PmaChecker

        pma_cls = PmaChecker

    uncacheable = [
        *sys.platform._on_chip_ranges(),
        *sys.platform._off_chip_ranges(),
        myaccel_range,  # ensure 0x10009000..0x10009fff is uncached
    ]
    sys.cpu[0].mmu.pma_checker = pma_cls(uncacheable=uncacheable)

    return sys


# build/RISCV/gem5.opt   --outdir run-mmio   --debug-file=dbg.log   --debug-flags=AddrRanges,XBar   configs/myaccel/riscv_baremetal_mmio.py --kernel configs/myaccel/guest/mmio_accel.elf


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

    sys = build_system(args)
    root = Root(full_system=True, system=sys)

    import m5

    m5.instantiate()
    print(">>> Running bare-metal RISCV with MyAccel MMIO @ 0x10009000")

    from m5 import ticks

    ev = m5.simulate(ticks.fromSeconds(0.01))

    print(f"Exited @ {m5.curTick()} : {ev.getCause()}")


main()
