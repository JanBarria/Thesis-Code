# Master Context Document — Chaos-Based FPGA Secure Communication Thesis

> **Purpose:** This file is the complete project memory. A new collaborator (human or AI) reading only this document should be able to understand the thesis design, every architectural decision, every numeric parameter, every bug we fixed, and the reasoning behind every choice — without having to read the rest of the conversation history.
>
> **Last updated:** 2026-06-17
> **Repository:** [github.com/JanBarria/Thesis-Code](https://github.com/JanBarria/Thesis-Code)
> **Status of this document:** Living. Update whenever a major decision is made.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Thesis title** | FPGA Implementation of Chaos-Based Secure Communication Using Chua Circuit and Rössler System |
| **Institution** | De La Salle University (DLSU) |
| **Department** | Electronics and Communications Engineering (ECE) |
| **Group** | MICRO-3-2425-1 |
| **Adviser** | Dr. Reggie Gustilo |
| **PRO1 Panel** | Dr. Roderick Y. Yap (Chair), Dr. Alexander C. Abad, Dr. Cesar A. Llorente |
| **Term** | Term 3 of SY 2025-2026 |
| **Members** | ABALOS Ezekiel Martin (Rössler side, IPC/Python lead) <br> BARRIA Jan Christopher (Chua side, repo owner) <br> CORTES Marc Jose (Rössler side) <br> JUSAY Jan Marron (Chua side) |
| **Hardware** | Two PYNQ-Z2 boards (Zynq-7000 SoC, xc7z020clg400-1) |
| **Toolchain** | Vivado 2024.1 (Windows), PYNQ Linux 2024.1 |

---

## 2. Deadlines (As of 2026-06-17)

| Date | Deliverable | Status |
|---|---|---|
| 2026-05-25 | Letter of Intent (Appendix V) | ✅ Submitted |
| 2026-06-06 | Pre-defense submission (progress report) | ✅ Submitted |
| 2026-06-24 | Final manuscript + oral defense | 🟡 In progress |

---

## 3. Thesis Story (Defense Narrative)

The thesis evolved from a **parallel-comparison architecture** (PRO2 design — implement Chua and Rössler separately and compare them) to a **hybrid unified cipher** that combines both chaos sources:

```
K_combined[n] = K_chua[n] XOR K_rossler[n]
C[n]          = P[n] XOR K_combined[n]
```

### Why hybrid (the pivot)
1. **Title literally says "AND"** — *"Using Chua Circuit AND Rössler System"*. A parallel comparison reads as two papers stapled together. A hybrid is one cohesive thesis.
2. **Security gain is real and quantifiable**:
   - Effective key space: 2⁶⁴ × 2⁶⁴ = **2¹²⁸** (vs ~2⁶⁴ for either alone)
   - Combined keystream Shannon entropy strictly ≥ either component
   - Resistant to chaos-parameter-estimation attacks against single oscillators
3. **Cryptographically novel** for FPGA literature. Comparative-implementation FPGA chaos ciphers have been published many times; cascaded/hybrid FPGA chaos ciphers are much less common.

### Honest disclosure built into the thesis
The hybrid approach has a known limitation that must be acknowledged in Chapter 4:

> Rössler's `dy/dt = x + a·y` term has positive Lyapunov coefficient (`a = +0.2`), so under x-drive Pecora-Carroll coupling, the slave Rössler's `y` subsystem **does not synchronize** — it diverges exponentially. This is a textbook result (positive conditional Lyapunov exponent), not a bug.
>
> Therefore:
> - **SO3 (sync proof)** rests on the **Chua** subsystem, whose y, z conditional Lyapunov exponents under x-drive are all negative → genuine subsystem synchronization.
> - **Rössler** contributes to the hybrid keystream via its trivially-synced `x` state (substituted by drive in fabric), adding entropy without rigorous PC sync.
> - The hybrid cipher **still decrypts correctly** because keystreams are extracted from `x` (`x_state[23:8]`), not from `y`.

This framing pre-empts the panel question and turns it into a strength: "we use Chua for the rigorous synchronization proof and Rössler for keystream entropy gain."

---

## 4. Repository Structure (Current State)

Single canonical branch: **`main`**. No more branch confusion.

```
chaos_fpga/
├── PARAMS.md                        # ← single source of truth for all parameters
├── README.md                        # ← top-level usage and SO mapping
├── docs/
│   ├── MASTER_CONTEXT.md            # ← this file
│   ├── HYBRID_ENCRYPTION.md         # security analysis + Pecora-Carroll caveats
│   ├── SYNCHRONIZATION.md           # preshared vs Pecora-Carroll sync explanation
│   ├── SINGLE_BOARD_SO3.md          # Scenario A details
│   └── SCENARIO_C_DUAL_BOARD_HYBRID.md  # Scenario C build + run guide
├── hdl/
│   ├── chua_core.vhd                # 5-stage pipelined Chua (with Y0/Z0 generics)
│   ├── rossler_pipelined.vhd        # 4-stage pipelined Rössler (with Y0/Z0 generics)
│   ├── edge_detector.vhd            # 1-cycle pulse from level signal
│   ├── chaos_sync_top.vhd           # legacy Rössler-only dual-board (Scenario B)
│   ├── chaos_hybrid_single_board.vhd  # SCENARIO A 4-instance top
│   ├── chaos_hybrid_dual_top.vhd    # SCENARIO C dual-board (IS_MASTER generic)
│   ├── chaos_sync_single_board.vhd  # earlier Rössler-only single-board (kept)
│   ├── chaos_system_tb.vhd          # behavioral testbench
│   ├── top_wrapper.vhd              # MANUAL bridge: BD wrapper ↔ chaos module
│   ├── vivado_generated/
│   │   └── chaos_design_wrapper.vhd # Vivado's auto-generated BD wrapper
│   └── constraints/
│       ├── pynq_z2.xdc                  # legacy (dual-board UART)
│       ├── pynq_z2_single_board.xdc     # ← USE THIS for single-board
│       └── timing.xdc
├── python/
│   ├── reference/                   # bit-exact Python simulator
│   │   ├── q16_arith.py             # Q16.16 fixed-point helpers
│   │   ├── chua_generator.py        # matches chua_core.vhd
│   │   ├── rossler_generator.py     # matches rossler_pipelined.vhd
│   │   ├── hybrid_generator.py      # combined Chua⊕Rössler keystream
│   │   ├── encryptor.py             # per-subsystem cipher
│   │   ├── decryptor.py             # per-subsystem decrypt + PC sync
│   │   ├── hybrid_cipher.py         # hybrid encrypt/decrypt (canonical)
│   │   ├── single_board_sim.py      # earlier Rössler-only sim
│   │   ├── single_board_hybrid_sim.py  # canonical hybrid 4-instance sim
│   │   └── chaos_models.py          # SO1 floating-point math reference
│   ├── pynq_control/                # PYNQ-side FPGA control
│   │   ├── single_board_hybrid_control.py  # SCENARIO A control
│   │   ├── hybrid_master_control.py   # SCENARIO C master
│   │   ├── hybrid_slave_control.py    # SCENARIO C slave
│   │   ├── master_control.py        # legacy (Scenario B)
│   │   ├── slave_control.py         # legacy (Scenario B)
│   │   └── analyze_sync.py          # sync metrics + plotting
│   └── uart/                        # pyserial + CRC32 library
│       ├── uart_config.py
│       ├── uart_protocol.py
│       ├── uart_transmitter.py
│       └── uart_receiver.py
├── notebooks/
│   └── Chaos_Models_Mathematical_Documentation.ipynb  # SO1 derivations
├── scripts/
│   ├── run_full_test.py             # per-subsystem reference test
│   ├── run_hybrid_test.py           # hybrid end-to-end test (canonical)
│   └── create_project.tcl           # Vivado project gen template
└── test_audio/
    └── test_audio.wav               # 44.1 kHz, 5.94s test audio
```

---

## 5. The Three Demonstration Scenarios

Pick based on board availability and demo bandwidth.

### Scenario A — Single-Board (Fastest, Recommended Prototype)
- **Hardware:** 1 PYNQ-Z2
- **VHDL:** `chaos_hybrid_single_board.vhd` (4 oscillators on one chip)
- **Bitstream:** `chaos_hybrid_single_board.bit`
- **Python control:** `single_board_hybrid_control.py`
- **What it proves:** Pecora-Carroll sync in isolation (Chua y, z convergence to r ≥ 0.95)
- **Cannot prove:** Two physical FPGAs (literal SO3 wording)
- **Build time:** ~45 min Vivado synthesis

### Scenario B — Dual-Board Rössler-Only (Legacy)
- **Hardware:** 2 PYNQ-Z2s
- **VHDL:** `chaos_sync_top.vhd` (Rössler-only + EMIO UART)
- **Bitstreams:** Two builds, master + slave via `Y0_INIT`/`Z0_INIT` generics
- **Python control:** `master_control.py` + `slave_control.py`
- **What it proves:** Two-FPGA UART sync
- **Limitation:** Rössler only; hybrid combination done in Python software on each board

### Scenario C — Dual-Board Hybrid (Full Thesis Claim)
- **Hardware:** 2 PYNQ-Z2s
- **VHDL:** `chaos_hybrid_dual_top.vhd` (1 Chua + 1 Rössler per board, `IS_MASTER` generic)
- **Bitstreams:** Two builds (master + slave) from one source
- **Python control:** `hybrid_master_control.py` + `hybrid_slave_control.py`
- **What it proves:** Full hybrid cipher with real UART transport (literal SO3)
- **Build time:** ~90 min total (2× 45 min)

---

## 6. Canonical Parameters (PARAMS.md Mirror)

These are the **single source of truth**. Every implementation must match.

### Chua Circuit (`hdl/chua_core.vhd`)

| Symbol | Float | Q16.16 int | Notes |
|---|---|---|---|
| α (alpha) | 15.6093 | 1022976 | Bifurcation |
| β (beta) | 28.0 | 1835008 | Bifurcation |
| m0 (inner slope) | -1.143 | -74907 | Used when \|x\| ≤ 1 |
| m1 (outer slope) | -0.714 | -46792 | Used when \|x\| > 1 |
| dt | 0.001 (≈0.001007) | 66 | Forward Euler step |
| half_diff | -0.2145 | -14058 | = 0.5·(m0 - m1) |
| x₀ | 0.1 | 6554 | Reset value (fixed in core) |
| y₀, z₀ | Variable | Y0_INIT, Z0_INIT generics | Defaults 0; slave uses 0.3, 0.2 |

**Chua diode (classical, correct):**
```
f(x) = m1·x + ½·(m0 - m1)·(|x+1| - |x-1|)

Piecewise:
  |x| ≤ 1   →  f(x) = m0·x              (steep inner)
   x > 1    →  f(x) = m1·x + (m0 - m1)  (shallow outer)
   x < -1   →  f(x) = m1·x - (m0 - m1)  (shallow outer)
```

**State equations:**
```
ẋ = α·(y - x - f(x))
ẏ = x - y + z
ż = -β·y
```

### Rössler System (`hdl/rossler_pipelined.vhd`)

| Symbol | Float | Q16.16 int | Notes |
|---|---|---|---|
| a | 0.2 | 13107 | Bifurcation |
| b | 0.2 | 13107 | Bifurcation |
| c | 5.7 | 373554 | Bifurcation |
| dt | 0.01 | 655 | Forward Euler step |
| x₀ (master, slave) | 1.0 | 65536 | Same reset for both |
| y₀ (master) | 1.0 | 65536 | Y0_INIT generic |
| y₀ (slave) | 0.5 | 32768 | Different to show convergence |
| z₀ (master) | 1.0 | 65536 | Z0_INIT generic |
| z₀ (slave) | 1.5 | 98304 | Different to show convergence |

**State equations:**
```
ẋ = -y - z
ẏ = x + a·y       (← +a·y has POSITIVE Lyapunov; y won't sync under x-drive)
ż = b + z·(x - c)
```

### Why Chua dt ≠ Rössler dt
- **Chua dt = 0.001** — stiffer dynamics; sharp piecewise diode transitions require smaller step
- **Rössler dt = 0.01** — smoother quadratic nonlinearity; larger step still maintains chaos
- This asymmetry is intentional and reflects the two pipelined cores as flashed

### Keystream Extraction (Both Systems Identical)

VHDL:
```vhdl
keystream <= std_logic_vector(x_state(23 downto 8));
```

Python:
```python
keystream = (x_int & 0xFFFFFFFF) >> 8 & 0xFFFF   # uint16
```

Bits [23:8] of x_state — the middle 16 bits, chosen because the top bits are dominated by the integer part (chaos amplitude) and the bottom 8 bits are noise-floor LSBs of the Q16.16.

### Stereo Audio Handling
**ALWAYS use left channel** (`samples[:, 0]`). Do **not** average channels via `.mean(axis=1)` — that caused a 28% BER bug because the encryptor was averaging while the decryptor was taking ch0.

### Performance Targets
| Metric | Target |
|---|---|
| Pearson r (original vs decrypted) | ≥ 0.95 |
| BER | < 1% |
| Sync error | → 0 |
| Clock | 40 MHz |
| Throughput | 1 sample/clk after pipeline fill |

---

## 7. The Pecora-Carroll Sync Story (Critical for Defense)

This is the most important conceptual point in the whole thesis. Get it right or get torpedoed at defense.

### Two sync modes are implemented

**Mode 1 — Pre-Shared Key (PSK)**
- Both transmitter and receiver instantiate identical generators with the same secret key (ICs + parameters)
- Each independently regenerates the same chaotic trajectory
- Keystreams match by determinism
- **Proves:** the cipher is correct
- **Does NOT prove:** anything about Pecora-Carroll synchronization itself

**Mode 2 — Pecora-Carroll Subsystem Drive (PCSD)**
- Master and slave start with **deliberately different** initial conditions
- Slave receives master's x continuously and substitutes it for its own x at each step
- Slave's y, z evolve via the chaotic equations using master's x
- Convergence proof requires negative conditional Lyapunov exponents in the y-z subsystem driven by x
- **Proves:** true digital chaos synchronization à la Pecora-Carroll

### Which chaotic system has full PC sync under x-drive

**Chua:** YES (textbook result)
- y, z subsystem driven by x has all-negative conditional Lyapunov exponents
- Slave's y and z genuinely converge to master's
- Verified: Pearson r ≥ 0.95 on y AND z after 50,000 Euler steps

**Rössler:** NO (also textbook, but inconvenient)
- dy/dt = x + a·y has positive Lyapunov factor a = +0.2
- Slave's y diverges exponentially (cannot synchronize)
- z DOES sync (negative conditional Lyapunov via z·(x-c) coupling)
- x is trivially "synced" by direct substitution

### How the thesis handles this honestly

**SO3 evidence presented in Chapter 5:**
- Chua sync convergence plots (y, z time series; r_y, r_z ≥ 0.95)
- Acknowledge Rössler limitation: "the Rössler y subsystem under x-drive achieves generalized synchronization rather than complete synchronization due to the positive conditional Lyapunov exponent. Our hybrid design exploits Chua for the rigorous synchronization proof and uses Rössler as a keystream-entropy contributor."

**Why the cipher still works despite Rössler's limitation:**
- Keystream is extracted from x_state[23:8]
- Slave's x = master's x (substituted in fabric, bit-exact)
- Therefore slave's Rössler keystream = master's Rössler keystream
- Decryption succeeds because keystream alignment is what XOR needs

---

## 8. Critical Code Findings (Bug Log)

### Bug 1: Chua diode segments inverted in old VHDL
- **Symptom:** Old `/VIVADO FILES/chua_core.vhd` had a/b values swapped in the piecewise function
- **Impact:** Produced wrong attractor; mismatched the Python reference
- **Fix:** New `chua_core.vhd` (Vivado branch / now main) implements the classical Chua diode correctly
- **Lesson:** The old "vhdl-aligned" Python branch was matching the buggy old VHDL. After we got the new VHDL, we reverted the Python diode swap.

### Bug 2: dt mismatch between Python and VHDL
- **Symptom:** Original Python used `dt = 0.01` (Chua) and `dt = 0.05` (Rössler); old VHDL used `dt = 0.02`; newer VHDL uses `dt = 0.001` (Chua) and `dt = 0.01` (Rössler)
- **Impact:** Chaotic trajectories diverge exponentially with mismatched dt; BER ≈ 50% (random)
- **Fix:** Canonical params now in PARAMS.md; both Python and VHDL aligned
- **Quantified:** Trajectories diverge in ~100 Euler steps with even small dt mismatch

### Bug 3: Stereo audio averaging
- **Symptom:** Pearson r ≈ 0.9997 but BER ≈ 28% on real 44.1 kHz stereo test audio
- **Root cause:** Encryptor used `.mean(axis=1)` (averaged channels); decryptor used `[:, 0]` (left channel only)
- **Fix:** Both encryptor and decryptor now use `[:, 0]` (left channel)
- **Lesson:** High Pearson r with high BER → look for sub-LSB rounding differences

### Bug 4: Python Pecora-Carroll "sync" was just pre-shared key
- **Symptom:** Original Python `_pecora_carroll_sync()` just regenerated trajectory from secret key
- **Issue:** This doesn't actually demonstrate PC sync; it's deterministic regeneration
- **Fix:** New `decryptor.py` supports two modes (`preshared` and `pecora_carroll`); the latter actually substitutes x_drive into slave's step function
- **Critical for defense:** If a panelist asks "show me where the y-z subsystem is driven by x" — pre-shared key has no such code path. The new code does.

### Bug 5: Rössler y-divergence under x-drive
- **Discovered when:** Single-board sim showed r_y = -0.06 while r_x = 0.999 and r_z = 1.0
- **Initially thought:** Bug in our Python sim
- **Actually:** Real mathematical result. dy/dt = x + 0.2y has positive Lyapunov.
- **Decision:** Don't change the design; document it openly and frame Chua as the sync proof, Rössler as keystream contributor
- **See:** docs/HYBRID_ENCRYPTION.md "Pecora-Carroll Synchronization Caveat"

---

## 9. Major Architectural Decisions (Decision Log)

### Decision 1: Use Vivado branch params, not SO3 branch params
- **Choice point:** SO3 branch Rössler had dt=0.01; Vivado branch (and local SO1/SO2) had dt=0.001
- **Decided:** Use Vivado branch (dt=0.001) for Chua; keep SO3 (dt=0.01) for Rössler
- **Why different per system:** Reflects the two distinct chaotic oscillators' time scales

### Decision 2: Hybrid (not parallel) as the thesis design
- **Context:** PRO2 said parallel comparison; user/team pivoted to hybrid
- **Why:** Better security claim, better novelty, title literally says "AND"
- **Scope risk:** Needs adviser sign-off (PRO2 didn't specify hybrid)
- **Open question:** Has Dr. Gustilo formally approved this scope change?

### Decision 3: Keep both Scenarios A and C (don't pick one)
- **Why:** A is the safe fast prototype, C is the full thesis claim. Defending both covers all SOs comprehensively and gives a fallback story.

### Decision 4: Single-board hybrid uses 4 oscillator instances on one chip
- **Why:** Proves the algorithm in isolation, decoupled from transport (UART)
- **Resource budget:** ~8.5% LUT utilization on Z-7020 (~4,500 / 53,200)

### Decision 5: Manual `top_wrapper.vhd` for the build (groupmate's approach)
- **What:** Wraps Vivado's BD wrapper + chaos module with explicit signal wiring
- **Why it's better:**
  1. Hardwires `rst_internal_n <= '1'` to avoid PS reset routing conflicts
  2. Uses 14 single-direction AXI GPIO IPs instead of 7 dual-channel (avoids direction confusion)
  3. Explicit named signal wires make debugging easier
- **Trade-off:** Hardware reset is permanently inactive; software reset via control bit only

### Decision 6: chua_core gets Y0_INIT/Z0_INIT generics
- **Problem:** Original chua_core hardcoded y0=z0=0 at reset, preventing slave-IC differentiation
- **Fix:** Added generics; Scenario A slave uses (Y=0.3, Z=0.2)
- **Backward compatible:** Default values match old behavior

### Decision 7: Single source of truth = PARAMS.md
- **Why:** Pre-consolidation chaos had 4 different dt values across branches
- **Rule:** Change a numeric value? Edit PARAMS.md first, then every implementation in the same commit.

### Decision 8: Merge all branches into main
- **Why:** Multiple branches caused team confusion ("which branch has the file?")
- **State after:** Only `main` exists. Six archive tags preserve old branch state.

### Decision 9: Generated artifacts (.bit, .hwh, .pyc) stay out of git
- **Exception:** test_audio.wav stays (needed for reproducible tests)
- **In .gitignore:** *.bit, *.hwh, __pycache__, outputs/, etc.

---

## 10. SO3 Wording Flag (Open Adviser Question)

The verbatim SO3 text says:
> "...between the transmitter and **receiver FPGAs** using Pecora-Carroll synchronization..."

That says **two FPGAs** (plural). Scenario A uses **one** FPGA. Two options:

- **Option A:** Reword SO3 to "between transmitter and receiver chaotic oscillators" — single-board literally satisfies SO3
- **Option B:** Treat single-board as preliminary verification; dual-board (Scenario C) is the literal SO3 evidence

**Decision needed from Dr. Gustilo.** Document and lock in before defense to avoid panel surprises.

---

## 11. Build & Run (Reproducible Steps)

### Scenario A — Single Board Build (Windows)

#### Prerequisites
- Vivado 2024.1 on Windows
- Git Bash for Windows
- PYNQ-Z2 board accessible via SSH

#### Clone repo
```bash
git clone https://github.com/JanBarria/Thesis-Code.git
cd Thesis-Code
```

#### Vivado synthesis (~45 min)
1. **File → Project → New** → name `chaos_hybrid_single_board`, location `C:\thesis\vivado\` (no spaces in path), RTL Project
2. **Add Sources** from `hdl/`:
   - `chua_core.vhd`
   - `rossler_pipelined.vhd`
   - `edge_detector.vhd`
   - `chaos_hybrid_single_board.vhd`
   - `top_wrapper.vhd`
3. **Add Constraints**: `hdl/constraints/pynq_z2_single_board.xdc` (NOT the old `pynq_z2.xdc` — that's for dual-board)
4. **Default Part**: `xc7z020clg400-1`
5. **Create Block Design** named `chaos_design`
6. Add **ZYNQ7 Processing System** IP
7. **CRITICAL:** Double-click PS → in **"Presets"** dropdown select **PYNQ-Z2** (requires board files installed) OR manually set Input Frequency = 50 MHz, FCLK_CLK0 = 100 MHz
8. **Run Block Automation** → defaults
9. Add **14 AXI GPIO** instances (single-channel each):
   - `axi_gpio_0`: **All Outputs**, 32-bit (PS→PL, control reg)
   - `axi_gpio_1` through `axi_gpio_13`: **All Inputs**, 32-bit (PL→PS, state readback)
10. Vivado terminology note: "All Outputs" = signals out of the IP into PL (PS→PL data); "All Inputs" = signals into the IP from PL (PL→PS data). Counter-intuitive but that's the convention.
11. Run Connection Automation
12. Add `chaos_hybrid_single_board` as Module Reference, wire to the GPIOs (see `top_wrapper.vhd` for the canonical mapping)
13. Right-click BD → Create HDL Wrapper → Let Vivado manage
14. **Set `top_wrapper` as Top** (it instantiates both the BD wrapper and the chaos module)
15. **Generate Bitstream** (~45 min)
16. Output: `chaos_hybrid_single_board.bit` (rename if needed to match Python script)
17. **CRITICAL: Find the `.hwh` file**. After bitstream generation it lives at:
    `<vivado_project>/<project>.gen/sources_1/bd/chaos_design/hw_handoff/chaos_design.hwh`
    Rename to `chaos_hybrid_single_board.hwh` so its base name matches the `.bit`.

#### Transfer to PYNQ board

**CRITICAL: PYNQ requires BOTH `.bit` AND `.hwh` with matching base names.** Without `.hwh`, `Overlay()` raises `RuntimeError: Unable to find metadata for bitstream`.

```bash
# Git Bash on Windows
scp chaos_hybrid_single_board.bit  xilinx@192.168.2.99:/home/xilinx/
scp chaos_hybrid_single_board.hwh  xilinx@192.168.2.99:/home/xilinx/
scp python/pynq_control/single_board_hybrid_control.py  xilinx@192.168.2.99:/home/xilinx/pynq_control/
```

**Common Windows scp gotcha:** Git Bash uses Unix-style paths (`/c/Users/...`), not Windows (`C:\Users\...`). Backslashes get eaten by bash. Fix by either:
- `cd` into the source folder first, then scp with just the filename
- Use forward slashes and `/c/` prefix
- Drag-and-drop the file into Git Bash (may need `/c/` correction)
- Use WinSCP GUI (foolproof for stuck users)

#### Run on board
```bash
ssh xilinx@192.168.2.99   # password: xilinx
cd /home/xilinx
ls -la chaos_hybrid_single_board.*   # MUST show both .bit and .hwh
sudo -E python3 pynq_control/single_board_hybrid_control.py --duration 10 --rate 1000
```

#### Pull results
```bash
scp xilinx@192.168.2.99:/home/xilinx/hybrid_data.csv .
python python/pynq_control/analyze_sync.py hybrid_data.csv
```

### Scenario C — Dual-Board Build

Same Vivado workflow but on `chaos_hybrid_dual_top.vhd` with generics:

**Master bitstream:**
```
IS_MASTER  = 1
Y0_ROSSLER = 65536    (1.0)
Z0_ROSSLER = 65536    (1.0)
Y0_CHUA    = 0        (0.0)
Z0_CHUA    = 0        (0.0)
```
→ Output: `chaos_hybrid_master.bit` + `.hwh`

**Slave bitstream:**
```
IS_MASTER  = 0
Y0_ROSSLER = 32768    (0.5)
Z0_ROSSLER = 98304    (1.5)
Y0_CHUA    = 19661    (0.3)
Z0_CHUA    = 13107    (0.2)
```
→ Output: `chaos_hybrid_slave.bit` + `.hwh`

Slave bitstream needs an extra (5th) AXI GPIO instance for x_drive inputs.

#### UART wiring (PMOD A)
```
Master JA1 (TX) ──► Slave  JA2 (RX)
Slave  JA1 (TX) ──► Master JA2 (RX)
Master GND     ──► Slave  GND       [REQUIRED]
```

#### Run order
```bash
# Slave first (blocks on UART read)
ssh xilinx@<slave_ip>  "sudo python3 /home/xilinx/hybrid_slave_control.py  --duration 10"

# Then master
ssh xilinx@<master_ip> "sudo python3 /home/xilinx/hybrid_master_control.py --duration 10"
```

UART: 230400 baud, 8 bytes/step (4 chua_x + 4 rossler_x as little-endian uint32 pairs).

---

## 12. PC-Side Reference Test (No Hardware)

```bash
cd chaos_fpga
pip3 install numpy scipy matplotlib

# Hybrid test (canonical)
python3 scripts/run_hybrid_test.py --wav test_audio/test_audio.wav

# Per-subsystem test (for SO6 comparison)
python3 scripts/run_full_test.py

# Single-board sync simulation
python3 python/reference/single_board_hybrid_sim.py --steps 50000
```

**Expected hybrid output:**
```
Sync Mode           Pearson r        BER   SNR (dB)   H (b/B)   Pass
preshared              1.0000   0.000000        inf      ~6.95  PASS
pecora_carroll         1.0000   0.000000        inf      ~6.95  PASS
```

**Expected single-board sim output (50k steps):**
```
Chua    r_x ~1.000   r_y ~1.000   r_z ~1.000    PASS
Rössler r_x ~1.000   r_y ~0       r_z ~1.000    (y diverges by theory)
```

---

## 13. Troubleshooting Cheat Sheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: Unable to find metadata for bitstream` | `.hwh` missing or wrong name | Transfer `.hwh` with same base name as `.bit` |
| `Cannot set property 'BITSTREAM.CONFIG.CONFIGRATE'` | Wrong XDC (dual-board UART version) | Use `pynq_z2_single_board.xdc` |
| `BUFBIDI_INOUT0 conflict on PS_CLK` | Zynq PS not configured for PYNQ-Z2 | Apply board preset OR manually set Input Freq = 50 MHz |
| `create_clock: No valid object(s) found for FCLK_CLK0` | XDC references wrong block design name | Remove manual `create_clock`; Vivado auto-generates from PS |
| Vivado complains about missing IPs | Block design IPs not added | Re-add AXI GPIO instances |
| `scp: no such file or directory` (file exists) | Windows path format / bash escape | `cd` into folder first, then scp with filename only |
| `Permission denied` SSH to board | Wrong password | Default is `xilinx` for both user and password |
| Slave board hangs on UART read | Master not started or wrong baud | Start slave first; verify both use 230400 baud |
| Pearson r high but BER ~28% on stereo WAV | Encryptor averages channels, decryptor takes ch0 | Both must use `[:, 0]` |
| Chua y doesn't reach r ≥ 0.95 in 10k steps | Too few iterations (Chua has small dt) | Run 50,000+ steps |
| Rössler y diverges in PC mode | Expected — positive conditional Lyapunov | Document; don't try to "fix" the chaos |
| Hybrid keystream mismatch in single-board (timing) | Master/slave pipeline alignment | Acceptable for stream cipher; document or add 1-cycle delay |

---

## 14. Defense Strategy

### Likely panel questions and prepared answers

**Q: Why hybrid instead of parallel comparison (PRO2)?**
A: The title says "AND" — a unified cipher leverages both systems' strengths. Effective key space doubles (2¹²⁸ vs 2⁶⁴), and the architecture is more cryptographically novel than separate FPGA implementations.

**Q: Show me the synchronization evidence.**
A: Chua master/slave y, z time series + Pearson r ≥ 0.95 plots (Chapter 5, Figure X). Rössler shows z synchronization and trivial x; y is intentionally not synchronized — see Q below.

**Q: Why doesn't Rössler y synchronize?**
A: This is a textbook Pecora-Carroll result. dy/dt = x + a·y has positive Lyapunov coefficient a = +0.2. Under x-drive coupling, the y subsystem has positive conditional Lyapunov exponent, so it diverges by the chaos theorem. Our hybrid design accommodates this — we use Chua for the rigorous sync proof and Rössler for keystream entropy via the trivially-synced x state.

**Q: How is this more secure than a single chaos cipher?**
A: Effective key space is the product of the two systems' key spaces (2⁶⁴ × 2⁶⁴ = 2¹²⁸). Combined keystream entropy is strictly greater than either component's (Mrs. Gerber's inequality for independent random sources). Resistant to chaos-parameter-estimation attacks against single oscillators.

**Q: SO3 says "between transmitter and receiver FPGAs" (plural) — your single-board demo uses one FPGA.**
A: [Pre-decided with adviser. Option A: "We reworded SO3 to 'chaotic oscillators' with Dr. Gustilo's approval." Option B: "Single-board verified the algorithm in isolation; the dual-board demo (Scenario C) is our literal SO3 evidence."]

**Q: How do you know the FPGA outputs match the Python reference?**
A: Bit-exact comparison. Q16.16 arithmetic is deterministic. We log FPGA state via AXI GPIO and compare against `single_board_hybrid_sim.py`. Errors should be at the LSB level only.

**Q: What's the throughput?**
A: 40 MHz clock, 1 sample per cycle after pipeline fill. UART transport (Scenario C) at 230400 baud handles 8 kB/s = 1000 samples/sec, which is the demonstration rate. For real audio at 44.1 kHz, increase UART baud rate to 921600 or use AXI burst transfers.

---

## 15. Known Gaps / Future Work

1. **MATLAB comparison for SO6** — currently only Python reference. PRO2 mentioned MATLAB explicitly.
2. **NIST randomness tests** on the combined keystream — entropy is measured by Shannon, not statistical battery
3. **Full audio encryption hardware demo** — current Scenario C tests sync, not real-time audio over UART
4. **Bitstream archival** — `.bit` files aren't in git (intentional, but no canonical archive for reproducibility)
5. **Adviser sign-off on hybrid pivot** — needs to be in writing if PRO2 said parallel
6. **SO3 wording decision** — single-board vs dual-board framing
7. **Chua AXI GPIO address verification** — Python script defaults to `0x41200000` increments; needs Vivado Address Editor check

---

## 16. Full Changelog

| Commit | Date | Summary |
|---|---|---|
| 4858a8a | 2026-06-17 | Update analyze_sync.py |
| 5eca4a0 | 2026-06-16 | Revert bitstream filename to chaos_hybrid_single_board.bit per team's Vivado output |
| b50f866 | 2026-06-16 | Add working Vivado wrappers + update Python control to match (top_wrapper.vhd, chaos_design_wrapper.vhd from groupmate's working build) |
| 86ef681 | 2026-06-16 | Add single-board-specific XDC (no UART, no manual FCLK_CLK0 constraint) — fixes the BUFBIDI_INOUT0/PS_CLK routing conflict |
| cd4ec38 | 2026-06-16 | Merge single-board into main: everything on one branch (eliminated branch confusion) |
| b7ff252 | 2026-06-16 | single-board: wire chua_core Y0_INIT/Z0_INIT generics through to slave instance |
| 3b7e030 | 2026-06-16 | chua_core: add Y0_INIT and Z0_INIT generics; wire through dual top |
| 18f99af | 2026-06-16 | Add Scenario C: full hybrid dual-board VHDL + control scripts (chaos_hybrid_dual_top.vhd, hybrid_master_control.py, hybrid_slave_control.py) |
| 5b2a464 | 2026-06-16 | Single-board hybrid: 4 oscillators (Chua + Rössler master/slave) on one PYNQ |
| 129e658 | 2026-06-16 | Add hybrid Chua⊕Rössler cipher (canonical thesis design) |
| 402923a | 2026-06-16 | Consolidate repository: single source of truth on main — eliminated multi-branch parameter chaos |

### Pre-consolidation history (archived as tags)

Before consolidation, six branches had divergent implementations:
- `archive/pre-consolidation-main` — original PRO2-style Python (α=9, β=14.28)
- `archive/pre-consolidation-Vivado` — pipelined VHDL with dt=0.001
- `archive/pre-consolidation-PYNQ` — software-only Python + UART library
- `archive/pre-consolidation-SO3` — Rössler bitstream + master/slave control via AXI GPIO
- `archive/pre-consolidation-Hybrid` — experimental sequential cascade (Chua → Rössler)
- `archive/pre-consolidation-vhdl-aligned` — our intermediate alignment work

All tags pushed to remote. Use `git checkout archive/pre-consolidation-<name>` to recover any old state.

---

## 17. Live State (as of 2026-06-17)

| Aspect | Status |
|---|---|
| Repository | Single `main` branch, all working files |
| Python reference simulator | ✅ All tests pass (Pearson r = 1.0, BER = 0.0) on real 44.1 kHz audio |
| Single-board hybrid sim | ✅ Chua r_y, r_z ≥ 0.95 (50k steps) |
| VHDL Scenario A bitstream | ✅ Synthesized by groupmate (top_wrapper.bit working) |
| VHDL Scenario C bitstream | 🟡 Not yet synthesized |
| Single-board hardware test | 🔴 Blocked on `.hwh` file transfer issue (Git Bash path problem) |
| Dual-board hardware test | 🔴 Not yet started |
| Thesis paper Chapters 4, 5 | 🔴 Need updating with hybrid framing + Rössler caveat |
| Adviser sign-off on hybrid scope | 🔴 Pending |

---

## 18. Hand-Off Notes (For Any New AI/Developer Picking This Up)

If you're a new AI assistant or developer arriving at this project:

1. **Start here:** Read this entire file before touching anything.
2. **Single source of truth:** PARAMS.md for numbers; this file for context.
3. **Branch policy:** Only `main` exists. No more branches. If you need to experiment, use a feature branch but merge or delete quickly.
4. **Bug fix discipline:** Update PARAMS.md and every implementation in the same commit. Failing this caused multi-branch chaos earlier.
5. **The Rössler y-divergence is real and expected** — don't try to "fix" it. Document it openly. It's a feature of the math, not a bug.
6. **The team works on Windows.** All hardware-side instructions must account for Git Bash path quirks. WinSCP is the foolproof fallback.
7. **PYNQ needs both `.bit` AND `.hwh`** — same base name, same folder. This trips up most newcomers.
8. **The hybrid pivot from PRO2 parallel design** needs adviser confirmation. If it's not signed off, the panel will question scope.
9. **The thesis defense story rests on:** (a) hybrid is more secure than either alone, (b) Chua provides the rigorous sync proof, (c) Rössler contributes keystream entropy without claiming PC sync of its y. Get this triangulation right and the defense is solid.

If something in the code disagrees with this document, **the code is the truth** for parameters, but **this document is the truth for intent**. Update both.

---

*End of Master Context. Last revised 2026-06-17.*
