# 🚀 HOW TO RUN - Simple Step-by-Step Guide

## For Complete Beginners - Start Here!

---

## ⚡ FASTEST WAY TO TEST (5 Minutes)

### Step 1: Open Command Prompt / Terminal

**Windows:**
- Press `Windows Key + R`
- Type `cmd` and press Enter

**Mac:**
- Press `Command + Space`
- Type `terminal` and press Enter

**Linux:**
- Press `Ctrl + Alt + T`

### Step 2: Navigate to Project Folder

```bash
# Replace this path with where you saved the project
cd C:/Users/JanChristopherRobinB/Desktop/chaos_secure_communication

# On Mac/Linux, it might be:
# cd ~/Desktop/chaos_secure_communication
```

### Step 3: Install Required Libraries (One Time Only)

```bash
pip install numpy scipy matplotlib
```

**If that doesn't work, try:**
```bash
python -m pip install numpy scipy matplotlib
```

**Or on Mac/Linux:**
```bash
pip3 install numpy scipy matplotlib
```

### Step 4: Create Test Audio File

Copy and paste this entire command:

**Windows Command Prompt:**
```bash
python -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"
```

**Mac/Linux Terminal:**
```bash
python3 -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"
```

You should see: `Test audio created!`

### Step 5: Test Chua Circuit Encryption

```bash
cd chua_system
python chua_encryptor.py ../test_audio/test_tone.wav
```

**On Mac/Linux, use `python3` instead:**
```bash
python3 chua_encryptor.py ../test_audio/test_tone.wav
```

**What you'll see:**
```
================================================================================
CHUA CIRCUIT AUDIO ENCRYPTION
================================================================================
Loaded audio: 44100 samples at 44100 Hz
Duration: 1.00 seconds
Generating 44100 keystream samples...
Keystream generated successfully
Encrypting audio...
Encrypted audio saved to: encrypted_audio.wav
Secret key saved to: encrypted_audio_secret_key.txt
Drive signal (x state) saved to: encrypted_audio_drive_signal.npy
...
ENCRYPTION COMPLETE
```

### Step 6: Test Chua Circuit Decryption

```bash
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

**What you'll see:**
```
================================================================================
CHUA CIRCUIT AUDIO DECRYPTION
================================================================================
Secret key loaded: x0=0.1, y0=0.0, z0=0.0
...
Pearson Correlation: 1.000000
Bit Error Rate (BER): 0.000000e+00 (0.0000%)
Mean Squared Error (MSE): 0.00

Performance Assessment:
  ✓ Correlation: EXCELLENT (≥0.95)
  ✓ BER: EXCELLENT (<1%)
================================================================================
```

### Step 7: Check the Results

Look in the `chua_system` folder. You should see these new files:
- ✅ `encrypted_audio.wav` - The encrypted audio (sounds like noise)
- ✅ `decrypted_audio.wav` - The decrypted audio (sounds like original)
- ✅ `encrypted_audio_secret_key.txt` - The secret key
- ✅ `encrypted_audio_waveforms.png` - Visualization
- ✅ `encrypted_audio_spectrograms.png` - Frequency analysis
- ✅ `decrypted_audio_comparison.png` - Comparison plot

**Play the audio files to verify:**
- Original: `../test_audio/test_tone.wav` (440 Hz tone)
- Encrypted: `encrypted_audio.wav` (white noise)
- Decrypted: `decrypted_audio.wav` (440 Hz tone - same as original!)

---

## 🎯 Test Rössler System (Optional)

```bash
# Go back and enter rossler_system folder
cd ../rossler_system

# Encrypt
python rossler_encryptor.py ../test_audio/test_tone.wav

# Decrypt
python rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

---

## 🐛 Common Problems and Solutions

### Problem 1: "python is not recognized"

**Solution:** Try `python3` instead of `python`
```bash
python3 chua_encryptor.py ../test_audio/test_tone.wav
```

### Problem 2: "No module named 'numpy'"

**Solution:** Install the libraries
```bash
pip install numpy scipy matplotlib
# or
python -m pip install numpy scipy matplotlib
# or
pip3 install numpy scipy matplotlib
```

### Problem 3: "No such file or directory"

**Solution:** Make sure you're in the right folder
```bash
# Check where you are
pwd  # Mac/Linux
cd   # Windows

# Navigate to project
cd chaos_secure_communication
cd chua_system
```

### Problem 4: Plots don't show up

**Solution:** The PNG files are saved in the folder. Just open them manually:
- Windows: Double-click the .png files
- Mac: Double-click or use Preview
- Linux: Use your image viewer

### Problem 5: "Permission denied"

**Solution (Windows):** Run Command Prompt as Administrator
- Right-click Command Prompt
- Select "Run as administrator"

---

## 📝 What Each File Does

### Input Files:
- `test_audio/test_tone.wav` - Your original audio (1 second, 440 Hz tone)

### Generated Files:
- `encrypted_audio.wav` - Encrypted version (sounds like noise)
- `encrypted_audio_secret_key.txt` - Secret key (initial conditions)
- `encrypted_audio_drive_signal.npy` - Synchronization signal
- `decrypted_audio.wav` - Recovered audio (should match original)
- `*.png` - Visualization plots

---

## 🎓 Understanding the Output

### Good Results (Success):
```
Pearson Correlation: 1.000000 or 0.999999
Bit Error Rate (BER): 0.000000e+00 (0.0000%)
Mean Squared Error (MSE): 0.00 or very small

✓ Correlation: EXCELLENT (≥0.95)
✓ BER: EXCELLENT (<1%)
```

This means:
- ✅ Decryption worked perfectly
- ✅ Recovered audio is identical to original
- ✅ System is working correctly

### Bad Results (Problem):
```
Pearson Correlation: 0.500000 (less than 0.95)
Bit Error Rate (BER): 5.0% (more than 1%)

✗ Correlation: POOR (<0.95)
✗ BER: POOR (≥1%)
```

This means something went wrong. Check:
- Did you use the correct files?
- Are all files from the same encryption run?
- Did the encryption complete successfully?

---

## 🔄 Run Again with Different Audio

### Use Your Own Audio File

1. **Prepare your audio:**
   - Must be mono (single channel)
   - Must be 16-bit PCM WAV format
   - Any sample rate is OK

2. **Convert if needed:**
```bash
python -c "
from scipy.io import wavfile
import numpy as np

# Load your audio
sr, audio = wavfile.read('your_audio.wav')

# Convert to mono
if audio.ndim == 2:
    mono = np.mean(audio, axis=1).astype(np.int16)
else:
    mono = audio

# Save
wavfile.write('test_audio/my_audio.wav', sr, mono)
print('Audio converted!')
"
```

3. **Encrypt it:**
```bash
cd chua_system
python chua_encryptor.py ../test_audio/my_audio.wav
python chua_decryptor.py encrypted_audio.wav ../test_audio/my_audio.wav
```

---

## 📊 Quick Command Reference

```bash
# Navigate to project
cd chaos_secure_communication

# Test Chua system
cd chua_system
python chua_encryptor.py ../test_audio/test_tone.wav
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# Test Rössler system
cd ../rossler_system
python rossler_encryptor.py ../test_audio/test_tone.wav
python rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# Test individual modules
python chua_chaotic_generator.py
python chua_keystream_extractor.py
python rossler_chaotic_generator.py
python rossler_keystream_extractor.py
```

---

## ✅ Success Checklist

After running, you should have:

- [ ] Test audio file created (`test_audio/test_tone.wav`)
- [ ] Encryption completed without errors
- [ ] `encrypted_audio.wav` file created
- [ ] `encrypted_audio_secret_key.txt` file created
- [ ] Decryption completed without errors
- [ ] `decrypted_audio.wav` file created
- [ ] Correlation ≥ 0.95 (ideally > 0.999)
- [ ] BER < 1% (ideally 0%)
- [ ] PNG visualization files created
- [ ] Can play and hear the audio files

If all checked, **congratulations!** Your system is working perfectly! 🎉

---

## 🆘 Still Having Problems?

1. **Check Python version:**
   ```bash
   python --version
   # Should be 3.6 or higher
   ```

2. **Check if libraries are installed:**
   ```bash
   python -c "import numpy, scipy, matplotlib; print('All OK!')"
   ```

3. **Check current directory:**
   ```bash
   # Windows
   cd
   dir
   
   # Mac/Linux
   pwd
   ls
   ```

4. **Try the full path:**
   ```bash
   python C:/Users/YourName/Desktop/chaos_secure_communication/chua_system/chua_encryptor.py C:/Users/YourName/Desktop/chaos_secure_communication/test_audio/test_tone.wav
   ```

---

## 🎯 Next Steps

Once this works on your PC:
1. ✅ Test with different audio files
2. ✅ Generate plots for your thesis
3. ✅ Compare Chua vs Rössler performance
4. ✅ Document your results
5. ✅ Deploy to PYNQ-Z2 board (see README.md)

**You're ready to go!** 🚀