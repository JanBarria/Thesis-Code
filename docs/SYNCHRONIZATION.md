# Pecora-Carroll Synchronization — Method and Verification

## Background

Pecora & Carroll (1990) showed that two identical chaotic systems can
synchronize if a subset of state variables from the "master" is used to
drive the "slave." The slave's remaining state variables converge to the
master's because the conditional Lyapunov exponents of the driven
subsystem are all negative.

For both Chua and Rössler systems, the standard PC drive is the `x`
variable. The slave evolves only `y, z`, with `x` substituted from the
received master signal.

---

## Two Sync Modes in This Repository

This codebase deliberately supports **both** synchronization paradigms.
They produce identical decryption results, but they prove different
things and the thesis paper claims one or the other in different sections.

### Mode 1 — Pre-Shared Key Sync (PSK)

| Aspect | Detail |
|---|---|
| What is shared | The full secret key (initial conditions `x₀, y₀, z₀` + parameters) |
| How sync happens | Both sides instantiate identical generators; trajectories are identical by determinism |
| Drive signal use | None — drive signal is recorded only for analysis |
| Realism | Idealized: assumes perfectly synchronized clocks, no noise |
| Hardware proof | None: no subsystem is being driven |

### Mode 2 — Pecora-Carroll Subsystem Drive (PCSD)

| Aspect | Detail |
|---|---|
| What is shared | Only the parameters (initial conditions deliberately differ) |
| How sync happens | Slave's x is *overwritten* by master's x at every step |
| Drive signal use | Continuously substituted into slave's state |
| Realism | Closer to how analog PC sync works — robust to slave IC error |
| Hardware proof | Slave's y, z exponentially converge to master's y, z (the proof) |

---

## VHDL Implementation

Both `chua_core.vhd` and `rossler_pipelined.vhd` expose two ports for PC sync:

```vhdl
sync_enable  : in std_logic;
x_drive      : in std_logic_vector(31 downto 0);
```

When `sync_enable = '1'`:
```vhdl
if sync_enable = '1' then
    x_s0 <= signed(x_drive);   -- substitute received master x
else
    x_s0 <= x_state;            -- free-running master mode
end if;
```

This single mux is the entire hardware implementation of PCSD. Everything
else (y, z evolution, dt step) is the same on both boards.

---

## Python Implementation

In [`python/reference/decryptor.py`](../python/reference/decryptor.py),
selecting `sync_mode='pecora_carroll'` triggers:

```python
x_arr, y_arr, z_arr, x_int = gen.generate(n, x_drive_int_arr=x_drive_int)
```

The generator's `generate()` method passes each drive sample to `step()`:

```python
def step(self, x_drive_q=None):
    x_used = x_drive_q if x_drive_q is not None else self.x_q
    # ... derivatives computed from x_used, not self.x_q
```

This bit-exactly mirrors the VHDL mux behavior.

---

## How to Verify Sync Convergence

The slave starts with deliberately different ICs (e.g. Rössler `(1, 0.5, 1.5)`
vs master `(1, 1, 1)`). After enough drive samples, slave y and z should
converge to master y and z.

Run:
```bash
python3 scripts/run_full_test.py
```

The script reports `sync err` which is the mean of `|x_master - x_slave|`
over the last 500 samples. For PCSD it's `0.0` by construction (x is
substituted). The *real* convergence proof is y and z error — checked
internally by the script.

---

## Convergence Time

For Rössler with the canonical parameters and dt = 0.01:
- y, z converge to within 1% in about **200-400 Euler steps** (~2-4 seconds
  of simulated time)
- At 1 kHz step rate (used in `master_control.py`), this is ~0.2-0.4 seconds
  of wall-clock time before decryption is reliable

For Chua with dt = 0.001:
- Slightly faster convergence: ~100-200 steps
- At 10 kHz step rate, ~10-20 ms wall-clock

A short "sync warm-up" period at the start of every session is
recommended before transmitting encrypted audio.

---

## Why Both Modes Exist

| Use case | Mode |
|---|---|
| Software-only PYNQ demo (no FPGA fabric) | PSK works, PCSD trivial |
| FPGA-only demo (two PYNQ boards, full hardware path) | PCSD is the actual sync mechanism |
| Thesis SO3 evidence (Pecora-Carroll proof) | PCSD must be shown |
| Thesis SO5 evidence (TX/RX role split) | Either, both produce same metrics |

The Python reference simulator supports both so that the same codebase
can validate either demo path.
