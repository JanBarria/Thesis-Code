# Chaos-Based Secure Communication on PYNQ-Z2

**FPGA Implementation of Chaos-Based Secure Communication Using Chua Circuit and Rössler System**

DLSU ECE Thesis Project | Team MICRO-3-2425-1 | Adviser: Dr. Reggie Gustilo
Members: Abalos, Barria, Cortes, Jusay

---

## Repository Layout

```
chaos_fpga/
├── PARAMS.md                # ← Single source of truth for all numeric params
├── README.md                # ← This file
├── hdl/                     # Synthesizable VHDL
│   ├── chua_core.vhd          # 5-stage pipelined Chua oscillator
│   ├── rossler_pipelined.vhd  # 4-stage pipelined Rössler oscillator
│   ├── chaos_sync_top.vhd     # AXI-GPIO + EMIO UART wrapper (PC sync demo)
│   ├── chaos_system_tb.vhd    # Behavioral testbench with file I/O
│   └── constraints/
│       ├── pynq_z2.xdc        # Board pinout
│       └── timing.xdc         # Timing constraints
├── python/
│   ├── reference/           # Bit-exact Python simulator
│   │   ├── q16_arith.py       # Q16.16 fixed-point helpers
│   │   ├── chua_generator.py    # Matches chua_core.vhd
│   │   ├── rossler_generator.py # Matches rossler_pipelined.vhd
│   │   ├── encryptor.py         # XOR stream cipher (TX side)
│   │   ├── decryptor.py         # XOR + PC sync (RX side)
│   │   └── chaos_models.py      # SO1 floating-point math reference
│   ├── pynq_control/        # On-board PYNQ Python (talks to FPGA via AXI GPIO)
│   │   ├── master_control.py    # MASTER board: free-running, transmit x
│   │   ├── slave_control.py     # SLAVE board:  receive x, PC sync
│   │   └── analyze_sync.py      # Plot + quantify sync quality
│   └── uart/                # Generic UART library (pyserial + CRC32)
│       ├── uart_config.py
│       ├── uart_protocol.py
│       ├── uart_transmitter.py
│       └── uart_receiver.py
├── notebooks/
│   └── Chaos_Models_Mathematical_Documentation.ipynb
├── scripts/
│   ├── run_full_test.py     # End-to-end reference test
│   └── create_project.tcl   # Vivado project generation
├── test_audio/
│   └── test_audio.wav       # Test audio
└── docs/                    # SO-aligned documentation (see below)
```

---

## Student Outcomes (SO1-SO6)

| SO | Description | Where to find evidence |
|---|---|---|
| **SO1** | Mathematical models + fixed-point discretization | `python/reference/chaos_models.py`, `notebooks/` |
| **SO2** | HDL implementation + simulation verification | `hdl/`, `hdl/chaos_system_tb.vhd` |
| **SO3** | Pecora-Carroll synchronization between two FPGAs | `hdl/chaos_sync_top.vhd`, `python/pynq_control/` |
| **SO4** | UART integration + real-time audio encryption | `python/uart/`, `python/reference/encryptor.py` |
| **SO5** | Separate FPGA roles for TX (encrypt) and RX (decrypt) | `python/pynq_control/master_control.py` & `slave_control.py` |
| **SO6** | Performance evaluation + MATLAB/Python comparison | `scripts/run_full_test.py` output |

---

## Quick Start

### 1. PC-side reference test (no hardware)

```bash
pip3 install numpy scipy matplotlib
cd chaos_fpga
python3 scripts/run_full_test.py
```

Expected output:
```
System     Sync Mode          Pearson r        BER   SNR (dB)   Pass
chua       preshared             1.0000   0.000000     ~167     PASS
chua       pecora_carroll        1.0000   0.000000     ~167     PASS
rossler    preshared             1.0000   0.000000     ~167     PASS
rossler    pecora_carroll        1.0000   0.000000     ~167     PASS
```

### 2. FPGA hardware test (two PYNQ-Z2 boards)

#### a. Synthesize bitstreams
```bash
cd hdl
vivado -mode batch -source ../scripts/create_project.tcl
# Build MASTER bitstream first
# Then edit chaos_sync_top.vhd Y0_INIT/Z0_INIT for slave, rebuild
```

#### b. Wire boards via PMOD A
```
Board 1 PMOD JA1 (TX) ─────► Board 2 PMOD JA2 (RX)
Board 2 PMOD JA1 (TX) ─────► Board 1 PMOD JA2 (RX)
Board 1 GND          ─────► Board 2 GND
```

#### c. Run control scripts
```bash
# On MASTER board (free-running Rössler, transmits x via UART)
scp python/pynq_control/master_control.py xilinx@<master_ip>:/home/xilinx/
ssh xilinx@<master_ip> "sudo python3 /home/xilinx/master_control.py"

# On SLAVE board (Pecora-Carroll sync)
scp python/pynq_control/slave_control.py xilinx@<slave_ip>:/home/xilinx/
ssh xilinx@<slave_ip> "sudo python3 /home/xilinx/slave_control.py"
```

#### d. Verify synchronization
```bash
python3 python/pynq_control/analyze_sync.py master_data.csv slave_data.csv
# Expects Pearson r ≥ 0.95
```

---

## Synchronization Modes Explained

Two modes are supported in this repository because they prove different
things:

### Mode 1: Pre-Shared Key (default, Python reference)
- Both transmitter and receiver instantiate identical generators with the
  **same** secret key (initial conditions + parameters).
- They independently regenerate the same chaotic trajectory.
- Decryption succeeds because the keystreams match by construction.
- **What this proves**: the cipher is correct end-to-end.
- **What this does NOT prove**: Pecora-Carroll synchronization itself.

### Mode 2: Pecora-Carroll Subsystem Drive (matches new VHDL)
- Master and slave start with **deliberately different** initial conditions
  (e.g. Rössler master at (1,1,1), slave at (1, 0.5, 1.5)).
- Slave receives master's x continuously and substitutes it for its own x.
- Slave's y, z then evolve via the chaotic equations using master's x.
- y, z exponentially converge to master's y, z due to the negative
  conditional Lyapunov exponents of the y-z subsystem.
- **What this proves**: true digital chaos synchronization à la Pecora-Carroll.

Both modes produce the same decryption result once synchronized. Mode 2
is what SO3 of the thesis title refers to.

---

## Parameter Reference

All parameters are pinned in [PARAMS.md](PARAMS.md). Whenever you see a
magic number in code, you should be able to trace it back to that file.

Notable values:
- **Chua dt = 0.001** (66 in Q16.16) — small to handle sharp diode transitions
- **Rössler dt = 0.01** (655 in Q16.16) — larger because of smoother dynamics
- **Keystream = x_state[23:8]** for both systems — middle 16 bits of x state

---

## Testing & CI Reproducibility

The `scripts/run_full_test.py` is the canonical regression test. It
validates:

1. Chua reference generator produces chaos (`std(x) > 0.05`)
2. Rössler reference generator produces chaos (`std(x) > 1`)
3. Pre-shared key encryption decrypts to original (Pearson r = 1.0, BER = 0)
4. True Pecora-Carroll sync decrypts to original after the slave converges
5. Both systems share the same keystream extraction formula

Run it as part of any PR or before tagging a release.

---

## Hardware Bitstreams

**Note:** `.bit` files are NOT committed to this repo because:
- They are large (~4 MB each)
- They are regenerable from the VHDL sources in `hdl/`
- They depend on specific Vivado tool versions

To reproduce: install Vivado 2020.1+, run `scripts/create_project.tcl`,
synthesize. Builds take 30-60 minutes per bitstream.

---

## Contributing / Editing Conventions

1. **Edit `PARAMS.md` first** when changing any numeric value. Then update
   every implementation (VHDL constants, Python constants) in the same
   commit. Failing this discipline is what caused the multi-branch
   parameter-mismatch chaos that this consolidation cleans up.
2. **Don't commit build artifacts**: no `.bit`, `.pyc`, `__pycache__/`,
   output `.wav` files, generated plots, or Vivado project directories.
   See `.gitignore`.
3. **Tag releases**: use `git tag -a vX.Y` so that "which version produced
   the SO6 numbers in chapter 5" has an authoritative answer.

---

## License

Academic use only. Contact the team before redistribution.
