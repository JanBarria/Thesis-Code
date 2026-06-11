# Vivado VHDL Source Files

This folder contains all VHDL source files for the chaotic oscillator FPGA implementation and verification.

## File Structure

```
vivado/
├── rossler_core.vhd          # Rössler oscillator (4-stage pipeline)
├── chua_core_cleaned.vhd     # Chua oscillator (5-stage pipeline, synchronized)
├── chaos_system_tb.vhd       # Comprehensive testbench with file I/O
├── PHASE1_SUMMARY.md         # Detailed documentation
└── README.md                 # This file
```

## Source Files

### 1. rossler_core.vhd (330 lines)
**Rössler Chaotic Oscillator**
- 4-stage pipelined architecture
- Q16.16 fixed-point arithmetic
- Parameters: a=0.2, b=0.2, c=5.7, dt=0.001
- Initial conditions: x=1.0, y=1.0, z=1.0
- Produces single-scroll attractor
- All multiplications synchronous (inside processes)

### 2. chua_core_cleaned.vhd (310 lines)
**Chua Chaotic Oscillator**
- 5-stage pipelined architecture (extra stage for piecewise diode)
- Q16.16 fixed-point arithmetic
- Parameters: α=15.6, β=28.0, m0=-1.143, m1=-0.714, dt=0.001
- Initial conditions: x=0.1, y=0.0, z=0.0
- Produces double-scroll attractor
- **CLEANED:** All multiplications now synchronous (matches rossler_core style)

### 3. chaos_system_tb.vhd (368 lines)
**Comprehensive Testbench**
- Instantiates both Rössler and Chua cores
- Generates 40 MHz clock (25 ns period)
- Active-high synchronous reset (10 cycles)
- Writes state vectors to files when output_valid is high
- Output format: hexadecimal, space-separated (x y z)
- Simulation duration: 100,000 cycles (2.5 ms)

## How to Use in Vivado

### Method 1: GUI
1. Open Vivado
2. Create new project or open existing
3. Add files:
   - Sources → Add Files → Select `rossler_core.vhd` and `chua_core_cleaned.vhd`
   - Simulation Sources → Add Files → Select `chaos_system_tb.vhd`
4. Set `chaos_system_tb` as top module for simulation
5. Run Behavioral Simulation
6. Execute: `run all`

### Method 2: TCL Script
```tcl
# Add source files
add_files -fileset sources_1 [glob vivado/rossler_core.vhd]
add_files -fileset sources_1 [glob vivado/chua_core_cleaned.vhd]

# Add testbench
add_files -fileset sim_1 [glob vivado/chaos_system_tb.vhd]
set_property top chaos_system_tb [get_filesets sim_1]

# Launch simulation
launch_simulation

# Run until testbench auto-stops
run all
```

## Expected Output Files

After simulation completes, two files will be generated in your Vivado project directory:

### rossler_hardware_vectors.txt
- Contains ~99,990 samples
- Format: `XXXXXXXX YYYYYYYY ZZZZZZZZ` (hex)
- File size: ~2.7 MB
- Represents Rössler single-scroll attractor trajectory

### chua_hardware_vectors.txt
- Contains ~99,985 samples
- Format: `XXXXXXXX YYYYYYYY ZZZZZZZZ` (hex)
- File size: ~2.7 MB
- Represents Chua double-scroll attractor trajectory

## Simulation Console Output

Expected messages during simulation:
```
========================================
Chaos System Testbench Started
========================================
Clock frequency: 40 MHz (25 ns period)
Reset duration: 10 cycles
Simulation duration: 100000 cycles
Expected runtime: 2500000 ns
Output files:
  - rossler_hardware_vectors.txt
  - chua_hardware_vectors.txt
========================================

# Rössler output file opened: rossler_hardware_vectors.txt
# Chua output file opened: chua_hardware_vectors.txt
# Simulation progress: 10000 / 100000 cycles (10%)
# Rössler: 10000 samples written
# Chua: 10000 samples written
...
# Simulation complete: 100000 cycles simulated
# Rössler output file closed. Total samples: 99990
# Chua output file closed. Total samples: 99985
```

## Timing Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Target Clock | 40 MHz | PYNQ-Z2 board clock |
| Clock Period | 25 ns | 1 / 40 MHz |
| Rössler Pipeline | 4 stages | Valid after 4 cycles |
| Chua Pipeline | 5 stages | Valid after 5 cycles |
| Throughput | 1 sample/cycle | After pipeline fills |
| DSP48 Usage | ~7 per core | Vivado synthesis estimate |

## Fixed-Point Format

All state variables use **Q16.16** format:
- 32 bits total
- 16 bits integer part (including sign)
- 16 bits fractional part
- Range: -32768.0 to +32767.99998
- Resolution: 1/65536 ≈ 0.000015

### Conversion Examples
| Float | Q16.16 Integer | Hex |
|-------|----------------|-----|
| 0.0 | 0 | 0x00000000 |
| 1.0 | 65536 | 0x00010000 |
| -1.0 | -65536 | 0xFFFF0000 |
| 0.5 | 32768 | 0x00008000 |
| 5.7 | 373554 | 0x0005B312 |

## Next Steps

After successful simulation:
1. Verify output files exist
2. Check file sizes (~2.7 MB each)
3. Proceed to Phase 2: Python visualization
4. Parse hex values and convert to floats
5. Generate 2D and 3D phase portraits
6. Verify chaotic attractor shapes

## Troubleshooting

### Files not created
- Check simulation ran to completion
- Verify `output_valid` signals went high
- Increase `SIM_CYCLES` if needed

### Compilation errors
- Ensure all three VHDL files are in project
- Check file paths are correct
- Verify VHDL-2008 or VHDL-93 compatibility

### Timing violations (post-synthesis)
- All multiplications are properly pipelined
- Should meet 40 MHz timing on Zynq-7000
- If issues persist, reduce clock frequency

## Documentation

See `PHASE1_SUMMARY.md` for:
- Detailed architecture explanation
- Synchronization changes rationale
- Complete testbench documentation
- File format specifications
- Phase 2 preparation guide

## Author
Senior Digital Design and FPGA Verification Engineer

## Date
2026-06-11

## Status
✅ Phase 1 Complete - Ready for Simulation and Phase 2 Analysis