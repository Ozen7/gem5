# configs/myaccel/fs_min.py
from m5.objects import MyAccel

from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

# 1) CPU/mem/cache
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.X86)
memory = SingleChannelDDR4_2400("3GiB")
caches = NoCache()
board = X86Board(
    clk_freq="3GHz", processor=processor, memory=memory, cache_hierarchy=caches
)

# 2) Set *FS* workload first (this flips the board into full-system mode)
# Option A: one-line “workload resource” (Ubuntu 24.04 boot)
board.set_workload(obtain_resource("x86-ubuntu-24.04-boot-no-systemd"))
# (Alt: explicit kernel+disk)
# board.set_kernel_disk_workload(
#     kernel=obtain_resource("x86-linux-kernel-5.4.49"),
#     disk_image=obtain_resource("x86-ubuntu-18.04-img"),
# )

# 3) Now the board has an IO bus; attach your MMIO device
accel = MyAccel(pio_addr=0xC0001000, pio_size=0x1000)
accel.pio = (
    board.get_io_bus().mem_side_ports
)  # MMIO is a PIO *slave* on the IOXBar

# 4) Run
sim = Simulator(board=board)
sim.run()
