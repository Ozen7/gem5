// src/dev/myaccel/MyAccel.hh
#pragma once

#include "dev/io_device.hh"     // BasicPioDevice
#include "params/MyAccel.hh"    // auto-generated from MyAccel.py

namespace gem5 {

class MyAccel : public BasicPioDevice
{
  public:
    MyAccel(const MyAccelParams &p);

    // Tell the bus which address range we own
    AddrRangeList getAddrRanges() const override;

    // Handle CPU MMIO transactions
    Tick read(PacketPtr pkt) override;
    Tick write(PacketPtr pkt) override;

  private:
    // Simple register file (all 32-bit for now)
    uint32_t src_lo  = 0;
    uint32_t dst_lo  = 0;
    uint32_t len     = 0;
    uint32_t cmd     = 0;
    bool     busy    = false;
    bool     done    = false;

    // Convenience: expose pioDelay (ticks) via base params
    Tick pioDelayTicks;

    // Helper: pack a 32-bit value into a response
    inline void resp32(PacketPtr pkt, uint32_t val) const;

    const bool resetDoneOnRead;
};

} // namespace gem5
