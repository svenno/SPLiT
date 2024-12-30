import unittest
from httpserver import HTTPD

class TestHTTP(unittest.TestCase):
    def setUp(self):
        self.http = HTTPD(
            ip='127.0.0.1',
            port=8080,
            mode_debug=True,
            work_directory='./http'
        )

    def test_server_init(self):
        self.assertEqual(self.http.ip, '127.0.0.1')
        self.assertEqual(self.http.port, 8080)
        self.assertTrue(self.http.mode_debug)
        self.assertEqual(self.http.work_directory, './http') 