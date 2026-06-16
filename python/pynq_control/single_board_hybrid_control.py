#!/usr/bin/env python3
"""
PYNQ-side control for top_wrapper.bit (single-board hybrid).

This script controls the bitstream produced from hdl/top_wrapper.vhd, which
wraps the auto-generated chaos_design_wrapper (block design with 14 single-
direction AXI GPIO IPs) plus chaos_hybrid_single_board.

GPIO layout (matches top_wrapper.vhd wiring):

    axi_gpio_0  →  control register (PS→PL): bit0=soft_rst, bit1=step_trig
    axi_gpio_1  ←  mc_x   (Chua master x)
    axi_gpio_2  ←  mc_y   (Chua master y)
    axi_gpio_3  ←  mc_z   (Chua master z)
    axi_gpio_4  ←  sc_x   (Chua slave x)
    axi_gpio_5  ←  sc_y   (Chua slave y)
    axi_gpio_6  ←  sc_z   (Chua slave z)
    axi_gpio_7  ←  mr_x   (Rössler master x)
    axi_gpio_8  ←  mr_y   (Rössler master y)
    axi_gpio_9  ←  mr_z   (Rössler master z)
    axi_gpio_10 ←  sr_x   (Rössler slave x)
    axi_gpio_11 ←  sr_y   (Rössler slave y)
    axi_gpio_12 ←  m_combined_ks  (master Chua⊕Rössler keystream)
    axi_gpio_13 ←  s_combined_ks  (slave  Chua⊕Rössler keystream)

NOTE: AXI GPIO base addresses below must match what Vivado assigned in the
Address Editor (Tools → Address Editor in the block design view). The
defaults below assume Vivado's standard auto-increment starting at
0x4120_0000. If your build shows different addresses, edit GPIO_ADDR
to match.

Usage:
    sudo python3 single_board_hybrid_control.py --duration 10 --rate 1000
"""

import time
import csv
import argparse

try:
    from pynq import Overlay
    from pynq.lib import AxiGPIO
except ImportError:
    print("[WARNING] pynq not available — must run on PYNQ-Z2")
    Overlay = None

# Bitstream lives here on the board
BITSTREAM = "/home/xilinx/top_wrapper.bit"

# AXI GPIO base addresses (CONFIRM in Vivado Address Editor!)
# Each address corresponds to a single-channel AXI GPIO IP
GPIO_ADDR = {
    'ctrl':  0x41200000,   # axi_gpio_0  (output PS→PL: control)
    'mc_x':  0x41210000,   # axi_gpio_1
    'mc_y':  0x41220000,   # axi_gpio_2
    'mc_z':  0x41230000,   # axi_gpio_3
    'sc_x':  0x41240000,   # axi_gpio_4
    'sc_y':  0x41250000,   # axi_gpio_5
    'sc_z':  0x41260000,   # axi_gpio_6
    'mr_x':  0x41270000,   # axi_gpio_7
    'mr_y':  0x41280000,   # axi_gpio_8
    'mr_z':  0x41290000,   # axi_gpio_9
    'sr_x':  0x412A0000,   # axi_gpio_10
    'sr_y':  0x412B0000,   # axi_gpio_11
    'm_ks':  0x412C0000,   # axi_gpio_12
    's_ks':  0x412D0000,   # axi_gpio_13
}


def q16_to_float(val):
    """Convert Q16.16 (unsigned 32-bit read) to float."""
    val = val & 0xFFFFFFFF
    if val & 0x80000000:
        val -= 0x100000000
    return val / 65536.0


def main(duration, rate, out_csv):
    if Overlay is None:
        raise RuntimeError("pynq library required — run on PYNQ-Z2 board")

    print(f"Loading {BITSTREAM}...")
    ol = Overlay(BITSTREAM)

    print("Mapping AXI GPIO instances...")
    gpio = {name: AxiGPIO(addr).channel1
            for name, addr in GPIO_ADDR.items()}

    # ── Soft reset cycle ─────────────────────────────────────────────────────
    print("Issuing soft reset...")
    gpio['ctrl'].write(0x1)   # rst high
    time.sleep(0.001)
    gpio['ctrl'].write(0x0)   # rst low
    time.sleep(0.001)

    n_steps = int(duration * rate)
    step_interval = 1.0 / rate
    rows = []

    print(f"Logging {n_steps} steps at {rate} Hz...")
    t0 = time.time()
    for n in range(n_steps):
        # Pulse step_trig (bit 1) — edge detector in fabric produces 1-cycle pulse
        gpio['ctrl'].write(0x2)
        gpio['ctrl'].write(0x0)

        # Read all state words
        row = [
            n / rate,
            q16_to_float(gpio['mc_x'].read()),
            q16_to_float(gpio['mc_y'].read()),
            q16_to_float(gpio['mc_z'].read()),
            q16_to_float(gpio['sc_x'].read()),
            q16_to_float(gpio['sc_y'].read()),
            q16_to_float(gpio['sc_z'].read()),
            q16_to_float(gpio['mr_x'].read()),
            q16_to_float(gpio['mr_y'].read()),
            q16_to_float(gpio['mr_z'].read()),
            q16_to_float(gpio['sr_x'].read()),
            q16_to_float(gpio['sr_y'].read()),
            gpio['m_ks'].read() & 0xFFFF,
            gpio['s_ks'].read() & 0xFFFF,
        ]
        rows.append(row)

        # Pace
        target = t0 + (n + 1) * step_interval
        sleep = target - time.time()
        if sleep > 0:
            time.sleep(sleep)

    wall = time.time() - t0
    print(f"Done. {len(rows)} samples in {wall:.2f}s "
          f"(rate ≈ {len(rows)/wall:.1f} Hz)")

    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t', 'mc_x', 'mc_y', 'mc_z', 'sc_x', 'sc_y', 'sc_z',
                    'mr_x', 'mr_y', 'mr_z', 'sr_x', 'sr_y',
                    'm_combined_ks', 's_combined_ks'])
        w.writerows(rows)
    print(f"Saved → {out_csv}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--rate", type=float, default=1000.0)
    p.add_argument("--out", default="hybrid_data.csv")
    args = p.parse_args()
    main(args.duration, args.rate, args.out)
