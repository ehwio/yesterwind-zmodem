#!/usr/bin/env python3
"""
Socket wrapper to provide file-like read/write interface for ZModem.

This wraps a raw socket to provide the read() and write() methods
that ZModem expects.
"""

import socket


class SocketStream:
    """Wrapper to make socket work with ZModem's read/write interface"""
    
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self._buffer = b""
        self._pushback = b""
        
    def read(self, n: int = -1) -> bytes:
        """Read from socket (like a file)"""
        # handle pushback first
        if self._pushback:
            if n == -1 or n > len(self._pushback):
                data = self._pushback
                self._pushback = b""
                if n == -1:
                    more = self.sock.recv(8192) or b""
                    return data + more
                else:
                    need = n - len(data)
                    more = self.sock.recv(need) or b""
                    return data + more
            else:
                data = self._pushback[:n]
                self._pushback = self._pushback[n:]
                return data

        if n == -1:
            # Read all available
            data = self.sock.recv(8192)
            return data or b""
            
        # Read exactly n bytes or return what's available
        while len(self._buffer) < n:
            chunk = self.sock.recv(n - len(self._buffer))
            if not chunk:
                break
            self._buffer += chunk
            
        result = self._buffer[:n]
        self._buffer = self._buffer[n:]
        return result
        
    def write(self, data: bytes) -> int:
        """Write to socket (like a file)"""
        return self.sock.send(data)
        
    def settimeout(self, timeout):
        """Set socket timeout"""
        self.sock.settimeout(timeout)
        
    def close(self):
        """Close socket"""
        self.sock.close()

    def push_back(self, data: bytes):
        """Push bytes back so next read will see them first (for lookahead in protocol)."""
        if data:
            self._pushback = data + self._pushback


def create_stream(host: str, port: int, timeout: int = 30) -> SocketStream:
    """Create a SocketStream connection"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((host, port))
    return SocketStream(sock)