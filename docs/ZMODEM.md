# ZModem Protocol Documentation

## Overview

ZModem is a file transfer protocol developed in 1986 by Chuck Forsberg. It's a full-duplex protocol designed for reliable and efficient file transfers over serial connections, with features like crash recovery, batch file transfers, and automatic file name negotiation.

## Key Features

- **Crash Recovery**: Resumes interrupted transfers
- **Variable-length sub-packets**: Adaptive packet sizes for different line qualities
- **CRC checking**: Polynomial CRC for error detection
- **Batch transfers**: Multiple files in one session
- **File management**: Skip, replace, append options
- **Progress reporting**: Real-time transfer statistics

## How ZModem Download Works

### 1. Session Initiation

The receiver (our implementation) initiates by waiting for the sender to begin. Old BBS programs and terminals detect a ZModem transaction through these methods:

#### Detection Methods

**a) Banner Detection (Legacy)**
```
rz\r**  (or rz\r + version info)
```
- The sender (sz) sends its banner starting with "rz"
- Old terminals see "rz" and know to spawn a ZModem receiver
- This is why the banner exists - it's a signal to the receiving end

**b) ZRQINIT Header**
The sender initiates with a ZRQINIT (0x02) header:
```
Z + ZRQINIT + flags(0) + data(0)
```
Or in hex: `Z 02 00000000`

This is the proper protocol way to request receiver initialization.

### 2. Handshake Sequence

```
Receiver                    Sender
   |                         |
   |    << ZRQINIT <<       |  (sender requests init)
   |                         |
   |    >> ZRINIT >>        |  (receiver ready)
   |                         |
   |    << ZFILE <<         |  (file header with name)
   |                         |
   |    >> ZRPOS >>         |  (receiver ready at position 0)
   |                         |
   |    << DATA subpkts >>  |  (file data transfer)
   |                         |
   |    << ZEOF >>          |  (end of file)
   |                         |
   |    << ZFIN >>          |  (session complete)
```

### 3. File Name Negotiation

When the sender sends ZFILE, it includes the filename and metadata:

**ZFILE Header Structure:**
- Frame type: ZFILE (0x05)
- Flags
- Data: File name and info (variable length)

The file name is encoded in the sub-packet following ZFILE, containing:
- Filename (null-terminated)
- File size (optional)
- Modification date (optional)
- Mode/permissions (optional)
- Serial number (optional)

### 4. Local File Existence Check

When receiving a file, the receiver (or external code) must check:

```python
def check_local_file(filename: str, output_dir: str = ".") -> str:
    """
    Determine output filename, handling existing files.
    
    Returns the path to write to.
    """
    import os
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        # Options depend on implementation:
        # 1. Append number: file.txt -> file_1.txt
        # 2. Overwrite: Replace existing
        # 3. Ask user: Interactive prompt
        # 4. Skip: Don't transfer
        
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(output_dir, f"{base}_{counter}{ext}")
            counter += 1
    
    return filepath
```

### 5. Download Start (Automatic Detection)

Old terminal programs handle this in several ways:

**Method A: Manual rz Command**
```
rz
```
User types `rz` on the sender side, which triggers sz.

**Method B: Automatic Protocol Detection**
```
sz --tcp-server ...
```
The sender runs in server mode, waiting for connection.

**Method C: Intercepted Banner**
1. Terminal sees "rz" banner
2. Spawns background rz process
3. Pipes data between connection and rz

Our implementation:
```python
# Wait for sender to initiate
result = read_header(timeout=30)

if result and result[0] == ZRQINIT:
    # Sender requested transfer - respond and receive
    send_zrinit()
    receive_files()
```

### 6. Data Transfer

Once file header is received and local filename resolved:

```
Sender sends: ZDATA (sub-packets with file data)
Receiver:   ACK each block, request next

Sub-packet types:
- ZBIN (0x31): Binary, no CRC
- ZHEX (0x32): Hex encoded, CRC
- ZBIN32 (0x33): Binary, 32-bit CRC
```

### 7. Completion

```
Sender: ZEOF (end of current file)
Sender: ZFIN (end of session)
Receiver: ZACK (acknowledge)
```

## Integration with Legacy Systems

### Detecting ZModem in Terminal Emulators

1. **Pattern matching on incoming data**: Look for "rz\r\n" or "rz\r"
2. **Protocol header detection**: Watch for 'Z' byte (0x5A)
3. **User-initiated**: User types 'rz' or clicks "Receive"

### Auto-Start on BBS

```python
def detect_and_spawn_zmodem(socket, output_dir):
    """Detect ZModem and spawn receiver"""
    import threading
    
    # Read initial data
    initial = socket.recv(1024)
    
    if b'rz' in initial or b'Z' in initial[:10]:
        # Likely ZModem - spawn receiver thread
        receiver = ZModemReceiver(socket, output_dir)
        thread = threading.Thread(target=receiver.receive)
        thread.start()
        return True
    return False
```

## Reference

- [GNU lrzsz Manual](https://www.gnu.org/software/lrzsz/manual/html_node/Zmodem-010.html)
- [ZModem Specification](https://www.textfiles.com/apple/magazine/commodore/cknow_110.txt)