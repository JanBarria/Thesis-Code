"""
Chua circuit chaotic oscillator — Python reference simulator.

Bit-exact match to hdl/chua_core.vhd (5-stage pipelined VHDL).

VHDL Q16.16 constants (from chua_core.vhd):
    ALPHA = 1022976  → 15.6093
    BETA  = 1835008  → 28.0
    M0    = -74907   → -1.143  (inner segment slope)
    M1    = -46792   → -0.714  (outer segment slope)
    DT    = 66       → 0.00101
    x0    = 6554     → 0.1
    half_diff = -14058 → 0.5 * (m0 - m1) = -0.2145

Classical Chua diode (matches VHDL):
    f(x) = m1*x + 0.5*(m0-m1) * (|x+1| - |x-1|)

Keystream extraction matches VHDL:
    keystream[15:0] = x_state[23:8]   (middle 16 bits of x)
"""

import numpy as np
from q16_arith import to_fixed, to_float, fixed_mul, fixed_add, fixed_sub, SCALE


# ─── VHDL parameter constants (exact integers) ───────────────────────────────
VHDL_ALPHA = 1022976   # = 15.6093
VHDL_BETA  = 1835008   # = 28.0
VHDL_M0    = -74907    # = -1.143 (inner slope)
VHDL_M1    = -46792    # = -0.714 (outer slope)
VHDL_DT    = 66        # = 0.001007
VHDL_HALF_DIFF = -14058  # = 0.5*(M0-M1) = -0.21449
VHDL_FP_ONE    = 65536   # = 1.0

VHDL_X0_INT = 6554   # = 0.1
VHDL_Y0_INT = 0      # = 0.0
VHDL_Z0_INT = 0      # = 0.0


class ChuaGenerator:
    """
    Q16.16 fixed-point Chua oscillator matching hdl/chua_core.vhd.

    Reset values reproduce the VHDL pipeline initial state:
        x0=0.1, y0=0.0, z0=0.0
    """

    def __init__(self, x0=None, y0=None, z0=None):
        # If user passes a float, convert; otherwise use VHDL reset value
        self.x_q = to_fixed(x0) if x0 is not None else VHDL_X0_INT
        self.y_q = to_fixed(y0) if y0 is not None else VHDL_Y0_INT
        self.z_q = to_fixed(z0) if z0 is not None else VHDL_Z0_INT

    # ─── Chua diode (matches VHDL stages 1-3 logic) ──────────────────────────
    def _chua_diode_fixed(self, x_q):
        """
        f(x) = m1*x + half_diff * (|x+1| - |x-1|)
        Computed in Q16.16, mirroring VHDL pipeline.
        """
        m1x_q     = fixed_mul(VHDL_M1, x_q)
        x_p1_q    = fixed_add(x_q,  VHDL_FP_ONE)
        x_m1_q    = fixed_sub(x_q,  VHDL_FP_ONE)
        abs_xp1_q = abs(x_p1_q)
        abs_xm1_q = abs(x_m1_q)
        abs_diff  = fixed_sub(abs_xp1_q, abs_xm1_q)
        hd_term   = fixed_mul(VHDL_HALF_DIFF, abs_diff)
        return fixed_add(m1x_q, hd_term)

    # ─── One Euler step (matches VHDL stages 4-5) ────────────────────────────
    def step(self, x_drive_q=None):
        """
        Advance one chaotic step.
        If x_drive_q is provided, substitute x with it (true Pecora-Carroll sync).
        """
        x_used = x_drive_q if x_drive_q is not None else self.x_q

        fx_q       = self._chua_diode_fixed(x_used)
        y_minus_x  = fixed_sub(self.y_q, x_used)
        alpha_arg  = fixed_sub(y_minus_x, fx_q)

        dx_q = fixed_mul(VHDL_ALPHA, alpha_arg)
        dy_q = fixed_add(fixed_sub(x_used, self.y_q), self.z_q)
        dz_q = -fixed_mul(VHDL_BETA, self.y_q)

        # Euler update.  In PC slave mode the VHDL pipeline drives
        # x_s0 from x_drive (the chaos_sync_top mux), so the integrated
        # x_state tracks the master's x rather than drifting on its own.
        # We mirror that here by substituting x_used in the x update.
        if x_drive_q is None:
            self.x_q = fixed_add(self.x_q, fixed_mul(VHDL_DT, dx_q))
        else:
            self.x_q = x_drive_q
        self.y_q = fixed_add(self.y_q, fixed_mul(VHDL_DT, dy_q))
        self.z_q = fixed_add(self.z_q, fixed_mul(VHDL_DT, dz_q))

    # ─── Generate full trajectory ────────────────────────────────────────────
    def generate(self, n_samples, x_drive_int_arr=None):
        """
        Run n_samples Euler steps.

        Args:
            n_samples: number of steps to run
            x_drive_int_arr: optional Q16.16 integer drive array (Pecora-Carroll
                             slave mode). If provided, x is substituted from
                             this array at each step.

        Returns:
            x_arr, y_arr, z_arr  — float arrays
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
        VHDL keystream extraction: x_state[23:8] (middle 16 bits of x).
        """
        # Mask 32-bit signed → take bits [23:8]
        masked = (x_int_arr.astype(np.int64) & 0xFFFFFFFF)
        return ((masked >> 8) & 0xFFFF).astype(np.uint16)


if __name__ == "__main__":
    # Sanity test: generate 5000 samples and verify chaos
    gen = ChuaGenerator()
    x, y, z, xi = gen.generate(5000)
    print(f"Chua generator test:")
    print(f"  x range: [{x.min():.3f}, {x.max():.3f}]  std={x.std():.3f}")
    print(f"  y range: [{y.min():.3f}, {y.max():.3f}]  std={y.std():.3f}")
    print(f"  z range: [{z.min():.3f}, {z.max():.3f}]  std={z.std():.3f}")
    assert x.std() > 0.05, "Chua collapse — should have std > 0.05"
    ks = gen.extract_keystream(xi)
    print(f"  Keystream uint16 sample: {ks[:5]}")
    print("  PASS")
