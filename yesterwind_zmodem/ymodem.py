"""
YModem protocol implementation

YModem is XModem with 1024-byte blocks and batch file transfer.
Inherits from XModem base.
"""

import os
import struct
import logging
from typing import Optional
from .xmodem import XModemSender as XModemBase, XModemReceiver as XModemReceiverBase

logger = logging.getLogger(__name__)

class YModemError(Exception):
    """Base exception for YModem errors"""
    pass


class YModemReceiver(XModemReceiverBase):
    """YModem file receiver"""
    
    def __init__(self, stream):
        """Initialize YModem receiver (always uses 1024-byte blocks with CRC)"""
        super().__init__(stream, checksum_mode=False, block_size=1024)
        
    def receive(self, output_dir: str = '.') -> list:
        """
        Receive files in batch mode
        
        Args:
            output_dir: Directory to save received files
            
        Returns:
            List of (filename, blocks) tuples
        """
        received = []
        
        # Send CRC request to start
        self.stream.write(b'C')
        self._started = True
        
        while True:
            # Read file header block
            result = self._read_block()
            
            if result is None:
                break
                
            block_num, data = result
            
            # First block contains file metadata
            if block_num == 1:
                # Parse file metadata
                metadata = data.split(b'\x00')
                filename = metadata[0].decode('ascii', errors='replace')
                
                if not filename:
                    # Empty filename = end of transfer
                    self.stream.write(b'ACK')
                    break
                    
                # Extract file size
                try:
                    file_size = int(metadata[1])
                except (ValueError, IndexError):
                    file_size = 0
                    
                logger.info(f"Receiving: {filename} ({file_size} bytes)")
                
                # Open output file
                filepath = os.path.join(output_dir, filename)
                f = open(filepath, 'wb')
                
                # Acknowledge header
                self.stream.write(b'ACK')
                
                # Receive data blocks
                while True:
                    result = self._read_block()
                    
                    if result is None:
                        f.close()
                        break
                        
                    block_num, data = result
                    
                    # Check for new file header (next file)
                    if block_num == 0:
                        f.close()
                        received.append((filename, 0))
                        break
                        
                    # Write data
                    f.write(data)
                    self.stream.write(b'ACK')
                    logger.debug(f"Received block {block_num}")
                    
                received.append((filename, block_num))
                
        return received


class YModemSender(XModemBase):
    """YModem file sender"""
    
    def __init__(self, stream):
        """Initialize YModem sender"""
        super().__init__(stream, checksum_mode=False, block_size=1024)
        
    def _create_header_block(self, filename: str, file_size: int) -> bytes:
        """Create file header block"""
        # Format: filename\x00filesize
        header = f"{filename}\x00{file_size}"
        header_bytes = header.encode('ascii')
        
        # Pad to 1024 bytes
        padding = b'\x00' * (self.block_size - len(header_bytes))
        return header_bytes + padding
        
    def send(self, file_list: list) -> list:
        """
        Send multiple files in batch mode
        
        Args:
            file_list: List of file paths
            
        Returns:
            List of (filename, blocks) tuples
        """
        sent = []
        
        # Wait for CRC request
        response = self.stream.read(1)
        if response != b'C':
            logger.warning(f"Invalid start: {response!r}")
            return sent
            
        for filepath in file_list:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            
            # Send header block
            header = self._create_header_block(filename, file_size)
            self._block_num = 1
            
            if not self._send_block(header, self._block_num):
                logger.error(f"Failed to send header for {filename}")
                continue
                
            # Send file data
            blocks = 0
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(self.block_size)
                    
                    if not data:
                        break
                        
                    self._block_num = (self._block_num + 1) & 0xFF
                    
                    if not self._send_block(data, self._block_num):
                        logger.error(f"Failed to send data block for {filename}")
                        break
                        
                    blocks += 1
                    
            sent.append((filename, blocks))
            logger.info(f"Sent {filename}: {blocks} blocks")
            
        # Send empty header to end transfer
        self._block_num = 0
        empty_header = b'\x00' * self.block_size
        self._send_block(empty_header, self._block_num)
        
        # Send EOT
        self.stream.write(b'\x04')
        self.stream.read(1)
        
        return sent