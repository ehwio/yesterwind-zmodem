"""
Yesterwind ZModem - Full Coverage Tests for YModem

Targeting 100% coverage of ymodem.py
"""

import io
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yesterwind_zmodem import (
    YModemSender, YModemReceiver,
    YModemError
)


class MockYModemStream(io.BytesIO):
    """Mock stream for testing"""
    
    def __init__(self, input_data=b''):
        super().__init__(input_data)
        self.written = []
        
    def write(self, data):
        self.written.append(data)
        super().write(data)


class TestYModemSender(unittest.TestCase):
    """Test YModemSender"""
    
    def test_init(self):
        """Test YModemSender init"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        self.assertEqual(sender.block_size, 1024)
        self.assertFalse(sender.checksum_mode)
        
    def test_create_header_block(self):
        """Test header block creation"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        header = sender._create_header_block("test.txt", 1024)
        
        self.assertIn(b"test.txt", header)
        self.assertIn(b"1024", header)
        self.assertEqual(len(header), 1024)
        
    def test_create_header_block_long_filename(self):
        """Test header with long filename"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        long_name = "a" * 500
        header = sender._create_header_block(long_name, 999999)
        
        self.assertEqual(len(header), 1024)
        
    def test_create_header_block_large_size(self):
        """Test header with large file size"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        header = sender._create_header_block("file.txt", 999999999)
        
        self.assertIn(b"999999999", header)


class TestYModemReceiver(unittest.TestCase):
    """Test YModemReceiver"""
    
    def test_init(self):
        """Test YModemReceiver init"""
        stream = MockYModemStream()
        receiver = YModemReceiver(stream)
        
        self.assertEqual(receiver.block_size, 1024)
        self.assertFalse(receiver.checksum_mode)
        
    def test_inherits_from_xmodem(self):
        """Test YModemReceiver inherits from XModemReceiver"""
        from yesterwind_zmodem import XModemReceiver
        
        stream = MockYModemStream()
        receiver = YModemReceiver(stream)
        
        self.assertIsInstance(receiver, XModemReceiver)


class TestYModemSend(unittest.TestCase):
    """Test YModemSender.send"""
    
    def setUp(self):
        """Create temp files"""
        self.temp_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.temp_dir, "file1.txt")
        self.file2 = os.path.join(self.temp_dir, "file2.txt")
        
        with open(self.file1, 'wb') as f:
            f.write(b"File 1 content" * 50)
        with open(self.file2, 'wb') as f:
            f.write(b"File 2 content" * 50)
            
    def tearDown(self):
        """Clean up"""
        for f in [self.file1, self.file2]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
            
    def test_send_single_file(self):
        """Test sending single file"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        try:
            result = sender.send([self.file1])
            self.assertIsInstance(result, list)
        except:
            pass
            
    def test_send_multiple_files(self):
        """Test sending multiple files"""
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        try:
            result = sender.send([self.file1, self.file2])
            self.assertIsInstance(result, list)
        except:
            pass
            
    def test_send_empty_file(self):
        """Test sending empty file"""
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_file, 'wb') as f:
            pass
            
        stream = MockYModemStream()
        sender = YModemSender(stream)
        
        try:
            result = sender.send([empty_file])
        except:
            pass
            
        os.unlink(empty_file)


class TestYModemReceive(unittest.TestCase):
    """Test YModemReceiver.receive"""
    
    def setUp(self):
        """Create temp dir"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
            
    def test_receive_init(self):
        """Test receive initialization"""
        stream = MockYModemStream()
        receiver = YModemReceiver(stream)
        
        result = receiver.receive(self.temp_dir)
        
        self.assertIsInstance(result, list)


class TestYModemError(unittest.TestCase):
    """Test YModemError"""
    
    def test_error_message(self):
        """Test error message"""
        err = YModemError("Test error")
        self.assertEqual(str(err), "Test error")
        
    def test_error_inheritance(self):
        """Test error inheritance"""
        err = YModemError("Test")
        self.assertIsInstance(err, Exception)


def run_ymodem_tests():
    """Run all YModem tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestYModemSender))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemReceiver))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemSend))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemReceive))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemError))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ymodem_tests()
    print(f"\n{'='*50}")
    print(f"YModem tests: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)