#!/usr/bin/env python3
"""
PYNQ-side control for chaos_hybrid_single_board.bit.

Drives a single PYNQ-Z2 hosting four chaotic oscillator instances
(Chua master + Chua slave + Rössler master + Rössler slave) via 7 AXI GPIO
instances. Pulses state_step at a user-defined rate, logs all twelve state
words + the combined master/slave keystreams, and writes CSV for the
analyze_sync.py script.

Usage (on PYNQ board, as root or in a sudo session):
    python3 single_board_hybrid_control.py --duration 10 --rate 1000

This emits hybrid_data.csv with columns:
    timestamp, mc_x, mc_y, mc_z, sc_x, sc_y, sc_z,
               mr_x, mr_y, mr_z, sr_x, sr_y, sr_z,
               m_combined_ks, s_combined_ks
"""

import time
import csv
import argparse
import struct

# These imports only work on a PYNQ-Z2 with the bitstream loaded
try:
    from pynq import Overlay
    from pynq.lib import AxiGPIO
except ImportError:
    print("[WARNING] pynq library not available — this script must run on PYNQ-Z2")
    Overlay = None

BITSTREAM = "/home/xilinx/chaos_hybrid_single_board.bit"

# AXI GPIO base addresses (from Vivado address editor — adjust to match yours)
GPIO_BASE = [
    0x41200000,  # GPIO0: ctrl in, mc_x out
    0x41210000,  # GPIO1: mc_y, mc_z
    0x41220000,  # GPIO2: sc_x, sc_y
    0x41230000,  # GPIO3: sc_z, mr_x
    0x41240000,  # GPIO4: mr_y, mr_z
    0x41250000,  # GPIO5: sr_x, sr_y
    0x41260000,  # GPIO6: m_combined_ks, s_combined_ks (only low 16 bits each used)
]


def q16_to_float(val):
    """Convert Q16.16 (unsigned 32-bit read) to float."""
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        val -= 0x100000000
    return val / 65536.0


def main(duration, rate, out_csv):
    if Overlay is None:
        raise RuntimeError("pynq not installed — run on the board")

    print(f"Loading {BITSTREAM}...")
    ol = Overlay(BITSTREAM)

    print("Mapping AXI GPIO instances...")
    gpio = [AxiGPIO(addr) for addr in GPIO_BASE]

    # Issue soft reset, then deassert
    gpio[0].channel1.write(0x1)
    time.sleep(0.001)
    gpio[0].channel1.write(0x0)
    time.sleep(0.001)

    n_steps = int(duration * rate)
    step_interval = 1.0 / rate
    rows = []

    print(f"Logging {n_steps} steps at {rate} Hz...")
    t0 = time.time()
    for n in range(n_steps):
        # Pulse step trigger: write trigger bit high, then low
        gpio[0].channel1.write(0x2)
        gpio[0].channel1.write(0x0)

        # Read all state words
        mc_x = q16_to_float(gpio[0].channel2.read())
        mc_y = q16_to_float(gpio[1].channel1.read())
        mc_z = q16_to_float(gpio[1].channel2.read())
        sc_x = q16_to_float(gpio[2].channel1.read())
        sc_y = q16_to_float(gpio[2].channel2.read())
        sc_z = q16_to_float(gpio[3].channel1.read())
        mr_x = q16_to_float(gpio[3].channel2.read())
        mr_y = q16_to_float(gpio[4].channel1.read())
        mr_z = q16_to_float(gpio[4].channel2.read())
        sr_x = q16_to_float(gpio[5].channel1.read())
        sr_y = q16_to_float(gpio[5].channel2.read())
        m_ks = gpio[6].channel1.read() & 0xFFFF
        s_ks = gpio[6].channel2.read() & 0xFFFF

        # Note: sr_z is not exposed in this minimal GPIO layout to keep
        # within 7 instances; if needed, expand to GPIO7 or pack with ks.

        rows.append([
            n / rate, mc_x, mc_y, mc_z, sc_x, sc_y, sc_z,
            mr_x, mr_y, mr_z, sr_x, sr_y, m_ks, s_ks,
        ])

        # Pace
        target = t0 + (n + 1) * step_interval
        sleep = target - time.time()
        if sleep > 0:
            time.sleep(sleep)

    print(f"Done. Writing {out_csv}...")
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t', 'mc_x', 'mc_y', 'mc_z', 'sc_x', 'sc_y', 'sc_z',
                    'mr_x', 'mr_y', 'mr_z', 'sr_x', 'sr_y',
                    'm_combined_ks', 's_combined_ks'])
        w.writerows(rows)
    print(f"Wall time: {time.time()-t0:.2f} s, actual rate ≈ {n_steps/(time.time()-t0):.1f} Hz")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=float, default=10.0, help="seconds to log")
    p.add_argument("--rate", type=float, default=1000.0, help="step rate Hz")
    p.add_argument("--out", default="hybrid_data.csv")
    args = p.parse_args()
    main(args.duration, args.rate, args.out)
