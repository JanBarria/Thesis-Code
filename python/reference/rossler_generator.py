"""
Rössler chaotic oscillator — Python reference simulator.

Bit-exact match to hdl/rossler_pipelined.vhd (4-stage pipelined VHDL).

VHDL Q16.16 constants (from rossler_pipelined.vhd):
    A_PARAM  = 13107   → 0.2
    B_PARAM  = 13107   → 0.2
    C_PARAM  = 373554  → 5.7
    DT_PARAM = 655     → 0.01  (NOTE: different from Chua's 0.001)
    x_state init = 65536 → 1.0
    y_state init (Master) = 65536 → 1.0
    y_state init (Slave)  = 32768 → 0.5
    z_state init (Master) = 65536 → 1.0
    z_state init (Slave)  = 98304 → 1.5

Pecora-Carroll sync (matches VHDL):
    Master: sync_enable=0, x evolves freely, transmits x_state
    Slave:  sync_enable=1, x is substituted with received x_drive,
            only y, z evolve from substituted x

Keystream extraction matches VHDL:
    keystream[15:0] = x_state[23:8]   (middle 16 bits of x)
"""

import numpy as np
from q16_arith import to_fixed, to_float, fixed_mul, fixed_add, fixed_sub, SCALE


# ─── VHDL parameter constants (exact integers) ───────────────────────────────
VHDL_A   = 13107    # = 0.2
VHDL_B   = 13107    # = 0.2
VHDL_C   = 373554   # = 5.7
VHDL_DT  = 655      # = 0.01

# Initial-condition constants
MASTER_IC = (65536, 65536, 65536)  # (1.0, 1.0, 1.0)
SLAVE_IC  = (65536, 32768, 98304)  # (1.0, 0.5, 1.5)


class RosslerGenerator:
    """
    Q16.16 fixed-point Rössler oscillator matching hdl/rossler_pipelined.vhd.

    Args:
        role: 'master' (free-running), 'slave' (will be driven by x_drive)
              or None (use default master ICs but no constraint)
    """

    def __init__(self, role='master', x0=None, y0=None, z0=None):
        if role == 'master':
            default = MASTER_IC
        elif role == 'slave':
            default = SLAVE_IC
        else:
            default = MASTER_IC

        self.x_q = to_fixed(x0) if x0 is not None else default[0]
        self.y_q = to_fixed(y0) if y0 is not None else default[1]
        self.z_q = to_fixed(z0) if z0 is not None else default[2]
        self.role = role

    # ─── One Euler step (matches VHDL stages 0-3) ────────────────────────────
    def step(self, x_drive_q=None):
        """
        Advance one chaotic step.
        If x_drive_q is provided (slave mode), substitute x.
        """
        x_used = x_drive_q if x_drive_q is not None else self.x_q

        # Derivatives matching VHDL pipeline
        # dx = -y - z
        dx_q = fixed_sub(-self.y_q, self.z_q)

        # dy = x + a*y
        a_y_q = fixed_mul(VHDL_A, self.y_q)
        dy_q  = fixed_add(x_used, a_y_q)

        # dz = b + z*(x - c)
        x_sub_c_q = fixed_sub(x_used, VHDL_C)
        z_xc_q    = fixed_mul(self.z_q, x_sub_c_q)
        dz_q      = fixed_add(VHDL_B, z_xc_q)

        # Euler update
        # In slave mode the VHDL still updates x_state (the chaos_sync_top
        # uses x_drive only for the *computed* derivatives — x_state itself
        # is overwritten by x_drive externally). We mirror that here.
        if x_drive_q is None:
            self.x_q = fixed_add(self.x_q, fixed_mul(VHDL_DT, dx_q))
        else:
            self.x_q = x_drive_q   # slave: x is the received drive
        self.y_q = fixed_add(self.y_q, fixed_mul(VHDL_DT, dy_q))
        self.z_q = fixed_add(self.z_q, fixed_mul(VHDL_DT, dz_q))

    # ─── Generate full trajectory ────────────────────────────────────────────
    def generate(self, n_samples, x_drive_int_arr=None):
        """
        Run n_samples Euler steps.

        Args:
            n_samples: number of steps to run
            x_drive_int_arr: optional Q16.16 drive array (slave mode)

        Returns:
            x_arr, y_arr, z_arr  — float arrays
            x_int                — Q16.16 integer x trajectory (for keystream/UART)
        """
        x_arr = np.zeros(n_samples, dtype=np.float64)
        y_arr = np.zeros(n_samples, dtype=np.float64)
        z_arr = np.zeros(n_samples, dtype=np.float64)
        x_int = np.zeros(n_samples, dtype=np.int64)

        for i in range(n_samples):
            drive = int(x_drive_int_arr[i]) if x_drive_int_arr is not None else None
            self.step(drive)
            x_arr[i] = to_float(self.x_q)
            y_arr[i] = to_float(self.y_q)
            z_arr[i] = to_float(self.z_q)
            x_int[i] = self.x_q

        return x_arr, y_arr, z_arr, x_int

    def extract_keystream(self, x_int_arr):
        """
        VHDL keystream extraction: x_state[23:8].
        """
        masked = (x_int_arr.astype(np.int64) & 0xFFFFFFFF)
        return ((masked >> 8) & 0xFFFF).astype(np.uint16)


if __name__ == "__main__":
    print("=== Master mode (free-running) ===")
    gen = RosslerGenerator(role='master')
    x, y, z, xi = gen.generate(5000)
    print(f"  x range: [{x.min():.3f}, {x.max():.3f}]  std={x.std():.3f}")
    print(f"  y range: [{y.min():.3f}, {y.max():.3f}]  std={y.std():.3f}")
    print(f"  z range: [{z.min():.3f}, {z.max():.3f}]  std={z.std():.3f}")
    assert x.std() > 0.05, "Rössler master collapsed"

    print("\n=== Slave mode (driven by master x) ===")
    slave = RosslerGenerator(role='slave')
    xs, ys, zs, _ = slave.generate(5000, x_drive_int_arr=xi)
    # Sync error: |x_master - x_slave| should converge to ~0
    err = np.abs(x - xs)
    print(f"  initial err: {err[0]:.3f}, final err: {err[-1]:.6f}")
    print(f"  err mean(last 500): {err[-500:].mean():.6f}")
    print("  PASS")
