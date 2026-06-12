"""
Yesterwind ZModem - Comprehensive Test Suite

Tests for XModem, YModem, and ZModem protocols.
Run with: python test_yesterwind_zmodem.py
"""

import io
import os
import sys
import unittest

# Add module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yesterwind_zmodem import (
    XModemSender, XModemReceiver,
    YModemSender, YModemReceiver,
    ZModemSender, ZModemReceiver,
    TransferProgress,
    __version__
)


class MockStream:
    """Mock stream for testing"""
    
    def __init__(self, input_data=b''):
        self.buffer = io.BytesIO(input_data)
        self.output = io.BytesIO()
        self._read_pos = 0
        
    def read(self, n=-1):
        if n == -1:
            return self.buffer.read()
        return self.buffer.read(n)
    
    def write(self, data):
        self.output.write(data)
        
    def tell(self):
        return self.buffer.tell()
    
    def seek(self, pos):
        return self.buffer.seek(pos)
    
    def getvalue(self):
        return self.output.getvalue()
    
    def reset(self):
        self.buffer.seek(0)


class MockStreamWithTimeout(MockStream):
    """Mock stream with settimeout support"""
    
    def __init__(self, input_data=b''):
        super().__init__(input_data)
        self._timeout = None
        
    def settimeout(self, timeout):
        self._timeout = timeout


class TestTransferProgress(unittest.TestCase):
    """Test TransferProgress class"""
    
    def test_init(self):
        """Test progress initialization"""
        progress = TransferProgress()
        self.assertEqual(progress.block, 0)
        self.assertEqual(progress.total_blocks, 0)
        self.assertEqual(progress.bytes, 0)
        self.assertEqual(progress.total_bytes, 0)
        self.assertEqual(progress.filename, "")
        self.assertEqual(progress.errors, 0)
        
    def test_init_with_callback(self):
        """Test progress with callback"""
        callback_called = []
        def cb(info):
            callback_called.append(info)
            
        progress = TransferProgress(cb)
        progress.update(block=5, bytes=5120)
        
        self.assertEqual(len(callback_called), 1)
        
    def test_reset(self):
        """Test progress reset"""
        progress = TransferProgress()
        progress.update(block=10, bytes=10240, errors=2)
        progress.reset()
        
        self.assertEqual(progress.block, 0)
        self.assertEqual(progress.bytes, 0)
        self.assertEqual(progress.errors, 0)
        
    def test_update(self):
        """Test progress update"""
        progress = TransferProgress()
        progress.update(block=5, total_blocks=100, bytes=5120, total_bytes=102400)
        
        self.assertEqual(progress.block, 5)
        self.assertEqual(progress.total_blocks, 100)
        self.assertEqual(progress.bytes, 5120)
        self.assertEqual(progress.total_bytes, 102400)
        
    def test_get_info(self):
        """Test get_info returns dict"""
        progress = TransferProgress()
        progress.update(block=5, total_blocks=100, bytes=5120, total_bytes=102400, filename="test.txt")
        
        info = progress.get_info()
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['block'], 5)
        self.assertEqual(info['total_blocks'], 100)
        self.assertEqual(info['bytes'], 5120)
        self.assertEqual(info['total_bytes'], 102400)
        self.assertEqual(info['filename'], "test.txt")
        self.assertIn('elapsed', info)
        self.assertIn('percent', info)
        
    def test_percent_calculation(self):
        """Test percent calculation"""
        progress = TransferProgress()
        progress.update(bytes=5120, total_bytes=10240)
        
        info = progress.get_info()
        
        self.assertEqual(info['percent'], 50.0)
        
    def test_percent_zero(self):
        """Test percent when total is zero"""
        progress = TransferProgress()
        progress.update(bytes=0, total_bytes=0)
        
        info = progress.get_info()
        
        self.assertEqual(info['percent'], 0)


class TestXModemCRC(unittest.TestCase):
    """Test XModem CRC mode"""
    
    def test_crc16_calculation(self):
        """Test CRC-16 calculation"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=False)
        
        data = b"Hello World"
        crc = receiver._calculate_crc(data)
        
        # Verify it produces a valid non-zero CRC
        self.assertGreater(crc, 0)
        
    def test_checksum_calculation(self):
        """Test checksum calculation"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=True)
        
        data = b"Hello World"
        checksum = receiver._calculate_checksum(data)
        
        expected = sum(b"Hello World") & 0xFF
        self.assertEqual(checksum, expected)
        
    def test_block_128(self):
        """Test 128-byte block"""
        stream = MockStream()
        receiver = XModemReceiver(stream, block_size=128)
        self.assertEqual(receiver.block_size, 128)
        
    def test_block_1024(self):
        """Test 1024-byte block"""
        stream = MockStream()
        receiver = XModemReceiver(stream, block_size=1024)
        self.assertEqual(receiver.block_size, 1024)
        
    def test_crc16_consistency(self):
        """Test CRC-16 is consistent"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=False)
        
        data = b"Test data"
        crc1 = receiver._calculate_crc(data)
        crc2 = receiver._calculate_crc(data)
        
        self.assertEqual(crc1, crc2)
        
    def test_crc16_different_data(self):
        """Test CRC-16 changes with different data"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=False)
        
        crc1 = receiver._calculate_crc(b"Data A")
        crc2 = receiver._calculate_crc(b"Data B")
        
        self.assertNotEqual(crc1, crc2)
        
    def test_read_block_empty(self):
        """Test read block with empty stream"""
        stream = MockStream(b'')
        receiver = XModemReceiver(stream)
        
        result = receiver._read_block()
        
        self.assertIsNone(result)


class TestXModemChecksum(unittest.TestCase):
    """Test XModem checksum mode"""
    
    def test_checksum_mode_flag(self):
        """Test that checksum mode flag is set"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=True)
        self.assertTrue(receiver.checksum_mode)


class TestXModemReceiver(unittest.TestCase):
    """Test XModemReceiver class"""
    
    def test_init_defaults(self):
        """Test init with defaults"""
        stream = MockStream()
        receiver = XModemReceiver(stream)
        
        self.assertEqual(receiver.block_size, 128)
        self.assertFalse(receiver.checksum_mode)
        
    def test_init_with_params(self):
        """Test init with parameters"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=True, block_size=1024)
        
        self.assertEqual(receiver.block_size, 1024)
        self.assertTrue(receiver.checksum_mode)
        
    def test_progress_attribute(self):
        """Test progress attribute exists"""
        stream = MockStream()
        receiver = XModemReceiver(stream)
        
        self.assertIsNotNone(receiver.progress)
        self.assertIsInstance(receiver.progress, TransferProgress)


class TestXModemSender(unittest.TestCase):
    """Test XModemSender class"""
    
    def test_init_defaults(self):
        """Test init with defaults"""
        stream = MockStream()
        sender = XModemSender(stream)
        
        self.assertEqual(sender.block_size, 128)
        self.assertFalse(sender.checksum_mode)
        
    def test_init_with_params(self):
        """Test init with parameters"""
        stream = MockStream()
        sender = XModemSender(stream, checksum_mode=True, block_size=1024)
        
        self.assertEqual(sender.block_size, 1024)
        self.assertTrue(sender.checksum_mode)
        
    def test_progress_attribute(self):
        """Test progress attribute exists"""
        stream = MockStream()
        sender = XModemSender(stream)
        
        self.assertIsNotNone(sender.progress)
        self.assertIsInstance(sender.progress, TransferProgress)


class TestYModem(unittest.TestCase):
    """Test YModem protocol"""
    
    def test_header_block_creation(self):
        """Test file header block creation"""
        stream = MockStream()
        sender = YModemSender(stream)
        
        header = sender._create_header_block("test.txt", 1024)
        
        self.assertIn(b"test.txt", header)
        self.assertIn(b"1024", header)
        self.assertEqual(len(header), 1024)


class TestYModemSender(unittest.TestCase):
    """Test YModemSender"""
    
    def test_inherits_from_xmodem(self):
        """Test YModemSender inherits from XModemSender"""
        stream = MockStream()
        sender = YModemSender(stream)
        
        self.assertIsInstance(sender, XModemSender)


class TestYModemReceiver(unittest.TestCase):
    """Test YModemReceiver"""
    
    def test_inherits_from_xmodem(self):
        """Test YModemReceiver inherits from XModemReceiver"""
        stream = MockStream()
        receiver = YModemReceiver(stream)
        
        self.assertIsInstance(receiver, XModemReceiver)


class TestZModem(unittest.TestCase):
    """Test ZModem protocol"""
    
    def test_constants(self):
        """Test ZModem constants (updated to current values)"""
        from yesterwind_zmodem.zmodem import (
            ZRINIT, ZRQINIT, ZFILE, ZDATA, ZEOF, ZFIN,
            ZBIN, ZHEX, ZBIN32
        )
        
        self.assertEqual(ZRINIT, 0x01)
        self.assertEqual(ZRQINIT, 0x00)
        self.assertEqual(ZFILE, 0x04)
        self.assertEqual(ZDATA, 0x05)
        self.assertEqual(ZEOF, 0x06)
        self.assertEqual(ZFIN, 0x0B)
        self.assertEqual(ZBIN, 0x41)
        self.assertEqual(ZHEX, 0x42)
        self.assertEqual(ZBIN32, 0x43)
        
    def test_header_creation(self):
        """Test header creation"""
        from yesterwind_zmodem.zmodem import ZModemConstants
        
        header = ZModemConstants.make_header(0x05, 0)
        
        self.assertEqual(header[0], ord('Z'))
        self.assertEqual(header[1], 0x05)
        
    def test_constants_class(self):
        """Test ZModemConstants defaults (updated to current values)"""
        from yesterwind_zmodem.zmodem import ZModemConstants
        
        self.assertEqual(ZModemConstants.DEFAULT_BLOCK_SIZE, 1024)
        self.assertEqual(ZModemConstants.MAX_SUBPACKET, 2048)
        self.assertEqual(ZModemConstants.ZINIT_TIMER, 45)
        self.assertEqual(ZModemConstants.TIMEOUT, 20)
        self.assertEqual(ZModemConstants.TIMEOUT_LONG, 60)
        self.assertEqual(ZModemConstants.MAX_RETRIES, 15)


class TestZModemSender(unittest.TestCase):
    """Test ZModemSender"""
    
    def test_init(self):
        """Test ZModemSender init"""
        stream = MockStream()
        sender = ZModemSender(stream)
        
        self.assertFalse(sender._started)
        self.assertEqual(sender._block_num, 0)
        
    def test_inherits_object(self):
        """Test ZModemSender is a class"""
        stream = MockStream()
        sender = ZModemSender(stream)
        
        self.assertIsNotNone(sender)


class TestZModemReceiver(unittest.TestCase):
    """Test ZModemReceiver"""
    
    def test_init(self):
        """Test ZModemReceiver init"""
        stream = MockStream()
        receiver = ZModemReceiver(stream)
        
        self.assertFalse(receiver._started)
        self.assertEqual(receiver._file_size, 0)
        self.assertEqual(receiver._received_size, 0)
        
    def test_init_with_output_dir(self):
        """Test ZModemReceiver init with output dir"""
        stream = MockStream()
        receiver = ZModemReceiver(stream, output_dir="/tmp")
        
        self.assertEqual(receiver.output_dir, "/tmp")


class TestModuleImport(unittest.TestCase):
    """Test module imports"""
    
    def test_imports(self):
        """Test all imports work"""
        from yesterwind_zmodem import (
            XModemSender, XModemReceiver,
            YModemSender, YModemReceiver,
            ZModemSender, ZModemReceiver,
            TransferProgress
        )
        
        self.assertIsNotNone(XModemSender)
        self.assertIsNotNone(XModemReceiver)
        self.assertIsNotNone(YModemSender)
        self.assertIsNotNone(YModemReceiver)
        self.assertIsNotNone(ZModemSender)
        self.assertIsNotNone(ZModemReceiver)
        self.assertIsNotNone(TransferProgress)
        
    def test_version(self):
        """Test version is set"""
        self.assertEqual(__version__, "0.1.0")
        
    def test_version_format(self):
        """Test version is semver-like"""
        self.assertRegex(__version__, r'\d+\.\d+\.\d+')


class TestErrorClasses(unittest.TestCase):
    """Test error classes"""
    
    def test_xmodem_error(self):
        """Test XModemError"""
        from yesterwind_zmodem import XModemError
        
        err = XModemError("test error")
        self.assertEqual(str(err), "test error")
        
    def test_ymodem_error(self):
        """Test YModemError"""
        from yesterwind_zmodem.ymodem import YModemError
        
        err = YModemError("test error")
        self.assertEqual(str(err), "test error")
        
    def test_zmodem_error(self):
        """Test ZModemError"""
        from yesterwind_zmodem.zmodem import ZModemError
        
        err = ZModemError("test error")
        self.assertEqual(str(err), "test error")


def run_tests():
    """Run all tests and return success status"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTransferProgress))
    suite.addTests(loader.loadTestsFromTestCase(TestXModemCRC))
    suite.addTests(loader.loadTestsFromTestCase(TestXModemChecksum))
    suite.addTests(loader.loadTestsFromTestCase(TestXModemReceiver))
    suite.addTests(loader.loadTestsFromTestCase(TestXModemSender))
    suite.addTests(loader.loadTestsFromTestCase(TestYModem))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemSender))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemReceiver))
    suite.addTests(loader.loadTestsFromTestCase(TestZModem))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemSender))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemReceiver))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleImport))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorClasses))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)