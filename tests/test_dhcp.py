import unittest
import socket
import struct
from pypxe.dhcp import DHCPD, default_lease

class TestDHCP(unittest.TestCase):
    def setUp(self):
        self.dhcp = DHCPD(
            ip='127.0.0.1',
            offerfrom='192.168.1.100',
            offerto='192.168.1.200',
            subnetmask='255.255.255.0',
            router='192.168.1.1',
            dnsserver='8.8.8.8',
            broadcast='192.168.1.255'
        )

    def test_default_lease(self):
        lease = default_lease()
        self.assertEqual(lease['ip'], '')
        self.assertEqual(lease['expire'], 0)

    def test_next_ip(self):
        ip = self.dhcp.nextIP()
        self.assertTrue(ip.startswith('192.168.1.'))
        self.assertNotEqual(ip, '192.168.1.0')  # Should not assign .0 address

    def test_tlv_encode(self):
        tag = 1
        value = b'test'
        result = self.dhcp.tlvEncode(tag, value)
        self.assertEqual(len(result), 6)  # 1 byte tag + 1 byte length + 4 bytes value 