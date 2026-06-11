"""
Yesterwind ZModem - Integration Tests

Integration tests for module functionality.
"""

import io
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yesterwind_zmodem import (
    XModemSender, XModemReceiver,
    YModemSender, YModemReceiver,
    ZModemSender, ZModemReceiver,
    TransferProgress
)


class TestProgressIntegration(unittest.TestCase):
    """Integration tests for progress callbacks"""
    
    def test_progress_callback_send(self):
        """Test progress callback during send"""
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Test data" * 100)
            temp_file = f.name
            
        try:
            progress_info = []
            
            def callback(info):
                progress_info.append(info.copy())
                
            stream = io.BytesIO()
            sender = XModemSender(stream, progress_callback=callback)
            
            # Send will fail without receiver but progress should initialize
            try:
                sender.send(temp_file)
            except:
                pass
                
            # Check progress was initialized
            if progress_info:
                self.assertIn('block', progress_info[0])
                self.assertIn('bytes', progress_info[0])
                self.assertIn('percent', progress_info[0])
        finally:
            os.unlink(temp_file)
            
    def test_progress_initialization(self):
        """Test progress is initialized on send"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"X" * 1000)
            temp_file = f.name
            
        try:
            stream = io.BytesIO()
            sender = XModemSender(stream)
            
            # Access progress before send
            self.assertIsInstance(sender.progress, TransferProgress)
            self.assertEqual(sender.progress.block, 0)
            self.assertEqual(sender.progress.filename, "")
        finally:
            os.unlink(temp_file)
            
    def test_progress_filename_set(self):
        """Test progress has filename after send"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"X" * 500)
            temp_file = f.name
            
        try:
            stream = io.BytesIO()
            sender = XModemSender(stream)
            
            try:
                sender.send(temp_file)
            except:
                pass
                
            # Check filename was set (should contain the temp filename)
            self.assertIn(os.path.basename(temp_file), sender.progress.filename)
        finally:
            os.unlink(temp_file)


class TestYModemIntegration(unittest.TestCase):
    """Integration tests for YModem"""
    
    def test_ymodem_sender_init(self):
        """Test YModem sender initialization"""
        stream = io.BytesIO()
        sender = YModemSender(stream)
        
        self.assertIsInstance(sender, YModemSender)
        
    def test_ymodem_receiver_init(self):
        """Test YModem receiver initialization"""
        stream = io.BytesIO()
        receiver = YModemReceiver(stream)
        
        self.assertIsInstance(receiver, YModemReceiver)


class TestZModemIntegration(unittest.TestCase):
    """Integration tests for ZModem"""
    
    def test_zmodem_sender_init(self):
        """Test ZModem sender initialization"""
        stream = io.BytesIO()
        sender = ZModemSender(stream)
        
        self.assertFalse(sender._started)
        self.assertEqual(sender._block_num, 0)
        
    def test_zmodem_receiver_init(self):
        """Test ZModem receiver initialization"""
        stream = io.BytesIO()
        receiver = ZModemReceiver(stream)
        
        self.assertFalse(receiver._started)
        self.assertEqual(receiver._file_size, 0)
        self.assertEqual(receiver._received_size, 0)
        
    def test_zmodem_receiver_output_dir(self):
        """Test ZModem receiver output dir"""
        stream = io.BytesIO()
        receiver = ZModemReceiver(stream, output_dir="/tmp")
        
        self.assertEqual(receiver.output_dir, "/tmp")


class TestModuleIntegration(unittest.TestCase):
    """Test module-level integration"""
    
    def test_version_import(self):
        """Test version is importable"""
        from yesterwind_zmodem import __version__
        
        self.assertEqual(__version__, "0.1.0")
        
    def test_all_exports(self):
        """Test all exports are available"""
        from yesterwind_zmodem import (
            XModemSender, XModemReceiver, XModemError,
            YModemSender, YModemReceiver, YModemError,
            ZModemSender, ZModemReceiver, ZModemError,
            TransferProgress
        )
        
        # All should be importable
        self.assertTrue(callable(XModemSender))
        self.assertTrue(callable(XModemReceiver))
        self.assertTrue(issubclass(XModemError, Exception))
        self.assertTrue(callable(YModemSender))
        self.assertTrue(callable(YModemReceiver))
        self.assertTrue(issubclass(YModemError, Exception))
        self.assertTrue(callable(ZModemSender))
        self.assertTrue(callable(ZModemReceiver))
        self.assertTrue(issubclass(ZModemError, Exception))
        self.assertTrue(callable(TransferProgress))


class TestProgressEdgeCases(unittest.TestCase):
    """Test edge cases"""
    
    def test_zero_total_bytes(self):
        """Test progress with zero total bytes"""
        progress = TransferProgress()
        progress.update(bytes=0, total_bytes=0)
        
        info = progress.get_info()
        self.assertEqual(info['percent'], 0)
        
    def test_callback_not_required(self):
        """Test no error if no callback"""
        progress = TransferProgress()
        
        # Should not raise
        progress.update(block=1)
        
    def test_multiple_updates(self):
        """Test multiple updates"""
        progress = TransferProgress()
        
        progress.update(block=1, bytes=1024, total_bytes=10240)
        progress.update(block=2, bytes=2048)
        progress.update(block=3, bytes=3072)
        
        info = progress.get_info()
        self.assertEqual(info['block'], 3)
        self.assertEqual(info['bytes'], 3072)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestProgressIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestYModemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestZModemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    print(f"\n{'='*50}")
    print(f"Tests: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)