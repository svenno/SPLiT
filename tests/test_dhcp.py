import unittest
import socket
import struct
from pypxe.dhcp import DHCPD, default_lease

class TestDHCP(unittest.TestCase):
    def setUp(self):
        self.dhcp = DHCPD(
            ip='127.0.0.1',
            port=1067,  # Use non-privileged port
            offerfrom='192.168.1.100',
            offerto='192.168.1.200',
            subnetmask='255.255.255.0',
            router='192.168.1.1',
            dnsserver='8.8.8.8',
            broadcast='192.168.1.255'
        )

    def tearDown(self):
        # Close the DHCP socket
        if hasattr(self.dhcp, 'sock'):
            self.dhcp.sock.close()

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

    def test_ip_range_validation(self):
        # Test that IPs are within the configured range
        for _ in range(10):
            ip = self.dhcp.nextIP()
            ip_parts = list(map(int, ip.split('.')))
            self.assertGreaterEqual(ip_parts[3], 100)  # Should be >= .100
            self.assertLessEqual(ip_parts[3], 200)     # Should be <= .200

    def test_broadcast_address(self):
        # Test broadcast address configuration
        self.assertEqual(self.dhcp.broadcast, '192.168.1.255')
        self.assertEqual(self.dhcp.subnetmask, '255.255.255.0')

    def test_dns_configuration(self):
        # Test DNS server configuration
        self.assertEqual(self.dhcp.dnsserver, '8.8.8.8')
        self.assertEqual(self.dhcp.router, '192.168.1.1') 