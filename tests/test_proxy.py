import unittest
import socket
from proxy import SipTracedUDPServer, UDPHandler

class TestProxy(unittest.TestCase):
    def setUp(self):
        self.proxy = SipTracedUDPServer(
            ('127.0.0.1', 5060),  # server_address tuple
            UDPHandler,           # handler_class
            main_logger=None      # optional main_logger
        )
    
    def test_server_init(self):
        self.assertIsNotNone(self.proxy)
        self.assertEqual(self.proxy.server_address[0], '127.0.0.1')
        self.assertEqual(self.proxy.server_address[1], 5060)

    # ... rest of test cases ... 