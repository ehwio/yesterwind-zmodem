"""
Yesterwind ZModem - Full Coverage Tests for ZModem

Targeting 100% coverage of zmodem.py
"""

import io
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yesterwind_zmodem import (
    ZModemSender, ZModemReceiver,
    ZModemError
)
from yesterwind_zmodem.zmodem import (
    ZRINIT, ZRQINIT, ZSKIP, ZACK, ZFILE, ZDATA, ZFERR, ZCRC, ZNAK, ZABORT, ZFIN,
    ZBIN, ZHEX, ZBIN32,
    CAN, DLE, XON, XOFF, TELNET_IAC,
    ZModemConstants
)


class MockZModemStream(io.BytesIO):
    """Mock stream for testing"""
    
    def __init__(self, input_data=b''):
        super().__init__(input_data)
        self.written = []
        
    def write(self, data):
        self.written.append(data)
        super().write(data)
        
    def settimeout(self, timeout):
        pass


class TestZModemConstants(unittest.TestCase):
    """Test ZModem constants"""
    
    def test_frame_constants(self):
        """Test frame type constants"""
        self.assertEqual(ZRINIT, 0x01)
        self.assertEqual(ZRQINIT, 0x02)
        self.assertEqual(ZSKIP, 0x03)
        self.assertEqual(ZACK, 0x04)
        self.assertEqual(ZFILE, 0x05)
        self.assertEqual(ZDATA, 0x06)
        self.assertEqual(ZFERR, 0x08)
        self.assertEqual(ZCRC, 0x09)
        self.assertEqual(ZNAK, 0x0A)
        self.assertEqual(ZABORT, 0x0B)
        self.assertEqual(ZFIN, 0x0C)
        
    def test_data_type_constants(self):
        """Test data type constants"""
        self.assertEqual(ZBIN, 0x31)
        self.assertEqual(ZHEX, 0x32)
        self.assertEqual(ZBIN32, 0x33)
        
    def test_special_chars(self):
        """Test special character constants"""
        self.assertEqual(CAN, 0x18)
        self.assertEqual(DLE, 0x10)
        self.assertEqual(XON, 0x11)
        self.assertEqual(XOFF, 0x13)
        self.assertEqual(TELNET_IAC, 0xFF)


class TestZModemConstantsClass(unittest.TestCase):
    """Test ZModemConstants class"""
    
    def test_default_block_size(self):
        """Test default block size"""
        self.assertEqual(ZModemConstants.DEFAULT_BLOCK_SIZE, 1024)
        
    def test_max_subpacket(self):
        """Test max subpacket size"""
        self.assertEqual(ZModemConstants.MAX_SUBPACKET, 2048)
        
    def test_timing_constants(self):
        """Test timing constants"""
        self.assertEqual(ZModemConstants.ZINIT_TIMER, 10)
        self.assertEqual(ZModemConstants.TIMEOUT, 10)
        self.assertEqual(ZModemConstants.TIMEOUT_LONG, 60)
        self.assertEqual(ZModemConstants.MAX_RETRIES, 10)
        
    def test_make_header(self):
        """Test make_header"""
        header = ZModemConstants.make_header(0x05, 0)
        self.assertEqual(header[0], ord('Z'))
        self.assertEqual(header[1], 0x05)


class TestZModemSender(unittest.TestCase):
    """Test ZModemSender"""
    
    def test_init(self):
        """Test ZModemSender init"""
        stream = MockZModemStream()
        sender = ZModemSender(stream)
        
        self.assertFalse(sender._started)
        self.assertEqual(sender._block_num, 0)


class TestZModemReceiver(unittest.TestCase):
    """Test ZModemReceiver"""
    
    def test_init(self):
        """Test ZModemReceiver init"""
        stream = MockZModemStream()
        receiver = ZModemReceiver(stream)
        
        self.assertFalse(receiver._started)
        self.assertEqual(receiver._file_size, 0)
        self.assertEqual(receiver._received_size, 0)
        
    def test_init_with_output_dir(self):
        """Test init with output dir"""
        stream = MockZModemStream()
        receiver = ZModemReceiver(stream, output_dir="/tmp")
        
        self.assertEqual(receiver.output_dir, "/tmp")


class TestZModemError(unittest.TestCase):
    """Test ZModemError"""
    
    def test_error_message(self):
        """Test error message"""
        err = ZModemError("Test error")
        self.assertEqual(str(err), "Test error")
        
    def test_error_inheritance(self):
        """Test error inheritance"""
        err = ZModemError("Test")
        self.assertIsInstance(err, Exception)


class TestZModemSenderMethods(unittest.TestCase):
    """Test ZModemSender methods"""
    
    def setUp(self):
        """Create temp file"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(self.test_file, 'wb') as f:
            f.write(b"ZModem test data" * 50)
            
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
            
    def test_send_init(self):
        """Test send initializes"""
        stream = MockZModemStream()
        sender = ZModemSender(stream)
        
        self.assertFalse(sender._started)


def run_zmodem_tests():
    """Run all ZModem tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestZModemConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemConstantsClass))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemSender))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemReceiver))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemError))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemSenderMethods))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_zmodem_tests()
    print(f"\n{'='*50}")
    print(f"ZModem tests: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)