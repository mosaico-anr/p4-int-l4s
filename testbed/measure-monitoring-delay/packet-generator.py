#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, sendpfast
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP, fragment
from scapy.utils import get_temp_file, tcpdump, wrpcap
import datetime, time

def main():

    if len(sys.argv) < 5:
        print( 'pass 4 arguments: <iface> <mac-next> <ip-dest> <nb_packets> [tcp-replay-argument]' )
        print( 'Example: sudo python packet-generator.py enp0s8 08:00:27:55:C7:75 10.0.1.11 10' )
        exit(1)

    iface = sys.argv[1]
    dmac   = sys.argv[2]
    dst_addr = socket.gethostbyname(sys.argv[3])
    nb_pkt = int(sys.argv[4])
    replay_args = sys.argv[5:]

    print( "sending on interface %s to %s" % (iface, str(dst_addr)) )
    pkt =  Ether(src=get_if_hwaddr(iface), dst=dmac)
    pkt = pkt / IP(dst=dst_addr, tos=3)
    
    for i in range(nb_pkt):
       print( "%d. %s sending ..." %( i, datetime.datetime.now()) )
       pkt_to_send = pkt / TCP(dport=1234, sport=(i+1), seq=i) / " "

       #sending via tcpreplay
       sendpfast([pkt_to_send], iface=iface, file_cache=False, replay_args=replay_args)
       #sleep 10 milli second
       time.sleep(0.01)

if __name__ == '__main__':
    main()
