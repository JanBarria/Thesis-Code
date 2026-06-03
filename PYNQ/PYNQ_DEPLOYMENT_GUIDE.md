# 🚀 PYNQ-Z2 Deployment & UART Implementation Guide

## FPGA Implementation of Chaos-Based Secure Communication
### De La Salle University - ECE Thesis Project

**Authors:** Barria, Jusay (Chua Circuit) | Cortes, Abalos (Rössler System)

---

## 📋 Table of Contents

1. [Project Status](#project-status)
2. [System Overview](#system-overview)
3. [Hardware Requirements](#hardware-requirements)
4. [Phase 1: PYNQ-Z2 Board Setup](#phase-1-pynq-z2-board-setup)
5. [Phase 2: Single-Board Testing](#phase-2-single-board-testing)
6. [Phase 3: UART Implementation](#phase-3-uart-implementation)
7. [Phase 4: Two-Board Integration](#phase-4-two-board-integration)
8. [Phase 5: Performance Validation](#phase-5-performance-validation)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Success Criteria](#success-criteria)

---

## 📊 Project Status

### ✅ Completed
- [x] Chua Circuit chaotic generator implementation
- [x] Rössler System chaotic generator implementation
- [x] Keystream extraction modules
- [x] Encryption/Decryption modules
- [x] Pecora-Carroll synchronization algorithm
- [x] PC testing with perfect results (Correlation=1.0, BER=0%)

### 🔄 In Progress
- [ ] PYNQ-Z2 board deployment
- [ ] UART communication implementation
- [ ] Two-board encrypted communication

### 📅 Timeline
- **Phase 1-2:** 1 week (Board setup + Single-board testing)
- **Phase 3:** 1 week (UART implementation)
- **Phase 4-5:** 1 week (Integration + Validation)
- **Total:** 3 weeks to full deployment

---

## 🎯 System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSMITTER (Board 1)                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │  Audio   │──▶│  Chaotic │──▶│ Keystream│──▶│   XOR    │   │
│  │  Input   │   │Generator │   │Extractor │   │Encryption│   │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘   │
│                       │                              │          │
│                       │ Drive Signal (x state)       │          │
│                       │                              │          │
│                       └──────────────┬───────────────┘          │
│                                      │                          │
│                              ┌───────▼────────┐                 │
│                              │  UART TX       │                 │
│                              │  (Encrypted +  │                 │
│                              │   Drive Signal)│                 │
│                              └───────┬────────┘                 │
└──────────────────────────────────────┼──────────────────────────┘
                                       │
                                       │ UART Cable
                                       │
┌──────────────────────────────────────▼──────────────────────────┐
│                     RECEIVER (Board 2)                          │
│                              ┌───────────────┐                  │
│                              │  UART RX      │                  │
│                              │  (Encrypted + │                  │
│                              │   Drive Signal)│                 │
│                              └───────┬───────┘                  │
│                                      │                          │
│                       ┌──────────────┴───────────────┐          │
│                       │                              │          │
│                       │ Drive Signal (x state)       │          │
│                       │                              │          │
│  ┌──────────┐   ┌────▼─────┐   ┌──────────┐   ┌───▼──────┐   │
│  │Decrypted │◀──│   XOR    │◀──│ Keystream│◀──│ Chaotic  │   │
│  │  Audio   │   │Decryption│   │Extractor │   │Generator │   │
│  │  Output  │   │          │   │          │   │(Sync'd)  │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features
- **Chaotic Systems:** Chua Circuit (double-scroll) & Rössler (spiral attractor)
- **Encryption:** Bitwise XOR with chaotic keystream
- **Synchronization:** Pecora-Carroll drive-response method
- **Communication:** UART serial interface
- **Audio Format:** Mono 16-bit PCM WAV files

---

## 🔧 Hardware Requirements

### Essential Components
- **2x PYNQ-Z2 FPGA Boards** (Zynq-7000 SoC)
- **2x MicroSD Cards** (8GB minimum, Class 10)
- **2x USB Cables** (Micro-USB for power/programming)
- **1x Ethernet Cable** (for network connection)
- **Jumper Wires** (for UART connection)
- **Computer** (Windows/Linux/Mac for development)

### Optional Components
- **USB-to-Serial Adapter** (for debugging)
- **Logic Analyzer** (for UART signal verification)
- **Powered USB Hub** (for stable power supply)

### PYNQ-Z2 UART Pin Connections

| Signal | Board 1 (TX) | Board 2 (RX) | Description |
|--------|--------------|--------------|-------------|
| TX     | PMOD JB1     | -            | Transmit Data |
| RX     | -            | PMOD JB1     | Receive Data |
| GND    | GND          | GND          | Common Ground |

**Physical Connection:**
```
Board 1 (Transmitter)          Board 2 (Receiver)
┌─────────────────┐            ┌─────────────────┐
│  PMOD JB1 (TX) ─┼────────────┼─ PMOD JB1 (RX) │
│  GND           ─┼────────────┼─ GND            │
└─────────────────┘            └─────────────────┘
```

---

## 📦 Phase 1: PYNQ-Z2 Board Setup

### Step 1.1: Flash PYNQ Image to SD Cards

**Download PYNQ Image:**
1. Visit [PYNQ.io Downloads](http://www.pynq.io/board.html)
2. Download PYNQ v2.7 or later for PYNQ-Z2
3. Extract the `.img` file

**Flash to SD Card (Windows):**
```powershell
# Using Win32DiskImager or Balena Etcher
1. Insert SD card into computer
2. Open Balena Etcher
3. Select PYNQ image file
4. Select SD card drive
5. Click "Flash!"
6. Wait for completion (10-15 minutes)
7. Repeat for second SD card
```

**Flash to SD Card (Linux/Mac):**
```bash
# Find SD card device
lsblk

# Flash image (replace /dev/sdX with your SD card)
sudo dd if=pynq_z2_v2.7.img of=/dev/sdX bs=4M status=progress
sync

# Repeat for second SD card
```

### Step 1.2: Configure Network Settings

**Board 1 (Transmitter) - Static IP: 192.168.2.99**
```bash
# After first boot, SSH into board
ssh xilinx@192.168.2.99
# Password: xilinx

# Edit network configuration
sudo nano /etc/network/interfaces.d/eth0

# Add these lines:
auto eth0
iface eth0 inet static
    address 192.168.2.99
    netmask 255.255.255.0
    gateway 192.168.2.1

# Reboot
sudo reboot
```

**Board 2 (Receiver) - Static IP: 192.168.2.100**
```bash
# SSH into board
ssh xilinx@192.168.2.99
# Password: xilinx

# Edit network configuration
sudo nano /etc/network/interfaces.d/eth0

# Add these lines:
auto eth0
iface eth0 inet static
    address 192.168.2.100
    netmask 255.255.255.0
    gateway 192.168.2.1

# Reboot
sudo reboot
```

### Step 1.3: Verify Board Boot

**Check Board Status:**
```bash
# Board 1
ping 192.168.2.99

# Board 2
ping 192.168.2.100

# SSH access
ssh xilinx@192.168.2.99
ssh xilinx@192.168.2.100
```

**Expected Output:**
```
64 bytes from 192.168.2.99: icmp_seq=1 ttl=64 time=1.23 ms
64 bytes from 192.168.2.100: icmp_seq=1 ttl=64 time=1.45 ms
```

### Step 1.4: Transfer Project Files

**Option A: Using SCP (Recommended)**
```bash
# From your PC, navigate to project directory
cd C:/Users/JanChristopherRobinB/Desktop

# Transfer to Board 1 (Transmitter)
scp -r chaos_secure_communication xilinx@192.168.2.99:/home/xilinx/

# Transfer to Board 2 (Receiver)
scp -r chaos_secure_communication xilinx@192.168.2.100:/home/xilinx/

# Verify transfer
ssh xilinx@192.168.2.99 "ls -la /home/xilinx/chaos_secure_communication"
ssh xilinx@192.168.2.100 "ls -la /home/xilinx/chaos_secure_communication"
```

**Option B: Using Jupyter Notebook**
```bash
# Open browser
http://192.168.2.99:9090
http://192.168.2.100:9090

# Login with password: xilinx
# Use Upload button to transfer files
```

### Step 1.5: Install Python Dependencies

**On Both Boards:**
```bash
# SSH into each board
ssh xilinx@192.168.2.99  # Board 1
ssh xilinx@192.168.2.100 # Board 2

# Update package manager
sudo apt-get update

# Install Python packages
sudo pip3 install numpy scipy matplotlib pyserial

# Verify installation
python3 -c "import numpy, scipy, matplotlib, serial; print('All packages installed!')"
```

**Expected Output:**
```
All packages installed!
```

---

## 🧪 Phase 2: Single-Board Testing

### Step 2.1: Test Board 1 (Transmitter)

**Create Test Audio:**
```bash
# SSH into Board 1
ssh xilinx@192.168.2.99

# Navigate to project
cd /home/xilinx/chaos_secure_communication

# Create test audio
python3 -c "
import numpy as np
from scipy.io import wavfile
import os

os.makedirs('test_audio', exist_ok=True)
sr = 44100
duration = 1.0
t = np.linspace(0, duration, int(sr * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)
wavfile.write('test_audio/test_tone.wav', sr, audio)
print('Test audio created: test_audio/test_tone.wav')
"
```

**Run Chua Encryption:**
```bash
cd chua_system
python3 chua_encryptor.py ../test_audio/test_tone.wav
```

**Expected Output:**
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
Transmitter states saved to: encrypted_audio_transmitter_states.npy

================================================================================
ENCRYPTION COMPLETE
================================================================================
```

**Verify Files Created:**
```bash
ls -lh encrypted_audio*
```

**Expected Files:**
- `encrypted_audio.wav` (~88 KB)
- `encrypted_audio_secret_key.txt` (~300 bytes)
- `encrypted_audio_drive_signal.npy` (~353 KB)
- `encrypted_audio_transmitter_states.npy` (~1 MB)

### Step 2.2: Test Board 2 (Receiver)

**Transfer Encrypted Files from Board 1 to Board 2:**
```bash
# On your PC
scp xilinx@192.168.2.99:/home/xilinx/chaos_secure_communication/chua_system/encrypted_audio* .
scp encrypted_audio* xilinx@192.168.2.100:/home/xilinx/chaos_secure_communication/chua_system/
```

**Run Chua Decryption on Board 2:**
```bash
# SSH into Board 2
ssh xilinx@192.168.2.100

cd /home/xilinx/chaos_secure_communication/chua_system
python3 chua_decryptor.py encrypted_audio.wav ../test_audio/test_tone.wav
```

**Expected Output:**
```
================================================================================
CHUA CIRCUIT AUDIO DECRYPTION
================================================================================
Secret key loaded: x0=0.1, y0=0.0, z0=0.0
Drive signal loaded: 44100 samples
Encrypted audio loaded: 44100 samples at 44100 Hz
Generating keystream from transmitter states...
Keystream generated successfully
Decrypting audio...
Decrypted audio saved to: decrypted_audio.wav

Performance Metrics:
  Pearson Correlation: 1.000000
  Bit Error Rate (BER): 0.000000e+00 (0.0000%)
  Mean Squared Error (MSE): 0.00

Performance Assessment:
  ✓ Correlation: EXCELLENT (≥0.95)
  ✓ BER: EXCELLENT (<1%)
================================================================================
```

### Step 2.3: Verify Results

**Check Correlation:**
- ✅ Correlation = 1.0 (Perfect)
- ✅ BER = 0% (No errors)
- ✅ MSE = 0 (No distortion)

**If results are not perfect, check:**
1. Files transferred correctly
2. Same secret key used
3. Drive signal matches
4. No file corruption during transfer

---

## 🔌 Phase 3: UART Implementation

### Step 3.1: Create UART Configuration Module

**File: `chaos_secure_communication/uart_lib/uart_config.py`**

```python
"""
UART Configuration for PYNQ-Z2 Board-to-Board Communication
"""

# UART Parameters
UART_PORT_TX = '/dev/ttyPS1'  # Transmitter UART port
UART_PORT_RX = '/dev/ttyPS1'  # Receiver UART port
BAUD_RATE = 115200            # Bits per second
TIMEOUT = 5                   # Seconds
BYTESIZE = 8                  # Data bits
PARITY = 'N'                  # No parity
STOPBITS = 1                  # Stop bits

# Protocol Parameters
HEADER = b'\xDE\xAD\xBE\xEF'  # Frame header (4 bytes)
MAX_PACKET_SIZE = 4096        # Maximum packet size in bytes
BUFFER_SIZE = 65536           # Receive buffer size

# GPIO Pins (PMOD JB)
TX_PIN = 'JB1'                # Transmit pin
RX_PIN = 'JB1'                # Receive pin

# Error Handling
MAX_RETRIES = 3               # Maximum retransmission attempts
ACK_TIMEOUT = 2               # Seconds to wait for acknowledgment
```

### Step 3.2: Create UART Protocol Module

**File: `chaos_secure_communication/uart_lib/uart_protocol.py`**

```python
"""
UART Protocol Implementation with Error Detection
"""

import struct
import zlib

class UARTProtocol:
    """UART communication protocol with CRC32 checksums"""
    
    HEADER = b'\xDE\xAD\xBE\xEF'
    
    @staticmethod
    def create_packet(data):
        """
        Create UART packet with header, length, data, and checksum
        
        Packet Structure:
        [HEADER (4 bytes)][LENGTH (4 bytes)][DATA (variable)][CRC32 (4 bytes)]
        """
        # Calculate CRC32 checksum
        checksum = zlib.crc32(data) & 0xFFFFFFFF
        
        # Pack header, length, data, checksum
        length = len(data)
        packet = UARTProtocol.HEADER
        packet += struct.pack('<I', length)  # Little-endian unsigned int
        packet += data
        packet += struct.pack('<I', checksum)
        
        return packet
    
    @staticmethod
    def parse_packet(packet):
        """
        Parse received UART packet and verify integrity
        
        Returns:
            (data, valid) tuple where valid is True if checksum matches
        """
        # Check minimum packet size
        if len(packet) < 12:  # Header(4) + Length(4) + CRC(4)
            return None, False
        
        # Verify header
        header = packet[:4]
        if header != UARTProtocol.HEADER:
            return None, False
        
        # Extract length
        length = struct.unpack('<I', packet[4:8])[0]
        
        # Extract data
        data = packet[8:8+length]
        
        # Extract checksum
        received_checksum = struct.unpack('<I', packet[8+length:8+length+4])[0]
        
        # Calculate checksum
        calculated_checksum = zlib.crc32(data) & 0xFFFFFFFF
        
        # Verify checksum
        valid = (received_checksum == calculated_checksum)
        
        return data, valid
    
    @staticmethod
    def create_ack():
        """Create acknowledgment packet"""
        return UARTProtocol.create_packet(b'ACK')
    
    @staticmethod
    def create_nack():
        """Create negative acknowledgment packet"""
        return UARTProtocol.create_packet(b'NACK')
```

### Step 3.3: Create UART Transmitter Module

**File: `chaos_secure_communication/uart_lib/uart_transmitter.py`**

```python
"""
UART Transmitter for PYNQ-Z2
Sends encrypted audio and drive signal to receiver
"""

import serial
import numpy as np
import time
from uart_protocol import UARTProtocol
from uart_config import *

class UARTTransmitter:
    """UART transmitter for chaos-based encrypted communication"""
    
    def __init__(self, port=UART_PORT_TX, baud_rate=BAUD_RATE):
        """Initialize UART transmitter"""
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        
    def connect(self):
        """Open UART connection"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT
            )
            print(f"✓ UART Transmitter connected on {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            print(f"✗ Failed to connect UART: {e}")
            return False
    
    def send_data(self, data, data_type='audio'):
        """
        Send data with error checking and retransmission
        
        Args:
            data: bytes or numpy array to send
            data_type: 'audio', 'drive_signal', or 'key'
        """
        # Convert numpy array to bytes if needed
        if isinstance(data, np.ndarray):
            data_bytes = data.tobytes()
        else:
            data_bytes = data
        
        # Create packet
        packet = UARTProtocol.create_packet(data_bytes)
        
        # Send with retries
        for attempt in range(MAX_RETRIES):
            try:
                # Send packet
                self.serial.write(packet)
                self.serial.flush()
                
                print(f"  Sent {data_type}: {len(data_bytes)} bytes (attempt {attempt+1})")
                
                # Wait for ACK
                ack_packet = self.serial.read(16)  # ACK packet size
                if ack_packet:
                    ack_data, valid = UARTProtocol.parse_packet(ack_packet)
                    if valid and ack_data == b'ACK':
                        print(f"  ✓ {data_type} acknowledged")
                        return True
                
                print(f"  ✗ No ACK received, retrying...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Transmission error: {e}")
                time.sleep(0.5)
        
        print(f"  ✗ Failed to send {data_type} after {MAX_RETRIES} attempts")
        return False
    
    def send_encrypted_audio(self, encrypted_audio, drive_signal):
        """
        Send encrypted audio and drive signal
        
        Args:
            encrypted_audio: numpy array of encrypted audio samples
            drive_signal: numpy array of x state (drive signal)
        """
        print("\n" + "="*80)
        print("UART TRANSMISSION")
        print("="*80)
        
        # Send encrypted audio
        print("\n[1/2] Sending encrypted audio...")
        success_audio = self.send_data(encrypted_audio, 'encrypted_audio')
        
        # Send drive signal
        print("\n[2/2] Sending drive signal...")
        success_drive = self.send_data(drive_signal, 'drive_signal')
        
        if success_audio and success_drive:
            print("\n" + "="*80)
            print("✓ TRANSMISSION COMPLETE")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("✗ TRANSMISSION FAILED")
            print("="*80)
            return False
    
    def disconnect(self):
        """Close UART connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✓ UART Transmitter disconnected")
```

### Step 3.4: Create UART Receiver Module

**File: `chaos_secure_communication/uart_lib/uart_receiver.py`**

```python
"""
UART Receiver for PYNQ-Z2
Receives encrypted audio and drive signal from transmitter
"""

import serial
import numpy as np
import time
from uart_protocol import UARTProtocol
from uart_config import *

class UARTReceiver:
    """UART receiver for chaos-based encrypted communication"""
    
    def __init__(self, port=UART_PORT_RX, baud_rate=BAUD_RATE):
        """Initialize UART receiver"""
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        
    def connect(self):
        """Open UART connection"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT
            )
            print(f"✓ UART Receiver connected on {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            print(f"✗ Failed to connect UART: {e}")
            return False
    
    def receive_data(self, data_type='audio'):
        """
        Receive data with error checking
        
        Args:
            data_type: 'audio', 'drive_signal', or 'key'
            
        Returns:
            numpy array of received data, or None if failed
        """
        print(f"  Waiting for {data_type}...")
        
        try:
            # Read header
            header = self.serial.read(4)
            if header != UARTProtocol.HEADER:
                print(f"  ✗ Invalid header")
                self.serial.write(UARTProtocol.create_nack())
                return None
            
            # Read length
            length_bytes = self.serial.read(4)
            length = struct.unpack('<I', length_bytes)[0]
            
            # Read data
            data_bytes = self.serial.read(length)
            
            # Read checksum
            checksum_bytes = self.serial.read(4)
            
            # Reconstruct packet
            packet = header + length_bytes + data_bytes + checksum_bytes
            
            # Parse and verify
            data, valid = UARTProtocol.parse_packet(packet)
            
            if valid:
                print(f"  ✓ {data_type} received: {len(data)} bytes")
                # Send ACK
                self.serial.write(UARTProtocol.create_ack())
                self.serial.flush()
                
                # Convert bytes to numpy array
                return np.frombuffer(data, dtype=np.int16)
            else:
                print(f"  ✗ Checksum verification failed")
                # Send NACK
                self.serial.write(UARTProtocol.create_nack())
                return None
                
        except Exception as e:
            print(f"  ✗ Reception error: {e}")
            return None
    
    def receive_encrypted_audio(self):
        """
        Receive encrypted audio and drive signal
        
        Returns:
            (encrypted_audio, drive_signal) tuple, or (None, None) if failed
        """
        print("\n" + "="*80)
        print("UART RECEPTION")
        print("="*80)
        
        # Receive encrypted audio
        print("\n[1/2] Receiving encrypted audio...")
        encrypted_audio = self.receive_data('encrypted_audio')
        
        # Receive drive signal
        print("\n[2/2] Receiving drive signal...")
        drive_signal = self.receive_data('drive_signal')
        
        if encrypted_audio is not None and drive_signal is not None:
            print("\n" + "="*80)
            print("✓ RECEPTION COMPLETE")
            print("="*80)
            return encrypted_audio, drive_signal
        else:
            print("\n" + "="*80)
            print("✗ RECEPTION FAILED")
            print("="*80)
            return None, None
    
    def disconnect(self):
        """Close UART connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✓ UART Receiver disconnected")
```

### Step 3.5: Physical UART Connection

**Wiring Diagram:**
```
PYNQ-Z2 Board 1 (Transmitter)    PYNQ-Z2 Board 2 (Receiver)
┌─────────────────────────┐      ┌─────────────────────────┐
│                         │      │                         │
│  PMOD JB Connector      │      │  PMOD JB Connector      │
│  ┌─────────────────┐    │      │  ┌─────────────────┐    │
│  │ Pin 1 (TX) ●────┼────┼──────┼──┤● Pin 1 (RX)     │    │
│  │ Pin 5 (GND)●────┼────┼──────┼──┤● Pin 5 (GND)    │    │
│  └─────────────────┘    │      │  └─────────────────┘    │
│                         │      │                         │
└─────────────────────────┘      └─────────────────────────┘
```

**Connection Steps:**
1. Power off both boards
2. Connect TX (Board 1 PMOD JB Pin 1) to RX (Board 2 PMOD JB Pin 1)
3. Connect GND (Board 1 PMOD JB Pin 5) to GND (Board 2 PMOD JB Pin 5)
4. Verify connections with multimeter (continuity test)
5. Power on both boards

**Safety Checks:**
- ✅ No short circuits between power and ground
- ✅ TX and RX not connected to same board
- ✅ Common ground established
- ✅ Voltage levels compatible (3.3V CMOS)

---

## 🔗 Phase 4: Two-Board Integration

### Step 4.1: Integrate UART with Encryptor

**File: `chaos_secure_communication/chua_system/uart_chua_transmitter.py`**

```python
"""
Chua Circuit Encryptor with UART Transmission
Integrates encryption with UART communication
"""

import sys
import os
sys.path.append('../uart_lib')

from chua_encryptor import ChuaEncryptor
from uart_transmitter import UARTTransmitter

def main():
    if len(sys.argv) < 2:
        print("Usage: python uart_chua_transmitter.py <input_audio.wav>")
        sys.exit(1)
    
    input_audio = sys.argv[1]
    
    # Step 1: Encrypt audio
    print("\n" + "="*80)
    print("STEP 1: ENCRYPTION")
    print("="*80)
    
    encryptor = ChuaEncryptor()
    result = encryptor.encrypt_audio(input_audio, visualize=False)
    
    encrypted_audio = result['ciphertext']
    drive_signal = result['drive_signal']
    
    # Step 2: Transmit via UART
    print("\n" + "="*80)
    print("STEP 2: UART TRANSMISSION")
    print("="*80)
    
    uart = UARTTransmitter()
    if uart.connect():
        success = uart.send_encrypted_audio(encrypted_audio, drive_signal)
        uart.disconnect()
        
        if success:
            print("\n✓✓✓ TRANSMISSION SUCCESSFUL ✓✓✓")
        else:
            print("\n✗✗✗ TRANSMISSION FAILED ✗✗✗")
    else:
        print("\n✗✗✗ UART CONNECTION FAILED ✗✗✗")

if __name__ == "__main__":
    main()
```

### Step 4.2: Integrate UART with Decryptor

**File: `chaos_secure_communication/chua_system/uart_chua_receiver.py`**

```python
"""
Chua Circuit Decryptor with UART Reception
Integrates UART reception with decryption
"""

import sys
import os
sys.path.append('../uart_lib')

from chua_decryptor import ChuaDecryptor
from uart_receiver import UARTReceiver
import numpy as np
from scipy.io import wavfile

def main():
    if len(sys.argv) < 2:
        print("Usage: python uart_chua_receiver.py <original_audio.wav>")
        sys.exit(1)
    
    original_audio = sys.argv[1]
    
    # Step 1: Receive via UART
    print("\n" + "="*80)
    print("STEP 1: UART RECEPTION")
    print("="*80)
    
    uart = UARTReceiver()
    if not uart.connect():
        print("\n✗✗✗ UART CONNECTION FAILED ✗✗✗")
        sys.exit(1)
    
    encrypted_audio, drive_signal = uart.receive_encrypted_audio()
    uart.disconnect()
    
    if encrypted_audio is None or drive_signal is None:
        print("\n✗✗✗ RECEPTION FAILED ✗✗✗")
        sys.exit(1)
    
    # Save received data temporarily
    np.save('received_encrypted_audio.npy', encrypted_audio)
    np.save('received_drive_signal.npy', drive_signal)
    
    # Step 2: Decrypt audio
    print("\n" + "="*80)
    print("STEP 2: DECRYPTION")
    print("="*80)
    
    decryptor = ChuaDecryptor()
    
    # Load secret key (must be shared securely beforehand)
    key_data = np.load('encrypted_audio_secret_key.txt', allow_pickle=True)
    
    result = decryptor.decrypt_audio(
        encrypted_audio=encrypted_audio,
        drive_signal=drive_signal,
        original_audio_path=original_audio,
        visualize=False
    )
    
    if result['correlation'] >= 0.95:
        print("\n✓✓✓ DECRYPTION SUCCESSFUL ✓✓✓")
        print(f"Correlation: {result['correlation']:.6f}")
        print(f"BER: {result['ber']:.6e} ({result['ber']*100:.4f}%)")
    else:
        print("\n✗✗✗ DECRYPTION QUALITY POOR ✗✗✗")
        print(f"Correlation: {result['correlation']:.6f} (target: ≥0.95)")

if __name__ == "__main__":
    main()
```

### Step 4.3: Run Two-Board Test

**On Board 1 (Transmitter):**
```bash
ssh xilinx@192.168.2.99
cd /home/xilinx/chaos_secure_communication/chua_system
python3 uart_chua_transmitter.py ../test_audio/test_tone.wav
```

**On Board 2 (Receiver) - Run simultaneously:**
```bash
ssh xilinx@192.168.2.100
cd /home/xilinx/chaos_secure_communication/chua_system
python3 uart_chua_receiver.py ../test_audio/test_tone.wav
```

**Expected Output (Board 1):**
```
================================================================================
STEP 1: ENCRYPTION
================================================================================
Loaded audio: 44100 samples at 44100 Hz
Encrypting audio...
Encrypted audio saved to: encrypted_audio.wav

================================================================================
STEP 2: UART TRANSMISSION
================================================================================
✓ UART Transmitter connected on /dev/ttyPS1 at 115200 baud

[1/2] Sending encrypted audio...
  Sent encrypted_audio: 88200 bytes (attempt 1)
  ✓ encrypted_audio acknowledged

[2/2] Sending drive signal...
  Sent drive_signal: 352800 bytes (attempt 1)
  ✓ drive_signal acknowledged

================================================================================
✓ TRANSMISSION COMPLETE
================================================================================

✓✓✓ TRANSMISSION SUCCESSFUL ✓✓✓
```

**Expected Output (Board 2):**
```
================================================================================
STEP 1: UART RECEPTION
================================================================================
✓ UART Receiver connected on /dev/ttyPS1 at 115200 baud

[1/2] Receiving encrypted audio...
  Waiting for encrypted_audio...
  ✓ encrypted_audio received: 88200 bytes

[2/2] Receiving drive signal...
  Waiting for drive_signal...
  ✓ drive_signal received: 352800 bytes

================================================================================
✓ RECEPTION COMPLETE
================================================================================

================================================================================
STEP 2: DECRYPTION
================================================================================
Secret key loaded: x0=0.1, y0=0.0, z0=0.0
Generating synchronized keystream...
Decrypting audio...
Decrypted audio saved to: decrypted_audio.wav

Performance Metrics:
  Pearson Correlation: 1.000000
  Bit Error Rate (BER): 0.000000e+00 (0.0000%)
  Mean Squared Error (MSE): 0.00

✓✓✓ DECRYPTION SUCCESSFUL ✓✓✓
Correlation: 1.000000
BER: 0.000000e+00 (0.0000%)
```

---

## 📊 Phase 5: Performance Validation

### Step 5.1: Measure Performance Metrics

**Create Performance Test Script:**

**File: `chaos_secure_communication/test_uart_performance.py`**

```python
"""
UART Performance Testing Script
Measures correlation, BER, latency, and throughput
"""

import time
import numpy as np
from scipy.io import wavfile
from scipy.stats import pearsonr

def test_performance(original_audio_path, decrypted_audio_path):
    """
    Comprehensive performance testing
    """
    print("\n" + "="*80)
    print("PERFORMANCE VALIDATION")
    print("="*80)
    
    # Load audio files
    sr_orig, audio_orig = wavfile.read(original_audio_path)
    sr_dec, audio_dec = wavfile.read(decrypted_audio_path)
    
    # Ensure same length
    min_len = min(len(audio_orig), len(audio_dec))
    audio_orig = audio_orig[:min_len]
    audio_dec = audio_dec[:min_len]
    
    # 1. Pearson Correlation
    correlation, _ = pearsonr(audio_orig, audio_dec)
    
    # 2. Bit Error Rate
    audio_orig_u16 = audio_orig.view(np.uint16)
    audio_dec_u16 = audio_dec.view(np.uint16)
    bit_errors = np.sum(np.unpackbits(
        np.bitwise_xor(audio_orig_u16, audio_dec_u16).view(np.uint8)
    ))
    total_bits = audio_orig_u16.size * 16
    ber = bit_errors / total_bits
    
    # 3. Mean Squared Error
    mse = np.mean((audio_orig.astype(float) - audio_dec.astype(float)) ** 2)
    
    # 4. Signal-to-Noise Ratio
    signal_power = np.mean(audio_orig.astype(float) ** 2)
    noise_power = np.mean((audio_orig.astype(float) - audio_dec.astype(float)) ** 2)
    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
    
    # Print results
    print("\n" + "-"*80)
    print("PERFORMANCE METRICS")
    print("-"*80)
    print(f"Pearson Correlation:  {correlation:.10f}")
    print(f"Bit Error Rate (BER): {ber:.10e} ({ber*100:.6f}%)")
    print(f"Mean Squared Error:   {mse:.6f}")
    print(f"Signal-to-Noise Ratio: {snr:.2f} dB")
    print("-"*80)
    
    # Assessment
    print("\nPERFORMANCE ASSESSMENT:")
    
    if correlation >= 0.999:
        print("  ✓✓✓ Correlation: PERFECT (≥0.999)")
    elif correlation >= 0.95:
        print("  ✓✓  Correlation: EXCELLENT (≥0.95)")
    else:
        print("  ✗   Correlation: POOR (<0.95)")
    
    if ber < 0.0001:
        print("  ✓✓✓ BER: PERFECT (<0.01%)")
    elif ber < 0.01:
        print("  ✓✓  BER: EXCELLENT (<1%)")
    else:
        print("  ✗   BER: POOR (≥1%)")
    
    if mse < 1.0:
        print("  ✓✓✓ MSE: PERFECT (<1.0)")
    elif mse < 100.0:
        print("  ✓✓  MSE: GOOD (<100)")
    else:
        print("  ✗   MSE: POOR (≥100)")
    
    print("\n" + "="*80)
    
    # Overall assessment
    if correlation >= 0.95 and ber < 0.01:
        print("✓✓✓ SYSTEM PERFORMANCE: EXCELLENT ✓✓✓")
        print("Ready for thesis demonstration!")
    else:
        print("✗✗✗ SYSTEM PERFORMANCE: NEEDS IMPROVEMENT ✗✗✗")
        print("Check synchronization and UART connection")
    
    print("="*80)
    
    return {
        'correlation': correlation,
        'ber': ber,
        'mse': mse,
        'snr': snr
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python test_uart_performance.py <original.wav> <decrypted.wav>")
        sys.exit(1)
    
    test_performance(sys.argv[1], sys.argv[2])
```

**Run Performance Test:**
```bash
# On Board 2 (after successful decryption)
python3 ../test_uart_performance.py ../test_audio/test_tone.wav decrypted_audio.wav
```

### Step 5.2: Compare Chua vs Rössler Performance

**Create Comparison Script:**

**File: `chaos_secure_communication/compare_systems.py`**

```python
"""
Compare Chua Circuit vs Rössler System Performance
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.stats import pearsonr

def compare_systems():
    """
    Generate comparison table and plots
    """
    print("\n" + "="*80)
    print("CHUA CIRCUIT vs RÖSSLER SYSTEM COMPARISON")
    print("="*80)
    
    # Test both systems
    systems = ['chua', 'rossler']
    results = {}
    
    for system in systems:
        print(f"\nTesting {system.upper()} system...")
        
        # Load decrypted audio
        sr, audio_dec = wavfile.read(f'{system}_system/decrypted_audio.wav')
        sr_orig, audio_orig = wavfile.read('test_audio/test_tone.wav')
        
        # Calculate metrics
        min_len = min(len(audio_orig), len(audio_dec))
        correlation, _ = pearsonr(audio_orig[:min_len], audio_dec[:min_len])
        
        audio_orig_u16 = audio_orig[:min_len].view(np.uint16)
        audio_dec_u16 = audio_dec[:min_len].view(np.uint16)
        bit_errors = np.sum(np.unpackbits(
            np.bitwise_xor(audio_orig_u16, audio_dec_u16).view(np.uint8)
        ))
        ber = bit_errors / (audio_orig_u16.size * 16)
        
        mse = np.mean((audio_orig[:min_len].astype(float) - 
                       audio_dec[:min_len].astype(float)) ** 2)
        
        results[system] = {
            'correlation': correlation,
            'ber': ber,
            'mse': mse
        }
    
    # Print comparison table
    print("\n" + "-"*80)
    print("PERFORMANCE COMPARISON TABLE")
    print("-"*80)
    print(f"{'Metric':<25} {'Chua Circuit':<20} {'Rössler System':<20}")
    print("-"*80)
    print(f"{'Correlation':<25} {results['chua']['correlation']:.10f}   {results['rossler']['correlation']:.10f}")
    print(f"{'BER (%)':<25} {results['chua']['ber']*100:.6f}%        {results['rossler']['ber']*100:.6f}%")
    print(f"{'MSE':<25} {results['chua']['mse']:.6f}         {results['rossler']['mse']:.6f}")
    print("-"*80)
    
    # Characteristics comparison
    print("\nSYSTEM CHARACTERISTICS:")
    print("-"*80)
    print(f"{'Feature':<25} {'Chua Circuit':<20} {'Rössler System':<20}")
    print("-"*80)
    print(f"{'Attractor Type':<25} {'Double-scroll':<20} {'Spiral':<20}")
    print(f"{'Time Step (dt)':<25} {'0.01':<20} {'0.05':<20}")
    print(f"{'Nonlinearity':<25} {'Piecewise diode':<20} {'Bilinear z(x-c)':<20}")
    print(f"{'Sync Speed':<25} {'Fast':<20} {'Moderate':<20}")
    print(f"{'Implementation':<25} {'Moderate':<20} {'Simpler':<20}")
    print("-"*80)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    compare_systems()
```

---

## 🔍 Troubleshooting Guide

### Issue 1: UART Connection Failed


    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
    
    # Print results
    print("\n" + "-"*80)
    print("PERFORMANCE METRICS")
    print("-"*80)
    print(f"Pearson Correlation:  {correlation:.10f}")
    print(f"Bit Error Rate (BER): {ber:.10e} ({ber*100:.6f}%)")
    print(f"Mean Squared Error:   {mse:.6f}")
    print(f"Signal-to-Noise Ratio: {snr:.2f} dB")
    print("-"*80)
    
    # Assessment
    print("\nPERFORMANCE ASSESSMENT:")
    
    if correlation >= 0.999:
        print("  ✓✓✓ Correlation: PERFECT (≥0.999)")
    elif correlation >= 0.95:
        print("  ✓✓  Correlation: EXCELLENT (≥0.95)")
    else:
        print("  ✗   Correlation: POOR (<0.95)")
    
    if ber < 0.0001:
        print("  ✓✓✓ BER: PERFECT (<0.01%)")
    elif ber < 0.01:
        print("  ✓✓  BER: EXCELLENT (<1%)")
    else:
        print("  ✗   BER: POOR (≥1%)")
    
    if mse < 1.0:
        print("  ✓✓✓ MSE: PERFECT (<1.0)")
    elif mse < 100.0:
        print("  ✓✓  MSE: GOOD (<100)")
    else:
        print("  ✗   MSE: POOR (≥100)")
    
    print("\n" + "="*80)
    
    # Overall assessment
    if correlation >= 0.95 and ber < 0.01:
        print("✓✓✓ SYSTEM PERFORMANCE: EXCELLENT ✓✓✓")
        print("Ready for thesis demonstration!")
    else:
        print("✗✗✗ SYSTEM PERFORMANCE: NEEDS IMPROVEMENT ✗✗✗")
        print("Check synchronization and UART connection")
    
    print("="*80)
    
    return {
        'correlation': correlation,
        'ber': ber,
        'mse': mse,
        'snr': snr
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python test_uart_performance.py <original.wav> <decrypted.wav>")
        sys.exit(1)
    
    test_performance(sys.argv[1], sys.argv[2])
```

**Run Performance Test:**
```bash
# On Board 2 (after successful decryption)
python3 ../test_uart_performance.py ../test_audio/test_tone.wav decrypted_audio.wav
```

### Step 5.2: Compare Chua vs Rössler Performance

**Create Comparison Script:**

**File: `chaos_secure_communication/compare_systems.py`**

```python
"""
Compare Chua Circuit vs Rössler System Performance
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.stats import pearsonr

def compare_systems():
    """
    Generate comparison table and plots
    """
    print("\n" + "="*80)
    print("CHUA CIRCUIT vs RÖSSLER SYSTEM COMPARISON")
    print("="*80)
    
    # Test both systems
    systems = ['chua', 'rossler']
    results = {}
    
    for system in systems:
        print(f"\nTesting {system.upper()} system...")
        
        # Load decrypted audio
        sr, audio_dec = wavfile.read(f'{system}_system/decrypted_audio.wav')
        sr_orig, audio_orig = wavfile.read('test_audio/test_tone.wav')
        
        # Calculate metrics
        min_len = min(len(audio_orig), len(audio_dec))
        correlation, _ = pearsonr(audio_orig[:min_len], audio_dec[:min_len])
        
        audio_orig_u16 = audio_orig[:min_len].view(np.uint16)
        audio_dec_u16 = audio_dec[:min_len].view(np.uint16)
        bit_errors = np.sum(np.unpackbits(
            np.bitwise_xor(audio_orig_u16, audio_dec_u16).view(np.uint8)
        ))
        ber = bit_errors / (audio_orig_u16.size * 16)
        
        mse = np.mean((audio_orig[:min_len].astype(float) - 
                       audio_dec[:min_len].astype(float)) ** 2)
        
        results[system] = {
            'correlation': correlation,
            'ber': ber,
            'mse': mse
        }
    
    # Print comparison table
    print("\n" + "-"*80)
    print("PERFORMANCE COMPARISON TABLE")
    print("-"*80)
    print(f"{'Metric':<25} {'Chua Circuit':<20} {'Rössler System':<20}")
    print("-"*80)
    print(f"{'Correlation':<25} {results['chua']['correlation']:.10f}   {results['rossler']['correlation']:.10f}")
    print(f"{'BER (%)':<25} {results['chua']['ber']*100:.6f}%        {results['rossler']['ber']*100:.6f}%")
    print(f"{'MSE':<25} {results['chua']['mse']:.6f}         {results['rossler']['mse']:.6f}")
    print("-"*80)
    
    # Characteristics comparison
    print("\nSYSTEM CHARACTERISTICS:")
    print("-"*80)
    print(f"{'Feature':<25} {'Chua Circuit':<20} {'Rössler System':<20}")
    print("-"*80)
    print(f"{'Attractor Type':<25} {'Double-scroll':<20} {'Spiral':<20}")
    print(f"{'Time Step (dt)':<25} {'0.01':<20} {'0.05':<20}")
    print(f"{'Nonlinearity':<25} {'Piecewise diode':<20} {'Bilinear z(x-c)':<20}")
    print(f"{'Sync Speed':<25} {'Fast':<20} {'Moderate':<20}")
    print(f"{'Implementation':<25} {'Moderate':<20} {'Simpler':<20}")
    print("-"*80)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    compare_systems()
```

---

## 🔍 Troubleshooting Guide

### Issue 1: UART Connection Failed

**Symptoms:**
```
✗ Failed to connect UART: [Errno 2] No such file or directory: '/dev/ttyPS1'
```

**Solutions:**
1. **Check UART device:**
   ```bash
   ls -l /dev/tty*
   # Look for ttyPS0, ttyPS1, or ttyUSB0
   ```

2. **Verify permissions:**
   ```bash
   sudo chmod 666 /dev/ttyPS1
   # Or add user to dialout group
   sudo usermod -a -G dialout xilinx
   ```

3. **Check if device is in use:**
   ```bash
   lsof /dev/ttyPS1
   # Kill any processes using the port
   ```

### Issue 2: Data Corruption During UART Transmission

**Symptoms:**
```
✗ Checksum verification failed
Received checksum: 0x12345678
Calculated checksum: 0x87654321
```

**Solutions:**
1. **Reduce baud rate:**
   ```python
   # In uart_config.py
   BAUD_RATE = 57600  # Try lower rate
   ```

2. **Add delays between packets:**
   ```python
   time.sleep(0.1)  # 100ms delay
   ```

3. **Check physical connections:**
   - Verify TX-RX crossover
   - Check ground connection
   - Ensure no loose wires

### Issue 3: Poor Decryption Quality (Correlation < 0.95)

**Symptoms:**
```
Pearson Correlation: 0.523456
✗ Correlation: POOR (<0.95)
```

**Solutions:**
1. **Verify secret key matches:**
   ```bash
   # Compare secret keys on both boards
   cat encrypted_audio_secret_key.txt
   ```

2. **Check drive signal integrity:**
   ```python
   # Verify drive signal received correctly
   drive_rx = np.load('received_drive_signal.npy')
   drive_tx = np.load('encrypted_audio_drive_signal.npy')
   print(f"Match: {np.allclose(drive_rx, drive_tx)}")
   ```

3. **Resynchronize systems:**
   - Restart both boards
   - Re-run encryption and decryption
   - Ensure same parameters used

### Issue 4: Board Not Responding

**Symptoms:**
```
ssh: connect to host 192.168.2.99 port 22: Connection refused
```

**Solutions:**
1. **Check board power:**
   - Verify green LED is solid (not blinking)
   - Check USB power supply (use powered hub if needed)

2. **Verify network connection:**
   ```bash
   ping 192.168.2.99
   # If no response, check Ethernet cable
   ```

3. **Reset board:**
   - Press reset button on PYNQ-Z2
   - Wait 30 seconds for boot
   - Try SSH again

### Issue 5: Out of Memory Error

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. **Process shorter audio files:**
   ```python
   # Limit audio duration
   max_samples = 44100  # 1 second at 44.1kHz
   audio = audio[:max_samples]
   ```

2. **Increase swap space:**
   ```bash
   sudo dd if=/dev/zero of=/swapfile bs=1M count=512
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Use streaming approach:**
   - Process audio in chunks
   - Send/receive in smaller packets

### Issue 6: Matplotlib Display Issues

**Symptoms:**
```
UserWarning: Matplotlib is currently using agg, which is a non-GUI backend
```

**Solutions:**
1. **Save plots instead of displaying:**
   ```python
   plt.savefig('plot.png')
   # Instead of plt.show()
   ```

2. **Disable visualization:**
   ```python
   encryptor.encrypt_audio('input.wav', visualize=False)
   decryptor.decrypt_audio('encrypted.wav', visualize=False)
   ```

---

## ✅ Success Criteria

### Minimum Requirements (Pass)
- ✅ Both boards boot and communicate
- ✅ Encryption completes without errors
- ✅ UART transmission successful
- ✅ Decryption completes without errors
- ✅ Correlation ≥ 0.95
- ✅ BER < 1%

### Excellent Performance (Thesis-Ready)
- ✅ Correlation ≥ 0.999 (near-perfect)
- ✅ BER < 0.01% (minimal errors)
- ✅ MSE < 1.0 (negligible distortion)
- ✅ Synchronization error → 0
- ✅ Real-time processing capability
- ✅ Reproducible results across multiple runs

### Demonstration Checklist
- [ ] Both systems (Chua & Rössler) working
- [ ] Performance metrics documented
- [ ] Comparison table generated
- [ ] Visualization plots created
- [ ] Audio files playable and verified
- [ ] Backup plan prepared (pre-recorded results)
- [ ] Troubleshooting guide available
- [ ] Team members trained on operation

---

## 📚 Additional Resources

### PYNQ Documentation
- Official PYNQ Docs: http://pynq.readthedocs.io/
- PYNQ-Z2 Board Guide: http://www.pynq.io/board.html
- PYNQ Community Forum: https://discuss.pynq.io/

### Chaos Theory References
1. Chua, L. O. (1992). "The Genesis of Chua's Circuit"
2. Rössler, O. E. (1976). "An Equation for Continuous Chaos"
3. Pecora, L. M., & Carroll, T. L. (1990). "Synchronization in Chaotic Systems"

### UART Communication
- PySerial Documentation: https://pyserial.readthedocs.io/
- UART Protocol Design: https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter

---

## 🎓 For Thesis Defense

### Key Points to Emphasize

1. **Security:**
   - Encrypted signal exhibits broadband chaotic characteristics
   - Impossible to decrypt without secret key
   - Spectrogram shows noise-like properties

2. **Synchronization:**
   - Pecora-Carroll method achieves perfect sync
   - Drive signal enables receiver to regenerate keystream
   - Synchronization error converges to zero

3. **Performance:**
   - Near-perfect correlation (≥0.999)
   - Zero bit errors (BER ≈ 0%)
   - Lossless audio recovery

4. **Implementation:**
   - Successfully deployed on FPGA hardware
   - Real-time processing capability
   - Two-board communication via UART

### Sample Presentation Script

> "We implemented a chaos-based secure communication system using two different chaotic oscillators: the Chua Circuit and Rössler System. Both systems were deployed on PYNQ-Z2 FPGA boards with UART communication between transmitter and receiver.
>
> The transmitter generates a chaotic keystream and encrypts audio using bitwise XOR. The encrypted signal, as shown in the spectrogram, exhibits broadband noise characteristics, making it cryptographically secure.
>
> The receiver uses Pecora-Carroll synchronization, where the transmitter's x-state drives the receiver's chaotic oscillator. This enables the receiver to independently regenerate the matching keystream and decrypt the audio.
>
> Our results demonstrate perfect synchronization with correlation coefficients of 1.0 and bit error rates of 0%, validating both the security and reliability of chaos-based encryption for real-time audio communication."

---

## 📞 Support Contacts

**Thesis Advisor:** [Your Advisor's Name]  
**Lab Technician:** [Lab Contact]  
**Team Leads:**
- Chua Circuit: Barria & Jusay
- Rössler System: Cortes & Abalos

---

## 📝 Version History

- **v1.0** (June 2026) - Initial deployment guide
- PC testing completed with perfect results
- UART implementation specifications defined
- Ready for PYNQ-Z2 deployment

---

## 🎉 Final Notes

This guide provides a complete roadmap from PC testing to full PYNQ-Z2 deployment with UART communication. Follow each phase systematically, verify results at each step, and document your progress.

**Remember:**
- Test thoroughly on single board before two-board integration
- Keep backup of working code and results
- Document any issues and solutions
- Practice demonstration multiple times
- Have contingency plan ready

**Good luck with your thesis defense! 🎓**

---

**De La Salle University**  
**Electronics and Communications Engineering**  
**FPGA Implementation of Chaos-Based Secure Communication**  
**Using Chua Circuit and Rössler System**
