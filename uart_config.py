"""
UART Configuration for PYNQ-Z2 Board-to-Board Communication
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

This module contains all configuration parameters for UART communication
between two PYNQ-Z2 boards.
"""

# UART Port Configuration
UART_PORT_TX = '/dev/ttyPS1'  # Transmitter UART port on PYNQ-Z2
UART_PORT_RX = '/dev/ttyPS1'  # Receiver UART port on PYNQ-Z2

# UART Communication Parameters
BAUD_RATE = 115200            # Bits per second (standard rate)
TIMEOUT = 5                   # Seconds to wait for data
BYTESIZE = 8                  # Data bits per byte
PARITY = 'N'                  # No parity bit
STOPBITS = 1                  # Number of stop bits

# Protocol Parameters
HEADER = b'\xDE\xAD\xBE\xEF'  # 4-byte frame header for packet identification
MAX_PACKET_SIZE = 4096        # Maximum packet size in bytes
BUFFER_SIZE = 65536           # Receive buffer size in bytes

# GPIO Pin Definitions (PMOD JB Connector)
TX_PIN = 'JB1'                # Transmit pin (PMOD JB Pin 1)
RX_PIN = 'JB1'                # Receive pin (PMOD JB Pin 1)
GND_PIN = 'JB5'               # Ground pin (PMOD JB Pin 5)

# Error Handling Parameters
MAX_RETRIES = 3               # Maximum number of retransmission attempts
ACK_TIMEOUT = 2               # Seconds to wait for acknowledgment
RETRY_DELAY = 0.5             # Seconds to wait before retry

# Performance Tuning
CHUNK_SIZE = 1024             # Size of data chunks for transmission
FLOW_CONTROL = False          # Hardware flow control (RTS/CTS)
XON_XOFF = False              # Software flow control

# Debug Settings
DEBUG_MODE = False            # Enable debug output
LOG_PACKETS = False           # Log all packets sent/received

def print_config():
    """Print current UART configuration"""
    print("="*80)
    print("UART CONFIGURATION")
    print("="*80)
    print(f"Port (TX):        {UART_PORT_TX}")
    print(f"Port (RX):        {UART_PORT_RX}")
    print(f"Baud Rate:        {BAUD_RATE} bps")
    print(f"Timeout:          {TIMEOUT} seconds")
    print(f"Data Bits:        {BYTESIZE}")
    print(f"Parity:           {PARITY}")
    print(f"Stop Bits:        {STOPBITS}")
    print(f"Max Packet Size:  {MAX_PACKET_SIZE} bytes")
    print(f"Buffer Size:      {BUFFER_SIZE} bytes")
    print(f"Max Retries:      {MAX_RETRIES}")
    print(f"ACK Timeout:      {ACK_TIMEOUT} seconds")
    print("="*80)

if __name__ == "__main__":
    print_config()

# Made with Bob
