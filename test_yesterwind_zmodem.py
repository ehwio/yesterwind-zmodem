"""
Yesterwind ZModem - Test Suite

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
    __version__
)


class MockStream:
    """Mock stream for testing"""
    
    def __init__(self, input_data=b''):
        self.buffer = io.BytesIO(input_data)
        self.output = io.BytesIO()
        
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


class TestXModemCRC(unittest.TestCase):
    """Test XModem CRC mode"""
    
    def test_crc16_calculation(self):
        """Test CRC-16 calculation produces consistent results"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=False)
        
        data = b"Hello World"
        crc = receiver._calculate_crc(data)
        
        # CRC-CCITT for "Hello World" should be consistent
        # Verify it produces a valid non-zero CRC
        self.assertGreater(crc, 0)
        
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


class TestXModemChecksum(unittest.TestCase):
    """Test XModem checksum mode"""
    
    def test_checksum_mode_flag(self):
        """Test that checksum mode flag is set"""
        stream = MockStream()
        receiver = XModemReceiver(stream, checksum_mode=True)
        self.assertTrue(receiver.checksum_mode)


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


class TestZModem(unittest.TestCase):
    """Test ZModem protocol"""
    
    def test_constants(self):
        """Test ZModem constants"""
        from yesterwind_zmodem.zmodem import (
            ZRINIT, ZRQINIT, ZFILE, ZDATA, ZEOF, ZFIN
        )
        
        self.assertEqual(ZRINIT, 0x01)
        self.assertEqual(ZRQINIT, 0x02)
        self.assertEqual(ZFILE, 0x05)
        self.assertEqual(ZDATA, 0x06)
        self.assertEqual(ZEOF, 0x07)
        self.assertEqual(ZFIN, 0x0C)
        
    def test_header_creation(self):
        """Test header creation"""
        from yesterwind_zmodem.zmodem import ZModemConstants
        
        header = ZModemConstants.make_header(0x05, 0)
        
        self.assertEqual(header[0], ord('Z'))
        self.assertEqual(header[1], 0x05)


class TestModuleImport(unittest.TestCase):
    """Test module imports"""
    
    def test_imports(self):
        """Test all imports work"""
        from yesterwind_zmodem import (
            XModemSender, XModemReceiver,
            YModemSender, YModemReceiver,
            ZModemSender, ZModemReceiver
        )
        
        self.assertIsNotNone(XModemSender)
        self.assertIsNotNone(XModemReceiver)
        self.assertIsNotNone(YModemSender)
        self.assertIsNotNone(YModemReceiver)
        self.assertIsNotNone(ZModemSender)
        self.assertIsNotNone(ZModemReceiver)
        
    def test_version(self):
        """Test version is set"""
        self.assertEqual(__version__, "0.1.0")


def run_tests():
    """Run all tests and return success status"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestXModemCRC))
    suite.addTests(loader.loadTestsFromTestCase(TestXModemChecksum))
    suite.addTests(loader.loadTestsFromTestCase(TestYModem))
    suite.addTests(loader.loadTestsFromTestCase(TestZModem))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleImport))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)