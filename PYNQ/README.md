# 🚀 PYNQ-Z2 Implementation Files

## Overview

This folder contains all the files needed to deploy the chaos-based secure communication system on PYNQ-Z2 FPGA boards with UART communication.

## 📁 Folder Structure

```
PYNQ/
├── README.md                           # This file
├── PYNQ_DEPLOYMENT_GUIDE.md           # Complete deployment guide
├── uart_lib/                          # UART communication library
│   ├── __init__.py                    # Package initializer
│   ├── uart_config.py                 # UART configuration
│   ├── uart_protocol.py               # Protocol with CRC32
│   ├── uart_transmitter.py            # Transmitter implementation
│   └── uart_receiver.py               # Receiver implementation
├── uart_chua_transmitter.py           # Chua transmitter with UART
├── uart_chua_receiver.py              # Chua receiver with UART
├── uart_rossler_transmitter.py        # Rössler transmitter with UART
├── uart_rossler_receiver.py           # Rössler receiver with UART
├── test_uart_performance.py           # Performance testing script
└── compare_systems.py                 # Chua vs Rössler comparison
```

## 🎯 Quick Start

### 1. Read the Deployment Guide
Start with `PYNQ_DEPLOYMENT_GUIDE.md` for complete step-by-step instructions.

### 2. Transfer Files to PYNQ Boards
```bash
# Transfer entire PYNQ folder to both boards
scp -r PYNQ xilinx@192.168.2.99:/home/xilinx/chaos_secure_communication/
scp -r PYNQ xilinx@192.168.2.100:/home/xilinx/chaos_secure_communication/
```

### 3. Install Dependencies
```bash
# On both boards
ssh xilinx@192.168.2.99
sudo pip3 install pyserial
```

### 4. Run Two-Board Test

**Board 1 (Transmitter):**
```bash
cd /home/xilinx/chaos_secure_communication/PYNQ
python3 uart_chua_transmitter.py ../test_audio/test_tone.wav
```

**Board 2 (Receiver):**
```bash
cd /home/xilinx/chaos_secure_communication/PYNQ
python3 uart_chua_receiver.py ../test_audio/test_tone.wav
```

## 📋 File Descriptions

### UART Library (`uart_lib/`)

**`uart_config.py`**
- UART port configuration
- Baud rate settings (115200 default)
- Protocol parameters
- GPIO pin definitions

**`uart_protocol.py`**
- Packet structure with CRC32 checksums
- Frame format: [HEADER][LENGTH][DATA][CRC32]
- ACK/NACK handling
- Error detection

**`uart_transmitter.py`**
- Send encrypted audio and drive signal
- Automatic retransmission on failure
- Progress monitoring
- Connection management

**`uart_receiver.py`**
- Receive encrypted audio and drive signal
- Checksum verification
- Buffer management
- Error handling

### Integration Scripts

**`uart_chua_transmitter.py`**
- Integrates Chua encryption with UART transmission
- Encrypts audio → Sends via UART
- For Board 1 (Transmitter)

**`uart_chua_receiver.py`**
- Integrates UART reception with Chua decryption
- Receives via UART → Decrypts audio
- For Board 2 (Receiver)

**`uart_rossler_transmitter.py`**
- Same as Chua but for Rössler system
- For Board 1 (Transmitter)

**`uart_rossler_receiver.py`**
- Same as Chua but for Rössler system
- For Board 2 (Receiver)

### Testing Scripts

**`test_uart_performance.py`**
- Measures correlation, BER, MSE, SNR
- Validates system performance
- Generates performance report

**`compare_systems.py`**
- Compares Chua vs Rössler performance
- Generates comparison tables
- For thesis documentation

## 🔌 Hardware Setup

### UART Pin Connections

```
Board 1 (TX)          Board 2 (RX)
PMOD JB Pin 1  ────── PMOD JB Pin 1
PMOD JB Pin 5  ────── PMOD JB Pin 5 (GND)
```

### Connection Steps
1. Power off both boards
2. Connect TX to RX using jumper wires
3. Connect GND to GND
4. Verify connections with multimeter
5. Power on both boards

## ✅ Success Criteria

### Minimum (Pass)
- ✅ UART connection established
- ✅ Data transmitted successfully
- ✅ Correlation ≥ 0.95
- ✅ BER < 1%

### Excellent (Thesis-Ready)
- ✅ Correlation ≥ 0.999
- ✅ BER < 0.01%
- ✅ MSE < 1.0
- ✅ Real-time processing

## 🐛 Troubleshooting

### UART Connection Failed
```bash
# Check UART devices
ls -l /dev/tty*

# Fix permissions
sudo chmod 666 /dev/ttyPS1
```

### Data Corruption
- Reduce baud rate in `uart_config.py`
- Check physical connections
- Add delays between packets

### Poor Decryption Quality
- Verify secret key matches
- Check drive signal integrity
- Ensure same parameters used

## 📚 Documentation

- **Full Guide:** `PYNQ_DEPLOYMENT_GUIDE.md`
- **Main README:** `../documentation/README.md`
- **How to Run:** `../documentation/HOW_TO_RUN.md`

## 🎓 For Thesis

This implementation demonstrates:
- ✅ FPGA-based chaos encryption
- ✅ Real-time audio processing
- ✅ Board-to-board UART communication
- ✅ Pecora-Carroll synchronization
- ✅ Perfect decryption (Correlation ≈ 1.0)

## 📞 Support

**Team:**
- Chua Circuit: Barria & Jusay
- Rössler System: Cortes & Abalos

**Institution:** De La Salle University  
**Program:** Electronics and Communications Engineering

---

**Ready to deploy! Follow PYNQ_DEPLOYMENT_GUIDE.md for detailed instructions.** 🚀