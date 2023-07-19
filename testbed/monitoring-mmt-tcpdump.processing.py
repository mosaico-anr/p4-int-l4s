#!/usr/bin/python3
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script parses the data.csv in each test configuration, then extract the necessaire metrics then write the result to another csv
#
# TCP rtt is calculated based on tsval and tsecr values
#
import os, csv, sys

def get_tcp_rtt(current_pkt, all_pkts):
    '''
    Get RTT in microsecond of TCP packets using tcp.tsval and tcp.tsecr
    '''
    ONE_M = 1000000 #microsecond
    
    # init "static" variables
    if len( get_tcp_rtt.tsval ) == 0:
        for pkt in all_pkts:
            ts = int(float(pkt["timestamp"]) * ONE_M)
            tsval = pkt["tcp.tsval"]
            tsecr = pkt["tcp.tsecr"]
            # get lattest tsval
            if (tsval not in get_tcp_rtt.tsval) or (get_tcp_rtt.tsval[ tsval ] < ts): 
                get_tcp_rtt.tsval[ tsval ] = ts
            # get oldest tsecr
            if (tsecr not in get_tcp_rtt.tsecr) or (get_tcp_rtt.tsecr[ tsecr ] > ts):
                get_tcp_rtt.tsecr[ tsecr ] = ts


    tsval = current_pkt["tcp.tsval"]
    tsecr = current_pkt["tcp.tsecr"]
    ts    = int(float(current_pkt["timestamp"]) * ONE_M)

    delta1 = 0
    #search packet which is echoed
    if tsecr in get_tcp_rtt.tsval:
        delta1 = ts - get_tcp_rtt.tsval[tsecr]

    delta2 = 0
    #search packet which echos the current packet
    if tsval in get_tcp_rtt.tsecr:
        delta2 = get_tcp_rtt.tsecr[tsval] - ts

    if delta1 > 0 and delta2 > 0:
        return delta1 + delta2
    elif delta1 < 0 or delta2 < 0:
        #print("unordered packet")
        None

    return 0
# global variables to cache tcp.tsval and tsecr
get_tcp_rtt.tsval = {}
get_tcp_rtt.tsecr = {}


def read_csv(file_name = "data.csv"):
    '''
    Read CSV into an array
    '''
    reader = csv.DictReader( open( file_name ), delimiter= ',', )
    data = []
    for row in reader:
        data.append( row )
    return data


def is_tcp_data( data ):
    '''
    whether data contain TCP (iperf3) instead of UDP (quic)
    '''
    for row in data:
        if "tcp.tsval" not in row:
            return False

        if row["tcp.tsval"] != "0" and row["tcp.tsval"] != None:
            return True
    return False


def process_data(data, ts_col="timestamp", cols=[]):
    '''
    Read data from a csv file. For each line in the csv, extract only the fields naming in `cols`
    return a dict whose keys are timestamp
    '''
    # end-to-end latency: either tcp.rtt or quic_ietf.rtt
    IS_TCP = is_tcp_data( DATA )

    #map metric from MMT to Marius' requrements
    MAP = {
        "timestamp"            : "timestamp",
        "ip.src"               : "src-ip",
        "ip.dst"               : "dst-ip",
        "meta.packet_len"      : "packet-len",
        "int.hop_latencies"    : "queue-delay",
        "int.hop_queue_occups" : "queue-occups",
        "int.mark_probability" : "mark-proba",
        "int.hop_l4s_mark"     : "step-mark"
    }
    if IS_TCP:
        MAP["tcp.src_port" ] = "src-port"
        MAP["tcp.dest_port"] = "dst-port"
        MAP["tcp.rtt"]       = "total-delay"
    else:
        MAP["udp.src_port" ] = "src-port"
        MAP["udp.dest_port"] = "dst-port"
        MAP["quic_ietf.rtt"] = "total-delay"

    new_data = []

    #max of 4 bytes
    MAX_PROBABILITY = 0xFFFFFFFF

    
    index = 0
    # for each row in the csv file
    for row in data:
        # empty IP? MMT may report ARP packet
        if row["ip.src"] == "" or row["ip.dst"] == "":
            continue

        index += 1
        new_row = {"index": index}
        for i in MAP:
            v = MAP[i]
            #for the first time => init the array

            val = 0
            # specific traitment for TCP rtt
            if i == "tcp.rtt":
                val = get_tcp_rtt(row, data)
            elif i == "int.mark_probability":
                val = int(int(row[i])*100/ MAX_PROBABILITY)
            elif i in row:
                val = row[i]

            new_row[v] = val
        new_data.append( new_row )

    return new_data


if len(sys.argv) != 2:
    print("Usage: {0} file.csv\n".format( sys.argv[0]))
    sys.exit(1)

FILE_PATH = sys.argv[1]
print("Processing {0}".format( FILE_PATH ))

DATA = read_csv( FILE_PATH )
new_data  = process_data( DATA )

dirname = os.path.dirname(FILE_PATH)
if len(dirname) == 0:
    dirname = "."

output_filename = "{0}/new_data.csv".format( dirname )
print(" --> writing to {0}".format( output_filename ))
with open(output_filename, 'w') as f:
    fieldnames = new_data[0].keys()

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows( new_data ) 
