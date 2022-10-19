#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, sendpfast
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from time import sleep
import datetime

def main():

    if len(sys.argv) != 5:
        print 'pass 4 arguments: <iface> <destination> <pps> <loop>'
        exit(1)

    iface = sys.argv[1]
    dst_addr = socket.gethostbyname(sys.argv[2])
    pps = int(sys.argv[3])
    loop = int(sys.argv[4])

    print "sending on interface %s to %s" % (iface, str(dst_addr))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
    payload = "1"*100
    pkt = pkt / IP(dst=dst_addr, tos=3) / TCP(dport=1234, sport=random.randint(49152,65535)) / payload
    pkt.show2() 

    nb_pkt = 0;
    iteration = 0;
    while True:
        new_pps = pps;
        iteration += 1
        if iteration >= 3:
            iteration = 0
            new_pps *= 100 #amplify to create a burst

        #sending via tcpreplay
        sendpfast(pkt, pps=new_pps, loop=loop, iface=iface)

        #sendp(pkt, count=loop, inter=1./pps)  # 20 packets per second
        nb_pkt += loop
        print" - %s sent %d packets " %( datetime.datetime.now(), nb_pkt )
        sleep(0.1)

if __name__ == '__main__':
    main()