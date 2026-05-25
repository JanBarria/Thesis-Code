# FPGA Implementation of Chaos-Based Secure Communication
## Using Chua Circuit and Rössler System

**De La Salle University - ECE Thesis Project**

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Hardware Requirements](#hardware-requirements)
4. [Software Requirements](#software-requirements)
5. [Installation Guide](#installation-guide)
6. [Quick Start Guide](#quick-start-guide)
7. [Detailed Usage Instructions](#detailed-usage-instructions)
8. [File Structure](#file-structure)
9. [Performance Metrics](#performance-metrics)
10. [Troubleshooting](#troubleshooting)
11. [Team Members](#team-members)

---

## 🎯 Project Overview

This project implements a chaos-based secure communication system using two different chaotic oscillators:
- **Chua Circuit** (Double-Scroll Attractor) - Team: Barria & Jusay
- **Rössler System** (Spiral Attractor) - Team: Cortes & Abalos

Both systems use:
- **Encryption Method**: Bitwise XOR with chaotic keystream
- **Synchronization**: Pecora-Carroll method
- **Hardware**: PYNQ-Z2 FPGA boards (Zynq-7000 SoC)
- **Communication**: UART interface
- **Audio Format**: Mono, 16-bit PCM .wav files

---

## 🏗️ System Architecture

```
TRANSMITTER (Board 1)              RECEIVER (Board 2)
┌─────────────────────┐           ┌─────────────────────┐
│  Audio Input (.wav) │           │                     │
└──────────┬──────────┘           │                     │
           │                       │                     │
           ▼                       │                     │
┌─────────────────────┐           │                     │
│ Chaotic Generator   │           │ Chaotic Generator   │
│ (Chua or Rössler)   │           │ (Synchronized)      │
└──────────┬──────────┘           └──────────▲──────────┘
           │                                  │
           ▼                                  │
┌─────────────────────┐           ┌──────────┴──────────┐
│ Keystream Extractor │           │  Drive Signal (x)   │
└──────────┬──────────┘           │  via UART           │
           │                       └─────────────────────┘
           ▼                                  │
┌─────────────────────┐                      │
│  XOR Encryption     │                      │
│  C[n] = P[n] ⊕ K[n] │                      │
└──────────┬──────────┘                      │
           │                                  │
           ▼                                  ▼
┌─────────────────────┐           ┌─────────────────────┐
│ Encrypted Audio     │──UART────▶│ Encrypted Audio     │
│ + Drive Signal      │           │ + Drive Signal      │
└─────────────────────┘           └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │ Keystream Extractor │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │  XOR Decryption     │
                                  │  P[n] = C[n] ⊕ K[n] │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │ Decrypted Audio     │
                                  └─────────────────────┘
```

---

## 🔧 Hardware Requirements

- **2x PYNQ-Z2 FPGA Boards** (Zynq-7000 SoC)
- **UART Cable** (for board-to-board communication)
- **MicroSD Cards** (8GB minimum, PYNQ image pre-flashed)
- **USB Cables** (for power and programming)
- **Computer** (Windows/Linux/Mac for development)

---

## 💻 Software Requirements

### On PYNQ-Z2 Boards:
- PYNQ v2.7 or later (pre-installed on SD card)
- Python 3.6+
- Required Python packages:
  - `numpy`
  - `scipy`
  - `matplotlib`

### On Development Computer:
- Python 3.6+
- Jupyter Notebook (optional, for remote access)
- SSH client (PuTTY for Windows, or built-in terminal for Linux/Mac)

---

## 📦 Installation Guide

### Step 1: Prepare PYNQ-Z2 Boards

1. **Flash PYNQ Image** (if not already done):
   - Download PYNQ v2.7 image from [PYNQ.io](http://www.pynq.io/)
   - Flash to microSD card using Win32DiskImager or Etcher
   - Insert SD card into PYNQ-Z2 board

2. **Boot the Board**:
   - Set boot mode jumper to SD card
   - Connect power via USB
   - Wait for board to boot (green LED should be solid)

3. **Connect to Network**:
   - Connect Ethernet cable or use USB-Ethernet
   - Default IP: `192.168.2.99`
   - Default credentials: `xilinx` / `xilinx`

### Step 2: Transfer Project Files

**Option A: Using SCP (Recommended)**
```bash
# From your computer, navigate to project directory
scp -r chaos_secure_communication xilinx@192.168.2.99:/home/xilinx/
```

**Option B: Using Jupyter Notebook**
1. Open browser: `http://192.168.2.99:9090`
2. Login with password: `xilinx`
3. Upload files via Jupyter interface

### Step 3: Install Dependencies (if needed)

SSH into the board:
```bash
ssh xilinx@192.168.2.99
```

Install packages:
```bash
sudo pip3 install numpy scipy matplotlib
```

---

## 🚀 Quick Start Guide

### Test with Chua Circuit System

#### 1. Create Test Audio File

First, create a simple test audio file:

```bash
cd /home/xilinx/chaos_secure_communication
python3 -c "
import numpy as np
from scipy.io import wavfile

# Generate 1-second test tone (440 Hz, A4 note)
sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)

# Save as WAV file
wavfile.write('test_audio/test_tone.wav', sample_rate, audio)
print('Test audio created: test_audio/test_tone.wav')
"
```

#### 2. Encrypt Audio (Transmitter)

```bash
cd chua_system
python3 chua_encryptor.py ../test_audio/test_tone.wav
```

**Expected Output:**
- `encrypted_audio.wav` - Encrypted audio file
- `encrypted_audio_secret_key.txt` - Secret key (initial conditions)
- `encrypted_audio_drive_signal.npy` - Drive signal for receiver
- `encrypted_audio_waveforms.png` - Visualization
- `encrypted_audio_spectrograms.png` - Frequency analysis

#### 3. Decrypt Audio (Receiver)

```bash
python3 chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

**Expected Output:**
- `decrypted_audio.wav` - Recovered audio
- `decrypted_audio_comparison.png` - Comparison plot
- Performance metrics printed to console

#### 4. Verify Results

Check the performance metrics:
- **Pearson Correlation**: Should be ≥ 0.95 (ideally > 0.99)
- **Bit Error Rate (BER)**: Should be < 1% (ideally < 0.01%)
- **Mean Squared Error (MSE)**: Should be very low

---

### Test with Rössler System

Follow the same steps, but use the `rossler_system` directory:

```bash
cd /home/xilinx/chaos_secure_communication/rossler_system
python3 rossler_encryptor.py ../test_audio/test_tone.wav
python3 rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

---

## 📖 Detailed Usage Instructions

### Working with Your Own Audio Files

#### 1. Prepare Audio File

Your audio must be:
- **Format**: WAV (`.wav`)
- **Channels**: Mono (single channel)
- **Bit Depth**: 16-bit PCM
- **Sample Rate**: Any (typically 44100 Hz or 48000 Hz)

**Convert stereo to mono using Python:**
```python
from scipy.io import wavfile
import numpy as np

# Load stereo audio
sr, audio = wavfile.read('stereo_audio.wav')

# Convert to mono (average channels)
if audio.ndim == 2:
    mono = np.mean(audio, axis=1).astype(np.int16)
else:
    mono = audio

# Save mono audio
wavfile.write('mono_audio.wav', sr, mono)
```

#### 2. Transfer Audio to PYNQ Board

```bash
scp your_audio.wav xilinx@192.168.2.99:/home/xilinx/chaos_secure_communication/test_audio/
```

#### 3. Run Encryption

**For Chua Circuit:**
```bash
cd /home/xilinx/chaos_secure_communication/chua_system
python3 chua_encryptor.py ../test_audio/your_audio.wav
```

**For Rössler System:**
```bash
cd /home/xilinx/chaos_secure_communication/rossler_system
python3 rossler_encryptor.py ../test_audio/your_audio.wav
```

#### 4. Simulate UART Transmission

In a real two-board setup, you would transmit:
1. Encrypted audio file
2. Drive signal (x state variable)

For testing on a single board, these files are already available locally.

#### 5. Run Decryption

**For Chua Circuit:**
```bash
python3 chua_decryptor.py encrypted_audio.wav ../test_audio/your_audio.wav
```

**For Rössler System:**
```bash
python3 rossler_decryptor.py encrypted_audio.wav ../test_audio/your_audio.wav
```

---

## 📁 File Structure

```
chaos_secure_communication/
│
├── README.md                          # This file
├── COMPARISON_TABLE.md                # Chua vs Rössler comparison
│
├── chua_system/                       # Chua Circuit Implementation
│   ├── chua_chaotic_generator.py     # Chaotic oscillator
│   ├── chua_keystream_extractor.py   # Keystream generation
│   ├── chua_encryptor.py             # Encryption (transmitter)
│   └── chua_decryptor.py             # Decryption (receiver)
│
├── rossler_system/                    # Rössler System Implementation
│   ├── rossler_chaotic_generator.py  # Chaotic oscillator
│   ├── rossler_keystream_extractor.py # Keystream generation
│   ├── rossler_encryptor.py          # Encryption (transmitter)
│   └── rossler_decryptor.py          # Decryption (receiver)
│
└── test_audio/                        # Test audio files
    └── (your .wav files here)
```

---

## 📊 Performance Metrics

### Expected Performance

| Metric | Target | Excellent | Good | Poor |
|--------|--------|-----------|------|------|
| **Pearson Correlation** | ≥ 0.95 | > 0.99 | 0.95-0.99 | < 0.95 |
| **Bit Error Rate (BER)** | < 1% | < 0.01% | 0.01-1% | > 1% |
| **Synchronization Error** | → 0 | < 0.001 | 0.001-0.01 | > 0.01 |
| **MSE** | Low | < 10 | 10-100 | > 100 |

### Interpreting Results

**Perfect Decryption:**
- Correlation = 1.0
- BER = 0%
- MSE = 0
- Decrypted audio identical to original

**Good Decryption:**
- Correlation > 0.99
- BER < 0.1%
- Audio sounds identical to original

**Poor Decryption:**
- Correlation < 0.95
- BER > 1%
- Audio has noticeable distortion

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Import Error: No module named 'scipy'"

**Solution:**
```bash
ssh xilinx@192.168.2.99
sudo pip3 install scipy
```

#### Issue 2: "Audio must be mono" Error

**Solution:** Convert your audio to mono first:
```python
from scipy.io import wavfile
import numpy as np

sr, audio = wavfile.read('stereo.wav')
mono = np.mean(audio, axis=1).astype(np.int16) if audio.ndim == 2 else audio
wavfile.write('mono.wav', sr, mono)
```

#### Issue 3: Low Correlation (< 0.95)

**Possible Causes:**
1. **Wrong secret key**: Ensure receiver uses same initial conditions
2. **Drive signal mismatch**: Verify drive signal file is correct
3. **Parameter mismatch**: Check that transmitter and receiver use same parameters

**Solution:** Verify all files are from the same encryption run.

#### Issue 4: "FileNotFoundError: Secret key file not found"

**Solution:** Ensure the secret key file is in the same directory as encrypted audio:
```bash
ls -la encrypted_audio*
# Should show:
# encrypted_audio.wav
# encrypted_audio_secret_key.txt
# encrypted_audio_drive_signal.npy
```

#### Issue 5: Matplotlib Display Issues on PYNQ

**Solution:** If plots don't display, disable visualization:
```python
# In encryptor
encryptor.encrypt_audio('input.wav', visualize=False)

# In decryptor
decryptor.decrypt_audio('encrypted.wav', visualize=False)
```

#### Issue 6: Out of Memory Error

**Solution:** Process shorter audio files or increase swap space:
```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🧪 Testing Checklist

Before final demonstration, verify:

- [ ] Both PYNQ boards boot successfully
- [ ] Network connectivity established
- [ ] All Python dependencies installed
- [ ] Test audio file encrypts successfully
- [ ] Encrypted audio is noise-like (check spectrogram)
- [ ] Decryption recovers original audio
- [ ] Correlation ≥ 0.95
- [ ] BER < 1%
- [ ] Both Chua and Rössler systems work
- [ ] UART communication tested (if using two boards)

---

## 👥 Team Members

### Chua Circuit Team
- **Barria**
- **Jusay**

### Rössler System Team
- **Cortes**
- **Abalos**

**Institution:** De La Salle University  
**Program:** Electronics and Communications Engineering  
**Project:** FPGA Implementation of Chaos-Based Secure Communication

---

## 📚 References

1. Chua, L. O. (1992). "The Genesis of Chua's Circuit"
2. Rössler, O. E. (1976). "An Equation for Continuous Chaos"
3. Pecora, L. M., & Carroll, T. L. (1990). "Synchronization in Chaotic Systems"
4. PYNQ Documentation: http://pynq.readthedocs.io/

---

## 📝 License

This project is for educational purposes as part of a thesis requirement at De La Salle University.

---

## 🆘 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the code comments in each module
3. Contact your thesis advisor
4. Refer to PYNQ documentation

---

**Last Updated:** May 2026  
**Version:** 1.0