"""
Single-board chaos_sync simulator — Python reference for SO3.

Mirrors hdl/chaos_sync_single_board.vhd in software:
  - One MASTER RosslerGenerator (Y0=1.0, Z0=1.0, sync_enable=0)
  - One SLAVE  RosslerGenerator (Y0=0.5, Z0=1.5, sync_enable=1)
  - Each "step" advances BOTH cores by one Forward Euler step
  - Slave's x is overwritten by master's x (fabric coupling in hardware)

Outputs time-series arrays that match what the hardware logs over AXI GPIO.

Convergence proof:
  Pearson r and e(t) should be ≈ 1.0 / 0 on y AND z (NOT x — x sync is
  trivial by construction). See docs/SINGLE_BOARD_SO3.md for the rationale.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from rossler_generator import RosslerGenerator


class SingleBoardSync:
    """
    Software model of chaos_sync_single_board.vhd.

    Step rate is implicit — each call to step() advances both cores once.
    The hardware equivalent is a single state_step pulse from the
    edge_detector, fanned out to both rossler_pipelined instances.
    """

    def __init__(self):
        self.master = RosslerGenerator(role='master')   # IC = (1.0, 1.0, 1.0)
        self.slave  = RosslerGenerator(role='slave')    # IC = (1.0, 0.5, 1.5)

    def step(self):
        """One atomic step of both cores. Slave's x is driven by master's x."""
        # Capture master's current x BEFORE advancing it — this is what
        # the slave's x_drive port sees during the same clock cycle.
        # (In hardware, master.x_out is read combinationally; in our Python
        #  model we read it before stepping master to mirror that timing.)
        x_master_now = self.master.x_q

        # Master advances freely
        self.master.step()

        # Slave: x is overwritten by master's pre-step x
        # (matches VHDL stage_0 mux: x_s0 <= signed(x_drive))
        # After substitution, slave.step() integrates y, z using x = x_drive.
        self.slave.step(x_drive_q=x_master_now)

    def run(self, n_steps):
        """
        Run n_steps and return arrays compatible with what the hardware
        would have logged via AXI GPIO.

        Returns:
            dict of float64 arrays, length n_steps:
                m_x, m_y, m_z  — master state
                s_x, s_y, s_z  — slave state
                m_ks, s_ks     — 16-bit keystreams (uint16)
        """
        mx = np.zeros(n_steps); my = np.zeros(n_steps); mz = np.zeros(n_steps)
        sx = np.zeros(n_steps); sy = np.zeros(n_steps); sz = np.zeros(n_steps)
        mk = np.zeros(n_steps, dtype=np.uint16)
        sk = np.zeros(n_steps, dtype=np.uint16)

        SCALE = 65536
        for i in range(n_steps):
            self.step()
            mx[i] = self.master.x_q / SCALE
            my[i] = self.master.y_q / SCALE
            mz[i] = self.master.z_q / SCALE
            sx[i] = self.slave.x_q  / SCALE
            sy[i] = self.slave.y_q  / SCALE
            sz[i] = self.slave.z_q  / SCALE
            # Keystream = x_state[23:8]
            mk[i] = ((self.master.x_q & 0xFFFFFFFF) >> 8) & 0xFFFF
            sk[i] = ((self.slave.x_q  & 0xFFFFFFFF) >> 8) & 0xFFFF

        return {
            'm_x': mx, 'm_y': my, 'm_z': mz,
            's_x': sx, 's_y': sy, 's_z': sz,
            'm_ks': mk, 's_ks': sk,
        }


def sync_metrics(data):
    """
    Compute the metrics that *actually* prove SO3 — Pearson r on y and z.
    r_x is included for completeness but flagged as trivial.
    """
    def pearson(a, b):
        if a.std() < 1e-9 or b.std() < 1e-9:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    r_x = pearson(data['m_x'], data['s_x'])
    r_y = pearson(data['m_y'], data['s_y'])
    r_z = pearson(data['m_z'], data['s_z'])

    e_y = np.abs(data['m_y'] - data['s_y'])
    e_z = np.abs(data['m_z'] - data['s_z'])
    e_combined = np.sqrt((data['m_y'] - data['s_y'])**2
                       + (data['m_z'] - data['s_z'])**2)

    return {
        'r_x_trivial': r_x,
        'r_y'        : r_y,
        'r_z'        : r_z,
        'e_y_final'  : float(e_y[-500:].mean()),
        'e_z_final'  : float(e_z[-500:].mean()),
        'e_combined_final': float(e_combined[-500:].mean()),
    }


if __name__ == "__main__":
    print("=== Single-board sync sim (5000 steps) ===")
    sim = SingleBoardSync()
    data = sim.run(5000)
    m = sync_metrics(data)

    print(f"  r_x (trivial, slave x driven by master) : {m['r_x_trivial']:.6f}")
    print(f"  r_y (meaningful proof of sync)          : {m['r_y']:.6f}")
    print(f"  r_z (meaningful proof of sync)          : {m['r_z']:.6f}")
    print(f"  e_y final 500 steps                     : {m['e_y_final']:.6e}")
    print(f"  e_z final 500 steps                     : {m['e_z_final']:.6e}")
    print(f"  e_combined final 500 steps              : {m['e_combined_final']:.6e}")
    pass_yz = m['r_y'] >= 0.95 and m['r_z'] >= 0.95
    print(f"  Verdict: {'PASS (r_y,r_z >= 0.95)' if pass_yz else 'FAIL'}")
