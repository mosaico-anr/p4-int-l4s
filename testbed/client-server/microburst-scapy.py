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
import time

def main():

    if len(sys.argv) < 6:
        print 'pass 4 arguments: <iface> <mac-next> <ip-dest> <ms> <nb_packet> [tcp-replay-argument]'
        exit(1)

    iface = sys.argv[1]
    dmac   = sys.argv[2]
    dst_addr = socket.gethostbyname(sys.argv[3])
    ms     = int(sys.argv[4]) #burst duration in millisecond
    nb_pkt = int(sys.argv[5])
    replay_args = sys.argv[6:]

    print "sending on interface %s to %s" % (iface, str(dst_addr))
    pkt =  Ether(src=get_if_hwaddr(iface), dst=dmac)
    pkt = pkt / IP(dst=dst_addr, tos=3)
    
    payload = " " * nb_pkt
    #pkt = pkt /  TCP(dport=1234, sport=sport) / payload
    #pkt_arr = fragment( pkt, fragsize=20 )
    pkt_arr = []
    
    for i in range(nb_pkt):
       pkt_arr.append( pkt / TCP(dport=1234, sport=random.randint(49152,65535), seq=i) / " ")

    #create microburst pattern
    interval = ms / 1000.0 / (nb_pkt/10)

    #a float number: second since the epoch
    now = time.time()
    #5/10: normal, 1/10: burst, 4/10: normal
    for i in range( nb_pkt ):
       pkt_arr[i].time = now
       now += interval

    now = pkt_arr[ nb_pkt/2 ].time
    for i in range( 5*nb_pkt/10, 6*nb_pkt/10 ):
       pkt_arr[i].time = now
    
    wrpcap( '/tmp/microburst.pcap', pkt_arr)

    #sending via tcpreplay
    sendpfast(pkt_arr, iface=iface, file_cache=True, replay_args=replay_args)

if __name__ == '__main__':
    main()
