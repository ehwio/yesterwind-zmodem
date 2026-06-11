# Yesterwind ZModem

[![Test](https://github.com/ehwio/yesterwind-zmodem/actions/workflows/Test/badge.svg)](https://github.com/ehwio/yesterwind-zmodem/actions/workflows/Test)
[![Python Versions](https://img.shields.io/pypi/pyversions/yesterwind-zmodem)](https://pypi.org/project/yesterwind-zmodem/)
[![Coverage](https://img.shields.io/codecov/c/github/ehwio/yesterwind-zmodem)](https://codecov.io/gh/ehwio/yesterwind-zmodem)

A pure-Python implementation of ZModem, YModem, and XModem file transfer protocols.

Designed for reliable file transfers over telnet/BBS-style connections.

## Features

- ZModem: Full implementation with crash recovery
- YModem: 1024-byte block support
- XModem: CRC and checksum modes
- Pure Python (no C dependencies)
- Telnet-compatible with proper escaping
- Progress callbacks for transfer monitoring

## Installation

```bash
pip install yesterwind-zmodem
```

## Usage

```python
from yesterwind_zmodem import ZModemSender, ZModemReceiver, TransferProgress

# Send a file with progress callback
def on_progress(info):
    print(f"Progress: {info['percent']:.1f}% - {info['block']}/{info['total_blocks']} blocks")

sender = ZModemSender(stream, progress_callback=on_progress)
sender.send("myfile.txt")

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

## Development

### GitFlow Workflow

- **main** (development branch) - Active development
- **feature/** - New features (e.g., `feature/new-protocol`)
- **bugfix/** - Bug fixes (e.g., `bugfix/fix-error`)

### Running Tests

```bash
# Run all tests
pytest test_*.py -v

# Run with coverage
pytest test_*.py -v --cov=yesterwind_zmodem --cov-report=term-missing
```

### Creating a Release

1. Update version in `pyproject.toml` and `setup.py`
2. Create a GitHub release (triggers PyPI publish)

## License

MIT