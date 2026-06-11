#!/usr/bin/env python3
"""
Demo 1: Connect to a remote sz (ZModem sender) via TCP and download a file.

Usage:
    python demo/download_via_zmodem.py <host> <port> [filename]

Example:
    python demo/download_via_zmodem.py localhost 9000 myfile.txt
"""

import sys
import socket
import argparse
from yesterwind_zmodem import ZModemReceiver, TransferProgress


def download_via_zmodem(host: str, port: int, output_file: str = None, progress_callback=None):
    """
    Connect to a ZModem sender and download a file.
    
    Args:
        host: Remote host address
        port: Remote port number
        output_file: Local filename to save (default: auto-detect from transfer)
        progress_callback: Optional callback for progress updates
    """
    print(f"Connecting to {host}:{port}...")
    
    # Create socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    sock.connect((host, port))
    
    print("Connected! Starting ZModem receive...")
    
    # Create ZModem receiver with progress
    receiver = ZModemReceiver(
        sock, 
        output_dir=".",
        progress_callback=progress_callback
    )
    
    # Receive files
    try:
        received = receiver.receive()
        
        if received:
            print(f"\nReceived {len(received)} file(s):")
            for filename, size in received:
                print(f"  - {filename} ({size} bytes)")
        else:
            print("\nNo files received")
            
    except Exception as e:
        print(f"Error during transfer: {e}")
        raise
        
    finally:
        sock.close()
        
    return received


def progress_bar(info: dict):
    """Progress callback that prints a simple progress bar."""
    percent = info.get('percent', 0)
    block = info.get('block', 0)
    total = info.get('total_blocks', 0)
    filename = info.get('filename', '')
    
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = '=' * filled + '-' * (bar_width - filled)
    
    sys.stdout.write(f'\r[{bar}] {percent:.1f}% Block {block}/{total} {filename}')
    sys.stdout.flush()
    
    if percent >= 100:
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Download a file via ZModem over TCP"
    )
    parser.add_argument('host', help="Remote host address")
    parser.add_argument('port', type=int, help="Remote port number")
    parser.add_argument('filename', nargs='?', help="Output filename (optional)")
    parser.add_argument('-v', '--verbose', action='store_true', help="Show verbose output")
    
    args = parser.parse_args()
    
    # Use progress callback if not verbose
    callback = None if args.verbose else progress_bar
    
    try:
        download_via_zmodem(
            args.host, 
            args.port, 
            args.filename,
            progress_callback=callback
        )
        print("\nDownload complete!")
        
    except socket.timeout:
        print("\nConnection timed out")
        sys.exit(1)
    except ConnectionRefusedError:
        print("\nConnection refused - is the remote running sz?")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()