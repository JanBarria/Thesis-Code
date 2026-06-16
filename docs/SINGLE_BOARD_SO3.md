# Single-Board SO3 — Hybrid Chua + Rössler on One PYNQ-Z2

## What this branch demonstrates

This branch (`single-board`) hosts everything needed to demonstrate
**Pecora-Carroll chaos synchronization on a single FPGA**, instantiating
**four** oscillator cores on one PYNQ-Z2:

| Instance | Type | Role | Initial conditions |
|---|---|---|---|
| `chua_master`    | Chua | free-running | (x, y, z) = (0.1, 0.0, 0.0) |
| `chua_slave`     | Chua | x-driven by master | (x, y, z) = (0.1, 0.3, 0.2) |
| `rossler_master` | Rössler | free-running | (x, y, z) = (1.0, 1.0, 1.0) |
| `rossler_slave`  | Rössler | x-driven by master | (x, y, z) = (1.0, 0.5, 1.5) |

The slaves' x ports are wired directly to the masters' x outputs in
fabric — no UART, no serialization. All four advance in lockstep on a
single `state_step` pulse (Rössler) and the chua_enable flag (Chua).

The combined hybrid keystream:
```
m_combined_ks = m_chua_ks XOR m_rossler_ks   (master side)
s_combined_ks = s_chua_ks XOR s_rossler_ks   (slave side)
```

This is the SO3 verification platform decoupled from the inter-board
transport problem (UART, baud sync, framing). When master and slave
hybrid keystreams match, decryption works end-to-end.

---

## ⚠️ SO3 Wording Decision — Raise With Adviser

The verbatim SO3 text in the PRO2 paper says:

> "...digital-to-digital chaos synchronization between the transmitter
> and **receiver FPGAs** using Pecora-Carroll synchronization techniques,
> ensuring the FPGA-based chaotic transmitter and receiver remain
> synchronized."

A single-board build co-locates both oscillators on **one** FPGA. This
is a legitimate verification of the Pecora-Carroll technique itself,
**but it does not literally satisfy "two FPGAs."**

**Decide explicitly which framing you'll defend:**

### Option A — Reword SO3
Change "transmitter and receiver FPGAs" → "transmitter and receiver
chaotic oscillators." This makes the single-board demo literally
satisfy SO3.

### Option B — Two-tier demonstration
- Single-board: **preliminary** verification of the PC sync technique
- Dual-board (`main` branch): **final** SO3 satisfaction
- Document both in Chapter 5; defend dual-board as the answer

**Recommendation:** Choose Option A if your team's bandwidth is tight
before June 24 (single-board is the safer demo path). Choose Option B
if dual-board UART will definitely be working by then.

Get Dr. Gustilo's sign-off on one of these before the panel sees it.

---

## ⚠️ Pecora-Carroll Synchronization Caveat (Real)

Different chaos systems behave very differently under x-drive PC sync.
This is established in the literature, and your defense needs to
acknowledge it explicitly:

### Chua (full PC sync — works)
- Conditional Lyapunov exponents of the (y, z) subsystem driven by x
  are all **negative**.
- Slave's y and z **genuinely converge** to master's y and z from
  arbitrary initial offsets.
- Pearson r ≥ 0.95 on both y and z is achievable; verified in
  `single_board_hybrid_sim.py` (typically ~r = 1.0 after 50,000 Euler
  steps with dt = 0.001 → 50 simulation-time units).

### Rössler (partial PC sync — x trivial, y diverges, z converges)
- dy/dt = x + **a**·y with a = +0.2 → positive conditional Lyapunov
  exponent on the y axis.
- The slave's y **does not synchronize** — it diverges exponentially.
  This is a textbook result of Pecora-Carroll analysis on Rössler.
- z subsystem converges (negative conditional Lyapunov via z·(x-c)).
- x synchronizes **trivially** (substituted by drive).

### Why the hybrid cipher still works correctly
The combined keystream is extracted from `x_state[23:8]` of each
oscillator. Because slave's x is overwritten by master's x at every
step (substitution mechanism), slave's keystream bits equal master's
keystream bits **independent of y, z divergence**. Decryption
succeeds.

### What this means for SO3 evidence
The SO3 "sync proof" is presented from the **Chua subsystem alone**
(textbook Pecora-Carroll convergence of y and z). The Rössler subsystem
is presented in the thesis as a **keystream-entropy contributor** to the
hybrid cipher, not as a sync demonstration. This framing is honest,
defensible, and aligns with the published literature on Pecora-Carroll
analyses of these two systems.

In Chapter 4 of the thesis, write something like:

> "Pecora-Carroll synchronization is verified through the Chua subsystem,
> whose y and z conditional Lyapunov exponents are negative; the slave
> Chua oscillator's y and z states converge to the master's with
> Pearson r ≥ 0.95 (Section 5.X). The Rössler subsystem, while not
> exhibiting complete subsystem synchronization due to the positive
> conditional Lyapunov exponent of its y subsystem under x-drive,
> contributes to the hybrid keystream via the trivially-synced x state.
> The hybrid system therefore combines a rigorously synchronized chaotic
> oscillator (Chua) with a high-entropy keystream contributor (Rössler)
> to achieve doubled effective key space."

This sentence pre-empts the entire panel question chain.

---

## Hardware Resource Estimate

| Component | Per instance | Total (4 instances) |
|---|---|---|
| LUTs | ~600 (Rössler), ~900 (Chua) | ~3,000 |
| DSP48 | ~5 | ~20 (DSP48E1 budget on Z-7020 = 220, ≈9%) |
| BRAM | 0 | 0 |
| Flip-flops | ~150 | ~600 |

Plus 7 AXI GPIO instances (~200 LUTs each) = ~1,400 LUTs.
Plus 1 edge_detector (~5 LUTs).

**Total: ~4,500 LUTs of the Z-7020's 53,200 (~8.5% utilization).**
Plenty of headroom. Hybrid single-board is well within PYNQ-Z2 capacity.

---

## Reproducing the Demo

### 1. Verify in Python (no hardware)
```bash
cd chaos_fpga
python3 python/reference/single_board_hybrid_sim.py --steps 50000
```

Expected output:
```
--- CHUA subsystem (textbook PC sync expected) ---
  r_x (trivial)        : 1.000000
  r_y (MEANINGFUL)     : ~1.0000  PASS
  r_z (MEANINGFUL)     : ~1.0000  PASS

--- ROSSLER subsystem (only partial PC sync) ---
  r_x (trivial)        : 1.000000
  r_y (DIVERGES)       : near 0  (expected — published behavior)
  r_z (CONVERGES)      : ~1.0000  PASS

--- HYBRID combined keystream ---
  ks match rate         : depends on hardware pipeline alignment
```

### 2. Build the bitstream (Vivado, ~45 minutes)
Synthesize `hdl/chaos_hybrid_single_board.vhd` with all four oscillator
instances. Pin assignments for AXI GPIO and PMOD A in
`hdl/constraints/pynq_z2.xdc`.

### 3. Flash and run on PYNQ
```bash
scp chaos_hybrid_single_board.bit xilinx@<pynq_ip>:/home/xilinx/
scp python/pynq_control/single_board_hybrid_control.py xilinx@<pynq_ip>:/home/xilinx/
ssh xilinx@<pynq_ip> "sudo python3 /home/xilinx/single_board_hybrid_control.py --duration 10 --rate 1000"
```

### 4. Analyze
```bash
scp xilinx@<pynq_ip>:/home/xilinx/hybrid_data.csv ./
python3 python/pynq_control/analyze_sync.py hybrid_data.csv
```

The analyzer reports Pearson r for Chua y, z (the meaningful metrics) and
flags the trivial r_x.

---

## Files in this Branch (Not on Main)

- `hdl/edge_detector.vhd` — 1-cycle pulse generator
- `hdl/chaos_sync_single_board.vhd` — earlier Rössler-only single-board top (kept for reference)
- `hdl/chaos_hybrid_single_board.vhd` — canonical hybrid 4-instance top
- `python/reference/single_board_sim.py` — earlier Rössler-only sim (kept for reference)
- `python/reference/single_board_hybrid_sim.py` — canonical hybrid sim
- `python/pynq_control/single_board_hybrid_control.py` — PYNQ control script
- `docs/SINGLE_BOARD_SO3.md` — this file

Everything from `main` (dual-board hybrid, per-subsystem tests, docs)
remains available too — this branch is additive.
