"""
UART Transmitter for PYNQ-Z2
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

This module implements the transmitter side of UART communication,
sending encrypted audio and drive signals to the receiver board.
"""

import serial
import numpy as np
import time
from .uart_protocol import UARTProtocol
from .uart_config import *


class UARTTransmitter:
    """
    UART transmitter for chaos-based encrypted communication
    
    Handles transmission of encrypted audio and chaotic drive signals
    from transmitter board to receiver board with error checking and
    automatic retransmission.
    """
    
    def __init__(self, port=UART_PORT_TX, baud_rate=BAUD_RATE):
        """
        Initialize UART transmitter
        
        Args:
            port (str): UART port device path (default: /dev/ttyPS1)
            baud_rate (int): Communication speed in bps (default: 115200)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.bytes_sent = 0
        self.packets_sent = 0
        self.retransmissions = 0
        
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
            print(f"✓ UART Transmitter connected on {self.port} at {self.baud_rate} baud")
            return True
        except Exception as e:
            print(f"✗ Failed to connect UART: {e}")
            return False
    
    def send_data(self, data, data_type='data'):
        """
        Send data with error checking and retransmission
        
        Args:
            data: bytes or numpy array to send
            data_type (str): Description of data being sent
            
        Returns:
            bool: True if transmission successful, False otherwise
        """
        # Convert numpy array to bytes if needed
        if isinstance(data, np.ndarray):
            data_bytes = data.tobytes()
        else:
            data_bytes = data
        
        # Create packet
        packet = UARTProtocol.create_packet(data_bytes)
        packet_size = len(packet)
        
        # Send with retries
        for attempt in range(MAX_RETRIES):
            try:
                # Send packet
                bytes_written = self.serial.write(packet)
                self.serial.flush()
                
                if DEBUG_MODE:
                    print(f"  Sent {data_type}: {len(data_bytes)} bytes "
                          f"(packet: {packet_size} bytes, attempt {attempt+1})")
                else:
                    print(f"  Sent {data_type}: {len(data_bytes)} bytes (attempt {attempt+1})")
                
                self.bytes_sent += bytes_written
                self.packets_sent += 1
                
                # Wait for ACK
                ack_start = time.time()
                ack_packet = b''
                
                while time.time() - ack_start < ACK_TIMEOUT:
                    if self.serial.in_waiting > 0:
                        ack_packet += self.serial.read(self.serial.in_waiting)
                        
                        # Check if we have enough data for ACK packet
                        if len(ack_packet) >= UARTProtocol.MIN_PACKET_SIZE:
                            if UARTProtocol.is_ack(ack_packet):
                                print(f"  ✓ {data_type} acknowledged")
                                return True
                            elif UARTProtocol.is_nack(ack_packet):
                                print(f"  ✗ NACK received, retrying...")
                                break
                    time.sleep(0.01)
                
                if not ack_packet:
                    print(f"  ✗ No ACK received, retrying...")
                
                self.retransmissions += 1
                time.sleep(RETRY_DELAY)
                
            except Exception as e:
                print(f"  ✗ Transmission error: {e}")
                time.sleep(RETRY_DELAY)
        
        print(f"  ✗ Failed to send {data_type} after {MAX_RETRIES} attempts")
        return False
    
    def send_encrypted_audio(self, encrypted_audio, drive_signal):
        """
        Send encrypted audio and drive signal
        
        Args:
            encrypted_audio: numpy array of encrypted audio samples (int16)
            drive_signal: numpy array of x state (drive signal) (float64)
            
        Returns:
            bool: True if both transmissions successful, False otherwise
        """
        print("\n" + "="*80)
        print("UART TRANSMISSION")
        print("="*80)
        print(f"Encrypted audio: {len(encrypted_audio)} samples")
        print(f"Drive signal: {len(drive_signal)} samples")
        print(f"Total data: {(len(encrypted_audio)*2 + len(drive_signal)*8)/1024:.2f} KB")
        
        # Send encrypted audio
        print("\n[1/2] Sending encrypted audio...")
        success_audio = self.send_data(encrypted_audio, 'encrypted_audio')
        
        if not success_audio:
            print("\n" + "="*80)
            print("✗ TRANSMISSION FAILED - Encrypted audio not sent")
            print("="*80)
            return False
        
        # Send drive signal
        print("\n[2/2] Sending drive signal...")
        success_drive = self.send_data(drive_signal, 'drive_signal')
        
        if success_audio and success_drive:
            print("\n" + "="*80)
            print("✓ TRANSMISSION COMPLETE")
            print("="*80)
            print(f"Total bytes sent: {self.bytes_sent}")
            print(f"Total packets sent: {self.packets_sent}")
            print(f"Retransmissions: {self.retransmissions}")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("✗ TRANSMISSION FAILED")
            print("="*80)
            return False
    
    def get_statistics(self):
        """
        Get transmission statistics
        
        Returns:
            dict: Statistics including bytes sent, packets sent, retransmissions
        """
        return {
            'bytes_sent': self.bytes_sent,
            'packets_sent': self.packets_sent,
            'retransmissions': self.retransmissions,
            'success_rate': (self.packets_sent - self.retransmissions) / max(1, self.packets_sent)
        }
    
    def disconnect(self):
        """Close UART connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("✓ UART Transmitter disconnected")


# Test the transmitter
if __name__ == "__main__":
    print("="*80)
    print("UART TRANSMITTER TEST")
    print("="*80)
    
    # Create test data
    print("\nCreating test data...")
    test_audio = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
    test_drive = np.random.randn(1000).astype(np.float64)
    
    print(f"Test audio: {len(test_audio)} samples ({len(test_audio)*2} bytes)")
    print(f"Test drive signal: {len(test_drive)} samples ({len(test_drive)*8} bytes)")
    
    # Initialize transmitter
    print("\nInitializing transmitter...")
    tx = UARTTransmitter()
    
    if tx.connect():
        print("\nSending test data...")
        success = tx.send_encrypted_audio(test_audio, test_drive)
        
        if success:
            print("\n✓✓✓ TEST PASSED ✓✓✓")
            stats = tx.get_statistics()
            print(f"\nStatistics:")
            print(f"  Bytes sent: {stats['bytes_sent']}")
            print(f"  Packets sent: {stats['packets_sent']}")
            print(f"  Retransmissions: {stats['retransmissions']}")
            print(f"  Success rate: {stats['success_rate']*100:.2f}%")
        else:
            print("\n✗✗✗ TEST FAILED ✗✗✗")
        
        tx.disconnect()
    else:
        print("\n✗✗✗ CONNECTION FAILED ✗✗✗")
    
    print("\n" + "="*80)

# Made with Bob
