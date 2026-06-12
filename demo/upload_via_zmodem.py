#!/usr/bin/env python3
"""
Demo 2: Act as ZModem sender, connect to rz --tcp-client receiver.

Usage:
    python demo/upload_via_zmodem.py <host> <port> 

Example:
    # On receiver side (nuc):
    rz --tcp-client
    
    # On sender side:
    python demo/upload_via_zmodem.py nuc 9000 myfile.txt
"""

import sys
import argparse
from yesterwind_zmodem import ZModemSender
from socket_wrapper import create_stream


def upload_via_zmodem(host: str, port: int, file_list: list, progress_callback=None, verbose: bool = False):
    """
    Connect to a ZModem receiver and upload files.
    
    Args:
        host: Remote host address
        port: Remote port number
        file_list: List of file paths to upload
        progress_callback: Optional callback for progress updates
        verbose: Enable debug output
    """
    print(f"Connecting to {host}:{port}...")
    
    # Create socket stream
    stream = create_stream(host, port)
    
    # Enable debug logging if verbose
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    print("Connected! Starting ZModem send...")
    
    # Create ZModem sender
    sender = ZModemSender(
        stream, 
        progress_callback=progress_callback
    )
    
    # Send files
    try:
        sent = sender.send(file_list)
        
        if sent:
            print(f"\nSent {len(sent)} file(s):")
            for filename, blocks in sent:
                print(f"  - {filename} ({blocks} blocks)")
        else:
            print("\nNo files sent")
            
    except Exception as e:
        print(f"Error during transfer: {e}")
        raise
        
    finally:
        stream.close()
        
    return sent


def progress_bar(info: dict):
    """Progress callback that prints a simple progress bar."""
    percent = info.get('percent', 0)
    block = info.get('block', 0)
    total = info.get('total_blocks', 0)
    filename = info.get('filename', '')
    bytes_val = info.get('bytes', 0)
    total_bytes = info.get('total_bytes', 0)
    
    bar_width = 30
    filled = int(bar_width * percent / 100)
    bar = '=' * filled + '-' * (bar_width - filled)
    
    # Format byte display
    if total_bytes > 0:
        size_str = f"{bytes_val}/{total_bytes} bytes"
    else:
        size_str = f"{bytes_val} bytes"
    
    sys.stdout.write(f'\r[{bar}] {percent:.1f}% {block}/{total} {size_str} {filename}')
    sys.stdout.flush()
    
    if percent >= 100:
        print(f"\n✓ Uploaded: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload a file via ZModem over TCP"
    )
    parser.add_argument('host', help="Remote host address")
    parser.add_argument('port', type=int, help="Remote port number")
    parser.add_argument('files', nargs='+', help="Files to upload")
    parser.add_argument('-v', '--verbose', action='store_true', help="Show debug output")
    
    args = parser.parse_args()
    
    # Use progress callback if not verbose
    callback = None if args.verbose else progress_bar
    
    try:
        upload_via_zmodem(
            args.host, 
            args.port, 
            args.files,
            progress_callback=callback,
            verbose=args.verbose
        )
        print("\nUpload complete!")
        
    except TimeoutError:
        print("\nConnection timed out")
        sys.exit(1)
    except ConnectionRefusedError:
        print("\nConnection refused - is the remote running rz?")
        print("On receiver side, run: rz --tcp-client")
        sys.exit(1)
    except OSError as e:
        print(f"\nNetwork error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()