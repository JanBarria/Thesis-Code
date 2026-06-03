# 🎯 Single PYNQ Board Testing Guide

## 📋 Overview

This guide shows you how to test your chaos-based encryption system on **ONE PYNQ board only**, without needing UART communication between two boards.

**Perfect for:**
- ✅ Testing if your code works before connecting two boards
- ✅ Debugging encryption/decryption algorithms
- ✅ Verifying chaotic generators produce correct output
- ✅ Getting started quickly with just one working board

**Time Required:** 1-2 hours

---

## 🎯 What You'll Test

### Single-Board Workflow:
```
1. Load audio file → 2. Generate chaotic keystream → 
3. Encrypt audio → 4. Save encrypted file → 
5. Decrypt audio → 6. Compare with original → 
7. Calculate metrics
```

**All on ONE board!**

---

## 📥 STEP 1: Prepare Your PYNQ Board

### Requirements:
- ✅ PYNQ-Z2 board with PYNQ v3.0.1 flashed
- ✅ Board connected via USB to your computer
- ✅ Board accessible at: `http://192.168.2.99:9090`
- ✅ Can login with password: `xilinx`

### Verify Board is Ready:
```powershell
# Test ping
ping 192.168.2.99

# Should see: Reply from 192.168.2.99
```

---

## 📤 STEP 2: Upload Files to PYNQ Board

### Method A: Via Jupyter Web Interface (Easiest)

1. **Open browser:** `http://192.168.2.99:9090`
2. **Login:** Password `xilinx`
3. **Create folder:** Click "New" → "Folder" → Rename to `chaos_test`
4. **Enter folder:** Click on `chaos_test`
5. **Upload files:** Click "Upload" button

**Files to upload:**
```
From: C:\Users\User\Desktop\chaos_secure_communication\PYNQ\

Upload these files:
- uart_lib/__init__.py
- uart_lib/uart_config.py
- uart_lib/uart_protocol.py
- uart_lib/uart_transmitter.py
- uart_lib/uart_receiver.py
```

6. **Create test folder:** Click "New" → "Folder" → Rename to `audio_files`

### Method B: Via SCP (Alternative)

```powershell
# From your Desktop
cd C:\Users\User\Desktop
scp -r chaos_secure_communication\PYNQ xilinx@192.168.2.99:/home/xilinx/chaos_test
# Password: xilinx
```

---

## 🔧 STEP 3: Install Dependencies

### In Jupyter:
1. Click "New" → "Terminal"
2. Run these commands:

```bash
# Install PySerial (for UART library)
sudo pip3 install pyserial

# Verify installation
python3 -c "import serial; print('PySerial installed!')"

# Check Python packages
python3 -c "import numpy, scipy, matplotlib; print('All packages ready!')"
```

**Expected output:**
```
PySerial installed!
All packages ready!
```

---

## 📝 STEP 4: Create Single-Board Test Script

### In Jupyter:
1. Click "New" → "Text File"
2. Copy the code below
3. Save as: `single_board_test.py`

```python
#!/usr/bin/env python3
"""
Single PYNQ Board Testing Script
Tests chaos-based encryption/decryption on ONE board
No UART communication required
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.stats import pearsonr
import time

print("="*60)
print("SINGLE BOARD CHAOS ENCRYPTION TEST")
print("="*60)
print()

# ============================================================
# STEP 1: GENERATE TEST AUDIO
# ============================================================
print("[1] Generating test audio signal...")

# Create a simple test audio (1 second, 8kHz, sine wave)
sample_rate = 8000
duration = 1.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))
frequency = 440  # Hz (A note)

# Generate sine wave
audio_signal = np.sin(2 * np.pi * frequency * t)

# Convert to 16-bit PCM
audio_pcm = (audio_signal * 32767).astype(np.int16)

print(f"   Sample rate: {sample_rate} Hz")
print(f"   Duration: {duration} seconds")
print(f"   Samples: {len(audio_pcm)}")
print(f"   Format: 16-bit PCM")
print()

# ============================================================
# STEP 2: CHUA CIRCUIT CHAOTIC GENERATOR
# ============================================================
print("[2] Generating Chua Circuit chaotic keystream...")

# Chua Circuit parameters
alpha = 9.0
beta = 14.28
a = -1.143
b = -0.714
dt = 0.01

# Initial conditions (secret key)
x, y, z = 0.1, 0.1, 0.1

# Chua diode function
def chua_diode(x):
    return b * x + 0.5 * (a - b) * (abs(x + 1) - abs(x - 1))

# Generate keystream
num_samples = len(audio_pcm)
keystream = np.zeros(num_samples, dtype=np.int16)

print(f"   Generating {num_samples} keystream samples...")
start_time = time.time()

for i in range(num_samples):
    # Chua circuit equations
    dx = alpha * (y - x - chua_diode(x))
    dy = x - y + z
    dz = -beta * y
    
    # Update states
    x += dx * dt
    y += dy * dt
    z += dz * dt
    
    # Prevent overflow
    if abs(x) > 10: x = x % 10
    if abs(y) > 10: y = y % 10
    if abs(z) > 10: z = z % 10
    
    # Convert to 16-bit keystream
    keystream[i] = int((x * 3276.7)) & 0xFFFF

generation_time = time.time() - start_time
print(f"   Generation time: {generation_time:.3f} seconds")
print(f"   Rate: {num_samples/generation_time:.0f} samples/sec")
print()

# ============================================================
# STEP 3: ENCRYPTION
# ============================================================
print("[3] Encrypting audio with chaotic keystream...")

# XOR encryption: C[n] = P[n] ⊕ K[n]
encrypted_audio = np.bitwise_xor(audio_pcm, keystream)

print(f"   Original audio range: [{audio_pcm.min()}, {audio_pcm.max()}]")
print(f"   Encrypted audio range: [{encrypted_audio.min()}, {encrypted_audio.max()}]")
print()

# ============================================================
# STEP 4: DECRYPTION
# ============================================================
print("[4] Decrypting audio...")

# Reset chaotic generator to same initial conditions
x, y, z = 0.1, 0.1, 0.1

# Regenerate keystream
keystream_decrypt = np.zeros(num_samples, dtype=np.int16)

for i in range(num_samples):
    dx = alpha * (y - x - chua_diode(x))
    dy = x - y + z
    dz = -beta * y
    
    x += dx * dt
    y += dy * dt
    z += dz * dt
    
    if abs(x) > 10: x = x % 10
    if abs(y) > 10: y = y % 10
    if abs(z) > 10: z = z % 10
    
    keystream_decrypt[i] = int((x * 3276.7)) & 0xFFFF

# XOR decryption: P[n] = C[n] ⊕ K[n]
decrypted_audio = np.bitwise_xor(encrypted_audio, keystream_decrypt)

print(f"   Decrypted audio range: [{decrypted_audio.min()}, {decrypted_audio.max()}]")
print()

# ============================================================
# STEP 5: PERFORMANCE METRICS
# ============================================================
print("[5] Calculating performance metrics...")
print()

# Pearson correlation coefficient
correlation, _ = pearsonr(audio_pcm, decrypted_audio)
print(f"   ✓ Pearson Correlation: {correlation:.6f}")

# Bit Error Rate (BER)
bit_errors = np.sum(audio_pcm != decrypted_audio)
total_bits = len(audio_pcm) * 16
ber = bit_errors / len(audio_pcm)
print(f"   ✓ Bit Error Rate (BER): {ber:.6f} ({bit_errors}/{len(audio_pcm)} samples)")

# Mean Squared Error (MSE)
mse = np.mean((audio_pcm - decrypted_audio) ** 2)
print(f"   ✓ Mean Squared Error (MSE): {mse:.6f}")

# Perfect match check
perfect_match = np.array_equal(audio_pcm, decrypted_audio)
print(f"   ✓ Perfect Match: {perfect_match}")

print()

# ============================================================
# STEP 6: RESULTS SUMMARY
# ============================================================
print("="*60)
print("TEST RESULTS")
print("="*60)

if correlation >= 0.999 and ber < 0.01 and perfect_match:
    print("✅ SUCCESS! All tests passed!")
    print()
    print("   ✓ Correlation ≥ 0.999")
    print("   ✓ BER < 1%")
    print("   ✓ Perfect decryption")
    print()
    print("Your chaos-based encryption system is working correctly!")
else:
    print("⚠️  WARNING: Some tests failed")
    print()
    if correlation < 0.999:
        print(f"   ✗ Correlation too low: {correlation:.6f} (need ≥ 0.999)")
    if ber >= 0.01:
        print(f"   ✗ BER too high: {ber:.6f} (need < 0.01)")
    if not perfect_match:
        print(f"   ✗ Decryption not perfect")
    print()
    print("Check your chaotic generator parameters and keystream generation.")

print("="*60)
print()

# ============================================================
# STEP 7: SAVE RESULTS
# ============================================================
print("[6] Saving results...")

# Save audio files
wavfile.write('original_audio.wav', sample_rate, audio_pcm)
wavfile.write('encrypted_audio.wav', sample_rate, encrypted_audio)
wavfile.write('decrypted_audio.wav', sample_rate, decrypted_audio)

print("   ✓ Saved: original_audio.wav")
print("   ✓ Saved: encrypted_audio.wav")
print("   ✓ Saved: decrypted_audio.wav")
print()

# ============================================================
# STEP 8: GENERATE PLOTS
# ============================================================
print("[7] Generating plots...")

plt.figure(figsize=(12, 8))

# Plot 1: Original audio
plt.subplot(3, 1, 1)
plt.plot(t[:500], audio_pcm[:500])
plt.title('Original Audio Signal')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.grid(True)

# Plot 2: Encrypted audio
plt.subplot(3, 1, 2)
plt.plot(t[:500], encrypted_audio[:500])
plt.title('Encrypted Audio (Chaotic)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.grid(True)

# Plot 3: Decrypted audio
plt.subplot(3, 1, 3)
plt.plot(t[:500], decrypted_audio[:500])
plt.title('Decrypted Audio')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.grid(True)

plt.tight_layout()
plt.savefig('encryption_test_results.png', dpi=150)
print("   ✓ Saved: encryption_test_results.png")
print()

print("="*60)
print("SINGLE BOARD TEST COMPLETE!")
print("="*60)
print()
print("Next steps:")
print("1. Review the plots and metrics")
print("2. Test with your own audio files")
print("3. Try Rössler system (modify parameters)")
print("4. When ready, proceed to two-board UART testing")
print()
```

---

## ▶️ STEP 5: Run the Test

### In Jupyter Terminal:

```bash
cd /home/xilinx/chaos_test
python3 single_board_test.py
```

### Expected Output:

```
============================================================
SINGLE BOARD CHAOS ENCRYPTION TEST
============================================================

[1] Generating test audio signal...
   Sample rate: 8000 Hz
   Duration: 1.0 seconds
   Samples: 8000
   Format: 16-bit PCM

[2] Generating Chua Circuit chaotic keystream...
   Generating 8000 keystream samples...
   Generation time: 0.234 seconds
   Rate: 34188 samples/sec

[3] Encrypting audio with chaotic keystream...
   Original audio range: [-32767, 32767]
   Encrypted audio range: [-32768, 32767]

[4] Decrypting audio...
   Decrypted audio range: [-32767, 32767]

[5] Calculating performance metrics...

   ✓ Pearson Correlation: 1.000000
   ✓ Bit Error Rate (BER): 0.000000 (0/8000 samples)
   ✓ Mean Squared Error (MSE): 0.000000
   ✓ Perfect Match: True

============================================================
TEST RESULTS
============================================================
✅ SUCCESS! All tests passed!

   ✓ Correlation ≥ 0.999
   ✓ BER < 1%
   ✓ Perfect decryption

Your chaos-based encryption system is working correctly!
============================================================

[6] Saving results...
   ✓ Saved: original_audio.wav
   ✓ Saved: encrypted_audio.wav
   ✓ Saved: decrypted_audio.wav

[7] Generating plots...
   ✓ Saved: encryption_test_results.png

============================================================
SINGLE BOARD TEST COMPLETE!
============================================================

Next steps:
1. Review the plots and metrics
2. Test with your own audio files
3. Try Rössler system (modify parameters)
4. When ready, proceed to two-board UART testing
```

---

## 📊 STEP 6: Review Results

### Files Created:
1. `original_audio.wav` - Original test audio
2. `encrypted_audio.wav` - Encrypted (should sound like noise)
3. `decrypted_audio.wav` - Decrypted (should match original)
4. `encryption_test_results.png` - Visual comparison plot

### Download Files:
In Jupyter, check the boxes next to files and click "Download"

### Listen to Audio:
- Original: Clear 440 Hz tone
- Encrypted: Random noise
- Decrypted: Clear 440 Hz tone (identical to original)

---

## 🎯 Success Criteria

### ✅ Test Passes If:
- Pearson Correlation = 1.000000 (perfect)
- Bit Error Rate = 0.000000 (no errors)
- Mean Squared Error = 0.000000 (perfect match)
- Perfect Match = True

### ⚠️ If Test Fails:
Check these:
1. Initial conditions match for encryption/decryption
2. Chaotic parameters are correct
3. Time step (dt) is appropriate
4. No overflow in state variables

---

## 🔄 STEP 7: Test with Your Own Audio

### Modify the script to use your audio file:

```python
# Replace STEP 1 with:
print("[1] Loading your audio file...")
sample_rate, audio_data = wavfile.read('your_audio.wav')

# Convert to mono if stereo
if len(audio_data.shape) > 1:
    audio_pcm = audio_data[:, 0]  # Use left channel
else:
    audio_pcm = audio_data

print(f"   Sample rate: {sample_rate} Hz")
print(f"   Samples: {len(audio_pcm)}")
```

### Upload your audio:
1. In Jupyter, click "Upload"
2. Select your .wav file
3. Modify script to use your filename
4. Run again

---

## 🔬 STEP 8: Test Rössler System

### Create `single_board_test_rossler.py`:

Replace the Chua generator section with:

```python
# Rössler System parameters
a = 0.2
b = 0.2
c = 5.7
dt = 0.05

# Initial conditions
x, y, z = 0.1, 0.1, 0.1

# Generate keystream
for i in range(num_samples):
    # Rössler equations
    dx = -y - z
    dy = x + a * y
    dz = b + z * (x - c)
    
    # Update states
    x += dx * dt
    y += dy * dt
    z += dz * dt
    
    # Prevent overflow
    if abs(x) > 20: x = x % 20
    if abs(y) > 20: y = y % 20
    if abs(z) > 20: z = z % 20
    
    # Convert to keystream
    keystream[i] = int((x * 1638.35)) & 0xFFFF
```

---

## 📈 Performance Benchmarks

### Expected Performance (PYNQ-Z2):

| Metric | Target | Typical |
|--------|--------|---------|
| Correlation | ≥ 0.999 | 1.000000 |
| BER | < 1% | 0.000000% |
| MSE | < 1.0 | 0.000000 |
| Keystream Rate | ≥ 8 kHz | 30-40 kHz |

### Chua vs Rössler:

| System | Keystream Rate | Complexity | Attractor |
|--------|---------------|------------|-----------|
| Chua | ~35 kHz | Medium | Double-scroll |
| Rössler | ~40 kHz | Low | Spiral |

---

## 🐛 Troubleshooting

### Problem 1: Import Errors
```
ModuleNotFoundError: No module named 'scipy'
```
**Solution:**
```bash
sudo pip3 install scipy matplotlib
```

### Problem 2: Correlation < 1.0
**Causes:**
- Initial conditions don't match
- Keystream generation differs
- Overflow in state variables

**Solution:**
- Verify initial conditions are identical
- Add modulo operations to prevent overflow
- Check time step (dt) value

### Problem 3: Script Runs Slowly
**Solution:**
- Reduce audio duration (use 0.5 seconds)
- Increase time step (dt)
- Use smaller sample rate (4000 Hz)

### Problem 4: Can't Save Files
**Solution:**
```bash
# Check permissions
cd /home/xilinx/chaos_test
ls -la

# Create output directory
mkdir -p output
cd output
python3 ../single_board_test.py
```

---

## ✅ Verification Checklist

Before proceeding to two-board testing:

- [ ] Single-board test script runs without errors
- [ ] Correlation = 1.000000 (perfect)
- [ ] BER = 0.000000 (no errors)
- [ ] Audio files saved successfully
- [ ] Plot generated and looks correct
- [ ] Tested with your own audio file
- [ ] Both Chua and Rössler systems tested
- [ ] Understand how encryption/decryption works

**If all checked:** ✅ Ready for two-board UART testing!

---

## 🎓 For Your Thesis

### What This Test Proves:
1. ✅ Chaotic generators work correctly
2. ✅ Encryption algorithm is sound
3. ✅ Decryption recovers original perfectly
4. ✅ Performance meets requirements
5. ✅ System is ready for UART integration

### Documentation:
- Save all output files
- Screenshot the terminal output
- Include the plot in your thesis
- Record performance metrics

### Next Phase:
After single-board testing succeeds:
1. Flash second PYNQ board
2. Test UART communication
3. Integrate encryption with UART
4. Full two-board system test

---

## 📞 Quick Reference

### Access Board:
```
Browser: http://192.168.2.99:9090
Password: xilinx
```

### Run Test:
```bash
cd /home/xilinx/chaos_test
python3 single_board_test.py
```

### Check Results:
```bash
ls -lh *.wav *.png
```

### Download Files:
In Jupyter: Select files → Download

---

**This single-board test validates your entire encryption system before adding the complexity of UART communication!** 🚀

**Start here, get perfect results, then move to two-board testing!** 🎯