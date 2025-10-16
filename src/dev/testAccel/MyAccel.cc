// src/dev/myaccel/MyAccel.cc
#include "dev/testAccel/MyAccel.hh"

#include "base/bitfield.hh"
#include "base/logging.hh"
#include "mem/packet.hh"
#include "mem/packet_access.hh"
#include "base/logging.hh"   // inform(), warn(), fatal()
#include "sim/cur_tick.hh"   // curTick()

namespace gem5 {

MyAccel::MyAccel(const MyAccelParams& p)
  : BasicPioDevice(p, p.pio_size),        // base takes BasicPioDeviceParams&
    pioDelayTicks(p.pio_latency),
    resetDoneOnRead(p.reset_done_on_read)
{
    pioAddr = p.pio_addr;
}

AddrRangeList
MyAccel::getAddrRanges() const
{
    // Advertise a single contiguous MMIO window
    return AddrRangeList{ RangeSize(pioAddr, pioSize) };
}

inline void
MyAccel::resp32(PacketPtr pkt, uint32_t val) const
{
    pkt->setLE<uint32_t>(val);
    pkt->makeResponse();
}

Tick MyAccel::read(PacketPtr pkt)
{
    const Addr off = pkt->getAddr() - pioAddr;
    inform("%s READ  off=0x%02x @%llu", name(), (unsigned)off, curTick());
    uint32_t val = 0;
    switch (off) {
        case 0x00: val = src_lo; break;
        case 0x04: val = dst_lo; break;
        case 0x08: val = len;    break;
        case 0x0C: val = cmd;    break;
        case 0x10: // STATUS: bit0=busy, bit1=done
            val = (busy ? 1u : 0u) | (done ? 2u : 0u);
            if (resetDoneOnRead) done = false;
            break;
        default:
            warn("%s: read unmapped offset 0x%x", name(), (unsigned)off);
            val = 0;
            break;
    }

    pkt->setLE<uint32_t>(val);
    pkt->makeResponse(); //we make a response but never send it
    return pioDelayTicks; // how long this MMIO takes
}

Tick MyAccel::write(PacketPtr pkt)
{
    const Addr off = pkt->getAddr() - pioAddr;
    const uint32_t w = pkt->getLE<uint32_t>();
    inform("%s WRITE off=0x%02x val=0x%08x @%llu",
            name(), (unsigned)off, w, (unsigned)curTick());
    switch (off) {
        case 0x00: src_lo = w; break;
        case 0x04: dst_lo = w; break;
        case 0x08: len    = w; break;
        case 0x0C:
            cmd = w;
            // Bit0=start; set busy, clear done (no DMA yet)
            if (w & 1) { busy = true; done = false; busy = false; done = true; }
            break;
        case 0x10:
            // STATUS is read-only; ignore writes for now
            break;
        default:
            warn("%s: write unmapped offset 0x%x", name(), (unsigned)off);
            break;
    }

    pkt->makeResponse();
    return pioDelayTicks;
}

} // namespace gem5
