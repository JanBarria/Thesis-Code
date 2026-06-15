"""
Mathematical Models of the Chua Circuit and Rössler System
Forward Euler Discretization with Floating-Point and Q-format Fixed-Point Arithmetic

Thesis: FPGA Implementation of Chaos-Based Secure Communication
        Using Chua Circuit and Rössler System
"""

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. CHUA CIRCUIT - Floating Point Reference Model
# ============================================================

def chua_diode(x, m0, m1):
    """Piecewise-linear Chua diode nonlinearity f(x)."""
    return m1 * x + 0.5 * (m0 - m1) * (np.abs(x + 1) - np.abs(x - 1))


def chua_step(state, params):
    """One Forward Euler step of the Chua circuit (dimensionless form)."""
    x, y, z = state
    alpha, beta, m0, m1, h = params

    fx = chua_diode(x, m0, m1)

    dx = alpha * (y - x - fx)
    dy = x - y + z
    dz = -beta * y

    x_next = x + h * dx
    y_next = y + h * dy
    z_next = z + h * dz

    return np.array([x_next, y_next, z_next])


def simulate_chua(n_steps, x0=(0.7, 0.0, 0.0),
                   alpha=15.6, beta=28.0, m0=-1.143, m1=-0.714, h=0.001):
    """Simulate the Chua circuit for n_steps using Forward Euler."""
    params = (alpha, beta, m0, m1, h)
    state = np.array(x0, dtype=np.float64)
    traj = np.zeros((n_steps, 3))

    for i in range(n_steps):
        traj[i] = state
        state = chua_step(state, params)

    return traj


# ============================================================
# 2. RÖSSLER SYSTEM - Floating Point Reference Model
# ============================================================

def rossler_step(state, params):
    """One Forward Euler step of the Rössler system."""
    x, y, z = state
    a, b, c, h = params

    dx = -y - z
    dy = x + a * y
    dz = b + z * (x - c)

    x_next = x + h * dx
    y_next = y + h * dy
    z_next = z + h * dz

    return np.array([x_next, y_next, z_next])


def simulate_rossler(n_steps, x0=(0.1, 0.0, 0.0),
                      a=0.2, b=0.2, c=5.7, h=0.001):
    """Simulate the Rössler system for n_steps using Forward Euler."""
    params = (a, b, c, h)
    state = np.array(x0, dtype=np.float64)
    traj = np.zeros((n_steps, 3))

    for i in range(n_steps):
        traj[i] = state
        state = rossler_step(state, params)

    return traj


# ============================================================
# 3. FIXED-POINT (Qm.n) UTILITIES
# ============================================================

def to_fixed(value, frac_bits, total_bits=32):
    """
    Quantize a float to a signed Qm.n fixed-point integer representation.
    total_bits = m + n + 1 (sign bit)
    frac_bits  = n
    """
    scale = 1 << frac_bits
    max_val = (1 << (total_bits - 1)) - 1
    min_val = -(1 << (total_bits - 1))

    fixed_int = int(round(value * scale))
    fixed_int = max(min(fixed_int, max_val), min_val)  # saturate
    return fixed_int


def from_fixed(fixed_int, frac_bits):
    """Convert a Qm.n fixed-point integer back to float."""
    scale = 1 << frac_bits
    return fixed_int / scale


def quantize_array(arr, frac_bits, total_bits=32):
    """Quantize a float array through fixed-point round trip (simulates HW precision loss)."""
    out = np.zeros_like(arr)
    flat_in = arr.flatten()
    flat_out = out.flatten()
    for i, v in enumerate(flat_in):
        fx = to_fixed(v, frac_bits, total_bits)
        flat_out[i] = from_fixed(fx, frac_bits)
    return flat_out.reshape(arr.shape)


# ============================================================
# 4. FIXED-POINT CHUA / RÖSSLER STEP (bit-accurate simulation)
# ============================================================

def chua_step_fixed(state_fx, params_fx, frac_bits, total_bits=32):
    """
    One Forward Euler step using integer arithmetic to emulate Qm.n fixed-point.
    state_fx, params_fx are integers already in Qm.n format.
    """
    scale = 1 << frac_bits
    x, y, z = state_fx
    alpha, beta, m0, m1, h = params_fx

    one = 1 << frac_bits  # represents 1.0 in Qm.n

    # f(x) = m1*x + 0.5*(m0-m1)*(|x+1| - |x-1|)
    term1 = (m1 * x) >> frac_bits
    abs_xp1 = abs(x + one)
    abs_xm1 = abs(x - one)
    term2 = (((m0 - m1) * (abs_xp1 - abs_xm1)) >> frac_bits) >> 1  # *0.5
    fx_val = term1 + term2

    dx = (alpha * (y - x - fx_val)) >> frac_bits
    dy = x - y + z
    dz = -((beta * y) >> frac_bits)

    x_next = x + ((h * dx) >> frac_bits)
    y_next = y + ((h * dy) >> frac_bits)
    z_next = z + ((h * dz) >> frac_bits)

    # saturate to total_bits
    max_val = (1 << (total_bits - 1)) - 1
    min_val = -(1 << (total_bits - 1))
    x_next = max(min(x_next, max_val), min_val)
    y_next = max(min(y_next, max_val), min_val)
    z_next = max(min(z_next, max_val), min_val)

    return np.array([x_next, y_next, z_next], dtype=np.int64)


def simulate_chua_fixed(n_steps, frac_bits, total_bits=32,
                         x0=(0.7, 0.0, 0.0),
                         alpha=15.6, beta=28.0, m0=-1.143, m1=-0.714, h=0.001):
    """Simulate Chua circuit using integer fixed-point arithmetic (Qm.n)."""
    params_fx = tuple(to_fixed(p, frac_bits, total_bits) for p in (alpha, beta, m0, m1, h))
    state_fx = np.array([to_fixed(v, frac_bits, total_bits) for v in x0], dtype=np.int64)

    traj_fx = np.zeros((n_steps, 3))
    for i in range(n_steps):
        traj_fx[i] = [from_fixed(v, frac_bits) for v in state_fx]
        state_fx = chua_step_fixed(state_fx, params_fx, frac_bits, total_bits)

    return traj_fx


def rossler_step_fixed(state_fx, params_fx, frac_bits, total_bits=32):
    """One Forward Euler step of Rössler using integer fixed-point arithmetic."""
    x, y, z = state_fx
    a, b, c, h = params_fx

    dx = -y - z
    dy = x + ((a * y) >> frac_bits)
    dz = b + (((z * (x - c))) >> frac_bits)

    x_next = x + ((h * dx) >> frac_bits)
    y_next = y + ((h * dy) >> frac_bits)
    z_next = z + ((h * dz) >> frac_bits)

    max_val = (1 << (total_bits - 1)) - 1
    min_val = -(1 << (total_bits - 1))
    x_next = max(min(x_next, max_val), min_val)
    y_next = max(min(y_next, max_val), min_val)
    z_next = max(min(z_next, max_val), min_val)

    return np.array([x_next, y_next, z_next], dtype=np.int64)


def simulate_rossler_fixed(n_steps, frac_bits, total_bits=32,
                            x0=(0.1, 0.0, 0.0),
                            a=0.2, b=0.2, c=5.7, h=0.001):
    """Simulate Rössler system using integer fixed-point arithmetic (Qm.n)."""
    params_fx = tuple(to_fixed(p, frac_bits, total_bits) for p in (a, b, c, h))
    state_fx = np.array([to_fixed(v, frac_bits, total_bits) for v in x0], dtype=np.int64)

    traj_fx = np.zeros((n_steps, 3))
    for i in range(n_steps):
        traj_fx[i] = [from_fixed(v, frac_bits) for v in state_fx]
        state_fx = rossler_step_fixed(state_fx, params_fx, frac_bits, total_bits)

    return traj_fx


# ============================================================
# 5. PRECISION COMPARISON METRICS
# ============================================================

def compare_precision(traj_float, traj_fixed):
    """Compute error metrics between floating-point and fixed-point trajectories."""
    error = traj_float - traj_fixed
    mse = np.mean(error ** 2, axis=0)
    max_abs_error = np.max(np.abs(error), axis=0)
    rmse = np.sqrt(mse)

    # Pearson correlation per axis
    corr = []
    for i in range(3):
        c = np.corrcoef(traj_float[:, i], traj_fixed[:, i])[0, 1]
        corr.append(c)

    return {
        "mse": mse,
        "rmse": rmse,
        "max_abs_error": max_abs_error,
        "correlation": np.array(corr),
    }


if __name__ == "__main__":
    N = 5000

    # Floating-point reference
    chua_float = simulate_chua(N)
    rossler_float = simulate_rossler(N)

    print("Chua (float) final state:", chua_float[-1])
    print("Rössler (float) final state:", rossler_float[-1])

    # Fixed-point Q16.16 (matches thesis spec)
    chua_fixed_16 = simulate_chua_fixed(N, frac_bits=16, total_bits=32)
    rossler_fixed_16 = simulate_rossler_fixed(N, frac_bits=16, total_bits=32)

    chua_metrics = compare_precision(chua_float, chua_fixed_16)
    rossler_metrics = compare_precision(rossler_float, rossler_fixed_16)

    print("\nChua Q16.16 vs float:")
    print("  RMSE:", chua_metrics["rmse"])
    print("  Max abs error:", chua_metrics["max_abs_error"])
    print("  Correlation:", chua_metrics["correlation"])

    print("\nRössler Q16.16 vs float:")
    print("  RMSE:", rossler_metrics["rmse"])
    print("  Max abs error:", rossler_metrics["max_abs_error"])
    print("  Correlation:", rossler_metrics["correlation"])
