#!/usr/bin/env python3
"""
slave_control.py - SLAVE Board Control Script for Chaos Synchronization

This script runs on the SLAVE PYNQ-Z2 board. It:
1. Initializes the Rossler oscillator with sync_enable=1 (driven by x_drive)
2. Receives x_state values from MASTER over UART
3. Writes received x values to x_drive register
4. Steps the chaos evolution synchronized with MASTER
5. Logs time-series data for synchronization analysis

Hardware: PYNQ-Z2 with chaos_sync_slave.bit loaded
UART: /dev/ttyPS1 (EMIO, connected to PMOD A)
"""

import time
import struct
import numpy as np
from pynq import Overlay, MMIO
from pynq.lib import AxiGPIO
import serial
import threading

# Configuration
BITSTREAM_PATH = "/home/xilinx/chaos_sync_slave.bit"
UART_PORT = "/dev/ttyPS1"
UART_BAUD = 115200
DURATION_SEC = 10    # Data collection duration
OUTPUT_FILE = "slave_data.csv"

# AXI GPIO base addresses (from Vivado address editor)
GPIO0_ADDR = 0x41200000  # Control/Status
GPIO1_ADDR = 0x41210000  # x_drive
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

class SlaveController:
    def __init__(self):
        print("Initializing SLAVE board...")
        
        # Load bitstream
        print(f"Loading bitstream: {BITSTREAM_PATH}")
        self.overlay = Overlay(BITSTREAM_PATH)
        
        # Initialize AXI GPIO
        print("Initializing AXI GPIO interfaces...")
        self.gpio0 = AxiGPIO(GPIO0_ADDR).channel1  # Control/Status
        self.gpio1 = AxiGPIO(GPIO1_ADDR).channel1  # x_drive
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
            timeout=0.1
        )
        
        # Data storage
        self.timestamps = []
        self.x_drive_values = []
        self.x_values = []
        self.y_values = []
        self.z_values = []
        
        # Thread control
        self.running = False
        self.uart_thread = None
        
        print("Initialization complete!")
    
    def reset_core(self):
        """Reset the chaos core"""
        print("Resetting chaos core...")
        # Set rst bit (bit 2)
        self.gpio0.write(0x04, 0xFFFFFFFF)
        time.sleep(0.01)
        # Clear rst, set sync_enable=1 (slave mode)
        self.gpio0.write(0x02, 0xFFFFFFFF)
        time.sleep(0.01)
        print("Reset complete. Slave mode (sync_enable=1)")
    
    def step_chaos(self):
        """Execute one chaos evolution step"""
        # Pulse state_step (bit 0), keep sync_enable=1 (bit 1)
        self.gpio0.write(0x03, 0xFFFFFFFF)
        time.sleep(0.000001)  # 1 us pulse
        self.gpio0.write(0x02, 0xFFFFFFFF)
    
    def write_x_drive(self, x_raw):
        """Write x_drive value"""
        self.gpio1.write(x_raw, 0xFFFFFFFF)
    
    def read_state(self):
        """Read current x, y, z state"""
        x_raw = self.gpio2.read()
        y_raw = self.gpio3.read()
        z_raw = self.gpio4.read()
        
        x = q16_to_float(x_raw)
        y = q16_to_float(y_raw)
        z = q16_to_float(z_raw)
        
        return x, y, z
    
    def uart_receiver_thread(self):
        """Background thread to receive x values from UART"""
        print("UART receiver thread started")
        
        while self.running:
            try:
                # Read 4 bytes (one x_state value)
                data = self.uart.read(4)
                
                if len(data) == 4:
                    # Unpack as little-endian unsigned int
                    x_raw = struct.unpack('<I', data)[0]
                    
                    # Write to x_drive register
                    self.write_x_drive(x_raw)
                    
                    # Step the chaos
                    self.step_chaos()
                    
                    # Read and log state
                    x, y, z = self.read_state()
                    x_drive = q16_to_float(x_raw)
                    
                    timestamp = time.time() - self.start_time
                    
                    self.timestamps.append(timestamp)
                    self.x_drive_values.append(x_drive)
                    self.x_values.append(x)
                    self.y_values.append(y)
                    self.z_values.append(z)
                    
                    # Progress indicator
                    if len(self.timestamps) % 1000 == 0:
                        print(f"  Samples: {len(self.timestamps)}, x_drive={x_drive:.4f}, x={x:.4f}, y={y:.4f}, z={z:.4f}")
                
            except serial.SerialException as e:
                print(f"UART error: {e}")
                break
            except Exception as e:
                print(f"Error in receiver thread: {e}")
                break
        
        print("UART receiver thread stopped")
    
    def run_experiment(self):
        """Run synchronization experiment"""
        print(f"\nStarting experiment:")
        print(f"  Duration: {DURATION_SEC} seconds")
        print(f"  Waiting for MASTER to transmit...")
        
        # Reset and initialize
        self.reset_core()
        time.sleep(0.1)
        
        # Clear UART buffer
        self.uart.reset_input_buffer()
        
        # Start receiver thread
        self.running = True
        self.start_time = time.time()
        self.uart_thread = threading.Thread(target=self.uart_receiver_thread)
        self.uart_thread.start()
        
        print("\nReceiving... (Press Ctrl+C to stop early)")
        
        try:
            # Wait for duration
            time.sleep(DURATION_SEC)
        except KeyboardInterrupt:
            print("\nExperiment stopped by user")
        finally:
            # Stop receiver thread
            self.running = False
            if self.uart_thread:
                self.uart_thread.join(timeout=2.0)
        
        elapsed = time.time() - self.start_time
        sample_count = len(self.timestamps)
        
        print(f"\nExperiment complete!")
        print(f"  Elapsed time: {elapsed:.2f} seconds")
        print(f"  Samples collected: {sample_count}")
        if sample_count > 0:
            print(f"  Actual rate: {sample_count/elapsed:.1f} Hz")
    
    def save_data(self):
        """Save collected data to CSV"""
        if len(self.timestamps) == 0:
            print("\nNo data to save!")
            return
        
        print(f"\nSaving data to {OUTPUT_FILE}...")
        
        data = np.column_stack([
            self.timestamps,
            self.x_drive_values,
            self.x_values,
            self.y_values,
            self.z_values
        ])
        
        np.savetxt(
            OUTPUT_FILE,
            data,
            delimiter=',',
            header='time,x_drive,x,y,z',
            comments='',
            fmt='%.6f'
        )
        
        print(f"Data saved: {len(self.timestamps)} samples")
    
    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")
        self.running = False
        if self.uart_thread and self.uart_thread.is_alive():
            self.uart_thread.join(timeout=2.0)
        if hasattr(self, 'uart') and self.uart.is_open:
            self.uart.close()
        print("Cleanup complete")

def main():
    """Main entry point"""
    print("="*60)
    print("SLAVE Board - Chaos Synchronization Experiment")
    print("="*60)
    
    controller = SlaveController()
    
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
