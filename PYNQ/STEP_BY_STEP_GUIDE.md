# 🎯 STEP-BY-STEP GUIDE: From Laptop to PYNQ Boards

## Your Current Situation
- 💻 **Laptop:** Has all the code (where you are now)
- 🖥️ **Desktop/Lab PC:** Has PYNQ boards connected
- 🎯 **Goal:** Deploy code to PYNQ boards and test

---

## 📦 STEP 1: Transfer Code from Laptop to Desktop PC

### Option A: Using USB Drive (Easiest)

**On Your Laptop:**
1. Insert USB drive
2. Open File Explorer
3. Navigate to: `C:\Users\JanChristopherRobinB\Desktop\chaos_secure_communication`
4. **Right-click** on the `PYNQ` folder
5. Click **"Copy"**
6. Open your USB drive
7. **Right-click** and select **"Paste"**
8. Wait for copy to complete (~150 KB, takes 5 seconds)
9. Safely eject USB drive

**On Desktop PC (where PYNQ boards are):**
1. Insert USB drive
2. Open File Explorer
3. Open USB drive
4. Find the `PYNQ` folder
5. **Right-click** on `PYNQ` folder
6. Click **"Copy"**
7. Navigate to Desktop or Documents
8. **Right-click** and select **"Paste"**
9. Note the location (e.g., `C:\Users\YourName\Desktop\PYNQ`)

### Option B: Using Network Share

**On Your Laptop:**
1. Right-click `PYNQ` folder
2. Select "Share" → "Specific people"
3. Add "Everyone" and click "Share"
4. Note the network path (e.g., `\\LAPTOP\Users\...\PYNQ`)

**On Desktop PC:**
1. Open File Explorer
2. Type the network path in address bar
3. Copy the `PYNQ` folder to Desktop

### Option C: Using Email/Cloud

**On Your Laptop:**
1. Compress `PYNQ` folder (Right-click → "Compress to ZIP")
2. Upload to Google Drive, OneDrive, or email to yourself
3. Download on Desktop PC
4. Extract the ZIP file

---

## 🔍 STEP 2: Find PYNQ Board IP Address

**On Desktop PC (where PYNQ boards are connected):**

1. Open the `PYNQ` folder you just copied
2. **Double-click** `find_pynq_board.bat`
3. A black window will appear and scan for boards
4. Wait for it to finish (30-60 seconds)
5. **Write down the IP address** it finds (e.g., 192.168.2.99)

**Expected Output:**
```
[SUCCESS] Board found at 192.168.2.99 (USB connection)

Try connecting with:
  ssh xilinx@192.168.2.99
  Password: xilinx
```

**If no board found:**
- Check green LED on PYNQ board (should be solid, not blinking)
- Wait 60 seconds after power-on
- Try unplugging and replugging USB cable
- Run `find_pynq_board.bat` again

---

## 🌐 STEP 3: Connect to PYNQ Board

**On Desktop PC:**

### Method A: Using Web Browser (Easiest)

1. Open your web browser (Chrome, Firefox, Edge)
2. Type in address bar: `http://192.168.2.99:9090`
   (Replace 192.168.2.99 with your board's IP if different)
3. Press Enter
4. You'll see PYNQ Jupyter login page
5. **Password:** `xilinx`
6. Click "Log in"
7. You're now connected! ✅

### Method B: Using SSH (Command Line)

1. Press `Windows + R`
2. Type `cmd` and press Enter
3. In the black window, type:
   ```
   ssh xilinx@192.168.2.99
   ```
   (Replace 192.168.2.99 with your board's IP)
4. Press Enter
5. Type password: `xilinx` (you won't see it as you type)
6. Press Enter
7. You'll see: `xilinx@pynq:~$` ✅

---

## 📤 STEP 4: Upload Files to PYNQ Board

### Using Jupyter (Web Browser Method):

**Already in Jupyter from Step 3:**

1. Click **"Upload"** button (top right)
2. Navigate to your `PYNQ` folder on Desktop
3. Select ALL files in `uart_lib` folder:
   - `__init__.py`
   - `uart_config.py`
   - `uart_protocol.py`
   - `uart_transmitter.py`
   - `uart_receiver.py`
4. Click "Open"
5. Click blue **"Upload"** button for each file
6. Also upload:
   - `README.md`
   - `PYNQ_DEPLOYMENT_GUIDE.md`
   - `QUICK_TROUBLESHOOTING.md`

**Create uart_lib folder in Jupyter:**
1. Click **"New"** → **"Folder"**
2. Check the checkbox next to "Untitled Folder"
3. Click **"Rename"**
4. Type: `uart_lib`
5. Press Enter
6. Open `uart_lib` folder
7. Upload the 5 Python files there

### Using SCP (SSH Method):

**In Command Prompt on Desktop PC:**

```bash
# Navigate to where you saved PYNQ folder
cd C:\Users\YourName\Desktop

# Copy entire PYNQ folder to board
scp -r PYNQ xilinx@192.168.2.99:/home/xilinx/

# Password: xilinx
```

---

## 🔧 STEP 5: Install Required Software on PYNQ

### Using Jupyter:

1. In Jupyter, click **"New"** → **"Terminal"**
2. A black terminal window opens
3. Type these commands one by one:

```bash
# Install pyserial
sudo pip3 install pyserial

# Press Enter, wait for installation

# Verify installation
python3 -c "import serial; print('PySerial installed successfully!')"
```

### Using SSH:

**In your SSH terminal:**

```bash
# Install pyserial
sudo pip3 install pyserial

# Verify
python3 -c "import serial; print('PySerial installed successfully!')"
```

**Expected Output:**
```
PySerial installed successfully!
```

---

## ✅ STEP 6: Test the UART Library

**In Jupyter Terminal or SSH:**

```bash
# Navigate to PYNQ folder
cd /home/xilinx/PYNQ

# Test configuration
python3 uart_lib/uart_config.py
```

**Expected Output:**
```
================================================================================
UART CONFIGURATION
================================================================================
Port (TX):        /dev/ttyPS1
Port (RX):        /dev/ttyPS1
Baud Rate:        115200 bps
...
================================================================================
```

**Test protocol:**
```bash
python3 uart_lib/uart_protocol.py
```

**Expected Output:**
```
================================================================================
UART PROTOCOL TEST
================================================================================
Test 1: Create and parse packet
...
ALL TESTS PASSED!
================================================================================
```

---

## 🎉 STEP 7: You're Ready!

**What You've Accomplished:**
- ✅ Transferred code from laptop to desktop PC
- ✅ Found PYNQ board IP address
- ✅ Connected to PYNQ board (Jupyter or SSH)
- ✅ Uploaded all files to board
- ✅ Installed required software (pyserial)
- ✅ Tested UART library

**What's Next:**
- 📚 Follow `PYNQ_DEPLOYMENT_GUIDE.md` for complete deployment
- 🔌 Connect two PYNQ boards with UART cable
- 🎵 Test with audio encryption/decryption
- 📊 Measure performance metrics

---

## 🆘 Troubleshooting

### Problem: Can't find PYNQ folder on Desktop PC
**Solution:** Go back to Step 1 and transfer again

### Problem: find_pynq_board.bat doesn't find board
**Solution:**
- Check PYNQ board green LED (should be solid)
- Wait 60 seconds after power-on
- Try different USB port
- Check USB cable connection

### Problem: Can't access http://192.168.2.99:9090
**Solution:**
- Verify IP address from find_pynq_board.bat
- Try SSH instead: `ssh xilinx@192.168.2.99`
- Check if board is fully booted (green LED solid)

### Problem: Upload fails in Jupyter
**Solution:**
- Try uploading files one at a time
- Or use SCP method instead
- Check internet connection

### Problem: pip install fails
**Solution:**
```bash
# Update pip first
sudo pip3 install --upgrade pip

# Try again
sudo pip3 install pyserial
```

---

## 📋 Quick Reference

**PYNQ Board Default Settings:**
- IP Address: 192.168.2.99 (USB) or assigned by router (Ethernet)
- Username: xilinx
- Password: xilinx
- Jupyter: http://[IP]:9090
- SSH: ssh xilinx@[IP]

**Important Files:**
- `find_pynq_board.bat` - Find board IP
- `PYNQ_DEPLOYMENT_GUIDE.md` - Complete guide
- `QUICK_TROUBLESHOOTING.md` - Common issues
- `uart_lib/` - UART communication code

**Commands to Remember:**
```bash
# Connect via SSH
ssh xilinx@192.168.2.99

# Copy files
scp -r PYNQ xilinx@192.168.2.99:/home/xilinx/

# Install software
sudo pip3 install pyserial

# Test code
python3 uart_lib/uart_config.py
```

---

## ✨ Summary

You now have a complete step-by-step process to:
1. ✅ Transfer code from laptop to desktop PC
2. ✅ Find PYNQ board IP address
3. ✅ Connect to PYNQ board
4. ✅ Upload files to board
5. ✅ Install required software
6. ✅ Test the system

**Follow these steps in order, and you'll have your PYNQ boards ready for chaos-based encryption testing!** 🚀

---

**Need Help?** Refer to:
- `PYNQ_DEPLOYMENT_GUIDE.md` - Detailed technical guide
- `QUICK_TROUBLESHOOTING.md` - Common problems
- `README.md` - Quick overview