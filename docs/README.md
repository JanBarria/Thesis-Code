# SO3: FPGA-Based Chaos Synchronization Implementation

## Project Overview

This directory contains the complete implementation for **Specific Objective 3 (SO3)** of the thesis:

> "To implement and verify digital-to-digital chaos synchronization between the transmitter and receiver FPGAs using Pecora–Carroll synchronization techniques, ensuring the FPGA-based chaotic transmitter and receiver remain synchronized."

### System Architecture

- **Hardware**: 2x PYNQ-Z2 boards (Zynq-7000 xc7z020clg400-1)
- **Oscillator**: Rossler chaotic system (a=0.2, b=0.2, c=5.7, dt=0.01)
- **Numeric Format**: Q16.16 fixed-point
- **Synchronization**: Pecora-Carroll (x-drive coupling)
- **Communication**: UART over PMOD A header (115200 baud)
- **Control Interface**: AXI GPIO (5 instances)

### Key Features

1. **Pipelined Rossler Core**: 4-stage pipeline for continuous derivative computation
2. **Stepped Execution**: Python-controlled chaos evolution via `state_step` pulses
3. **Dual Configuration**: Master (free-running) and Slave (x-driven) variants
4. **Different Initial Conditions**: Master (y=1.0, z=1.0), Slave (y=0.5, z=1.5)
5. **Real-time Data Logging**: Time-series capture for synchronization analysis

---

## Directory Structure

```
SO3/
├── hdl/
│   ├── rossler_pipelined.vhd      # Core Rossler oscillator
│   └── chaos_sync_top.vhd         # Top-level wrapper with AXI GPIO
├── scripts/
│   └── create_project.tcl         # Vivado project creation script
├── constraints/
│   └── pynq_z2.xdc               # Pin assignments and timing
├── python/
│   ├── master_control.py         # Master board control script
│   ├── slave_control.py          # Slave board control script
│   └── analyze_sync.py           # Synchronization analysis
└── docs/
    └── README.md                 # This file
```

---

## Hardware Setup

### Physical Connections

**PMOD A Header Wiring** (between Board 1 and Board 2):

```
Board 1 (Master)          Board 2 (Slave)
PMOD-A Pin 1 (TX) ────────► PMOD-A Pin 2 (RX)
PMOD-A Pin 2 (RX) ◄──────── PMOD-A Pin 1 (TX)
PMOD-A Pin 5 (GND) ──────── PMOD-A Pin 5 (GND)
```

### Board Configuration

- **Board 1 (Master)**: Laptop 1 via USB, runs `master_control.py`
- **Board 2 (Slave)**: Laptop 2 via USB, runs `slave_control.py`
- Both boards must be powered and running PYNQ OS

---

## Build Instructions

### Step 1: Generate Bitstreams

#### For MASTER Board:

1. Open Vivado (tested with 2020.1+)
2. Navigate to `SO3/scripts/`
3. Run TCL script:
   ```tcl
   cd SO3/scripts
   vivado -mode batch -source create_project.tcl
   ```
4. Open the generated project:
   ```tcl
   vivado vivado_project/chaos_sync_master.xpr
   ```
5. Verify `chaos_sync_top.vhd` generics are set to:
   ```vhdl
   Y0_INIT => 65536  -- 1.0 in Q16.16
   Z0_INIT => 65536  -- 1.0 in Q16.16
   ```
6. Run synthesis and implementation:
   ```tcl
   launch_runs synth_1 -jobs 4
   wait_on_run synth_1
   launch_runs impl_1 -to_step write_bitstream -jobs 4
   wait_on_run impl_1
   ```
7. Bitstream location: `vivado_project/chaos_sync_master.runs/impl_1/system_wrapper.bit`

#### For SLAVE Board:

1. Modify `chaos_sync_top.vhd` generics:
   ```vhdl
   Y0_INIT => 32768  -- 0.5 in Q16.16
   Z0_INIT => 98304  -- 1.5 in Q16.16
   ```
2. Change project name in `create_project.tcl`:
   ```tcl
   set project_name "chaos_sync_slave"
   ```
3. Repeat steps 2-7 from Master build
4. Bitstream location: `vivado_project/chaos_sync_slave.runs/impl_1/system_wrapper.bit`

### Step 2: Deploy to PYNQ Boards

#### Transfer Files:

```bash
# Master board
scp vivado_project/chaos_sync_master.runs/impl_1/system_wrapper.bit \
    xilinx@<master_ip>:/home/xilinx/chaos_sync_master.bit

scp python/master_control.py xilinx@<master_ip>:/home/xilinx/

# Slave board
scp vivado_project/chaos_sync_slave.runs/impl_1/system_wrapper.bit \
    xilinx@<slave_ip>:/home/xilinx/chaos_sync_slave.bit

scp python/slave_control.py xilinx@<slave_ip>:/home/xilinx/
```

Default PYNQ credentials: `xilinx` / `xilinx`

---

## Running the Experiment

### Prerequisites

On both PYNQ boards, ensure required packages are installed:

```bash
pip3 install numpy pyserial
```

### Execution Sequence

**IMPORTANT**: Start SLAVE before MASTER to ensure receiver is ready.

#### 1. Start SLAVE Board (Board 2):

```bash
ssh xilinx@<slave_ip>
cd /home/xilinx
python3 slave_control.py
```

Expected output:
```
============================================================
SLAVE Board - Chaos Synchronization Experiment
============================================================
Initializing SLAVE board...
Loading bitstream: /home/xilinx/chaos_sync_slave.bit
...
Waiting for MASTER to transmit...
```

#### 2. Start MASTER Board (Board 1):

```bash
ssh xilinx@<master_ip>
cd /home/xilinx
python3 master_control.py
```

Expected output:
```
============================================================
MASTER Board - Chaos Synchronization Experiment
============================================================
Initializing MASTER board...
...
Running... (Press Ctrl+C to stop early)
  Samples: 1000, x=2.3456, y=-1.2345, z=3.4567
```

#### 3. Wait for Completion

Both scripts will run for 10 seconds (configurable via `DURATION_SEC`), collecting ~10,000 samples at 1 kHz.

#### 4. Retrieve Data Files

```bash
# From master board
scp xilinx@<master_ip>:/home/xilinx/master_data.csv ./

# From slave board
scp xilinx@<slave_ip>:/home/xilinx/slave_data.csv ./
```

---

## Data Analysis

### Run Analysis Script

On your local machine (with matplotlib, scipy installed):

```bash
cd SO3/python
python3 analyze_sync.py
```

### Generated Outputs

The script creates an `analysis_results/` directory containing:

1. **time_series.png**: Time-domain comparison of master vs slave states
2. **phase_space.png**: Phase portraits (x-y, x-z planes)
3. **correlation.png**: Scatter plots showing state correlation
4. **report.txt**: Quantitative synchronization metrics

### Success Criteria (from Thesis Section 4.7)

**Target**: Pearson correlation coefficient **r ≥ 0.95** for all states (x, y, z)

Example report output:
```
PEARSON CORRELATION COEFFICIENTS:
  X: r = 0.998765 (p = 0.00e+00)  ✓ PASS
  Y: r = 0.996543 (p = 0.00e+00)  ✓ PASS
  Z: r = 0.997890 (p = 0.00e+00)  ✓ PASS

OVERALL ASSESSMENT:
  ✓ SYNCHRONIZATION SUCCESSFUL - All states meet target threshold
```

---

## Troubleshooting

### Issue: UART Communication Failure

**Symptoms**: Slave receives no data, sample count = 0

**Solutions**:
1. Verify physical wiring (TX-RX crossover, GND connection)
2. Check UART device exists: `ls -l /dev/ttyPS1`
3. Verify baud rate matches (115200) on both boards
4. Ensure EMIO UART1 is enabled in Vivado block design

### Issue: Low Correlation (r < 0.95)

**Symptoms**: Synchronization error remains high, states diverge

**Solutions**:
1. Verify `sync_enable` is set correctly (0=master, 1=slave)
2. Check initial conditions differ between master/slave builds
3. Increase `DURATION_SEC` to allow more convergence time
4. Verify `state_step` pulse timing is consistent

### Issue: Bitstream Load Fails

**Symptoms**: `Overlay()` raises exception

**Solutions**:
1. Verify bitstream path is correct
2. Check file permissions: `chmod 644 *.bit`
3. Ensure bitstream matches board (PYNQ-Z2, xc7z020clg400-1)
4. Try manual load: `from pynq import Overlay; ol = Overlay('path.bit')`

### Issue: AXI GPIO Address Errors

**Symptoms**: `AxiGPIO()` initialization fails

**Solutions**:
1. Open Vivado project, check Address Editor
2. Verify base addresses match Python scripts:
   - GPIO0: 0x41200000
   - GPIO1: 0x41210000
   - GPIO2: 0x41220000
   - GPIO3: 0x41230000
   - GPIO4: 0x41240000
3. Regenerate bitstream if addresses changed

---

## Technical Details

### Q16.16 Fixed-Point Format

- **Range**: -32768.0 to +32767.99998
- **Resolution**: 1/65536 ≈ 0.000015
- **Conversion**:
  - Float to Q16.16: `int_val = int(float_val * 65536)`
  - Q16.16 to Float: `float_val = int_val / 65536.0`

### Rossler Parameters (Q16.16)

| Parameter | Float | Q16.16 Integer | Hex        |
|-----------|-------|----------------|------------|
| a         | 0.2   | 13107          | 0x00003333 |
| b         | 0.2   | 13107          | 0x00003333 |
| c         | 5.7   | 373554         | 0x0005B332 |
| dt        | 0.01  | 655            | 0x0000028F |

### AXI GPIO Register Map

**GPIO0 (Control/Status)**:
- Bit 0: `state_step` (write 1 to pulse)
- Bit 1: `sync_enable` (0=master, 1=slave)
- Bit 2: `rst` (active high reset)

**GPIO1**: `x_drive` input (32-bit, slave only)

**GPIO2-4**: `x_out`, `y_out`, `z_out` readback (32-bit each)

### UART Protocol

- **Format**: 4 bytes per transmission (little-endian)
- **Content**: x_state value in Q16.16 format
- **Rate**: ~1 kHz (1 transmission per chaos step)
- **Total bandwidth**: 4 KB/s (well within 115200 baud capacity)

---

## Performance Metrics

### Expected Results

- **Synchronization time**: < 1 second (transient convergence)
- **Steady-state error**: < 0.001 (mean absolute error)
- **Correlation coefficient**: > 0.99 (typically 0.995-0.999)
- **Sample rate**: 1000 Hz (configurable)
- **Data collection**: 10 seconds = 10,000 samples

### Resource Utilization (per board)

Estimated for xc7z020:
- **LUTs**: ~2000 (< 5% of 53,200)
- **FFs**: ~1500 (< 3% of 106,400)
- **DSPs**: 15 (< 7% of 220) - for multiplications
- **BRAMs**: 0 (all registers)

---

## References

1. Thesis Section 4.7: Synchronization Performance Metrics
2. Pecora, L. M., & Carroll, T. L. (1990). "Synchronization in chaotic systems"
3. PYNQ Documentation: http://pynq.readthedocs.io/
4. Vivado Design Suite User Guide (UG893)

---

## Contact

For questions or issues, contact the thesis team at De La Salle University ECE Department.

**Last Updated**: June 2026