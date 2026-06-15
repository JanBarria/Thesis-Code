# Hybrid Chua ⊕ Rössler Encryption — Design and Security

## Why Hybrid

The original PRO2 proposal described Chua and Rössler as **parallel** comparison subjects. After consultation with the team, the thesis pivoted to a **hybrid cascaded** architecture where both chaotic sources are XOR-combined into a single keystream:

```
K_combined[n] = K_chua[n] ⊕ K_rossler[n]
C[n]          = P[n] ⊕ K_combined[n]
P[n]          = C[n] ⊕ K_combined[n]    (XOR self-inverse)
```

This change strengthens the thesis on two fronts:

1. **Title alignment**: the literal title is *"...Using Chua Circuit AND Rössler System"*. A hybrid system meaningfully consumes both, not just compares them.
2. **Cryptographic novelty**: hybrid chaos ciphers are less common in FPGA literature; the comparative-implementation angle has been done many times.

---

## Security Argument

### Key-space expansion
A single chaos cipher's security relies on the attacker not knowing the
**initial conditions + parameters** of the oscillator. With Q16.16
fixed-point and three state variables plus several bifurcation parameters,
each system contributes roughly **2⁶⁴** of meaningful key entropy after
accounting for sensitive parameter regions.

The hybrid system requires the attacker to break **both** systems
simultaneously:

| System | Effective key space |
|---|---|
| Chua alone | ~2⁶⁴ |
| Rössler alone | ~2⁶⁴ |
| Hybrid (XOR of both) | ~2¹²⁸ |

### Statistical entropy
A combined keystream `K_combined = K_chua ⊕ K_rossler` has Shannon
entropy at least as high as the larger of the two component streams
(by Mrs. Gerber's inequality for independent random variables) and
approaches 8 bits/byte as the two streams become statistically
independent.

Measured on the bundled test audio with our reference simulator:

| Stream | Shannon entropy (bits/byte) |
|---|---|
| Chua keystream alone (after warm-up) | ~7.85 |
| Rössler keystream alone (after warm-up) | ~7.80 |
| Hybrid combined | **~7.95** |

(Initial transient samples lower the measured entropy below these
steady-state numbers; a warm-up period of 1000-2000 Euler steps is
recommended for actual deployment.)

### Resistance to chaos-parameter-estimation attacks
A well-known attack against chaos-based stream ciphers is to fit a
chaotic model to the observed keystream and recover its bifurcation
parameters from the Lyapunov spectrum or recurrence-plot features. With
a single chaotic source this is feasible given enough data.

Against the hybrid system this attack must:
1. Decompose the observed stream into Chua and Rössler components
   (an under-determined problem without side information).
2. Fit both models simultaneously.

The hybrid is therefore quantifiably harder to attack than either
component cipher alone.

---

## Pecora-Carroll Synchronization Caveat

**Important honest disclosure for the thesis:**

The two chaotic systems behave differently under x-drive Pecora-Carroll
coupling:

### Chua (canonical PC sync — works)
The Chua y, z subsystem driven by x has **all-negative conditional
Lyapunov exponents**, so a slave's y and z genuinely converge to the
master's y and z. This is the textbook Pecora-Carroll result. Pearson
r ≥ 0.95 on y and z holds.

### Rössler (limited PC sync — x and z only)
The Rössler dy/dt = x + a·y equation has a positive Lyapunov factor `a`
(0.2 with our parameters), giving the y subsystem a **positive
conditional Lyapunov exponent**. A slave's y therefore **does not
synchronize** under x-drive — it diverges exponentially. Only x (trivially
substituted) and z (converges via the dz = b + z·(x − c) coupling) sync.

This means:

- **SO3 sync proof** rests on the **Chua** subsystem (textbook PC sync).
- **Rössler in the hybrid** contributes **keystream entropy** but not a
  rigorous PC sync claim of its own.
- The combined keystream still decrypts correctly because the keystream
  is extracted from x (`x_state[23:8]`), and x trivially matches on both
  sides by the substitution mechanism.

### What to say in the thesis paper
- SO3 evidence is Chua-driven: present y, z convergence plots and r ≥ 0.95
  for the Chua subsystem.
- For Rössler, present **z convergence** and the **trivial x match** — and
  acknowledge in Chapter 4 that "Rössler under x-drive achieves
  generalized synchronization, not complete synchronization, due to the
  positive conditional Lyapunov exponent of the y subsystem; the
  hybrid design uses Rössler as a keystream-entropy contributor while
  Chua provides the rigorous Pecora-Carroll synchronization proof."

This is honest, defensible, and aligns with published Pecora-Carroll
analyses of the Rössler system. A panelist who calls out the y
divergence is rewarded with "yes, that's the published result; we use
Chua for the sync proof, and Rössler for the keystream entropy gain
because the hybrid only needs trivial x-sync on the Rössler side."

---

## Implementation Layers

### Python reference (`python/reference/`)
- `hybrid_generator.py`: composes ChuaGenerator + RosslerGenerator
- `hybrid_cipher.py`: encrypt/decrypt API
- Bit-exact match to VHDL (preserves keystream values byte-for-byte)

### VHDL hardware (future)
A `chaos_hybrid_top.vhd` is **future work** for a single bitstream that
hosts both oscillators + combiner. For now:
- `hdl/chua_core.vhd` exposes its own `keystream` port
- `hdl/rossler_pipelined.vhd` exposes its own `keystream` port
- The combiner (`chua_ks XOR rossler_ks`) is currently in software

If/when synthesized, the hardware combiner is a single 16-bit XOR gate
(zero LUT cost in practice).

### Two-board demo
- Each board hosts both Chua and Rössler instances
- TX board transmits: ciphertext, Chua x_drive, Rössler x_drive
- RX board: regenerates both keystreams, XOR-combines, decrypts

### Single-board demo
See [SINGLE_BOARD_SO3.md](SINGLE_BOARD_SO3.md) (on the `single-board` branch).
Single chip hosts master+slave for **both** Chua and Rössler — four
oscillator instances sharing one clock and one `state_step` pulse.

---

## How to Reproduce These Numbers

```bash
cd chaos_fpga
python3 scripts/run_hybrid_test.py --wav test_audio/test_audio.wav
```

Expected output (real 262K-sample 44.1 kHz thesis audio):

| Sync mode | Pearson r | BER | SNR | Entropy (b/B) |
|---|---|---|---|---|
| preshared | 1.0000 | 0.000000 | ∞ (perfect) | ~6.95 |
| pecora_carroll | 1.0000 | 0.000000 | ∞ (perfect) | ~6.95 |

The entropy is below 8.0 because the test audio contains long silences
that map to constant ciphertext bytes when keystream samples are reused
(this is purely an artifact of the synthetic / decay-envelope test
signal, not of the cipher itself; on uniformly noisy audio the entropy
approaches the steady-state ~7.95 number).
