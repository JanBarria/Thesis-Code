"""
UART Receiver for PYNQ-Z2
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

This module implements the receiver side of UART communication,
receiving encrypted audio and drive signals from the transmitter board.
"""

import serial
import numpy as np
import time
import struct
from .uart_protocol import UARTProtocol
from .uart_config import *


class UARTReceiver:
    """
    UART receiver for chaos-based encrypted communication
    
    Handles reception of encrypted audio and chaotic drive signals
    from transmitter board with error checking and acknowledgments.
    """
    
    def __init__(self, port=UART_PORT_RX, baud_rate=BAUD_RATE):
        """
        Initialize UART receiver
        
        Args:
            port (str): UART port device path (default: /dev/ttyPS1)
            baud_rate (int): Communication speed in bps (default: 115200)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.bytes_received = 0
        self.packets_received = 0
        self.errors = 0
        
    def connect(self):
        """
        Open UART connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT,
                xonxoff=XON_XOFF,
                rtscts=FLOW_CONTROL
            )
            print(f"✓ UART Receiver connected on {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            print(f"✗ Failed to connect UART: {e}")
            return False
    
    def receive_data(self, data_type='data', expected_dtype=np.int16):
        """
        Receive data with error checking
        
        Args:
            data_type (str): Description of data being received
            expected_dtype: Expected numpy dtype for conversion
            
        Returns:
            numpy array of received data, or None if failed
        """
        print(f"  Waiting for {data_type}...")
        
        try:
            # Read header
            header = self.serial.read(4)
            if len(header) < 4:
                print(f"  ✗ Timeout waiting for header")
                self.serial.write(UARTProtocol.create_nack())
                self.errors += 1
                return None
            
            if header != UARTProtocol.HEADER:
                print(f"  ✗ Invalid header: {header.hex()}")
                self.serial.write(UARTProtocol.create_nack())
                self.errors += 1
                return None
            
            # Read length
            length_bytes = self.serial.read(4)
            if len(length_bytes) < 4:
                print(f"  ✗ Timeout waiting for length")
                self.serial.write(UARTProtocol.create_nack())
                self.errors += 1
                return None
            
            length = struct.unpack('<I', length_bytes)[0]
            
            if DEBUG_MODE:
                print(f"  Receiving {length} bytes...")
            
            # Read data
            data_bytes = b''
            bytes_remaining = length
            read_start = time.time()
            
            while bytes_remaining > 0:
                if time.time() - read_start > TIMEOUT * 2:
                    print(f"  ✗ Timeout receiving data")
                    self.serial.write(UARTProtocol.create_nack())
                    self.errors += 1
                    return None
                
                chunk = self.serial.read(min(bytes_remaining, CHUNK_SIZE))
                if chunk:
                    data_bytes += chunk
                    bytes_remaining -= len(chunk)
                    if DEBUG_MODE and len(data_bytes) % 10000 == 0:
                        print(f"    Received {len(data_bytes)}/{length} bytes...")
            
            # Read checksum
            checksum_bytes = self.serial.read(4)
            if len(checksum_bytes) < 4:
                print(f"  ✗ Timeout waiting for checksum")
                self.serial.write(UARTProtocol.create_nack())
                self.errors += 1
                return None
            
            # Reconstruct packet
            packet = header + length_bytes + data_bytes + checksum_bytes
            
            # Parse and verify
            data, valid = UARTProtocol.parse_packet(packet)
            
            if valid:
                print(f"  ✓ {data_type} received: {len(data)} bytes")
                # Send ACK
                self.serial.write(UARTProtocol.create_ack())
                self.serial.flush()
                
                self.bytes_received += len(data)
                self.packets_received += 1
                
                # Convert bytes to numpy array
                return np.frombuffer(data, dtype=expected_dtype)
            else:
                print(f"  ✗ Checksum verification failed")
                # Send NACK
                self.serial.write(UARTProtocol.create_nack())
                self.errors += 1
                return None
                
        except Exception as e:
            print(f"  ✗ Reception error: {e}")
            try:
                self.serial.write(UARTProtocol.create_nack())
            except:
                pass
            self.errors += 1
            return None
    
    def receive_encrypted_audio(self):
        """
        Receive encrypted audio and drive signal
        
        Returns:
            tuple: (encrypted_audio, drive_signal) or (None, None) if failed
        """
        print("\n" + "="*80)
        print("UART RECEPTION")
        print("="*80)
        
        # Receive encrypted audio (int16)
        print("\n[1/2] Receiving encrypted audio...")
        encrypted_audio = self.receive_data('encrypted_audio', np.int16)
        
        if encrypted_audio is None:
            print("\n" + "="*80)
            print("✗ RECEPTION FAILED - Encrypted audio not received")
            print("="*80)
            return None, None
        
        # Receive drive signal (float64)
        print("\n[2/2] Receiving drive signal...")
        drive_signal = self.receive_data('drive_signal', np.float64)
        
        if encrypted_audio is not None and drive_signal is not None:
            print("\n" + "="*80)
            print("✓ RECEPTION COMPLETE")
            print("="*80)
            print(f"Encrypted audio: {len(encrypted_audio)} samples")
            print(f"Drive signal: {len(drive_signal)} samples")
            print(f"Total bytes received: {self.bytes_received}")
            print(f"Total packets received: {self.packets_received}")
            print(f"Errors: {self.errors}")
            print("="*80)
            return encrypted_audio, drive_signal
        else:
            print("\n" + "="*80)
            print("✗ RECEPTION FAILED")
            print("="*80)
            return None, None
    
    def get_statistics(self):
        """
        Get reception statistics
        
        Returns:
            dict: Statistics including bytes received, packets received, errors
        """
        return {
            'bytes_received': self.bytes_received,
            'packets_received': self.packets_received,
            'errors': self.errors,
            'success_rate': (self.packets_received - self.errors) / max(1, self.packets_received)
        }
    
    def disconnect(self):
        """Close UART connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✓ UART Receiver disconnected")


# Test the receiver
if __name__ == "__main__":
    print("="*80)
    print("UART RECEIVER TEST")
    print("="*80)
    print("\nWaiting for transmitter to send data...")
    print("(Run uart_transmitter.py on the other board)")
    
    # Initialize receiver
    print("\nInitializing receiver...")
    rx = UARTReceiver()
    
    if rx.connect():
        print("\nListening for data...")
        encrypted_audio, drive_signal = rx.receive_encrypted_audio()
        
        if encrypted_audio is not None and drive_signal is not None:
            print("\n✓✓✓ TEST PASSED ✓✓✓")
            print(f"\nReceived data:")
            print(f"  Encrypted audio: {len(encrypted_audio)} samples")
            print(f"  Drive signal: {len(drive_signal)} samples")
            
            stats = rx.get_statistics()
            print(f"\nStatistics:")
            print(f"  Bytes received: {stats['bytes_received']}")
            print(f"  Packets received: {stats['packets_received']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Success rate: {stats['success_rate']*100:.2f}%")
        else:
            print("\n✗✗✗ TEST FAILED ✗✗✗")
        
        rx.disconnect()
    else:
        print("\n✗✗✗ CONNECTION FAILED ✗✗✗")
    
    print("\n" + "="*80)

# Made with Bob
