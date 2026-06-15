"""
Hybrid Chua ⊕ Rössler keystream generator.

This module composes the two existing chaotic generators into a single
combined-keystream source for the unified thesis design:

    K_combined[n] = K_chua[n] XOR K_rossler[n]

Both chaos systems advance independently with their own dt (Chua 0.001,
Rössler 0.01) — they don't have to step in lockstep because each
generates its own 16-bit stream value per Euler step. The combiner XORs
them sample-by-sample at the output stage, just before XOR-encryption
with audio.

Why this is more secure than either alone:
  1. Effective key space doubles: requires breaking BOTH systems.
  2. Statistical entropy of the combined stream is ≥ entropy of either
     alone, by the convolution-of-pmfs argument for independent streams.
  3. Combined stream is resistant to chaos-parameter-estimation attacks
     against a single oscillator (an attacker fitting a Chua model to the
     observed keystream will see Rössler-shaped noise residuals, and
     vice versa).

Why this works for the thesis SO3 claim:
  - Chua x-drive Pecora-Carroll DOES achieve true subsystem sync:
    y, z subsystem driven by x is asymptotically stable for the
    canonical parameters → r_y, r_z ≥ 0.95 demonstrable.
  - Rössler x-drive does NOT achieve full PC sync (y subsystem has
    positive conditional Lyapunov exponent) — its contribution here
    is keystream entropy, not state synchronization.
  - The thesis SO3 evidence rests on Chua. Rössler appears in SO5 as
    the second keystream source.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from chua_generator    import ChuaGenerator
from rossler_generator import RosslerGenerator


class HybridGenerator:
    """
    Combined Chua + Rössler keystream generator.

    Both subsystems run in lockstep at the Python level (one Euler step
    each per `generate` iteration). Each contributes a 16-bit keystream
    sample; the outputs are XORed to form the combined keystream.

    Args:
        chua_ics    : dict with x0,y0,z0 for Chua (None → VHDL default)
        rossler_role: 'master' or 'slave' — selects Rössler IC defaults
        rossler_ics : optional override dict for Rössler ICs
    """

    def __init__(self, chua_ics=None, rossler_role='master', rossler_ics=None):
        cics = chua_ics or {}
        rics = rossler_ics or {}
        self.chua    = ChuaGenerator(
            x0=cics.get('x0'), y0=cics.get('y0'), z0=cics.get('z0'))
        self.rossler = RosslerGenerator(
            role=rossler_role,
            x0=rics.get('x0'), y0=rics.get('y0'), z0=rics.get('z0'))

    def generate(self, n_samples, chua_drive=None, rossler_drive=None):
        """
        Generate n_samples worth of (chua_state, rossler_state, combined_keystream).

        Args:
            n_samples     : number of Euler steps each subsystem runs
            chua_drive    : optional Q16.16 x-drive array for Chua (slave/PC mode)
            rossler_drive : optional Q16.16 x-drive array for Rössler

        Returns:
            dict with:
              chua    = {x, y, z, x_int}     float arrays + int trajectory
              rossler = {x, y, z, x_int}
              keystream = combined uint16 array (chua_ks XOR rossler_ks)
        """
        cx, cy, cz, cxi = self.chua.generate(n_samples, x_drive_int_arr=chua_drive)
        rx, ry, rz, rxi = self.rossler.generate(n_samples, x_drive_int_arr=rossler_drive)
        chua_ks    = self.chua.extract_keystream(cxi)
        rossler_ks = self.rossler.extract_keystream(rxi)
        combined   = np.bitwise_xor(chua_ks, rossler_ks).astype(np.uint16)

        return {
            'chua':    {'x': cx, 'y': cy, 'z': cz, 'x_int': cxi, 'ks': chua_ks},
            'rossler': {'x': rx, 'y': ry, 'z': rz, 'x_int': rxi, 'ks': rossler_ks},
            'keystream': combined,
        }


if __name__ == "__main__":
    print("=== Hybrid keystream sanity test ===")
    gen = HybridGenerator()
    data = gen.generate(5000)
    ks = data['keystream']
    print(f"  Chua    keystream sample: {data['chua']['ks'][:5]}")
    print(f"  Rössler keystream sample: {data['rossler']['ks'][:5]}")
    print(f"  Combined sample:          {ks[:5]}")
    print(f"  Combined entropy (bits/byte estimate from byte histogram):")
    # Crude entropy estimate
    ks_bytes = ks.tobytes()
    hist = np.bincount(np.frombuffer(ks_bytes, dtype=np.uint8), minlength=256)
    p = hist / hist.sum()
    p = p[p > 0]
    H = -np.sum(p * np.log2(p))
    print(f"    H = {H:.4f}  (ideal = 8.0)")
    print("  PASS" if H > 7.5 else "  WARN: entropy low")
