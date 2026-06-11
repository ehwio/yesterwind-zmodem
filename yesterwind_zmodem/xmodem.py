"""
XModem protocol implementation

XModem uses 128-byte (or optional 1024-byte) blocks with CRC-16 or checksum.
"""

import struct
import binascii
import io
import logging
from typing import Optional, Callable
from enum import IntEnum

logger = logging.getLogger(__name__)

# XModem constants
SOH = 0x01    # 128-byte block
STX = 0x02    # 1024-byte block
EOT = 0x04    # End of transmission
ACK = 0x06    # Acknowledge
NAK = 0x15    # Negative acknowledge
CAN = 0x18    # Cancel
CRC = 0x43    # 'C' - request CRC-16 mode

class XModemError(Exception):
    """Base exception for XModem errors"""
    pass

class XModemReceiver:
    """XModem file receiver"""
    
    # Block sizes
    BLOCK_128 = 128
    BLOCK_1024 = 1024
    
    def __init__(self, stream, checksum_mode: bool = False, block_size: int = 128):
        """
        Initialize XModem receiver
        
        Args:
            stream: Readable stream (file-like object)
            checksum_mode: If True, use checksum instead of CRC-16
            block_size: 128 or 1024
        """
        self.stream = stream
        self.checksum_mode = checksum_mode
        self.block_size = block_size
        
        # CRC-16 table (XModem uses CRC-CCITT)
        self._crc_table = []
        for i in range(256):
            crc = i << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            self._crc_table.append(crc & 0xFFFF)
        
        # State
        self._block_num = 0
        self._started = False
        
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate simple checksum (sum of all bytes mod 256)"""
        return sum(data) & 0xFF
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC-16 (XModem uses CRC-CCITT)"""
        crc = 0
        for byte in data:
            index = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ self._crc_table[index]) & 0xFFFF
        return crc
    
    def _read_block(self) -> Optional[tuple]:
        """
        Read a single block from stream
        
        Returns:
            (block_num, data) on success, None on error/EOT
        """
        # Read header byte
        header = self.stream.read(1)
        if not header:
            return None
            
        if header == EOT:
            logger.info("Received EOT")
            return None
            
        if header == CAN:
            logger.warning("Received CAN - transfer cancelled")
            return None
            
        # Determine block size
        if header == SOH:
            size = 128
        elif header == STX:
            size = 1024
        else:
            logger.error(f"Invalid header: {header!r}")
            return None
            
        # Read block number and its complement
        block_info = self.stream.read(2)
        if len(block_info) != 2:
            logger.error("Failed to read block info")
            return None
            
        block_num = block_info[0]
        block_comp = block_info[1]
        
        # Verify block number matches complement
        if (block_num ^ 0xFF) != block_comp:
            logger.error(f"Block number mismatch: {block_num} vs {block_comp}")
            return None
            
        # Read data
        data = self.stream.read(size)
        if len(data) != size:
            logger.error(f"Failed to read data: got {len(data)} bytes")
            return None
            
        # Read checksum/CRC
        if self.checksum_mode:
            checksum = self.stream.read(1)
            if len(checksum) != 1:
                logger.error("Failed to read checksum")
                return None
            calc = self._calculate_checksum(data)
            if calc != checksum[0]:
                logger.error(f"Checksum mismatch: expected {calc}, got {checksum[0]}")
                return None
        else:
            crc = self.stream.read(2)
            if len(crc) != 2:
                logger.error("Failed to read CRC")
                return None
            calc = self._calculate_crc(data)
            if calc != struct.unpack('>H', crc)[0]:
                logger.error(f"CRC mismatch: expected {calc}, got {struct.unpack('>H', crc)[0]}")
                return None
                
        return (block_num, data)
    
    def receive(self, output_file: str) -> int:
        """
        Receive file
        
        Args:
            output_file: Path to save received file
            
        Returns:
            Number of blocks received
        """
        blocks = 0
        
        # Send initial NAK or CRC request
        if self.checksum_mode:
            self.stream.write(bytes([NAK]))
        else:
            self.stream.write(bytes([CRC]))
            
        self._started = True
        
        # Open output file
        with open(output_file, 'wb') as f:
            while True:
                result = self._read_block()
                
                if result is None:
                    # EOT or error
                    self.stream.write(bytes([ACK]))
                    break
                    
                block_num, data = result
                
                # Check for sequence error
                expected = (blocks + 1) & 0xFF
                if block_num != expected:
                    logger.warning(f"Block sequence error: expected {expected}, got {block_num}")
                    self.stream.write(bytes([NAK]))
                    continue
                    
                # Write data
                f.write(data)
                blocks += 1
                
                # Acknowledge
                self.stream.write(bytes([ACK]))
                logger.debug(f"Received block {block_num}")
                
        return blocks


class XModemSender:
    """XModem file sender"""
    
    def __init__(self, stream, checksum_mode: bool = False, block_size: int = 128):
        """
        Initialize XModem sender
        
        Args:
            stream: Writable stream (file-like object)
            checksum_mode: If True, use checksum instead of CRC-16
            block_size: 128 or 1024
        """
        self.stream = stream
        self.checksum_mode = checksum_mode
        self.block_size = block_size
        
        # CRC-16 table (XModem uses CRC-CCITT)
        self._crc_table = []
        for i in range(256):
            crc = i << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            self._crc_table.append(crc & 0xFFFF)
        
        # State
        self._block_num = 0
        
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate simple checksum"""
        return sum(data) & 0xFF
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate CRC-16 (XModem uses CRC-CCITT)"""
        crc = 0
        for byte in data:
            index = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ self._crc_table[index]) & 0xFFFF
        return crc
    
    def _send_block(self, data: bytes, block_num: int) -> bool:
        """
        Send a single block
        
        Args:
            data: Block data (must match block_size)
            block_num: Block number
            
        Returns:
            True on ACK, False on NAK
        """
        # Select header based on block size
        header = STX if len(data) == 1024 else SOH
        
        # Build block: header + num + ~num + data + checksum/CRC
        block = bytes([header, block_num, block_num ^ 0xFF])
        
        if self.checksum_mode:
            block += data + bytes([self._calculate_checksum(data)])
        else:
            crc = struct.pack('>H', self._calculate_crc(data))
            block += data + crc
            
        self.stream.write(block)
        
        # Wait for response
        response = self.stream.read(1)
        
        if response == ACK:
            return True
        elif response == NAK:
            return False
        elif response == CAN:
            logger.warning("Receiver cancelled")
            return False
        else:
            logger.error(f"Invalid response: {response!r}")
            return False
    
    def send(self, input_file: str) -> int:
        """
        Send file
        
        Args:
            input_file: Path to file to send
            
        Returns:
            Number of blocks sent
        """
        blocks = 0
        
        # Read input file
        with open(input_file, 'rb') as f:
            while True:
                # Read block
                data = f.read(self.block_size)
                
                if not data:
                    break
                    
                # Pad to block size
                if len(data) < self.block_size:
                    data = data + bytes([0] * (self.block_size - len(data)))
                
                # Increment block number
                self._block_num = (self._block_num + 1) & 0xFF
                
                # Send block (retry once on NAK)
                if not self._send_block(data, self._block_num):
                    # Try once more
                    if not self._send_block(data, self._block_num):
                        raise XModemError("Failed to send block after retry")
                        
                blocks += 1
                logger.debug(f"Sent block {self._block_num}")
                
        # Send EOT
        self.stream.write(bytes([EOT]))
        
        # Wait for final ACK
        self.stream.read(1)
        
        return blocks