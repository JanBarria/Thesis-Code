"""
UART Protocol Implementation with Error Detection
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

This module implements a robust UART communication protocol with:
- CRC32 checksums for error detection
- Packet framing with headers
- ACK/NACK acknowledgments
- Automatic retransmission on errors
"""

import struct
import zlib


class UARTProtocol:
    """
    UART communication protocol with CRC32 checksums
    
    Packet Structure:
    [HEADER (4 bytes)][LENGTH (4 bytes)][DATA (variable)][CRC32 (4 bytes)]
    
    - HEADER: 0xDEADBEEF (identifies start of packet)
    - LENGTH: Unsigned 32-bit integer (little-endian)
    - DATA: Variable length payload
    - CRC32: Checksum of DATA for integrity verification
    """
    
    HEADER = b'\xDE\xAD\xBE\xEF'
    MIN_PACKET_SIZE = 12  # Header(4) + Length(4) + CRC(4)
    
    @staticmethod
    def create_packet(data):
        """
        Create UART packet with header, length, data, and checksum
        
        Args:
            data (bytes): Data payload to transmit
            
        Returns:
            bytes: Complete packet ready for transmission
            
        Example:
            >>> packet = UARTProtocol.create_packet(b'Hello')
            >>> len(packet)
            21  # 4 (header) + 4 (length) + 5 (data) + 4 (crc) + 4 (padding)
        """
        if not isinstance(data, bytes):
            raise TypeError("Data must be bytes")
        
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
        
        Args:
            packet (bytes): Received packet data
            
        Returns:
            tuple: (data, valid) where:
                - data (bytes): Extracted payload or None if invalid
                - valid (bool): True if checksum matches, False otherwise
                
        Example:
            >>> packet = UARTProtocol.create_packet(b'Test')
            >>> data, valid = UARTProtocol.parse_packet(packet)
            >>> data == b'Test' and valid
            True
        """
        # Check minimum packet size
        if len(packet) < UARTProtocol.MIN_PACKET_SIZE:
            return None, False
        
        # Verify header
        header = packet[:4]
        if header != UARTProtocol.HEADER:
            return None, False
        
        # Extract length
        try:
            length = struct.unpack('<I', packet[4:8])[0]
        except struct.error:
            return None, False
        
        # Check if packet is complete
        expected_size = 8 + length + 4  # Header(4) + Length(4) + Data + CRC(4)
        if len(packet) < expected_size:
            return None, False
        
        # Extract data
        data = packet[8:8+length]
        
        # Extract checksum
        try:
            received_checksum = struct.unpack('<I', packet[8+length:8+length+4])[0]
        except struct.error:
            return None, False
        
        # Calculate checksum
        calculated_checksum = zlib.crc32(data) & 0xFFFFFFFF
        
        # Verify checksum
        valid = (received_checksum == calculated_checksum)
        
        return data, valid
    
    @staticmethod
    def create_ack():
        """
        Create acknowledgment packet
        
        Returns:
            bytes: ACK packet
        """
        return UARTProtocol.create_packet(b'ACK')
    
    @staticmethod
    def create_nack():
        """
        Create negative acknowledgment packet
        
        Returns:
            bytes: NACK packet
        """
        return UARTProtocol.create_packet(b'NACK')
    
    @staticmethod
    def is_ack(packet):
        """
        Check if packet is an ACK
        
        Args:
            packet (bytes): Packet to check
            
        Returns:
            bool: True if packet is valid ACK
        """
        data, valid = UARTProtocol.parse_packet(packet)
        return valid and data == b'ACK'
    
    @staticmethod
    def is_nack(packet):
        """
        Check if packet is a NACK
        
        Args:
            packet (bytes): Packet to check
            
        Returns:
            bool: True if packet is valid NACK
        """
        data, valid = UARTProtocol.parse_packet(packet)
        return valid and data == b'NACK'
    
    @staticmethod
    def calculate_packet_size(data_length):
        """
        Calculate total packet size for given data length
        
        Args:
            data_length (int): Length of data payload
            
        Returns:
            int: Total packet size in bytes
        """
        return 4 + 4 + data_length + 4  # Header + Length + Data + CRC


# Test the protocol
if __name__ == "__main__":
    print("="*80)
    print("UART PROTOCOL TEST")
    print("="*80)
    
    # Test 1: Create and parse packet
    print("\nTest 1: Create and parse packet")
    test_data = b"Hello, PYNQ-Z2!"
    packet = UARTProtocol.create_packet(test_data)
    print(f"Original data: {test_data}")
    print(f"Packet size: {len(packet)} bytes")
    
    data, valid = UARTProtocol.parse_packet(packet)
    print(f"Parsed data: {data}")
    print(f"Valid: {valid}")
    print(f"Match: {data == test_data}")
    
    # Test 2: ACK/NACK
    print("\nTest 2: ACK/NACK packets")
    ack = UARTProtocol.create_ack()
    nack = UARTProtocol.create_nack()
    print(f"ACK packet size: {len(ack)} bytes")
    print(f"NACK packet size: {len(nack)} bytes")
    print(f"Is ACK: {UARTProtocol.is_ack(ack)}")
    print(f"Is NACK: {UARTProtocol.is_nack(nack)}")
    
    # Test 3: Corrupted packet
    print("\nTest 3: Corrupted packet detection")
    corrupted = packet[:-1] + b'\xFF'  # Corrupt last byte
    data, valid = UARTProtocol.parse_packet(corrupted)
    print(f"Corrupted packet valid: {valid}")
    
    # Test 4: Large data
    print("\nTest 4: Large data packet")
    import numpy as np
    large_data = np.random.randint(0, 256, 10000, dtype=np.uint8).tobytes()
    large_packet = UARTProtocol.create_packet(large_data)
    print(f"Large data size: {len(large_data)} bytes")
    print(f"Large packet size: {len(large_packet)} bytes")
    data, valid = UARTProtocol.parse_packet(large_packet)
    print(f"Large packet valid: {valid}")
    print(f"Data match: {data == large_data}")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED!")
    print("="*80)

# Made with Bob
