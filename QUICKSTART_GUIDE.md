# ============================================================
# CHAOS-BASED SECURE COMMUNICATION — PYNQ-Z2 QUICK-START GUIDE
# DLSU ECE Thesis | Chua Circuit + Rössler System
# ============================================================

## PROJECT STRUCTURE

chaos_fpga/
├── run_full_test.py              ← START HERE — runs both systems
├── chua/
│   ├── chua_chaotic_generator.py   (Barria & Jusay)
│   ├── chua_keystream_extractor.py
│   ├── chua_encryptor.py
│   └── chua_decryptor.py
├── rossler/
│   ├── rossler_chaotic_generator.py (Cortes & Abalos)
│   ├── rossler_keystream_extractor.py
│   ├── rossler_encryptor.py
│   └── rossler_decryptor.py
└── outputs/                        ← all generated files appear here

---

## STEP 1 — SET UP YOUR PYNQ-Z2 BOARD

1. Insert SD card with PYNQ image → power on board
2. Connect via USB-UART (Micro-USB port labeled JTAG/UART)
3. Open a terminal and connect:

   Windows:  Use PuTTY → Serial → COM<X> → 115200 baud
   Linux/Mac: screen /dev/ttyUSB0 115200

4. Default credentials:
   Username: xilinx
   Password: xilinx

5. Find board IP address:
   hostname -I

6. SSH from your laptop (easier than serial):
   ssh xilinx@<board_ip_address>

---

## STEP 2 — TRANSFER PROJECT FILES TO BOARD

From your laptop terminal:

    scp -r chaos_fpga/ xilinx@<board_ip>:/home/xilinx/

Or use the Jupyter interface:
    Open http://<board_ip>:9090 in browser
    Password: xilinx
    Upload files via the file browser

---

## STEP 3 — INSTALL REQUIRED LIBRARIES

On the PYNQ board terminal:

    pip3 install numpy scipy matplotlib --break-system-packages

Verify:
    python3 -c "import numpy, scipy, matplotlib; print('OK')"

NOTE: PYNQ image includes numpy by default.
     scipy and matplotlib may need installation.

---

## STEP 4 — LOAD YOUR TEST AUDIO FILE

Transfer a .wav file to the board:

    scp your_audio.wav xilinx@<board_ip>:/home/xilinx/chaos_fpga/

Requirements for your .wav file:
  - Format:    16-bit PCM
  - Channels:  Mono (stereo will be auto-downmixed)
  - Duration:  1–10 seconds recommended
  - Sample rate: 8000–44100 Hz (any)

To convert an existing file to the right format:
    # Using ffmpeg (run on your laptop):
    ffmpeg -i input.mp3 -ac 1 -ar 8000 -sample_fmt s16 output.wav

---

## STEP 5 — RUN THE FULL TEST (RECOMMENDED FIRST STEP)

Navigate to the project directory on the board:

    cd /home/xilinx/chaos_fpga/

Run with synthetic test audio (no .wav needed):

    python3 run_full_test.py

Run with your own audio file:

    python3 run_full_test.py --wav your_audio.wav

This will:
  ✓ Generate chaotic trajectories for both Chua and Rössler
  ✓ Encrypt your audio with both systems
  ✓ Run Pecora-Carroll synchronization on receiver side
  ✓ Decrypt and compute performance metrics
  ✓ Save all outputs to outputs/ folder
  ✓ Generate comparison_summary.png for thesis documentation

---

## STEP 6 — RUN INDIVIDUAL SYSTEMS

CHUA CIRCUIT (Barria & Jusay):

    # Encrypt:
    cd /home/xilinx/chaos_fpga/chua/
    python3 chua_encryptor.py --input ../your_audio.wav

    # Decrypt:
    python3 chua_decryptor.py \
        --encrypted ../outputs/chua/chua_your_audio_encrypted.wav \
        --original  ../your_audio.wav \
        --drive     ../outputs/chua/chua_your_audio_drive_signal.npy

RÖSSLER SYSTEM (Cortes & Abalos):

    # Encrypt:
    cd /home/xilinx/chaos_fpga/rossler/
    python3 rossler_encryptor.py --input ../your_audio.wav

    # Decrypt:
    python3 rossler_decryptor.py \
        --encrypted ../outputs/rossler/rossler_your_audio_encrypted.wav \
        --original  ../your_audio.wav \
        --drive     ../outputs/rossler/rossler_your_audio_drive_signal.npy

---

## STEP 7 — VERIFY THE SYSTEM IS WORKING

GOOD signs (system working correctly):
  ✓ Pearson r >= 0.95  printed in terminal
  ✓ BER < 0.01         printed in terminal
  ✓ "CHAOS CHECK PASSED" message during generation
  ✓ Encrypted .wav sounds like white noise when played
  ✓ Decrypted .wav sounds identical to original

BAD signs (something went wrong):
  ✗ "CHAOS COLLAPSE DETECTED" → reduce dt
  ✗ Pearson r < 0.5           → synchronization failed
  ✗ BER > 0.1                 → keystream mismatch
  ✗ Python crashes on import  → check library installation

---

## STEP 8 — RETRIEVE OUTPUT FILES

Copy outputs back to your laptop for thesis documentation:

    scp -r xilinx@<board_ip>:/home/xilinx/chaos_fpga/outputs/ ./

Output files for your thesis:
  comparison_summary.png         → Chapter 5/6 performance comparison table
  chua/*_encrypt_plot.png        → Figure: original vs encrypted waveform
  chua/*_metrics.png             → Figure: decryption metrics (Chua)
  rossler/*_metrics.png          → Figure: decryption metrics (Rössler)

---

## COMMON ERRORS AND FIXES

ERROR: "ModuleNotFoundError: No module named 'scipy'"
FIX:   pip3 install scipy --break-system-packages

ERROR: "FileNotFoundError: Audio file not found"
FIX:   Check the path. Use absolute paths:
       python3 chua_encryptor.py --input /home/xilinx/chaos_fpga/audio.wav

ERROR: "CHAOS COLLAPSE DETECTED: std < 0.01"
FIX:   Reduce dt. For Chua: use dt=0.005. For Rössler: use dt=0.01
       python3 chua_encryptor.py --input audio.wav  (dt is set in code)
       Edit ChuaEncryptor(dt=0.005) in the script

ERROR: "AssertionError: Keystream std too low"
FIX:   The chaotic attractor collapsed. Restart with different initial conditions:
       python3 chua_encryptor.py --input audio.wav --x0 0.3 --y0 0.1

ERROR: "Pearson r < 0.5 after decryption"
FIX:   Synchronization failed. Ensure both boards use IDENTICAL parameters:
       alpha, beta, a, b, dt must match exactly.
       Check that drive_signal.npy is the correct file from the encryptor.

ERROR: Memory error on large .wav files
FIX:   Use shorter audio clips (< 5 seconds) or lower sample rate:
       ffmpeg -i long_audio.wav -t 5 -ar 8000 short_audio.wav

ERROR: "Permission denied" on PYNQ board
FIX:   sudo chmod 755 /home/xilinx/chaos_fpga/ -R

---

## TWO-BOARD UART SETUP (Advanced)

For the full thesis demonstration with two physical PYNQ-Z2 boards:

1. Connect boards via UART:
   BOARD 1 (TX) Pin 14 (TXD) → BOARD 2 (RX) Pin 16 (RXD)
   Connect GND pins together

2. On BOARD 1 (Transmitter) — run encryptor then transmit:
   The drive_signal.npy represents x bytes to send over UART.
   Replace np.save(drive_path, x_arr) with:
       import serial
       ser = serial.Serial('/dev/ttyPS0', 115200)
       for val in x_arr:
           ser.write(struct.pack('f', val))

3. On BOARD 2 (Receiver) — receive and decrypt:
   Replace np.load(drive_signal_path) with:
       x_drive = []
       for _ in range(n_samples):
           raw = ser.read(4)
           x_drive.append(struct.unpack('f', raw)[0])
       x_drive = np.array(x_drive)

See your thesis Chapter 5.4 HDL Design section for the
Vivado block design integration of the UART AXI module.

---

## TEAM WORKFLOW REMINDER (per Gantt Chart — ECE Project 3)

  Barria & Jusay  → chua/     folder (Chua Circuit)
  Cortes & Abalos → rossler/  folder (Rössler System)

Both folders follow IDENTICAL file structure.
Both can be developed and tested in parallel.
run_full_test.py integrates both for final SO6 evaluation.

---

## THESIS DELIVERABLES CHECKLIST (SO1–SO6)

  SO1: Mathematical models + discretization
       ✓ Forward Euler implemented in *_chaotic_generator.py
       ✓ Q16.16 fixed-point arithmetic in all generator files

  SO2: HDL implementation
       → Use *_chaotic_generator.py as reference for VHDL translation
       → See Section 5.4 of thesis for MyHDL workflow

  SO3: Pecora-Carroll synchronization
       ✓ Implemented in *_decryptor.py (_pecora_carroll_sync method)

  SO4: UART communication + real-time encryption
       ✓ Simulated in run_full_test.py
       → See Two-Board UART Setup above for hardware deployment

  SO5: Separate FPGA implementations
       ✓ Encryptor = BOARD 1 (Transmitter)
       ✓ Decryptor = BOARD 2 (Receiver)

  SO6: FPGA vs MATLAB comparison + metrics
       ✓ Pearson r, BER, MSE, SNR computed in *_decryptor.py
       ✓ comparison_summary.png generated by run_full_test.py
