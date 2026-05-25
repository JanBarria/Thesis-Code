# 🐍 How to Run in Python - Visual Guide

## Method 1: Using Command Prompt/Terminal (Easiest)

### Step 1: Open Command Prompt

**On Windows:**
1. Click Start menu (Windows icon)
2. Type `cmd`
3. Press Enter

You'll see a black window like this:
```
C:\Users\YourName>
```

### Step 2: Go to Your Project Folder

Type this command (replace with your actual path):
```
cd C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication
```

Press Enter. You should see:
```
C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication>
```

### Step 3: Install Required Libraries

Type this command:
```
pip install numpy scipy matplotlib
```

Press Enter. You'll see installation progress. Wait until it finishes.

### Step 4: Create Test Audio

Copy this ENTIRE command and paste it (right-click in Command Prompt to paste):
```
python -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"
```

Press Enter. You should see:
```
Test audio created!
```

### Step 5: Run the Encryption

Type these commands one by one:
```
cd chua_system
```
Press Enter, then:
```
python chua_encryptor.py ../test_audio/test_tone.wav
```

Press Enter. You'll see output like:
```
================================================================================
CHUA CIRCUIT AUDIO ENCRYPTION
================================================================================
Loaded audio: 44100 samples at 44100 Hz
Duration: 1.00 seconds
Generating 44100 keystream samples...
...
ENCRYPTION COMPLETE
```

### Step 6: Run the Decryption

Type this command:
```
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

Press Enter. You should see:
```
Pearson Correlation: 1.000000
Bit Error Rate (BER): 0.000000e+00 (0.0000%)
✓ Correlation: EXCELLENT (≥0.95)
✓ BER: EXCELLENT (<1%)
```

**SUCCESS!** ✅ Your system is working!

---

## Method 2: Using Python IDLE (Built-in Python Editor)

### Step 1: Open Python IDLE

**On Windows:**
1. Click Start menu
2. Type `IDLE`
3. Click on "IDLE (Python 3.x)"

You'll see a window with `>>>` prompt.

### Step 2: Install Libraries First

Close IDLE and use Command Prompt (Method 1, Step 3) to install libraries first.

### Step 3: Run the Code

In IDLE, click `File` → `Open` → Navigate to:
```
C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication\chua_system\chua_encryptor.py
```

Then press `F5` or click `Run` → `Run Module`

**Note:** You'll need to modify the file path in the code or use Command Prompt method instead (easier).

---

## Method 3: Using VS Code (If You Have It)

### Step 1: Open VS Code

1. Open Visual Studio Code
2. Click `File` → `Open Folder`
3. Select: `C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication`

### Step 2: Open Terminal in VS Code

1. Click `Terminal` → `New Terminal` (or press Ctrl + `)
2. You'll see a terminal at the bottom

### Step 3: Install Libraries

In the terminal, type:
```
pip install numpy scipy matplotlib
```

### Step 4: Create Test Audio

In the terminal, paste:
```
python -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"
```

### Step 5: Run Encryption

In the terminal:
```
cd chua_system
python chua_encryptor.py ../test_audio/test_tone.wav
```

### Step 6: Run Decryption

In the terminal:
```
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

---

## Method 4: Using Jupyter Notebook (Interactive)

### Step 1: Install Jupyter

In Command Prompt:
```
pip install jupyter
```

### Step 2: Start Jupyter

In Command Prompt:
```
cd C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication
jupyter notebook
```

Your browser will open with Jupyter.

### Step 3: Create New Notebook

1. Click `New` → `Python 3`
2. A new notebook opens

### Step 4: Run Code in Cells

**Cell 1 - Create Test Audio:**
```python
import numpy as np
from scipy.io import wavfile
import os

# Create test audio
os.makedirs('test_audio', exist_ok=True)
sr = 44100
t = np.linspace(0, 1, sr)
audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16)
wavfile.write('test_audio/test_tone.wav', sr, audio)
print('Test audio created!')
```
Press `Shift + Enter` to run.

**Cell 2 - Import and Run Encryption:**
```python
import sys
sys.path.append('chua_system')
from chua_encryptor import ChuaEncryptor

# Create encryptor
encryptor = ChuaEncryptor(x0=0.1, y0=0.0, z0=0.0)

# Encrypt
results = encryptor.encrypt_audio(
    'test_audio/test_tone.wav',
    'chua_system/encrypted_audio.wav',
    visualize=True
)
```
Press `Shift + Enter` to run.

**Cell 3 - Run Decryption:**
```python
from chua_decryptor import ChuaDecryptor

# Create decryptor
decryptor = ChuaDecryptor()

# Decrypt
results = decryptor.decrypt_audio(
    'chua_system/encrypted_audio.wav',
    'chua_system/decrypted_audio.wav',
    original_path='test_audio/test_tone.wav',
    visualize=True
)

# Print results
print(f"Correlation: {results['correlation']:.6f}")
print(f"BER: {results['ber']:.6e}")
```
Press `Shift + Enter` to run.

---

## 🎯 RECOMMENDED METHOD

**For Beginners:** Use **Method 1** (Command Prompt/Terminal)
- ✅ Simplest
- ✅ No extra software needed
- ✅ Works on any computer
- ✅ Copy-paste commands

**For Developers:** Use **Method 3** (VS Code)
- ✅ Better code editing
- ✅ Integrated terminal
- ✅ Easier debugging

**For Interactive Testing:** Use **Method 4** (Jupyter)
- ✅ Run code step-by-step
- ✅ See results immediately
- ✅ Good for experimentation

---

## 📝 Complete Command List (Copy-Paste Ready)

### For Windows Command Prompt:

```batch
REM Step 1: Navigate to project
cd C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication

REM Step 2: Install libraries (one time only)
pip install numpy scipy matplotlib

REM Step 3: Create test audio
python -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"

REM Step 4: Test Chua system
cd chua_system
python chua_encryptor.py ../test_audio/test_tone.wav
python chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

REM Step 5: Test Rössler system
cd ..\rossler_system
python rossler_encryptor.py ../test_audio/test_tone.wav
python rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

### For Mac/Linux Terminal:

```bash
# Step 1: Navigate to project
cd ~/Desktop/chaos_secure_communication

# Step 2: Install libraries (one time only)
pip3 install numpy scipy matplotlib

# Step 3: Create test audio
python3 -c "import numpy as np; from scipy.io import wavfile; import os; os.makedirs('test_audio', exist_ok=True); sr = 44100; t = np.linspace(0, 1, sr); audio = (np.sin(2*np.pi*440*t) * 32767 * 0.5).astype(np.int16); wavfile.write('test_audio/test_tone.wav', sr, audio); print('Test audio created!')"

# Step 4: Test Chua system
cd chua_system
python3 chua_encryptor.py ../test_audio/test_tone.wav
python3 chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav

# Step 5: Test Rössler system
cd ../rossler_system
python3 rossler_encryptor.py ../test_audio/test_tone.wav
python3 rossler_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

---

## ✅ What Success Looks Like

After running the commands, you should see:

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

**And these files will be created:**
- ✅ `encrypted_audio.wav`
- ✅ `decrypted_audio.wav`
- ✅ `encrypted_audio_secret_key.txt`
- ✅ `encrypted_audio_waveforms.png`
- ✅ `encrypted_audio_spectrograms.png`
- ✅ `decrypted_audio_comparison.png`

---

## 🐛 Troubleshooting

### "python is not recognized"
**Try:** `python3` instead of `python`

### "pip is not recognized"
**Try:** `python -m pip install numpy scipy matplotlib`

### "No module named 'numpy'"
**Solution:** Run `pip install numpy scipy matplotlib` first

### "No such file or directory"
**Solution:** Make sure you're in the right folder. Use `cd` command to navigate.

### Still stuck?
**Check:** 
1. Is Python installed? Type `python --version`
2. Are you in the right folder? Type `cd` (Windows) or `pwd` (Mac/Linux)
3. Did you install libraries? Type `pip list` to see installed packages

---

## 🎉 You're Done!

Once you see the success message with:
- ✅ Correlation: 1.000000
- ✅ BER: 0.000000%

Your chaos-based encryption system is working perfectly! 🚀

**Next steps:**
1. Try with your own audio files
2. Compare Chua vs Rössler systems
3. Generate plots for your thesis
4. Deploy to PYNQ-Z2 when ready