import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_dhcp import TestDHCP
from test_tftp import TestTFTP
from test_http import TestHTTP
from test_proxy import TestProxy

if __name__ == '__main__':
    unittest.main() 