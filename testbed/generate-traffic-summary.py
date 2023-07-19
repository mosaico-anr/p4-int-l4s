#!/usr/bin/python
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script parses the execution log to generate a summary table of tests
#
import re
import json
import os
import sys
from datetime import datetime
import glob
import numpy as np
import json

if len(sys.argv) != 2:
    print("Usage: {0} ./round-1/".format( sys.argv[0]))
    sys.exit(1)




FILE_PATH = sys.argv[1]

#print("{0}".format( json.dumps(result, indent=2 )))

def get_log(filename):
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
 
            if not line:
                break
            if line.startswith("|traffic type|"):
                return f.readline()
 

def get_nic_stat(filename):
    data = {}
    with open(filename, 'r') as f:
        data = json.load(f)
        #|svr tx pkt|cli rx pkt|cli tx pkt|svr rx pkt|
        return "{0:>9} |{1:>9} |{2:>9} |{3:>9} |".format( data["server_tx_packets"], data["client_rx_packets"], data["client_tx_packets"], data["server_rx_packets"] )
    return "          |          |          |          |"

output = open(FILE_PATH + "/traffic-summary.md", "w")

def log(msg):
    global output
    print(msg)
    output.write("{0}\n".format(msg))

log("|cli/svrs|traffic type|lim bw|mean bw-Mbps|  dura-s|# stepmark|mean lq delay-ms|med lq dlay-ms|mean w0 lq delay-ms|med w0 lq dlay-ms|mean tot dlay-ms|med tot dlay-ms|mean pkt-byte|# packets|svr tx pkt|cli rx pkt|cli tx pkt|svr rx pkt|")

filenames=[]
for filename in glob.iglob(FILE_PATH + '/**/script.log', recursive=True):
    filenames.append( filename )

REGEX = r"(?P<type>(unrespECN|iperf3|legit))-bw_(?P<bw>\d+)Mbps-duration_(?P<duration>\d+)s-clients_(?P<clients>\d+)-servers_(?P<servers>\d+)"

def _sort( s ):
    match = re.search(REGEX, s )

    # if we cannot guess the traffic type and limited bandwidth
    if not match:
        return ""
    s =  "{:s}-{:04d}-{:4d}-{:04d}-{:04d}".format(match["type"],  int(match["bw"]), int(match["duration"]), int(match["clients"]), int(match["servers"]))
    #print(s)
    return s


filenames.sort( reverse=True, key=_sort )


for filename in filenames:
    # FILE_PATH = ".../unrespECN-bw_50Mbps-duration_60s--20230322-124338/data.csv"
    match = re.search(REGEX, filename )

    # if we cannot guess the traffic type and limited bandwidth
    if not match:
        continue

    line = get_log( filename )
    if not line:
        continue

    nic_stat_filename = os.path.join( os.path.dirname(filename), "stat_nic.json")
    #v = [float(i) for i in v]

    log("|{0:>4}/{1:>2} |{2:>11} |{3:>5} |{4}{5}".format( match["clients"], match["servers"], match["type"], match["bw"], line[26:-1], get_nic_stat(nic_stat_filename) ))
    
output.close()
print("\n")

