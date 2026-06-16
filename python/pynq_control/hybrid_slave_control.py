#!/usr/bin/env python3
"""
PYNQ-side control for the SLAVE board in Scenario C (dual-board hybrid).

Runs on the SLAVE PYNQ-Z2. Loads the slave bitstream (built with
IS_MASTER=0 generic), receives the master's x values over UART, writes
them into the slave oscillators' x_drive AXI GPIO inputs, pulses the
step trigger, then reads back the slave's state to verify sync
convergence and capture the hybrid keystream for decryption.

UART protocol matches hybrid_master_control.py:
    [4 bytes chua_x][4 bytes rossler_x] per step.

Logged CSV columns:
    t, mc_x, sc_x, sc_y, sc_z, mr_x, sr_x, sr_y, sr_z, hybrid_keystream

The slave's hybrid_keystream is compared against the master's (received
via UART) to validate hybrid sync. If keystreams match after Chua
sync converges, the cipher is verified.

Usage:
    sudo python3 hybrid_slave_control.py --duration 10 --rate 1000
"""

import time
import struct
import csv
import argparse

try:
    from pynq import Overlay
    from pynq.lib import AxiGPIO
    import serial
except ImportError:
    print("[WARNING] pynq or pyserial not available — run on PYNQ-Z2")
    Overlay = None

BITSTREAM = "/home/xilinx/chaos_hybrid_slave.bit"
UART_PORT = "/dev/ttyPS1"
UART_BAUD = 230400

GPIO_BASE = [
    0x41200000,  # GPIO0 ch1=control, ch2=chua_x (slave's chua_x_state — should match master's after sync)
    0x41210000,  # GPIO1 ch1=chua_y, ch2=chua_z
    0x41220000,  # GPIO2 ch1=rossler_x, ch2=rossler_y
    0x41230000,  # GPIO3 ch1=rossler_z, ch2=hybrid_keystream
    0x41240000,  # GPIO4 ch1=chua_x_drive (PS->PL), ch2=rossler_x_drive (PS->PL)
]


def q16_to_float(val):
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        val -= 0x100000000
    return val / 65536.0


def main(duration, rate, out_csv):
    if Overlay is None:
        raise RuntimeError("pynq/pyserial not installed — run on the board")

    print(f"Loading {BITSTREAM}...")
    ol = Overlay(BITSTREAM)

    gpio = [AxiGPIO(addr) for addr in GPIO_BASE]

    gpio[0].channel1.write(0x1)
    time.sleep(0.001)
    gpio[0].channel1.write(0x0)
    time.sleep(0.001)

    print(f"Opening UART {UART_PORT} @ {UART_BAUD} baud...")
    uart = serial.Serial(UART_PORT, UART_BAUD, timeout=1.0)

    n_steps = int(duration * rate)
    rows = []
    t0 = time.time()
    print(f"Receiving and processing {n_steps} samples...")

    for n in range(n_steps):
        # Read 8 bytes (block until they arrive — master controls pace)
        data = uart.read(8)
        if len(data) < 8:
            print(f"[Warning] short read at step {n}: {len(data)} bytes")
            continue
        chua_x_drv, rossler_x_drv = struct.unpack('<II', data)

        # Write received values into slave's x_drive AXI GPIO ports
        gpio[4].channel1.write(chua_x_drv & 0xFFFFFFFF)
        gpio[4].channel2.write(rossler_x_drv & 0xFFFFFFFF)

        # Pulse step trigger (Rössler advances; Chua sees new x_drive immediately)
        gpio[0].channel1.write(0x2)
        gpio[0].channel1.write(0x0)

        # Read slave's state and keystream
        sc_x = q16_to_float(gpio[0].channel2.read())
        sc_y = q16_to_float(gpio[1].channel1.read())
        sc_z = q16_to_float(gpio[1].channel2.read())
        sr_x = q16_to_float(gpio[2].channel1.read())
        sr_y = q16_to_float(gpio[2].channel2.read())
        sr_z = q16_to_float(gpio[3].channel1.read())
        ks   = gpio[3].channel2.read() & 0xFFFF

        rows.append([
            n / rate,
            q16_to_float(chua_x_drv),    # master chua_x (for r-comparison)
            sc_x, sc_y, sc_z,
            q16_to_float(rossler_x_drv), # master rossler_x
            sr_x, sr_y, sr_z,
            ks
        ])

    uart.close()
    dt = time.time() - t0
    print(f"Received {len(rows)} samples in {dt:.2f}s ({len(rows)/dt:.1f} Hz)")

    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t', 'mc_x', 'sc_x', 'sc_y', 'sc_z',
                    'mr_x', 'sr_x', 'sr_y', 'sr_z', 'hybrid_keystream'])
        w.writerows(rows)
    print(f"Saved → {out_csv}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--rate", type=float, default=1000.0)
    p.add_argument("--out", default="hybrid_slave_data.csv")
    args = p.parse_args()
    main(args.duration, args.rate, args.out)
