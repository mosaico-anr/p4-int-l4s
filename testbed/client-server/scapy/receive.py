#!/usr/bin/env python
import sys
import struct
import os
from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr
from scapy.all import Packet, IPOption
from scapy.all import IP, TCP, UDP, Raw


def handle_pkt(pkt):
    if TCP in pkt and pkt[TCP].dport == 1234:
        print "got a packet"
        #pkt.show2()
    #    hexdump(pkt)
        sys.stdout.flush()


def main():
    if len(sys.argv) != 2:
        print 'pass 1 argument: <iface>'
        exit(1)
    iface = sys.argv[1]

    print "sniffing on %s" % iface
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()