# 🔧 Quick Troubleshooting Guide

## ❌ Error: "ssh: connect to host 192.168.2.99 port 22: Connection timed out"

### Why This Happens
This error means the PYNQ-Z2 board is **not yet set up** or **not connected to your network**. The IP address 192.168.2.99 doesn't exist yet because you haven't completed the board setup.

### ✅ Solution: Complete Phase 1 First

You need to set up your PYNQ-Z2 boards before you can SSH into them. Follow these steps:

---

## 📋 Pre-Deployment Checklist

Before you can use SSH, you MUST complete these steps:

### Step 1: Do You Have PYNQ-Z2 Boards?
- [ ] I have 2 PYNQ-Z2 FPGA boards
- [ ] I have 2 microSD cards (8GB minimum)
- [ ] I have USB cables for power
- [ ] I have an Ethernet cable or USB-Ethernet adapter

**If NO:** You need to acquire the hardware first. The PYNQ folder is ready for when you get the boards.

**If YES:** Continue to Step 2.

---

### Step 2: Flash PYNQ Image to SD Cards

**You need to do this FIRST before SSH will work!**

#### Download PYNQ Image
1. Go to: http://www.pynq.io/board.html
2. Download **PYNQ v2.7 or later** for PYNQ-Z2
3. Extract the `.img` file (it will be several GB)

#### Flash to SD Card (Windows)
1. Download **Balena Etcher**: https://www.balena.io/etcher/
2. Insert microSD card into your computer
3. Open Balena Etcher
4. Click "Flash from file" → Select the PYNQ `.img` file
5. Click "Select target" → Choose your SD card
6. Click "Flash!" and wait 10-15 minutes
7. **Repeat for second SD card**

#### Flash to SD Card (Linux/Mac)
```bash
# Find SD card device
lsblk

# Flash image (replace /dev/sdX with your SD card)
sudo dd if=pynq_z2_v2.7.img of=/dev/sdX bs=4M status=progress
sync
```

---

### Step 3: Boot the PYNQ-Z2 Board

1. **Insert SD card** into PYNQ-Z2 board
2. **Set boot mode jumper** to SD card (check board manual)
3. **Connect Ethernet cable** from board to your router/switch
4. **Connect USB cable** for power
5. **Wait 30-60 seconds** for board to boot
6. **Check LED:** Green LED should be solid (not blinking)

---

### Step 4: Find the Board's IP Address

The board uses **DHCP by default**, so it gets an IP from your router.

#### Option A: Check Your Router
1. Log into your router's admin page (usually 192.168.1.1 or 192.168.0.1)
2. Look for "Connected Devices" or "DHCP Clients"
3. Find device named "pynq" or "xilinx"
4. Note the IP address (e.g., 192.168.1.100)

#### Option B: Use Network Scanner
```bash
# Windows (install nmap first)
nmap -sn 192.168.1.0/24

# Linux/Mac
sudo nmap -sn 192.168.1.0/24

# Look for device with hostname "pynq"
```

#### Option C: Direct USB Connection
1. Connect PYNQ board to PC via USB
2. Board will appear as USB Ethernet device
3. Default IP: **192.168.2.99**
4. Your PC should auto-configure to 192.168.2.x

---

### Step 5: Test SSH Connection

Once you know the board's IP address:

```bash
# Replace with your board's actual IP
ssh xilinx@192.168.1.100

# Default password: xilinx
```

**Expected Output:**
```
The authenticity of host '192.168.1.100' can't be established.
Are you sure you want to continue connecting (yes/no)? yes
xilinx@192.168.1.100's password: [type: xilinx]

Welcome to PYNQ!
xilinx@pynq:~$
```

---

## 🎯 Current Status Check

### Where Are You Now?

**Scenario 1: I don't have PYNQ-Z2 boards yet**
- ✅ PYNQ folder is ready
- ✅ All code is prepared
- ⏳ Waiting for hardware
- **Action:** Acquire 2 PYNQ-Z2 boards, then start Phase 1

**Scenario 2: I have boards but haven't flashed SD cards**
- ✅ PYNQ folder is ready
- ✅ Hardware available
- ❌ SD cards not flashed
- **Action:** Download PYNQ image and flash SD cards (Step 2 above)

**Scenario 3: SD cards flashed but board not booting**
- ✅ SD cards ready
- ❌ Board not responding
- **Action:** Check power, boot jumper, LED status

**Scenario 4: Board booting but can't find IP**
- ✅ Board powered and booting
- ❌ Can't connect via SSH
- **Action:** Find board's IP using router or network scanner (Step 4 above)

**Scenario 5: Everything working!**
- ✅ Board booting
- ✅ SSH connection successful
- **Action:** Continue with Phase 1 of PYNQ_DEPLOYMENT_GUIDE.md

---

## 📖 What to Do Next

### If You Don't Have Boards Yet
1. ✅ Review the PYNQ_DEPLOYMENT_GUIDE.md to understand the process
2. ✅ Test the existing Chua/Rössler code on your PC (it already works!)
3. ✅ Prepare your thesis documentation
4. ⏳ Wait for hardware to arrive
5. 🚀 When boards arrive, start with Step 2 (Flash SD cards)

### If You Have Boards
1. 🔥 Flash PYNQ image to SD cards (Step 2 above)
2. 🔌 Boot the boards (Step 3 above)
3. 🔍 Find the IP addresses (Step 4 above)
4. 🔐 Test SSH connection (Step 5 above)
5. 📚 Follow PYNQ_DEPLOYMENT_GUIDE.md Phase 1

---

## 🆘 Still Having Problems?

### Problem: Can't download PYNQ image
**Solution:** 
- Check internet connection
- Try different browser
- Use download manager for large files
- Alternative: Ask your university lab if they have PYNQ images

### Problem: SD card not recognized
**Solution:**
- Try different SD card reader
- Format SD card as FAT32 first
- Use SD card 8GB or larger, Class 10
- Check if SD card is write-protected

### Problem: Board not booting (LED blinking or off)
**Solution:**
- Check boot jumper position (must be set to SD)
- Verify SD card is fully inserted
- Try different power source (use powered USB hub)
- Check if SD card was flashed correctly

### Problem: Can't find board on network
**Solution:**
- Connect board directly to PC via USB (will be 192.168.2.99)
- Check Ethernet cable connection
- Verify router DHCP is enabled
- Try connecting to Jupyter: http://192.168.2.99:9090 (password: xilinx)

---

## ✅ Summary

**The SSH error is NORMAL** - it means you haven't set up the boards yet!

**Next Steps:**
1. If you have boards → Flash SD cards and boot them
2. If you don't have boards → Wait for hardware, code is ready
3. Once boards are booting → Find IP address and SSH will work
4. Then follow PYNQ_DEPLOYMENT_GUIDE.md from Phase 1

**The PYNQ folder and all code are ready to go when your boards are set up!** 🚀

---

**Questions?** Refer to:
- `PYNQ_DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `README.md` - Quick start guide
- PYNQ Documentation: http://pynq.readthedocs.io/