# Yesterwind ZModem Demos

This directory contains demo scripts showing how to use yesterwind-zmodem.

## Demo 1: download_via_zmodem.py

Download a file from a remote ZModem sender (like `sz`) over TCP.

```bash
# Connect to a local sz on port 9000
python demo/download_via_zmodem.py localhost 9000

# Specify output filename
python demo/download_via_zmodem.py localhost 9000 myfile.txt

# With verbose output
python demo/download_via_zmodem.py localhost 9000 -v
```

## Demo 2: bbs_zmodem.py

Connect to a BBS or telnet service with automatic ZModem detection.

```bash
# Connect to BBS without login
python demo/bbs_zmodem.py bbs.example.com 23

# Connect with credentials
python demo/bbs_zmodem.py bbs.example.com 23 myuser mypass

# Verbose output
python demo/bbs_zmodem.py bbs.example.com 23 -v
```

### How ZModem Auto-Detection Works

The script monitors incoming data for common ZModem transfer indicators:
- ZMODEM in banner/menu
- SEND command prompts
- C or CR (transfer start character)

When detected, it automatically switches to ZModem receive mode.

## Requirements

```bash
pip install yesterwind-zmodem
```

## Notes

- Both demos require a remote service running the corresponding protocol
- The TCP demos use blocking sockets - for production use, consider async I/O
- ZModem detection is heuristic-based and may need adjustment for specific systems