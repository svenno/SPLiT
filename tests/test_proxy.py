import unittest
import socket
from proxy import SipTracedUDPServer, UDPHandler

class TestProxy(unittest.TestCase):
    def setUp(self):
        class Options:
            sip_password = 'test123'
            sip_redirect = False
            
        self.options = Options()
        self.proxy = SipTracedUDPServer(
            ('127.0.0.1', 5060),
            UDPHandler,
            None,  # sip_logger
            None,  # main_logger 
            self.options
        )

    def test_server_init(self):
        self.assertEqual(self.proxy.options.sip_password, 'test123')
        self.assertFalse(self.proxy.options.sip_redirect)
        self.assertTrue('Record-Route:' in self.proxy.recordroute)
        self.assertTrue('Via:' in self.proxy.topvia) 