CROSS   ?= riscv64-unknown-elf
CC      := $(CROSS)-gcc
OBJCOPY := $(CROSS)-objcopy

CFLAGS  := -O2 -march=rv64gc -mabi=lp64 -nostdlib -static
LDFLAGS := -T linker.ld

all: mmio_accel.elf

mmio_accel.elf: start.S mmio_accel.c linker.ld
	$(CC) $(CFLAGS) $(LDFLAGS) start.S mmio_accel.c -o $@

bin: all
	$(OBJCOPY) -O binary mmio_accel.elf mmio_accel.bin

clean:
	rm -f mmio_accel.elf mmio_accel.bin
