import unittest
import socket
from proxy import SipTracedUDPServer, UDPHandler
import logging

class TestProxy(unittest.TestCase):
    def setUp(self):
        import logging
        # Create loggers
        self.sip_logger = logging.getLogger('SipLogger')
        self.sip_logger.setLevel(logging.INFO)
        
        self.main_logger = logging.getLogger('MainLogger')
        self.main_logger.setLevel(logging.INFO)
        # Add a handler to see the output
        handler = logging.StreamHandler()
        self.main_logger.addHandler(handler)
        
        # Create options object with all required attributes
        class Options:
            def __init__(self):
                self.terminal = True
                self.debug = False
                self.dump = False
                self.sip_no_record_route = False
                self.sip_no_via = False
                self.sip_no_proxy_auth = False
                self.sip_no_hacks = False
                self.sip_exposed_ip = None
                self.sip_exposed_port = None
        
        self.proxy = SipTracedUDPServer(
            ('127.0.0.1', 5060),
            UDPHandler,
            sip_logger=self.sip_logger, 
            main_logger=self.main_logger,
            options=Options()
        )
    
    def test_server_init(self):
        self.assertIsNotNone(self.proxy)
        self.assertEqual(self.proxy.server_address[0], '127.0.0.1')
        self.assertEqual(self.proxy.server_address[1], 5060)

    # ... rest of test cases ... 