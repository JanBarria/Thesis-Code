"""
Single-board hybrid chaos_sync simulator — Python reference for SO3.

Mirrors hdl/chaos_hybrid_single_board.vhd: four oscillator instances on
one chip, master/slave for both Chua and Rössler, fabric-coupled.

The combined master keystream is XOR'd with audio for encryption; the
combined slave keystream should match after Chua y-z convergence.

Sync proof: Chua's y and z subsystem driven by x has all-negative
conditional Lyapunov exponents, so the Chua slave's (y, z) genuinely
converge to the Chua master's (y, z). This is the SO3 evidence.

Rössler caveat (also true in hardware): its y subsystem has positive
conditional Lyapunov exponent — y diverges. The hybrid still decrypts
correctly because the keystream is extracted from x, which is trivially
matched on master and slave by the substitution in fabric.

See docs/HYBRID_ENCRYPTION.md and docs/SINGLE_BOARD_SO3.md.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from chua_generator    import ChuaGenerator
from rossler_generator import RosslerGenerator


class SingleBoardHybridSync:
    """
    Software model of chaos_hybrid_single_board.vhd.

    All four oscillators advance in lockstep (one step() call advances
    each by one Euler step). x_drive coupling is in-process.
    """

    def __init__(self):
        # Chua master: VHDL default ICs (0.1, 0.0, 0.0)
        self.chua_master = ChuaGenerator()
        # Chua slave: deliberately different y, z to show convergence
        self.chua_slave  = ChuaGenerator(x0=0.1, y0=0.3, z0=0.2)

        # Rössler master: (1.0, 1.0, 1.0)
        self.rossler_master = RosslerGenerator(role='master')
        # Rössler slave: (1.0, 0.5, 1.5) — different ICs to show partial sync
        self.rossler_slave  = RosslerGenerator(role='slave')

    def step(self):
        """One atomic step of all four cores. Slaves take master x as drive."""
        # Capture master x BEFORE advancing (matches VHDL fabric timing)
        x_chua_master_now    = self.chua_master.x_q
        x_rossler_master_now = self.rossler_master.x_q

        # Advance masters freely
        self.chua_master.step()
        self.rossler_master.step()

        # Advance slaves with drive
        self.chua_slave.step(x_drive_q=x_chua_master_now)
        self.rossler_slave.step(x_drive_q=x_rossler_master_now)

    def run(self, n_steps):
        """Run n_steps and return time series + combined keystreams."""
        S = 65536
        arrs = {k: np.zeros(n_steps) for k in
                ('mc_x','mc_y','mc_z','sc_x','sc_y','sc_z',
                 'mr_x','mr_y','mr_z','sr_x','sr_y','sr_z')}
        mc_int = np.zeros(n_steps, dtype=np.int64)
        sc_int = np.zeros(n_steps, dtype=np.int64)
        mr_int = np.zeros(n_steps, dtype=np.int64)
        sr_int = np.zeros(n_steps, dtype=np.int64)

        for i in range(n_steps):
            self.step()
            arrs['mc_x'][i] = self.chua_master.x_q/S
            arrs['mc_y'][i] = self.chua_master.y_q/S
            arrs['mc_z'][i] = self.chua_master.z_q/S
            arrs['sc_x'][i] = self.chua_slave.x_q/S
            arrs['sc_y'][i] = self.chua_slave.y_q/S
            arrs['sc_z'][i] = self.chua_slave.z_q/S
            arrs['mr_x'][i] = self.rossler_master.x_q/S
            arrs['mr_y'][i] = self.rossler_master.y_q/S
            arrs['mr_z'][i] = self.rossler_master.z_q/S
            arrs['sr_x'][i] = self.rossler_slave.x_q/S
            arrs['sr_y'][i] = self.rossler_slave.y_q/S
            arrs['sr_z'][i] = self.rossler_slave.z_q/S
            mc_int[i] = self.chua_master.x_q
            sc_int[i] = self.chua_slave.x_q
            mr_int[i] = self.rossler_master.x_q
            sr_int[i] = self.rossler_slave.x_q

        # Keystream extraction matches VHDL: x_state[23:8]
        def ks(arr):
            return ((arr.astype(np.int64) & 0xFFFFFFFF) >> 8 & 0xFFFF).astype(np.uint16)

        mc_ks = ks(mc_int); sc_ks = ks(sc_int)
        mr_ks = ks(mr_int); sr_ks = ks(sr_int)

        arrs['mc_ks'] = mc_ks
        arrs['sc_ks'] = sc_ks
        arrs['mr_ks'] = mr_ks
        arrs['sr_ks'] = sr_ks
        arrs['m_combined_ks'] = np.bitwise_xor(mc_ks, mr_ks).astype(np.uint16)
        arrs['s_combined_ks'] = np.bitwise_xor(sc_ks, sr_ks).astype(np.uint16)
        return arrs


def sync_metrics(d):
    """
    Compute the meaningful SO3 metrics.

    For each subsystem, r_x is trivially ~1.0 (substitution) and excluded
    from the "is sync achieved" verdict. The real proof is r_y and r_z.
    """
    def pearson(a, b):
        if a.std() < 1e-9 or b.std() < 1e-9:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    out = {
        # CHUA subsystem (full PC sync expected)
        'chua_r_x_trivial': pearson(d['mc_x'], d['sc_x']),
        'chua_r_y'        : pearson(d['mc_y'], d['sc_y']),
        'chua_r_z'        : pearson(d['mc_z'], d['sc_z']),
        'chua_e_y_final'  : float(np.abs(d['mc_y'] - d['sc_y'])[-500:].mean()),
        'chua_e_z_final'  : float(np.abs(d['mc_z'] - d['sc_z'])[-500:].mean()),

        # ROSSLER subsystem (only partial PC sync expected)
        'rossler_r_x_trivial': pearson(d['mr_x'], d['sr_x']),
        'rossler_r_y_diverges': pearson(d['mr_y'], d['sr_y']),
        'rossler_r_z'        : pearson(d['mr_z'], d['sr_z']),

        # HYBRID combined keystreams should match (after Chua converges)
        'combined_ks_match_rate': float(np.mean(
            d['m_combined_ks'][-500:] == d['s_combined_ks'][-500:])),
    }
    return out


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=50000,
                   help="Number of Euler steps to simulate (default 50000 — enough for Chua sync)")
    args = p.parse_args()

    print("="*70)
    print(f"  SINGLE-BOARD HYBRID SYNC SIM ({args.steps} steps)")
    print("="*70)
    sim = SingleBoardHybridSync()
    d   = sim.run(args.steps)
    m   = sync_metrics(d)

    print("\n--- CHUA subsystem (textbook PC sync expected) ---")
    print(f"  r_x (trivial, by substitution) : {m['chua_r_x_trivial']:.6f}")
    print(f"  r_y (MEANINGFUL)               : {m['chua_r_y']:.6f}  "
          f"{'PASS' if m['chua_r_y'] >= 0.95 else 'FAIL'}")
    print(f"  r_z (MEANINGFUL)               : {m['chua_r_z']:.6f}  "
          f"{'PASS' if m['chua_r_z'] >= 0.95 else 'FAIL'}")
    print(f"  e_y final 500 steps            : {m['chua_e_y_final']:.6e}")
    print(f"  e_z final 500 steps            : {m['chua_e_z_final']:.6e}")

    print("\n--- ROSSLER subsystem (only partial PC sync, by theory) ---")
    print(f"  r_x (trivial, by substitution) : {m['rossler_r_x_trivial']:.6f}")
    print(f"  r_y (DIVERGES, expected)       : {m['rossler_r_y_diverges']:.6f}")
    print(f"  r_z (CONVERGES, expected)      : {m['rossler_r_z']:.6f}  "
          f"{'PASS' if m['rossler_r_z'] >= 0.95 else 'FAIL'}")

    print("\n--- HYBRID combined keystream ---")
    print(f"  master/slave combined-ks match rate (last 500): "
          f"{m['combined_ks_match_rate']*100:.1f}%")

    verdict = ('PASS' if (m['chua_r_y'] >= 0.95 and m['chua_r_z'] >= 0.95
                          and m['rossler_r_z'] >= 0.95) else 'FAIL')
    print(f"\nVerdict (SO3): {verdict}")
    print("  SO3 sync proof rests on Chua y,z convergence (rigorous)")
    print("  Rössler contributes keystream entropy via x-trivial sync only")
