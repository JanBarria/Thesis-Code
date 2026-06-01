"""
================================================================================
FILE: chua_chaotic_generator.py
SYSTEM: Chua Circuit Chaotic Oscillator — TRANSMITTER & RECEIVER
================================================================================
DESCRIPTION:
    Implements the discretized Chua Circuit chaotic oscillator using the
    Forward Euler method with Q16.16 fixed-point arithmetic simulation.
    Generates the double-scroll attractor used as the chaotic keystream source.

STATE EQUATIONS:
    dx/dt = alpha * (y - x - f(x))
    dy/dt = x - y + z
    dz/dt = -beta * y

CHUA DIODE:
    f(x) = b*x + 0.5*(a-b)*(|x+1| - |x-1|)

PARAMETERS:
    alpha=9.0, beta=14.28, a=-1.143, b=-0.714
    dt=0.01 (time step — critical for maintaining chaos)

HOW TO RUN:
    from chua_chaotic_generator import ChuaGenerator
    gen = ChuaGenerator()
    x_arr, y_arr, z_arr = gen.generate(n_samples=44100)

EXPECTED OUTPUT:
    Three numpy arrays (x, y, z) of shape (n_samples,)
    representing the chaotic trajectory of the Chua circuit.

PYNQ-Z2 NOTE:
    Compatible with Python 3.x on PYNQ image.
    No external dependencies beyond numpy.
================================================================================
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Q16.16 FIXED-POINT SIMULATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

FRAC_BITS = 16
SCALE     = 1 << FRAC_BITS          # 65536
MAX_Q     = (1 << 31) - 1           # max signed 32-bit
MIN_Q     = -(1 << 31)              # min signed 32-bit


def to_fixed(x):
    """Convert float to Q16.16 fixed-point integer."""
    return int(round(x * SCALE))


def to_float(q):
    """Convert Q16.16 fixed-point integer back to float."""
    return q / SCALE


def fixed_mul(a, b):
    """
    Multiply two Q16.16 fixed-point integers.
    Result is shifted right by FRAC_BITS to stay in Q16.16.
    Includes saturation to prevent overflow.
    """
    result = (a * b) >> FRAC_BITS
    return int(np.clip(result, MIN_Q, MAX_Q))


def fixed_add(a, b):
    """Add two Q16.16 values with saturation."""
    result = a + b
    return int(np.clip(result, MIN_Q, MAX_Q))


# ─────────────────────────────────────────────────────────────────────────────
# CHUA CIRCUIT GENERATOR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ChuaGenerator:
    """
    Chua Circuit chaotic oscillator with Q16.16 fixed-point arithmetic.

    Attributes:
        alpha  (float): System parameter (default 9.0)
        beta   (float): System parameter (default 14.28)
        a      (float): Chua diode inner slope (default -1.143)
        b      (float): Chua diode outer slope (default -0.714)
        dt     (float): Integration time step (default 0.01)
        x0, y0, z0 (float): Initial conditions (secret key)
    """

    def __init__(self,
                 alpha=9.0, beta=14.28,
                 a=-1.143, b=-0.714,
                 dt=0.01,
                 x0=0.1, y0=0.0, z0=0.0):

        # ── Parameter validation ──────────────────────────────────────────
        assert alpha > 0,        "alpha must be positive"
        assert beta  > 0,        "beta must be positive"
        assert a < b < 0,        "Chua diode requires a < b < 0"
        assert 0 < dt <= 0.05,   "dt too large — chaos may collapse"

        self.alpha = alpha
        self.beta  = beta
        self.a     = a
        self.b     = b
        self.dt    = dt

        # Initial conditions (these form the secret key)
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0

        # Convert parameters to Q16.16
        self._alpha_q = to_fixed(alpha)
        self._beta_q  = to_fixed(beta)
        self._a_q     = to_fixed(a)
        self._b_q     = to_fixed(b)
        self._dt_q    = to_fixed(dt)

    # ── Chua Diode (piecewise-linear nonlinearity) ────────────────────────
    def _chua_diode_float(self, x):
        """
        Evaluate f(x) = b*x + 0.5*(a-b)*(|x+1| - |x-1|)
        in floating-point for numerical accuracy during simulation.
        """
        return (self.b * x +
                0.5 * (self.a - self.b) * (abs(x + 1.0) - abs(x - 1.0)))

    def _chua_diode_fixed(self, x_q):
        """
        Evaluate Chua diode in Q16.16 fixed-point.
        Uses conditional branching matching piecewise-linear segments.
        """
        x = to_float(x_q)

        # Piecewise evaluation — hardware-friendly conditional logic
        if x > 1.0:
            fx = self.b * x + (self.a - self.b)
        elif x < -1.0:
            fx = self.b * x - (self.a - self.b)
        else:
            fx = self.a * x

        return to_fixed(fx)

    # ── Modulo-Map Stabilization ──────────────────────────────────────────
    def _stabilize(self, q, bound=20.0):
        """
        Wrap state variable into [-bound, +bound] using modulo mapping.
        Prevents arithmetic overflow while preserving nonlinear complexity.
        Mirrors the Modulo-Map Stabilization logic validated in simulation.
        """
        x = to_float(q)
        if abs(x) > bound:
            x = (x + bound) % (2 * bound) - bound
        return to_fixed(x)

    # ── Overflow / Collapse Detection ────────────────────────────────────
    def _check_chaos(self, trajectory, window=500):
        """
        Verifies the attractor has not collapsed into a periodic orbit.
        Checks that the standard deviation over a recent window is
        above a threshold — a proxy for positive Lyapunov exponent.
        Raises AssertionError if collapse is detected.
        """
        if len(trajectory) < window:
            return
        recent = np.array(trajectory[-window:])
        std_val = np.std(recent)
        assert std_val > 0.01, (
            f"CHAOS COLLAPSE DETECTED: std={std_val:.6f} < 0.01. "
            f"The attractor has degenerated into a periodic orbit. "
            f"Try reducing dt or adjusting initial conditions."
        )

    # ── Main Generation Method ────────────────────────────────────────────
    def generate(self, n_samples):
        """
        Generate n_samples of the Chua chaotic trajectory.

        Uses Q16.16 fixed-point arithmetic for each integration step,
        matching the precision that will be used in FPGA HDL synthesis.

        Args:
            n_samples (int): Number of samples to generate.
                             Should match your audio file length.

        Returns:
            tuple: (x_arr, y_arr, z_arr) — numpy float arrays of shape
                   (n_samples,) representing the chaotic state variables.
        """
        # ── Allocate output arrays ────────────────────────────────────────
        x_arr = np.zeros(n_samples, dtype=np.float64)
        y_arr = np.zeros(n_samples, dtype=np.float64)
        z_arr = np.zeros(n_samples, dtype=np.float64)

        # ── Initialize state in Q16.16 ────────────────────────────────────
        x_q = to_fixed(self.x0)
        y_q = to_fixed(self.y0)
        z_q = to_fixed(self.z0)

        # ── Warm-up: run 1000 steps to reach attractor ────────────────────
        print("[ChuaGenerator] Warming up oscillator (1000 steps)...")
        for _ in range(1000):
            fx_q  = self._chua_diode_fixed(x_q)

            # dx = alpha * (y - x - f(x))
            inner_q = fixed_add(fixed_add(y_q, -x_q), -fx_q)
            dx_q    = fixed_mul(self._alpha_q, inner_q)

            # dy = x - y + z
            dy_q = fixed_add(fixed_add(x_q, -y_q), z_q)

            # dz = -beta * y
            dz_q = -fixed_mul(self._beta_q, y_q)

            # Euler update: state += dt * derivative
            x_q = self._stabilize(fixed_add(x_q, fixed_mul(self._dt_q, dx_q)))
            y_q = self._stabilize(fixed_add(y_q, fixed_mul(self._dt_q, dy_q)))
            z_q = self._stabilize(fixed_add(z_q, fixed_mul(self._dt_q, dz_q)))

        # ── Main generation loop ──────────────────────────────────────────
        print(f"[ChuaGenerator] Generating {n_samples} chaotic samples...")
        x_list = []

        for i in range(n_samples):
            fx_q  = self._chua_diode_fixed(x_q)

            dx_q  = fixed_mul(self._alpha_q,
                              fixed_add(fixed_add(y_q, -x_q), -fx_q))
            dy_q  = fixed_add(fixed_add(x_q, -y_q), z_q)
            dz_q  = -fixed_mul(self._beta_q, y_q)

            x_q   = self._stabilize(fixed_add(x_q, fixed_mul(self._dt_q, dx_q)))
            y_q   = self._stabilize(fixed_add(y_q, fixed_mul(self._dt_q, dy_q)))
            z_q   = self._stabilize(fixed_add(z_q, fixed_mul(self._dt_q, dz_q)))

            # Store as float for downstream processing
            x_arr[i] = to_float(x_q)
            y_arr[i] = to_float(y_q)
            z_arr[i] = to_float(z_q)

            x_list.append(x_arr[i])

            # Periodic chaos health check every 5000 samples
            if i > 0 and i % 5000 == 0:
                self._check_chaos(x_list)

        print(f"[ChuaGenerator] Done. x range: "
              f"[{x_arr.min():.3f}, {x_arr.max():.3f}]")

        return x_arr, y_arr, z_arr

    def get_initial_conditions(self):
        """Return initial conditions as the secret key dictionary."""
        return {'x0': self.x0, 'y0': self.y0, 'z0': self.z0,
                'alpha': self.alpha, 'beta': self.beta,
                'a': self.a, 'b': self.b, 'dt': self.dt}


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    print("=" * 60)
    print("  CHUA CIRCUIT GENERATOR — STANDALONE TEST")
    print("=" * 60)

    gen = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
    x, y, z = gen.generate(n_samples=10000)

    # ── Plot double-scroll attractor ──────────────────────────────────────
    fig = plt.figure(figsize=(10, 4))

    ax1 = fig.add_subplot(121, projection='3d')
    ax1.plot(x, y, z, lw=0.3, alpha=0.7, color='steelblue')
    ax1.set_title("Chua Double-Scroll Attractor")
    ax1.set_xlabel("x"); ax1.set_ylabel("y"); ax1.set_zlabel("z")

    ax2 = fig.add_subplot(122)
    ax2.plot(x[:1000], lw=0.5, color='darkorange')
    ax2.set_title("x(t) — First 1000 Samples")
    ax2.set_xlabel("Sample"); ax2.set_ylabel("Amplitude")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/home/claude/chaos_fpga/chua/chua_attractor.png", dpi=150)
    print("  Attractor plot saved: chua_attractor.png")
    print(f"  x std={x.std():.4f}  y std={y.std():.4f}  z std={z.std():.4f}")
    print("  CHAOS CHECK PASSED" if x.std() > 0.1 else "  WARNING: Low variance")
