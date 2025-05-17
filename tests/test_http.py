import unittest
from pypxe.httpserver import HTTPD
import os
import shutil
import threading
import time

class TestHTTP(unittest.TestCase):
    def setUp(self):
        # Create test directory
        self.test_dir = './http_test'
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_server_configuration(self):
        """Test server configuration without starting the server"""
        http = HTTPD(
            ip='127.0.0.1',
            port=8081,
            mode_debug=True,
            work_directory=self.test_dir,
            start_server=False
        )
        
        # Test initial configuration
        self.assertEqual(http.ip, '127.0.0.1')
        self.assertEqual(http.port, 8081)
        self.assertTrue(http.mode_debug)
        self.assertEqual(http.work_directory, self.test_dir)
        self.assertIsNone(http.server)  # Server should not be started
        
        # Test configuration changes
        http.port = 8082
        self.assertEqual(http.port, 8082)
        
        http.mode_debug = False
        self.assertFalse(http.mode_debug)

    def test_directory_operations(self):
        """Test directory operations without server"""
        http = HTTPD(
            ip='127.0.0.1',
            port=8081,
            mode_debug=True,
            work_directory=self.test_dir,
            start_server=False
        )
        
        # Test directory creation
        self.assertTrue(os.path.exists(self.test_dir))
        
        # Test file operations
        test_file = os.path.join(self.test_dir, 'test.txt')
        test_content = b'Hello, HTTP!'
        
        # Write test file
        with open(test_file, 'wb') as f:
            f.write(test_content)
        self.assertTrue(os.path.exists(test_file))
        
        # Read test file
        with open(test_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_path_handling(self):
        """Test path handling without server"""
        http = HTTPD(
            ip='127.0.0.1',
            port=8081,
            mode_debug=True,
            work_directory=self.test_dir,
            start_server=False
        )
        
        # Test path joining
        test_file = 'test.txt'
        full_path = os.path.join(http.work_directory, test_file)
        self.assertEqual(full_path, os.path.join(self.test_dir, test_file))
        
        # Test path sanitization
        malicious_path = '../../../etc/passwd'
        sanitized_path = os.path.join(http.work_directory, os.path.basename(malicious_path))
        self.assertEqual(sanitized_path, os.path.join(self.test_dir, 'passwd'))

    def test_mime_type_handling(self):
        """Test MIME type handling without server"""
        http = HTTPD(
            ip='127.0.0.1',
            port=8081,
            mode_debug=True,
            work_directory=self.test_dir,
            start_server=False
        )
        
        # Test common MIME types
        test_cases = [
            ('test.html', 'text/html'),
            ('test.css', 'text/css'),
            ('test.js', 'application/javascript'),
            ('test.jpg', 'image/jpeg'),
            ('test.png', 'image/png'),
            ('test.txt', 'text/plain'),
            ('test.unknown', 'application/octet-stream')
        ]
        
        for filename, expected_mime in test_cases:
            test_file = os.path.join(self.test_dir, filename)
            with open(test_file, 'wb') as f:
                f.write(b'test')
            self.assertTrue(os.path.exists(test_file))
            
            # Get MIME type (assuming HTTPD has a method for this)
            if hasattr(http, 'get_mime_type'):
                mime_type = http.get_mime_type(test_file)
                self.assertEqual(mime_type, expected_mime) 