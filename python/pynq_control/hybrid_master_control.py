#!/usr/bin/env python3
"""
PYNQ-side control for the MASTER board in Scenario C (dual-board hybrid).

Runs on the MASTER PYNQ-Z2. Loads the master bitstream (built with
IS_MASTER=1 generic), steps both chaotic oscillators at a controlled
rate, reads their x states via AXI GPIO, and transmits both x values
over UART to the slave board.

UART protocol (8 bytes per step):
    [4 bytes  chua_x   (Q16.16 int32, little-endian)]
    [4 bytes  rossler_x (Q16.16 int32, little-endian)]

The slave board's hybrid_slave_control.py reads this and feeds the
values into the slave oscillators' x_drive ports via its own AXI GPIO.

Usage:
    sudo python3 hybrid_master_control.py --duration 10 --rate 1000
"""

import time
import struct
import argparse

try:
    from pynq import Overlay
    from pynq.lib import AxiGPIO
    import serial
except ImportError:
    print("[WARNING] pynq or pyserial not available — run on PYNQ-Z2")
    Overlay = None

BITSTREAM = "/home/xilinx/chaos_hybrid_master.bit"
UART_PORT = "/dev/ttyPS1"
UART_BAUD = 230400      # high baud: 8 bytes × 1000 Hz = 8 kB/s ≈ 80 kbaud needed

GPIO_BASE = [
    0x41200000,  # GPIO0 ch1=control, ch2=chua_x
    0x41210000,  # GPIO1 ch1=chua_y, ch2=chua_z
    0x41220000,  # GPIO2 ch1=rossler_x, ch2=rossler_y
    0x41230000,  # GPIO3 ch1=rossler_z, ch2=hybrid_keystream
    # GPIO4 (x_drive) is unused on master board
]


def main(duration, rate):
    if Overlay is None:
        raise RuntimeError("pynq/pyserial not installed — run on the board")

    print(f"Loading {BITSTREAM}...")
    ol = Overlay(BITSTREAM)

    gpio = [AxiGPIO(addr) for addr in GPIO_BASE]

    # Reset, then unreset
    gpio[0].channel1.write(0x1)
    time.sleep(0.001)
    gpio[0].channel1.write(0x0)
    time.sleep(0.001)

    print(f"Opening UART {UART_PORT} @ {UART_BAUD} baud...")
    uart = serial.Serial(UART_PORT, UART_BAUD, timeout=0.001)

    n_steps = int(duration * rate)
    step_interval = 1.0 / rate
    t0 = time.time()
    sent = 0

    print(f"Transmitting {n_steps} samples to slave...")
    for n in range(n_steps):
        # Pulse step trigger (Rössler advances; Chua advances every cycle anyway)
        gpio[0].channel1.write(0x2)
        gpio[0].channel1.write(0x0)

        # Brief settle (4-cycle Rössler pipeline at 40 MHz = 100 ns; PYNQ
        # syscalls are slower than this so no explicit delay needed).

        chua_x    = gpio[0].channel2.read() & 0xFFFFFFFF
        rossler_x = gpio[2].channel1.read() & 0xFFFFFFFF

        # Pack as little-endian uint32 ×2 = 8 bytes
        uart.write(struct.pack('<II', chua_x, rossler_x))
        sent += 8

        # Pace
        target = t0 + (n + 1) * step_interval
        sleep = target - time.time()
        if sleep > 0:
            time.sleep(sleep)

    uart.close()
    dt = time.time() - t0
    print(f"Done. Sent {sent} bytes in {dt:.2f}s ({sent/dt:.0f} B/s, "
          f"rate ≈ {n_steps/dt:.1f} Hz)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--rate", type=float, default=1000.0)
    args = p.parse_args()
    main(args.duration, args.rate)
