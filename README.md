# Yesterwind ZModem

A pure-Python implementation of ZModem, YModem, and XModem file transfer protocols.

Designed for reliable file transfers over telnet/BBS-style connections.

## Features

- ZModem: Full implementation with crash recovery
- YModem: 1024-byte block support
- XModem: CRC and checksum modes
- Pure Python (no C dependencies)
- Telnet-compatible with proper escaping

## Installation

```bash
pip install yesterwind-zmodem
```

## Usage

```python
from yesterwind_zmodem import ZModemSender, ZModemReceiver

# Send a file
sender = ZModemSender(stream)
sender.send_file("myfile.txt")

# Receive a file
receiver = ZModemReceiver(stream)
receiver.receive_file()
```

## Protocol Overview

| Protocol | Block Size | CRC | Crash Recovery |
|----------|-----------|-----|---------------|
| XModem   | 128/1024 | Optional | No |
| YModem  | 1024     | Yes     | No |
| ZModem  | 1024     | Yes     | Yes |

## License

MIT