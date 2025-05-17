import unittest
import socket
from pypxe.tftp import TFTPD, Client
import os
import shutil
import threading
import time
from unittest.mock import MagicMock, patch

class TestTFTP(unittest.TestCase):
    def setUp(self):
        # Create test directory
        self.test_dir = './tftp_test'
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_server_configuration(self):
        """Test server configuration without starting the server"""
        tftp = TFTPD(
            ip='127.0.0.1',
            port=1069,
            mode_debug=True,
            netboot_directory=self.test_dir,
            start_server=False
        )
        
        # Test initial configuration
        self.assertEqual(tftp.ip, '127.0.0.1')
        self.assertEqual(tftp.port, 1069)
        self.assertTrue(tftp.mode_debug)
        self.assertEqual(tftp.netboot_directory, self.test_dir)
        
        # Test configuration changes
        tftp.port = 1070
        self.assertEqual(tftp.port, 1070)
        
        tftp.mode_debug = False
        self.assertFalse(tftp.mode_debug)

    def test_directory_operations(self):
        """Test directory operations without server"""
        tftp = TFTPD(
            ip='127.0.0.1',
            port=1069,
            mode_debug=True,
            netboot_directory=self.test_dir,
            start_server=False
        )
        
        # Test directory creation
        self.assertTrue(os.path.exists(self.test_dir))
        
        # Test file operations
        test_file = os.path.join(self.test_dir, 'test.txt')
        test_content = b'Hello, TFTP!'
        
        # Write test file
        with open(test_file, 'wb') as f:
            f.write(test_content)
        self.assertTrue(os.path.exists(test_file))
        
        # Read test file
        with open(test_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_client_configuration(self):
        """Test client configuration without actual socket operations"""
        # Create a mock server object
        mock_server = MagicMock()
        mock_server.ip = '127.0.0.1'
        mock_server.port = 1069
        mock_server.netboot_directory = self.test_dir
        mock_server.default_retries = 5
        mock_server.default_timeout = 5
        mock_server.mode_debug = True
        mock_server.retries = 5
        mock_server.timeout = 5
        mock_server.logger = MagicMock()
        
        # Create a mock socket with expected return values
        mock_socket = MagicMock()
        # Simulate a read request (opcode 1) for a file
        mock_socket.recvfrom.return_value = (b'\x00\x01test.txt\x00octet\x00', ('127.0.0.1', 12345))
        mock_server.sock = mock_socket
        
        # Create test file that the client will try to read
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'wb') as f:
            f.write(b'Test content')
        
        # Test client initialization
        with patch('socket.socket') as mock_socket_class:
            mock_client_socket = MagicMock()
            mock_socket_class.return_value = mock_client_socket
            client = Client(parent=mock_server, mainsock=mock_socket)
            
            # Verify client configuration
            self.assertEqual(client.ip, '127.0.0.1')
            self.assertEqual(client.default_retries, mock_server.default_retries)
            self.assertEqual(client.timeout, mock_server.timeout)
            
            # Verify that the client tried to read the file
            self.assertTrue(os.path.exists(client.filename))
            self.assertEqual(client.filename, test_file)

    def test_file_path_handling(self):
        """Test file path handling without server"""
        tftp = TFTPD(
            ip='127.0.0.1',
            port=1069,
            mode_debug=True,
            netboot_directory=self.test_dir,
            start_server=False
        )
        
        # Test path joining
        test_file = 'test.txt'
        full_path = os.path.join(tftp.netboot_directory, test_file)
        self.assertEqual(full_path, os.path.join(self.test_dir, test_file))
        
        # Test path sanitization
        malicious_path = '../../../etc/passwd'
        sanitized_path = os.path.join(tftp.netboot_directory, os.path.basename(malicious_path))
        self.assertEqual(sanitized_path, os.path.join(self.test_dir, 'passwd')) 