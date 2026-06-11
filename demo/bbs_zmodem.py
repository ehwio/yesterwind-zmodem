#!/usr/bin/env python3
"""
Demo 2: Connect to a remote telnet/BBS service with ZModem auto-detection.

This demo connects to a remote service (like a BBS) and monitors for
ZModem file transfer requests. If detected, it automatically switches
to ZModem receive mode.

Usage:
    python demo/bbs_zmodem.py <host> <port> [username] [password]

Example:
    python demo/bbs_zmodem.py bbs.example.com 23 myuser mypass
"""

import sys
import socket
import argparse
import time
from yesterwind_zmodem import ZModemReceiver, TransferProgress


class BBSConnection:
    """Connection to a BBS with ZModem auto-detection"""
    
    def __init__(self, host: str, port: int, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.zmodem_mode = False
        self.receiver = None
        
    def connect(self):
        """Establish connection to BBS"""
        print(f"Connecting to {self.host}:{self.port}...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.host, self.port))
        print("Connected!")
        return True
        
    def send(self, data: str):
        """Send data to BBS"""
        if self.socket and not self.zmodem_mode:
            self.socket.send(data.encode())
            
    def receive(self, size: int = 4096) -> bytes:
        """Receive data from BBS"""
        if self.socket:
            return self.socket.recv(size)
        return b""
        
    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()
            
    def check_for_zmodem(self, data: bytes) -> bool:
        """
        Check if data contains ZModem initialization.
        
        ZModem typically starts with:
        - **ZMODEM** (in banner/menu)
        - C or CR (to initiate transfer)
        - File transfer prompt
        """
        # Look for common ZModem indicators
        data_str = data.decode('ascii', errors='ignore').upper()
        
        # Check for ZModem keywords
        zmodem_indicators = [
            b'ZMODEM',
            b'**ZMODEM',
            b'SEND',
            b'FILE:',
            b'**SEND',
            b'READY TO RECEIVE',
        ]
        
        for indicator in zmodem_indicators:
            if indicator in data_str.encode():
                return True
                
        # Check for C or CR pattern (common ZModem start)
        if b'\x43' in data or b'\x0D' in data[-4:]:
            # Could be ZModem start - check context
            if b'C\r\n' in data or b'C\n' in data:
                return True
                
        return False
        
    def handle_zmodem_transfer(self, progress_callback=None):
        """Handle incoming ZModem transfer"""
        print("\n*** ZModem transfer detected! ***")
        
        # Create ZModem receiver using existing socket
        self.zmodem_mode = True
        self.receiver = ZModemReceiver(
            self.socket,
            output_dir=".",
            progress_callback=progress_callback
        )
        
        try:
            received = self.receiver.receive()
            
            if received:
                print(f"\nReceived {len(received)} file(s):")
                for filename, size in received:
                    print(f"  - {filename} ({size} bytes)")
            else:
                print("\nNo files received")
                
        except Exception as e:
            print(f"Transfer error: {e}")
            raise
            
        finally:
            self.zmodem_mode = False
            self.socket = None
            
        return received


def bbs_connect(host: str, port: int, username: str = None, password: str = None, 
                progress_callback=None):
    """
    Connect to BBS and monitor for ZModem.
    
    Args:
        host: BBS host address
        port: BBS port number
        username: Optional username
        password: Optional password
        progress_callback: Optional progress callback
    """
    bbs = BBSConnection(host, port)
    bbs.connect()
    
    # Login if credentials provided
    if username:
        print(f"Logging in as {username}...")
        bbs.send(username + "\r\n")
        time.sleep(1)
        
        if password:
            bbs.send(password + "\r\n")
            time.sleep(1)
    
    # Monitor for ZModem
    print("Monitoring for ZModem transfer...")
    print("(Press Ctrl+C to exit)")
    
    buffer = b""
    
    try:
        while True:
            data = bbs.receive(4096)
            
            if not data:
                break
                
            # Print to console (but not file transfer data)
            if not bbs.zmodem_mode:
                try:
                    sys.stdout.write(data.decode('ascii', errors='replace'))
                    sys.stdout.flush()
                except:
                    pass
                    
            # Check for ZModem
            if bbs.check_for_zmodem(data):
                bbs.handle_zmodem_transfer(progress_callback)
                break
                
    except KeyboardInterrupt:
        print("\n\nExiting...")
        
    finally:
        bbs.close()


def progress_bar(info: dict):
    """Simple progress bar callback"""
    percent = info.get('percent', 0)
    block = info.get('block', 0)
    total = info.get('total_blocks', 0)
    filename = info.get('filename', '')
    
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = '=' * filled + '-' * (bar_width - filled)
    
    sys.stdout.write(f'\r[{bar}] {percent:.1f}% {filename}')
    sys.stdout.flush()
    
    if percent >= 100:
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Connect to BBS with ZModem auto-detection"
    )
    parser.add_argument('host', help="BBS host address")
    parser.add_argument('port', type=int, help="BBS port number")
    parser.add_argument('username', nargs='?', help="Username (optional)")
    parser.add_argument('password', nargs='?', help="Password (optional)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose output")
    
    args = parser.parse_args()
    
    callback = None if args.verbose else progress_bar
    
    try:
        bbs_connect(
            args.host,
            args.port,
            args.username,
            args.password,
            callback
        )
        
    except socket.timeout:
        print("\nConnection timed out")
        sys.exit(1)
    except ConnectionRefusedError:
        print("\nConnection refused")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()