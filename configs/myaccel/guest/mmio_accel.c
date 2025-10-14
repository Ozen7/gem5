#define ACCEL_BASE   0x10009000u
#define REG32(off) (*(volatile unsigned int*)(ACCEL_BASE + (off)))

int main(void) {
    // Example DRAM buffers (inside 0x8000_0000..)
    const unsigned src = 0x80010000u;
    const unsigned dst = 0x80020000u;

    // Program registers
    REG32(0x00) = src;       // SRC_LO
    REG32(0x04) = dst;       // DST_LO
    REG32(0x08) = 1024;      // LEN
    REG32(0x0C) = 1;         // CMD: start

    // Poll STATUS (bit1 = done)
    while ((REG32(0x10) & 2u) == 0) { }

    // Done. Spin forever in _start after return.
    return 0;
}
