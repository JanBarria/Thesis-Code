# Testing on Your PC Before FPGA Deployment

## ✅ YES! You Can Test Everything on Your Computer First

All the Python code is designed to run on **any standard Python environment** (Windows, Linux, Mac) before deploying to the PYNQ-Z2 board. This allows you to:

- ✅ Test and debug the algorithms
- ✅ Verify encryption/decryption works
- ✅ Generate test results for your thesis
- ✅ Develop without needing the FPGA board
- ✅ Work offline

---

## 🖥️ Setup on Your PC

### Step 1: Install Python

**Windows:**
1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify: Open Command Prompt and type `python --version`

**Mac/Linux:**
```bash
# Usually pre-installed, verify with:
python3 --version

# If not installed:
# Mac: brew install python3
# Ubuntu/Debian: sudo apt-get install python3
```

### Step 2: Install Required Libraries

Open terminal/command prompt in the project directory:

```bash
# Navigate to project folder
cd chaos_secure_communication

# Install dependencies
pip install numpy scipy matplotlib

# Or use pip3 on Mac/Linux
pip3 install numpy scipy matplotlib
```

**Verify installation:**
```bash
python -c "import numpy, scipy, matplotlib; print('All libraries installed!')"
```

---

## 🧪 Quick Test on Your PC

### Test 1: Generate Test Audio File

Create a simple test audio file:

```bash
cd chaos_secure_communication
python -c "
import numpy as np
from scipy.io import wavfile
import os

# Create test_audio directory if it doesn't exist
os.makedirs('test_audio', exist_ok=True)

# Generate 1-second test tone (440 Hz A4 note)
sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)

# Save
wavfile.write('test_audio/test_tone.wav', sample_rate, audio)
print('✓ Test audio created: test_audio/test_tone.wav')
print(f'  Duration: {duration} seconds')
print(f'  Sample rate: {sample_rate} Hz')
print(f'  Samples: {len(audio)}')
"
```

### Test 2: Test Chua Circuit System

```bash
# Test the generator
cd chua_system
python chua_chaotic_generator.py

# Expected output: Statistics and demonstration
```

```bash
# Test the keystream extractor
python chua_keystream_extractor.py

# Expected output: Keystream statistics and entropy
```

```bash
# Test encryption
python chua_encryptor.py ../test_audio/test_tone.wav

# Expected output:
# - encrypted_audio.wav
# - encrypted_audio_secret_key.txt
# - encrypted_audio_drive_signal.npy
# - encrypted_audio_waveforms.png
# - encrypted_audio_spectrograms.png
```

```bash
# Test decryption
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# Expected output:
# - decrypted_audio.wav
# - decrypted_audio_comparison.png
# - Performance metrics (Correlation, BER, MSE)
```

### Test 3: Test Rössler System

```bash
# Same process for Rössler
cd ../rossler_system
python rossler_chaotic_generator.py
python rossler_keystream_extractor.py
python rossler_encryptor.py ../test_audio/test_tone.wav
python rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

---

## 📊 Expected Results on PC

### Successful Test Output:

```
================================================================================
CHUA CIRCUIT AUDIO DECRYPTION
================================================================================
Secret key loaded: x0=0.1, y0=0.0, z0=0.0
Drive signal loaded: 44100 samples
Encrypted audio loaded: 44100 samples at 44100 Hz
Synchronizing and generating keystream...
Keystream regenerated successfully
Decrypting audio...
Decrypted audio saved to: decrypted_audio.wav

Computing performance metrics...

================================================================================
DECRYPTION COMPLETE
================================================================================
Pearson Correlation: 1.000000
Bit Error Rate (BER): 0.000000e+00 (0.0000%)
Mean Squared Error (MSE): 0.00

Performance Assessment:
  ✓ Correlation: EXCELLENT (≥0.95)
  ✓ BER: EXCELLENT (<1%)
================================================================================
```

---

## 🎵 Listen to Results on PC

After running the tests, you can play the audio files:

**Windows:**
- Double-click the .wav files
- Or use Windows Media Player

**Mac:**
- Double-click to open in QuickTime
- Or use: `afplay test_audio/test_tone.wav`

**Linux:**
- Use: `aplay test_audio/test_tone.wav`
- Or: `vlc test_audio/test_tone.wav`

**Compare:**
1. Original: `test_audio/test_tone.wav`
2. Encrypted: `chua_system/encrypted_audio.wav` (should sound like noise)
3. Decrypted: `chua_system/decrypted_audio.wav` (should sound identical to original)

---

## 🖼️ View Visualizations on PC

The code generates PNG images that you can view:

**Generated Files:**
- `encrypted_audio_waveforms.png` - Original vs Encrypted waveforms
- `encrypted_audio_spectrograms.png` - Frequency analysis
- `decrypted_audio_comparison.png` - Original vs Decrypted comparison

**View on:**
- Windows: Double-click or use Photos app
- Mac: Double-click or use Preview
- Linux: Use image viewer or `eog filename.png`

---

## 🔬 Advanced Testing on PC

### Test with Your Own Audio

```bash
# Convert any audio to mono 16-bit PCM
python -c "
from scipy.io import wavfile
import numpy as np

# Load your audio
sr, audio = wavfile.read('your_audio.wav')

# Convert to mono if stereo
if audio.ndim == 2:
    mono = np.mean(audio, axis=1).astype(np.int16)
else:
    mono = audio

# Ensure 16-bit
if mono.dtype != np.int16:
    mono = (mono / np.max(np.abs(mono)) * 32767).astype(np.int16)

# Save
wavfile.write('test_audio/my_audio.wav', sr, mono)
print('✓ Audio converted and saved')
"

# Then encrypt it
cd chua_system
python chua_encryptor.py ../test_audio/my_audio.wav
python chua_decryptor.py encrypted_audio.wav ../test_audio/my_audio.wav
```

### Batch Testing

Create a test script `run_all_tests.py`:

```python
import os
import subprocess

print("=" * 80)
print("RUNNING ALL TESTS")
print("=" * 80)

tests = [
    ("Chua Generator", "chua_system/chua_chaotic_generator.py"),
    ("Chua Keystream", "chua_system/chua_keystream_extractor.py"),
    ("Rössler Generator", "rossler_system/rossler_chaotic_generator.py"),
    ("Rössler Keystream", "rossler_system/rossler_keystream_extractor.py"),
]

for name, script in tests:
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print('='*80)
    result = subprocess.run(["python", script], capture_output=False)
    if result.returncode == 0:
        print(f"✓ {name} PASSED")
    else:
        print(f"✗ {name} FAILED")

print("\n" + "=" * 80)
print("ALL TESTS COMPLETE")
print("=" * 80)
```

Run with: `python run_all_tests.py`

---

## 🐛 Troubleshooting on PC

### Issue: "ModuleNotFoundError: No module named 'numpy'"

**Solution:**
```bash
pip install numpy scipy matplotlib
# or
pip3 install numpy scipy matplotlib
```

### Issue: "No module named 'matplotlib.pyplot'"

**Solution:**
```bash
pip install matplotlib
```

If still fails, try:
```bash
pip install --upgrade matplotlib
```

### Issue: Plots don't show up

**Solution:** Add this at the end of your script:
```python
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg'
import matplotlib.pyplot as plt
```

### Issue: "Permission denied" on Windows

**Solution:** Run Command Prompt as Administrator

### Issue: Python not found

**Solution:** 
- Windows: Reinstall Python and check "Add to PATH"
- Mac/Linux: Use `python3` instead of `python`

---

## 📈 Performance Comparison: PC vs PYNQ-Z2

| Aspect | Your PC | PYNQ-Z2 |
|--------|---------|---------|
| **Processing Speed** | Faster (modern CPU) | Slower (ARM processor) |
| **Development** | Easier (full IDE) | Limited (SSH/Jupyter) |
| **Debugging** | Full tools available | Basic tools |
| **Visualization** | Native display | Remote viewing |
| **Purpose** | Development & Testing | Final deployment |

**Recommendation:**
1. ✅ Develop and test on PC first
2. ✅ Verify all algorithms work correctly
3. ✅ Generate thesis results and plots
4. ✅ Then deploy to PYNQ-Z2 for hardware demo

---

## 🎓 Workflow for Your Thesis

### Phase 1: PC Development (Weeks 1-4)
- ✅ Test all modules on PC
- ✅ Generate performance metrics
- ✅ Create visualizations for thesis
- ✅ Debug and optimize algorithms
- ✅ Test with various audio files

### Phase 2: PYNQ Deployment (Weeks 5-6)
- ✅ Transfer code to PYNQ-Z2
- ✅ Verify same results on hardware
- ✅ Test UART communication
- ✅ Demonstrate real-time processing

### Phase 3: Documentation (Weeks 7-8)
- ✅ Write thesis with PC-generated results
- ✅ Include PYNQ hardware validation
- ✅ Compare PC vs FPGA performance

---

## ✅ Verification Checklist

Before moving to PYNQ-Z2, verify on PC:

- [ ] All modules run without errors
- [ ] Test audio encrypts successfully
- [ ] Encrypted audio sounds like noise
- [ ] Decryption recovers original audio
- [ ] Correlation ≥ 0.95
- [ ] BER < 1%
- [ ] Visualizations generate correctly
- [ ] Both Chua and Rössler systems work
- [ ] Can process your own audio files

Once all checked, you're ready for PYNQ deployment! ✨

---

## 🚀 Quick Command Reference

```bash
# Create test audio
python -c "import numpy as np; from scipy.io import wavfile; ..."

# Test Chua system
cd chua_system
python chua_encryptor.py ../test_audio/test_tone.wav
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# Test Rössler system
cd ../rossler_system
python rossler_encryptor.py ../test_audio/test_tone.wav
python rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# View results
# (Open .png files and play .wav files)
```

---

**Bottom Line:** Yes, you can and **should** test everything on your PC first! It's faster, easier to debug, and you can generate all your thesis results before ever touching the FPGA board. 🎉