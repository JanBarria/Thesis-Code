#!/usr/bin/env python3
"""
master_control.py - MASTER Board Control Script for Chaos Synchronization

This script runs on the MASTER PYNQ-Z2 board. It:
1. Initializes the Rossler oscillator with sync_enable=0 (free-running)
2. Steps the chaos evolution at a controlled rate
3. Transmits x_state values over UART to the SLAVE board
4. Logs time-series data for synchronization analysis

Hardware: PYNQ-Z2 with chaos_sync_master.bit loaded
UART: /dev/ttyPS1 (EMIO, connected to PMOD A)
"""

import time
import struct
import numpy as np
from pynq import Overlay, MMIO
from pynq.lib import AxiGPIO
import serial

# Configuration
BITSTREAM_PATH = "/home/xilinx/chaos_sync_master.bit"
UART_PORT = "/dev/ttyPS1"
UART_BAUD = 115200
STEP_RATE_HZ = 1000  # Chaos evolution rate (1 kHz)
DURATION_SEC = 10    # Data collection duration
OUTPUT_FILE = "master_data.csv"

# AXI GPIO base addresses (from Vivado address editor)
GPIO0_ADDR = 0x41200000  # Control/Status
GPIO1_ADDR = 0x41210000  # x_drive (unused on master)
GPIO2_ADDR = 0x41220000  # x_out
GPIO3_ADDR = 0x41230000  # y_out
GPIO4_ADDR = 0x41240000  # z_out

# Q16.16 fixed-point conversion
def q16_to_float(val):
    """Convert Q16.16 fixed-point to float"""
    if val & 0x80000000:  # Negative
        val = val - 0x100000000
    return val / 65536.0

def float_to_q16(f):
    """Convert float to Q16.16 fixed-point"""
    return int(f * 65536) & 0xFFFFFFFF

class MasterController:
    def __init__(self):
        print("Initializing MASTER board...")
        
        # Load bitstream
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        self.overlay = Overlay(BITSTREAM_PATH)
        
        # Initialize AXI GPIO
        print("Initializing AXI GPIO interfaces...")
        self.gpio0 = AxiGPIO(GPIO0_ADDR).channel1  # Control/Status
        self.gpio2 = AxiGPIO(GPIO2_ADDR).channel1  # x_out
        self.gpio3 = AxiGPIO(GPIO3_ADDR).channel1  # y_out
        self.gpio4 = AxiGPIO(GPIO4_ADDR).channel1  # z_out
        
        # Initialize UART
        print(f"Opening UART: {UART_PORT} @ {UART_BAUD} baud")
        self.uart = serial.Serial(
            port=UART_PORT,
            baudrate=UART_BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.001
        )
        
        # Data storage
        self.timestamps = []
        self.x_values = []
        self.y_values = []
        self.z_values = []
        
        print("Initialization complete!")
    
    def reset_core(self):
        """Reset the chaos core"""
        print("Resetting chaos core...")
        # Set rst bit (bit 2)
        self.gpio0.write(0x04, 0xFFFFFFFF)
        time.sleep(0.01)
        # Clear rst, set sync_enable=0 (master mode)
        self.gpio0.write(0x00, 0xFFFFFFFF)
        time.sleep(0.01)
        print("Reset complete. Master mode (sync_enable=0)")
    
    def step_chaos(self):
        """Execute one chaos evolution step"""
        # Pulse state_step (bit 0)
        self.gpio0.write(0x01, 0xFFFFFFFF)
        time.sleep(0.000001)  # 1 us pulse
        self.gpio0.write(0x00, 0xFFFFFFFF)
    
    def read_state(self):
        """Read current x, y, z state"""
        x_raw = self.gpio2.read()
        y_raw = self.gpio3.read()
        z_raw = self.gpio4.read()
        
        x = q16_to_float(x_raw)
        y = q16_to_float(y_raw)
        z = q16_to_float(z_raw)
        
        return x, y, z, x_raw
    
    def transmit_x(self, x_raw):
        """Transmit x_state to slave over UART"""
        # Send as 4 bytes (little-endian)
        data = struct.pack('<I', x_raw)
        self.uart.write(data)
    
    def run_experiment(self):
        """Run synchronization experiment"""
        print(f"\nStarting experiment:")
        print(f"  Duration: {DURATION_SEC} seconds")
        print(f"  Step rate: {STEP_RATE_HZ} Hz")
        print(f"  Expected samples: {DURATION_SEC * STEP_RATE_HZ}")
        
        # Reset and initialize
        self.reset_core()
        time.sleep(0.1)
        
        # Calculate step period
        step_period = 1.0 / STEP_RATE_HZ
        
        # Run experiment
        start_time = time.time()
        next_step_time = start_time
        sample_count = 0
        
        print("\nRunning... (Press Ctrl+C to stop early)")
        
        try:
            while (time.time() - start_time) < DURATION_SEC:
                current_time = time.time()
                
                if current_time >= next_step_time:
                    # Step the chaos
                    self.step_chaos()
                    
                    # Read state
                    x, y, z, x_raw = self.read_state()
                    
                    # Transmit x to slave
                    self.transmit_x(x_raw)
                    
                    # Log data
                    self.timestamps.append(current_time - start_time)
                    self.x_values.append(x)
                    self.y_values.append(y)
                    self.z_values.append(z)
                    
                    sample_count += 1
                    
                    # Progress indicator
                    if sample_count % 1000 == 0:
                        print(f"  Samples: {sample_count}, x={x:.4f}, y={y:.4f}, z={z:.4f}")
                    
                    # Schedule next step
                    next_step_time += step_period
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.0001)
        
        except KeyboardInterrupt:
            print("\nExperiment stopped by user")
        
        elapsed = time.time() - start_time
        print(f"\nExperiment complete!")
        print(f"  Elapsed time: {elapsed:.2f} seconds")
        print(f"  Samples collected: {sample_count}")
        print(f"  Actual rate: {sample_count/elapsed:.1f} Hz")
    
    def save_data(self):
        """Save collected data to CSV"""
        print(f"\nSaving data to {OUTPUT_FILE}...")
        
        data = np.column_stack([
            self.timestamps,
            self.x_values,
            self.y_values,
            self.z_values
        ])
        
        np.savetxt(
            OUTPUT_FILE,
            data,
            delimiter=',',
            header='time,x,y,z',
            comments='',
            fmt='%.6f'
        )
        
        print(f"Data saved: {len(self.timestamps)} samples")
    
    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")
        if hasattr(self, 'uart') and self.uart.is_open:
            self.uart.close()
        print("Cleanup complete")

def main():
    """Main entry point"""
    print("="*60)
    print("MASTER Board - Chaos Synchronization Experiment")
    print("="*60)
    
    controller = MasterController()
    
    try:
        controller.run_experiment()
        controller.save_data()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        controller.cleanup()
    
    print("\nDone!")

if __name__ == "__main__":
    main()

# Made with Bob
