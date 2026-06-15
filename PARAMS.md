# Single Source of Truth — System Parameters

This file is the **canonical reference** for every numeric parameter used by
the VHDL hardware, the Python reference simulator, and the PYNQ control
scripts. Any value that appears in code should match this table. If you
change a value here, change it in every implementation in the same commit.

---

## Q16.16 Fixed-Point Format

All hardware arithmetic uses signed 32-bit Q16.16:
- 16 integer bits + 16 fractional bits
- Range: [-32768.0, +32767.999984...]
- Precision: 2⁻¹⁶ ≈ 1.526 × 10⁻⁵
- Conversion: `float → int = round(float × 65536)`
- Multiplication: 64-bit intermediate, `>> 16` to return to Q16.16

---

## Chua Circuit Parameters

Source of truth: [`hdl/chua_core.vhd`](hdl/chua_core.vhd) (5-stage pipeline).

| Symbol | Meaning | Float Value | Q16.16 Integer |
|---|---|---|---|
| α (ALPHA) | Bifurcation parameter | 15.6093 | **1022976** |
| β (BETA) | Bifurcation parameter | 28.0 | **1835008** |
| m0 | Inner segment slope | -1.143 | **-74907** |
| m1 | Outer segment slope | -0.714 | **-46792** |
| dt | Euler integration step | 0.001007 | **66** |
| half_diff | 0.5 × (m0 - m1) | -0.21449 | **-14058** |
| x₀ | Initial condition (x) | 0.1 | **6554** |
| y₀ | Initial condition (y) | 0.0 | 0 |
| z₀ | Initial condition (z) | 0.0 | 0 |

### Chua Diode (Classical, Correct)
```
f(x) = m1·x + ½·(m0 - m1)·(|x+1| - |x-1|)

Piecewise:
  |x| ≤ 1:   f(x) = m0·x                    (steep inner slope)
   x > 1:    f(x) = m1·x + (m0 - m1)        (shallow outer slope)
   x < -1:   f(x) = m1·x - (m0 - m1)        (shallow outer slope)
```

### State Equations
```
ẋ = α·(y - x - f(x))
ẏ = x - y + z
ż = -β·y
```

### Forward Euler Update
```
x[n+1] = x[n] + dt·ẋ[n]
y[n+1] = y[n] + dt·ẏ[n]
z[n+1] = z[n] + dt·ż[n]
```

---

## Rössler System Parameters

Source of truth: [`hdl/rossler_pipelined.vhd`](hdl/rossler_pipelined.vhd) (4-stage pipeline).

| Symbol | Meaning | Float Value | Q16.16 Integer |
|---|---|---|---|
| a | Bifurcation parameter | 0.2 | **13107** |
| b | Bifurcation parameter | 0.2 | **13107** |
| c | Bifurcation parameter | 5.7 | **373554** |
| dt | Euler integration step | 0.01 | **655** |
| x₀ (Master, Slave) | Initial condition (x) | 1.0 | **65536** |
| y₀ (Master) | Initial condition (y) | 1.0 | **65536** |
| y₀ (Slave) | Initial condition (y) | 0.5 | **32768** |
| z₀ (Master) | Initial condition (z) | 1.0 | **65536** |
| z₀ (Slave) | Initial condition (z) | 1.5 | **98304** |

### State Equations
```
ẋ = -y - z
ẏ = x + a·y
ż = b + z·(x - c)
```

### Pecora-Carroll Subsystem Driving
- **Master**: `sync_enable = 0`, runs all three equations freely.
- **Slave**: `sync_enable = 1`, x is overwritten by received `x_drive`,
  only y and z evolve from substituted x.
- Slave's y, z converge to master's y, z because the Rössler y-z subsystem
  is stable when driven by x.

---

## Why Chua dt ≠ Rössler dt

| System | dt | Reason |
|---|---|---|
| Chua | 0.001 | Stiffer dynamics, sharper double-scroll transitions. Smaller dt prevents Euler instability near the diode boundaries. |
| Rössler | 0.01 | Smoother quadratic nonlinearity. Larger dt yields fewer steps per orbit while preserving chaos. |

This asymmetry is intentional and matches the two pipelined cores as
flashed. Comparison tables in the thesis (SO6) report normalized per-orbit
metrics rather than per-step.

---

## Keystream Extraction (Both Systems)

Both VHDL cores expose a 16-bit keystream taken from the middle bits of x:

```vhdl
keystream <= std_logic_vector(x_state(23 downto 8));
```

In Python:
```python
keystream = (x_int & 0xFFFFFFFF) >> 8 & 0xFFFF   # uint16
```

This is **identical** between Chua and Rössler — only the source x state
differs.

---

## Encryption Method (Hybrid)

The canonical thesis cipher is hybrid Chua ⊕ Rössler:

```
K_combined[n] = K_chua[n] ⊕ K_rossler[n]
C[n]          = P[n] ⊕ K_combined[n]
P[n]          = C[n] ⊕ K_combined[n]   (XOR is self-inverse)
```

Where:
- P[n]            : 16-bit signed plaintext audio sample
- K_chua[n]       : 16-bit keystream from Chua x_state[23:8]
- K_rossler[n]    : 16-bit keystream from Rössler x_state[23:8]
- K_combined[n]   : K_chua[n] XOR K_rossler[n]
- C[n]            : 16-bit encrypted ciphertext

### Per-subsystem mode (used in SO6 comparison only)

For per-system performance comparison (SO6), encryption can also be run
with a single chaotic source:
```
C_chua[n]    = P[n] ⊕ K_chua[n]      (Chua-only, for comparison)
C_rossler[n] = P[n] ⊕ K_rossler[n]   (Rössler-only, for comparison)
```
These per-subsystem ciphers are evaluated in `scripts/run_full_test.py`.
The hybrid cipher in `scripts/run_hybrid_test.py` is the canonical thesis
implementation.

---

## Stereo Audio Handling

If the input .wav is stereo (2 channels), **always use the LEFT channel**
(`samples[:, 0]`). Do **not** average channels via `.mean(axis=1)` — that
introduces sub-LSB rounding that breaks XOR decryption. The Python encryptor
and decryptor are aligned on this convention.

---

## Performance Targets

| Metric | Target | Notes |
|---|---|---|
| Pearson r | ≥ 0.95 | Original vs decrypted audio |
| BER | < 0.01 (1%) | Bit error rate |
| Sync error | → 0 | Drive x vs regenerated x |
| Clock | 40 MHz | Pipeline timing budget on PYNQ-Z2 |
| Throughput | 1 sample/clk after pipeline fill | After 4-5 cycle latency |
