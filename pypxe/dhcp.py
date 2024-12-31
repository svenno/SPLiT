'''
This file contains classes and functions that implement the PyPXE DHCP service
'''

import socket
import struct
import os
import pickle
import logging
from collections import defaultdict
from time import time
from socket import error

def default_lease():
    return {'ip': '', 'expire': 0}

class DHCPD:
    '''
        This class implements a DHCP Server, limited to pxe options,
        where the subnet /24 is hard coded. Implemented from RFC2131,
        RFC2132, https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol
        and http://www.pix.net/software/pxeboot/archive/pxespec.pdf
    '''
    def __init__(self, **serverSettings):
        
        self.ip = serverSettings.get('ip', '')
        self.port = serverSettings.get('port', 67)
        self.offerfrom = serverSettings.get('offerfrom', '')
        self.offerto = serverSettings.get('offerto', '')
        self.subnetmask = serverSettings.get('subnetmask', '')
        self.router = serverSettings.get('router', '')
        self.dnsserver = serverSettings.get('dnsserver', '')
        self.broadcast = serverSettings.get('broadcast', '<broadcast>')
        self.fileserver = serverSettings.get('fileserver', '')
        self.filename = serverSettings.get('filename', '')
        self.leases_file = serverSettings.get('leases_file', 'dhcp_leases.dat')
        
        if self.ip == '':
            raise Exception('DHCP IP server')
        if self.port == '':
            raise Exception('DHCP port')
        if self.offerfrom == '':
            raise Exception('DHCP pool start undefined')
        if self.offerto == '':
            raise Exception('DHCP pool end undefined')
        if self.broadcast == '':
            raise Exception('DHCP broadcast undefined')

        try:
            socket.inet_aton(self.offerfrom)
        except:
            raise Exception("Invalid DHCP pool start")
        try:
            socket.inet_aton(self.offerto)
        except:
            raise Exception("Invalid DHCP pool end")
        try:
            socket.inet_aton(self.broadcast)
        except:
            raise Exception("Invalid DHCP broadcast")
        if self.dnsserver != '':
            try:
                socket.inet_aton(self.dnsserver)
            except:
                raise Exception("Invalid DHCP DNS server")
        if self.router != '':
            try:
                socket.inet_aton(self.router)
            except:
                raise Exception("Invalid DHCP Gateway")

        self.mode_debug = serverSettings.get('mode_debug', False) #debug mode
        self.magic = struct.pack('!I', 0x63825363) #magic cookie
        self.logger = serverSettings.get('logger', None)
        
        self.running = True

        # setup logger
        if self.logger == None:
            self.logger = logging.getLogger("DHCP")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        if self.mode_debug:
            self.logger.setLevel(logging.DEBUG)

        if self.router == '':
            self.logger.warning('DHCP router undefined: DHCP opt.3 will not be sent')
        if self.dnsserver == '':
            self.logger.warning('DHCP DNS server undefined: DHCP opt.6 will not be sent')

        self.logger.info(f"NOTICE: DHCP server starting on {self.ip}:{self.port}")
        self.logger.debug('DHCP server is using the following:')
        self.logger.debug('  DHCP Server IP: {}'.format(self.ip))
        self.logger.debug('  DHCP Server Port: {}'.format(self.port))
        self.logger.debug('  DHCP Lease Range: {} - {}'.format(self.offerfrom, self.offerto))
        self.logger.debug('  DHCP Subnet Mask: {}'.format(self.subnetmask))
        self.logger.debug('  DHCP Router: {}'.format(self.router))
        self.logger.debug('  DHCP DNS Server: {}'.format(self.dnsserver))
        self.logger.debug('  DHCP Broadcast Address: {}'.format(self.broadcast))
        self.logger.debug('  DHCP File Server IP: {}'.format(self.fileserver))
        self.logger.debug('  DHCP File Name: {}'.format(self.filename))
        self.logger.debug('  DHCP Leases file: {}'. format(self.leases_file))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port ))
        
        if os.path.isfile(self.leases_file):
            try:
                self.logger.info("Reading leases file: %s" % self.leases_file)
                self.leases = pickle.load(open(self.leases_file, 'r'))
                try:
                    for k,v in self.leases.iteritems():
                        self.logger.info("Imported leases:")
                        self.logger.info("\t%s - %s" % (self.printMAC(k), v))
                except Exception as e:
                    self.logger.error("Cannot read leses file: %s" % e)
            except Exception as e:
                self.logger.error("Cannot load the leases file: %s" % self.leases_file)
                self.leases = defaultdict(default_lease)
        else:
            #key is mac
            #self.leases = defaultdict(lambda: {'ip': '', 'expire': 0})
            self.leases = defaultdict(default_lease)

    def nextIP(self):
        '''
            This method returns the next unleased IP from range;
            also does lease expiry by overwrite.
        '''

        #if we use ints, we don't have to deal with octet overflow
        #or nested loops (up to 3 with 10/8); convert both to 32bit integers
        
        #e.g '192.168.1.1' to 3232235777
        encode = lambda x: struct.unpack('!I', socket.inet_aton(x))[0]
        
        #e.g 3232235777 to '192.168.1.1'
        decode = lambda x: socket.inet_ntoa(struct.pack('!I', x))
        
        fromhost = encode(self.offerfrom)
        tohost = encode(self.offerto)
        
        #pull out already leased ips
        leased = [self.leases[i]['ip'] for i in self.leases
                if self.leases[i]['expire'] > time()]
        
        #convert to 32bit int
        leased = list(map(encode, leased))
        
        #loop through, make sure not already leased and not in form X.Y.Z.0
        for offset in range(tohost - fromhost):
            if (fromhost + offset) % 256 and fromhost + offset not in leased:
                return decode(fromhost + offset)

    def tlvEncode(self, tag, value):
        '''
            Encode a TLV option
        '''
        return struct.pack("BB", tag, len(value)) + value

    def tlvParse(self, raw):
        '''
            Parse a string of TLV encoded options.
        '''
        ret = {}
        while(raw):
            tag = struct.unpack('B', raw[0])[0]
            if tag == 0:  #padding
                raw = raw[1:]
                continue
            if tag == 255:  #end marker
                break
            length = struct.unpack('B', raw[1])[0]
            value = raw[2:2 + length]
            raw = raw[2 + length:]
            if tag in ret:
                ret[tag].append(value)
            else:
                ret[tag] = [value]
        return ret

    def printMAC(self, mac):
        '''
            This method converts the MAC Address from binary to
            human-readable format for logging.
        '''
        return ':'.join(map(lambda x: hex(x)[2:].zfill(2), struct.unpack('BBBBBB', mac))).upper()

    def craftHeader(self, message):
        '''This method crafts the DHCP header using parts of the message'''
        xid, flags, yiaddr, giaddr, chaddr = struct.unpack('!4x4s2x2s4x4s4x4s16s', message[:44])
        clientmac = chaddr[:6]
        
        #op, htype, hlen, hops, xid
        response =  struct.pack('!BBBB4s', 2, 1, 6, 0, xid)
        response += struct.pack('!HHI', 0, 0, 0) #secs, flags, ciaddr
        offer = None
        if self.leases[clientmac]['ip']: #OFFER
            offer = self.leases[clientmac]['ip']
            try:
                socket.inet_aton(offer)
            except Exception:
                self.logger.error('DHCP: Trying to offer an ivalid IP from lease file: %s' % offer)
                return (clientmac, None) 

            self.logger.info('DHCP Assignment from leases file - MAC: {MAC} -> IP: {IP}'.format(MAC = self.printMAC(clientmac), IP = self.leases[clientmac]['ip']))
        else: #ACK
            try:
                offer = self.nextIP()
                socket.inet_aton(offer)
            except Exception:
                self.logger.error('DHCP: Trying to offer an ivalid new IP: %s' % offer)
                return (clientmac, None) 

            self.leases[clientmac]['ip'] = offer
            self.leases[clientmac]['expire'] = time() + 86400
            self.logger.info("Writing to the leases file: %s" % self.leases_file)
            pickle.dump(self.leases, open(self.leases_file, "wb"))
            self.logger.info('New DHCP Assignment - MAC: {MAC} -> IP: {IP}'.format(MAC = self.printMAC(clientmac), IP = self.leases[clientmac]['ip']))

        response += socket.inet_aton(offer) #yiaddr
        response += socket.inet_aton(self.ip) #siaddr
        response += socket.inet_aton('0.0.0.0') #giaddr
        response += chaddr #chaddr
        
        #bootp legacy pad
        response += chr(0) * 64 #server name
        response += chr(0) * 128
        response += self.magic #magic section
        return (clientmac, response)

    def craftOptions(self, opt53, clientmac):
        '''This method crafts the DHCP option fields
            opt53:
                2 - DHCPOFFER
                5 - DHCPACK
            (See RFC2132 9.6)
        '''
        response = self.tlvEncode(53, chr(opt53)) #message type, offer
        response += self.tlvEncode(54, socket.inet_aton(self.ip)) #DHCP Server
        response += self.tlvEncode(1, socket.inet_aton(self.subnetmask)) #SubnetMask
        if self.router != '':
            response += self.tlvEncode(3, socket.inet_aton(self.router)) #Router
        if self.dnsserver != '':
            response += self.tlvEncode(6, socket.inet_aton(self.dnsserver)) #DNS
        response += self.tlvEncode(51, struct.pack('!I', 86400)) #lease time
       
        if self.fileserver != '':
            #TFTP Server OR HTTP Server; if iPXE, need both
            response += self.tlvEncode(66, self.fileserver)
            self.logger.info("Encoded option 66: %s" % self.fileserver)
        
        #filename null terminated
        if self.filename != '':
            response += self.tlvEncode(67, self.filename + chr(0))
            self.logger.info("Encoded option 67: %s" % self.filename)

        response += '\xff'
        return response

    def dhcpOffer(self, message):
        '''This method responds to DHCP discovery with offer'''
        clientmac, headerResponse = self.craftHeader(message)
        if headerResponse == None:
            self.logger.warning("DHCP response not valid, ignoring the request")
            return
        optionsResponse = self.craftOptions(2, clientmac) #DHCPOFFER
        response = headerResponse + optionsResponse
        self.logger.debug('DHCPOFFER - Sending the following')
        self.logger.debug('  <--BEGIN HEADER-->\n\t{headerResponse}\n\t<--END HEADER-->'.format(headerResponse = repr(headerResponse)))
        self.logger.debug('  <--BEGIN OPTIONS-->\n\t{optionsResponse}\n\t<--END OPTIONS-->'.format(optionsResponse = repr(optionsResponse)))
        #self.logger.debug('  <--BEGIN RESPONSE-->\n\t{response}\n\t<--END RESPONSE-->'.format(response = repr(response)))
        try:
            self.sock.sendto(response, (self.broadcast, 68))
        except Exception as e:
            self.logger.error("DHCP: error sending Offer: %s" % e)

    def dhcpAck(self, message):
        '''This method responds to DHCP request with acknowledge'''
        clientmac, headerResponse = self.craftHeader(message)
        if headerResponse == None:
            self.logger.warning("DHCP response not valid, ignoring the request")
            return
        optionsResponse = self.craftOptions(5, clientmac) #DHCPACK
        response = headerResponse + optionsResponse
        self.logger.debug('DHCPACK - Sending the following')
        self.logger.debug('  <--BEGIN HEADER-->\n\t{headerResponse}\n\t<--END HEADER-->'.format(headerResponse = repr(headerResponse)))
        self.logger.debug('  <--BEGIN OPTIONS-->\n\t{optionsResponse}\n\t<--END OPTIONS-->'.format(optionsResponse = repr(optionsResponse)))
        #self.logger.debug('  <--BEGIN RESPONSE-->\n\t{response}\n\t<--END RESPONSE-->'.format(response = repr(response)))
        self.sock.sendto(response, (self.broadcast, 68))

    def validateReq(self):
        # TODO
        # client request is valid only if contains Vendor-Class = PXEClient
        #if 60 in self.options and 'PXEClient' in self.options[60][0]:
        #    self.logger.debug('Valid client request received')
        #    return True
        #if self.mode_debug:
        #    self.logger.debug('Invalid client request received')
        #return False
        return True

    def listen(self):
        '''Main listen loop'''
        self.logger.info("DHCP service running")
        while True:
            if self.running == False:
                self.logger.info("Closing.")
                break
            try:
                message, address = self.sock.recvfrom(1024)
            except error as e:
                continue
            try:
                clientmac = struct.unpack('!28x6s', message[:34])
            except struct.error as e:
                self.logger.debug("Error parsing client mac")
                continue
            self.logger.debug('Received message')
            #self.logger.debug('  <--BEGIN MESSAGE-->\n\t{message}\n\t<--END MESSAGE-->'.format(message = repr(message)))
            self.options = self.tlvParse(message[240:])
            self.logger.debug('Parsed received options')
            self.logger.debug('  <--BEGIN OPTIONS-->\n\t{options}\n\t<--END OPTIONS-->'.format(options = repr(self.options)))
            if not self.validateReq():
                continue
            type = ord(self.options[53][0]) #see RFC2131 page 10
            if type == 1:
                self.logger.debug('Received DHCPOFFER')
                self.dhcpOffer(message)
            elif type == 3 and address[0] == '0.0.0.0':
                self.logger.debug('Received DHCPACK')
                self.dhcpAck(message)
            elif type == 3 and address[0] != '0.0.0.0':
                self.logger.debug('Received DHCPACK')
                self.dhcpAck(message)

    def shutdown(self):
        self.sock.sendto("", (self.ip, self.port))
        self.sock.close()
        self.running = False
