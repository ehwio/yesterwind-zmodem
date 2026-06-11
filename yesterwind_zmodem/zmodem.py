"""
ZModem protocol implementation

ZModem is a full-featured file transfer protocol with:
- Crash recovery
- Variable length sub-packets
- Polynomial CRC checking
- File management
- Skipping files

Reference: https://www.gnu.org/software/lrzsz/manual/html_node/Zmodem-010.html
"""

import os
import struct
import logging
import time
from typing import Optional, Callable, Dict, Any
from enum import IntEnum

logger = logging.getLogger(__name__)

# ZModem constants
ZRHS = b'Z'     # ZModem header
ZRINIT = 0x01   # Receiver ready
ZRQINIT = 0x02  # Sender init request
ZSKIP = 0x03   # Skip file
ZACK = 0x04     # Ack
ZFILE = 0x05     # File header
ZDATA = 0x06     # Data sub-packet
ZEOF = 0x07     # End of file
ZFERR = 0x08    # Fatal error
ZCRC = 0x09     # CRC request (receiver)
ZNAK = 0x0A     # Negative ack
ZABORT = 0x0B   # Abort
ZFIN = 0x0C     # Finish
ZRQDATA = 0x0D   # Request data
ZPOLL = 0x0E    # Polled ack

# ZModem data types
ZBIN = 0x31     # Binary (no encoding)
ZHEX = 0x32     # Hex encoding
ZBIN32 = 0x33    # Binary with 32-bit CRC

# ZModem special characters
CAN = 0x18       # Cancel
DLE = 0x10       # Data link escape
XON = 0x11        # Resume
XOFF = 0x13       # Suspend
TELNET_IAC = 0xFF # Telnet IAC

class ZModemError(Exception):
    """Base exception for ZModem errors"""
    pass


class TransferProgress:
    """Progress callback for file transfers"""
    
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.reset()
        
    def reset(self):
        self.block = 0
        self.total_blocks = 0
        self.bytes = 0
        self.total_bytes = 0
        self.filename = ""
        self.errors = 0
        self.started_at = time.time()
        self.last_callback = 0
        
    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        if self.callback:
            now = time.time()
            if now - self.last_callback >= 0.1:
                self.callback(self.get_info())
                self.last_callback = now
                
    def get_info(self) -> Dict[str, Any]:
        elapsed = time.time() - self.started_at
        return {
            "block": self.block,
            "total_blocks": self.total_blocks,
            "bytes": self.bytes,
            "total_bytes": self.total_bytes,
            "filename": self.filename,
            "errors": self.errors,
            "started_at": self.started_at,
            "elapsed": elapsed,
            "percent": (self.bytes / self.total_bytes * 100) if self.total_bytes > 0 else 0
        }


class ZModemConstants:
    """ZModem constants and utilities"""
    
    # Default options
    DEFAULT_BLOCK_SIZE = 1024
    MAX_SUBPACKET = 2048
    
    # Timing
    ZINIT_TIMER = 10     # Initial timeout
    TIMEOUT = 10        # Block timeout
    TIMEOUT_LONG = 60   # Long operations
    
    # Retries
    MAX_RETRIES = 10
    
    @staticmethod
    def make_header(frame_type: int, flags: int = 0) -> bytes:
        """Build ZModem header"""
        return ZRHS + bytes([frame_type, flags, 0, 0])
    
    @staticmethod
    def make_hex_header(frame_type: int, data: int = 0) -> bytes:
        """Build ZModem hex header"""
        header = bytes([ord('Z'), frame_type])
        hex_data = b'%08X' % data
        crc = ZModemConstants._calc_crc(header + hex_data)
        hex_crc = b'%04X' % crc
        return header + hex_data + b'\r' + hex_crc + b'\r\n'
    
    @staticmethod
    def _calc_crc(data: bytes) -> int:
        """Calculate CRC-32 for ZModem"""
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF


class ZModemReceiver:
    """ZModem file receiver"""
    
    def __init__(self, stream, output_dir: str = '.',
                 progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize ZModem receiver
        
        Args:
            stream: Readable stream
            output_dir: Directory for received files
            progress_callback: Optional callback for progress updates
        """
        self.stream = stream
        self.output_dir = output_dir
        self.progress = TransferProgress(progress_callback)
        self._started = False
        self._file_size = 0
        self._received_size = 0
        
    def _read_header(self, timeout: int = 10) -> Optional[tuple]:
        """Read and parse ZModem header"""
        self.stream.settimeout(timeout)
        
        try:
            # Look for Z header
            while True:
                byte = self.stream.read(1)
                if not byte:
                    return None
                    
                if byte == b'Z':
                    break
                    
            # Read frame type
            frame_type = self.stream.read(1)
            if not frame_type:
                return None
                
            frame_type = frame_type[0]
            
            # Parse based on frame type
            if frame_type == ZBIN:
                return self._read_bin_header()
            elif frame_type == ZHEX:
                return self._read_hex_header()
            elif frame_type == ZBIN32:
                return self._read_bin32_header()
            else:
                return (frame_type, 0)
                
        except Exception as e:
            logger.error(f"Header read error: {e}")
            return None
    
    def _read_bin_header(self) -> Optional[tuple]:
        """Read binary header"""
        try:
            flags = self.stream.read(1)[0]
            data = self.stream.read(4)
            data_val = struct.unpack('>I', data)[0]
            return (ZBIN, flags, data_val)
        except:
            return None
    
    def _read_hex_header(self) -> Optional[tuple]:
        """Read hex header"""
        try:
            data = b''
            while True:
                byte = self.stream.read(1)
                if byte == b'\r':
                    break
                data += byte
                
            # Parse hex data
            data_val = int(data, 16) if data else 0
            return (ZHEX, 0, data_val)
        except:
            return None
    
    def _read_bin32_header(self) -> Optional[tuple]:
        """Read binary 32-bit CRC header"""
        try:
            flags = self.stream.read(1)[0]
            data = self.stream.read(4)
            data_val = struct.unpack('>I', data)[0]
            return (ZBIN32, flags, data_val)
        except:
            return None
    
    def receive(self) -> list:
        """
        Receive files
        
        Returns:
            List of (filename, size) tuples
        """
        received = []
        
        # Send ZRQINIT to start
        self.stream.write(ZRHS + bytes([ZRQINIT, 0, 0, 0]))
        self._started = True
        
        while True:
            result = self._read_header()
            
            if result is None:
                break
                
            frame_type, flags, data = result
            
            if frame_type == ZFILE:
                # File header
                filename, file_size = self._receive_file_header()
                if not filename:
                    break
                    
                logger.info(f"Receiving: {filename}")
                
                # Create output file
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    received_size = self._receive_file_data(f)
                    
                received.append((filename, received_size))
                
            elif frame_type == ZFIN:
                # Finish
                self.stream.write(ZRHS + bytes([ZACK, 0, 0, 0]))
                break
                
            elif frame_type == ZSKIP:
                # Skip file
                logger.info("Skipping file")
                continue
                
        return received
    
    def _receive_file_header(self) -> Optional[tuple]:
        """Receive file header block"""
        # Read file info (first data subpacket)
        # This is a simplified version
        data = self.stream.read(1024)
        if not data:
            return None
            
        # Parse filename and size
        parts = data.split(b'\x00')
        filename = parts[0].decode('ascii', errors='replace')
        
        try:
            file_size = int(parts[1])
        except:
            file_size = 0
            
        self._file_size = file_size
        self._received_size = 0
        
        # Acknowledge
        self.stream.write(ZRHS + bytes([ZACK, 0, 0, 0]))
        
        return (filename, file_size)
    
    def _receive_file_data(self, f) -> int:
        """Receive file data"""
        received = 0
        
        while True:
            result = self._read_header()
            
            if result is None:
                break
                
            frame_type, flags, data = result
            
            if frame_type == ZDATA:
                # Data subpacket
                subpkt = self.stream.read(1024)
                f.write(subpkt)
                received += len(subpkt)
                self._received_size += len(subpkt)
                
                # ACK with block number
                self.stream.write(ZRHS + bytes([ZACK, 0, 0, 0]))
                
            elif frame_type == ZEOF:
                break
                
        return received


class ZModemSender:
    """ZModem file sender"""
    
    def __init__(self, stream, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize ZModem sender
        
        Args:
            stream: Writable stream
            progress_callback: Optional callback for progress updates
        """
        self.stream = stream
        self.progress = TransferProgress(progress_callback)
        self._started = False
        self._block_num = 0
        
    def send(self, file_list: list) -> list:
        """
        Send files
        
        Args:
            file_list: List of file paths
            
        Returns:
            List of (filename, blocks) tuples
        """
        sent = []
        
        # Wait for ZRINIT (receiver ready)
        self._wait_for_init()
        
        for filepath in file_list:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            
            # Send file header
            self._send_file_header(filename, file_size)
            
            # Send file data
            blocks = self._send_file_data(filepath)
            sent.append((filename, blocks))
            
            logger.info(f"Sent {filename}: {blocks} blocks")
            
        # Send ZFIN
        self.stream.write(ZRHS + bytes([ZFIN, 0, 0, 0]))
        
        return sent
    
    def _wait_for_init(self, timeout: int = 30) -> bool:
        """Wait for receiver to initialize"""
        self.stream.settimeout(timeout)
        
        try:
            while True:
                byte = self.stream.read(1)
                if not byte:
                    continue
                    
                if byte == b'Z':
                    frame = self.stream.read(1)
                    if frame and frame[0] == ZRINIT:
                        self._started = True
                        return True
        except:
            return False
            
    def _send_file_header(self, filename: str, file_size: int) -> bool:
        """Send file header"""
        # Build header data
        header = f"{filename}\x00{file_size}".encode('ascii')
        header = header.ljust(1024, b'\x00')
        
        # Send ZFILE header
        self.stream.write(ZRHS + bytes([ZFILE, 0, 0, 0]))
        self.stream.write(header)
        
        # Wait for ACK
        try:
            response = self.stream.read(2)
            return response[1] == ZACK if len(response) == 2 else False
        except:
            return False
    
    def _send_file_data(self, filepath: str) -> int:
        """Send file data"""
        blocks = 0
        
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024)
                
                if not data:
                    break
                    
                self._block_num = (self._block_num + 1) & 0xFF
                
                # Send ZDATA
                self.stream.write(ZRHS + bytes([ZDATA, 0, 0, 0]))
                self.stream.write(data)
                
                # Wait for ACK
                try:
                    self.stream.settimeout(5)
                    response = self.stream.read(2)
                    if response and response[1] != ZACK:
                        logger.warning(f"NAK on block {self._block_num}")
                except:
                    pass
                    
                blocks += 1
                
        # Send ZEOF
        self.stream.write(ZRHS + bytes([ZEOF, 0, 0, 0]))
        
        return blocks