"""
================================================================================
FILE: rossler_chaotic_generator.py
SYSTEM: Rössler System Chaotic Oscillator — TRANSMITTER & RECEIVER
================================================================================
DESCRIPTION:
    Implements the discretized Rössler chaotic oscillator using Forward Euler
    with Q16.16 fixed-point arithmetic simulation.
    Generates the spiral attractor used as the chaotic keystream source.

STATE EQUATIONS:
    dx/dt = -y - z
    dy/dt =  x + a*y
    dz/dt =  b + z*(x - c)

PARAMETERS:
    a=0.2, b=0.2, c=5.7
    dt=0.05 (larger dt viable due to smooth nonlinearity)

HOW TO RUN:
    from rossler_chaotic_generator import RosslerGenerator
    gen = RosslerGenerator()
    x_arr, y_arr, z_arr = gen.generate(n_samples=44100)

EXPECTED OUTPUT:
    Three numpy arrays (x, y, z) of shape (n_samples,)

NOTE FOR TEAM (Cortes & Abalos):
    The Rössler system has SMOOTH quadratic nonlinearity (z*x product),
    which requires DSP48 multiplier blocks in VHDL — plan your
    pipeline registers accordingly to meet timing closure.
================================================================================
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Q16.16 FIXED-POINT HELPERS (identical interface to chua module)
# ─────────────────────────────────────────────────────────────────────────────

FRAC_BITS = 16
SCALE     = 1 << FRAC_BITS
MAX_Q     = (1 << 31) - 1
MIN_Q     = -(1 << 31)


def to_fixed(x):
    return int(round(x * SCALE))


def to_float(q):
    return q / SCALE


def fixed_mul(a, b):
    result = (a * b) >> FRAC_BITS
    return int(np.clip(result, MIN_Q, MAX_Q))


def fixed_add(a, b):
    result = a + b
    return int(np.clip(result, MIN_Q, MAX_Q))


# ─────────────────────────────────────────────────────────────────────────────
# RÖSSLER GENERATOR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class RosslerGenerator:
    """
    Rössler system chaotic oscillator with Q16.16 fixed-point arithmetic.

    Advantages over Chua for FPGA:
        - Smooth nonlinearity (one z*x multiply vs piecewise Chua diode)
        - Lower arithmetic complexity → higher achievable clock speeds
        - Reduced quantization-induced degradation at boundaries
        - Produces spiral attractor with well-characterized entropy

    Attributes:
        a, b, c  (float): Bifurcation parameters
        dt       (float): Integration time step — VHDL: 1310/65536 ≈ 0.02
        x0,y0,z0 (float): Initial conditions — VHDL resets to (1.0, 1.0, 1.0)

    NOTE: dt and initial conditions are matched to rossler_core.vhd.
    The VHDL resets all state registers to 65536 (= 1.0 in Q16.16) and
    uses 1310/65536 as the Euler step, identical to chua_core.vhd.
    """

    # Exact Q16.16 integer from rossler_core.vhd, decoded
    _VHDL_DT = 1310 / 65536   # ≈ 0.01999

    def __init__(self,
                 a=0.2, b=0.2, c=5.7,
                 dt=1310/65536,
                 x0=1.0, y0=1.0, z0=1.0):

        # ── Parameter validation ──────────────────────────────────────────
        assert a > 0,          "Parameter a must be positive for chaos"
        assert b > 0,          "Parameter b must be positive for chaos"
        assert c > 0,          "Parameter c must be positive for chaos"
        assert 0 < dt <= 0.1,  "dt too large — may diverge"

        self.a  = a
        self.b  = b
        self.c  = c
        self.dt = dt

        self.x0 = x0
        self.y0 = y0
        self.z0 = z0

        # Q16.16 parameter representations
        self._a_q  = to_fixed(a)
        self._b_q  = to_fixed(b)
        self._c_q  = to_fixed(c)
        self._dt_q = to_fixed(dt)

    # ── Modulo-Map Stabilization ──────────────────────────────────────────
    def _stabilize(self, q, bound=500.0):
        """
        Safety clamp only — rossler_core.vhd has NO modulo stabilization.
        Bound is set high (500) so it never triggers during normal operation,
        matching VHDL behavior while preventing Python float overflow.
        """
        x = to_float(q)
        if abs(x) > bound:
            x = (x + bound) % (2 * bound) - bound
        return to_fixed(x)

    # ── Overflow / Collapse Detection ─────────────────────────────────────
    def _check_chaos(self, trajectory, window=500):
        """Verify spiral attractor has not degenerated."""
        if len(trajectory) < window:
            return
        recent  = np.array(trajectory[-window:])
        std_val = np.std(recent)
        assert std_val > 0.01, (
            f"CHAOS COLLAPSE in Rössler: std={std_val:.6f}. "
            f"Reduce dt or adjust parameters."
        )

    # ── Main Generation ────────────────────────────────────────────────────
    def generate(self, n_samples):
        """
        Generate n_samples of Rössler chaotic trajectory.

        The quadratic nonlinearity z*(x-c) is computed as:
            z*(x-c) = z*x - z*c
        Using two fixed-point multiplications — matches the pipelined
        multiplier block architecture in VHDL implementation.

        Args:
            n_samples (int): Number of samples (match audio length)

        Returns:
            tuple: (x_arr, y_arr, z_arr) — float64 numpy arrays
        """
        x_arr = np.zeros(n_samples, dtype=np.float64)
        y_arr = np.zeros(n_samples, dtype=np.float64)
        z_arr = np.zeros(n_samples, dtype=np.float64)

        # ── Initialize in Q16.16 ──────────────────────────────────────────
        x_q = to_fixed(self.x0)
        y_q = to_fixed(self.y0)
        z_q = to_fixed(self.z0)

        # ── Warm-up ───────────────────────────────────────────────────────
        print("[RosslerGenerator] Warming up oscillator (2000 steps)...")
        for _ in range(2000):
            # dx = -y - z
            dx_q = fixed_add(-y_q, -z_q)

            # dy = x + a*y
            dy_q = fixed_add(x_q, fixed_mul(self._a_q, y_q))

            # dz = b + z*(x - c)
            # Computed as: b + z*x - z*c  (two multiplications)
            zx_q  = fixed_mul(z_q, x_q)
            zc_q  = fixed_mul(z_q, self._c_q)
            dz_q  = fixed_add(self._b_q, fixed_add(zx_q, -zc_q))

            x_q = self._stabilize(fixed_add(x_q, fixed_mul(self._dt_q, dx_q)))
            y_q = self._stabilize(fixed_add(y_q, fixed_mul(self._dt_q, dy_q)))
            z_q = self._stabilize(fixed_add(z_q, fixed_mul(self._dt_q, dz_q)),
                                  bound=30.0)   # z has larger range

        # ── Main loop ─────────────────────────────────────────────────────
        print(f"[RosslerGenerator] Generating {n_samples} chaotic samples...")
        x_list = []

        for i in range(n_samples):
            dx_q = fixed_add(-y_q, -z_q)
            dy_q = fixed_add(x_q, fixed_mul(self._a_q, y_q))

            zx_q = fixed_mul(z_q, x_q)
            zc_q = fixed_mul(z_q, self._c_q)
            dz_q = fixed_add(self._b_q, fixed_add(zx_q, -zc_q))

            x_q = self._stabilize(fixed_add(x_q, fixed_mul(self._dt_q, dx_q)))
            y_q = self._stabilize(fixed_add(y_q, fixed_mul(self._dt_q, dy_q)))
            z_q = self._stabilize(fixed_add(z_q, fixed_mul(self._dt_q, dz_q)),
                                  bound=30.0)

            x_arr[i] = to_float(x_q)
            y_arr[i] = to_float(y_q)
            z_arr[i] = to_float(z_q)

            x_list.append(x_arr[i])

            if i > 0 and i % 5000 == 0:
                self._check_chaos(x_list)

        print(f"[RosslerGenerator] Done. x range: "
              f"[{x_arr.min():.3f}, {x_arr.max():.3f}]")

        return x_arr, y_arr, z_arr

    def get_initial_conditions(self):
        return {'x0': self.x0, 'y0': self.y0, 'z0': self.z0,
                'a': self.a, 'b': self.b, 'c': self.c, 'dt': self.dt}


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    print("=" * 60)
    print("  RÖSSLER GENERATOR — STANDALONE TEST")
    print("=" * 60)

    gen = RosslerGenerator()
    x, y, z = gen.generate(n_samples=10000)

    fig = plt.figure(figsize=(10, 4))

    ax1 = fig.add_subplot(121, projection='3d')
    ax1.plot(x, y, z, lw=0.3, alpha=0.7, color='darkorchid')
    ax1.set_title("Rössler Spiral Attractor")
    ax1.set_xlabel("x"); ax1.set_ylabel("y"); ax1.set_zlabel("z")

    ax2 = fig.add_subplot(122)
    ax2.plot(x[:1000], lw=0.5, color='darkorange')
    ax2.set_title("x(t) — First 1000 Samples")
    ax2.set_xlabel("Sample"); ax2.set_ylabel("Amplitude")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/home/claude/chaos_fpga/rossler/rossler_attractor.png", dpi=150)
    print("  Attractor plot saved: rossler_attractor.png")
    print(f"  x std={x.std():.4f}  y std={y.std():.4f}  z std={z.std():.4f}")
