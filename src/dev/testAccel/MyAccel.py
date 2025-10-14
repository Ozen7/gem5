# src/dev/myaccel/MyAccel.py
from m5.objects import BasicPioDevice
from m5.params import *


class MyAccel(BasicPioDevice):
    type = "MyAccel"
    cxx_class = "gem5::MyAccel"
    cxx_header = "dev/testAccel/MyAccel.hh"

    # Where in physical address space the MMIO window lives
    pio_addr = Param.Addr(0xC0001000, "MMIO base address")
    pio_size = Param.Addr(0x1000, "MMIO size (bytes)")
    pio_latency = Param.Latency("50ns", "MMIO access latency")

    # A couple of toy knobs so we can see params plumbed through
    reset_done_on_read = Param.Bool(True, "Clear DONE when STATUS is read")
