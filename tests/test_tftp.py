import unittest
import socket
from pypxe.tftp import TFTPD, Client

class TestTFTP(unittest.TestCase):
    def setUp(self):
        self.tftp = TFTPD(
            ip='127.0.0.1',
            port=69,
            mode_debug=True,
            netboot_directory='./tftp'
        )

    def test_server_init(self):
        self.assertEqual(self.tftp.ip, '127.0.0.1')
        self.assertEqual(self.tftp.port, 69)
        self.assertTrue(self.tftp.mode_debug)
        self.assertEqual(self.tftp.netboot_directory, './tftp') 