#!/usr/bin/python
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script loads a qlog file and extract interested fields which are defined in "csv_header"
#
# Note: https://www.ietf.org/id/draft-ietf-quic-qlog-quic-events-03.html#name-metrics_updated

import sys
import json, csv
import traceback
import os
from os.path import isfile, join

def fetch(dic, field_arr, default_value=0 ):
    for f in field_arr:
        if f in dic:
            dic = dic[f]
        else:
            return default_value
    return dic

class qlogExtract:
    def __init__(self, output_io):
        self.csv_io = csv.writer(output_io, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.csv_io.writerow( self.csv_header() )
        self.reset_values()

    def reset_values( self ):
        self.relative_time = 0 #unit: us
        self.udp_payload_size = 0 #size of UDP payload
        self.is_packet_sent = 0 #0: received, 1: sent
        self.min_rtt = 0
        self.latest_rtt = 0
        self.smoothed_rtt = 0
        self.bytes_in_flight = 0
        self.cwnd = 0

    def csv_header( self ):
        return [
            "relative_time",
            "udp_payload_size",
            "is_packet_sent",
            "min_rtt",
            "latest_rtt",
            "smoothed_rtt",
            "bytes_in_flight",
            "cwnd"
        ]
    def csv_row( self ):
        return [
            self.relative_time,
            self.udp_payload_size,
            self.is_packet_sent,
            self.min_rtt,
            self.latest_rtt,
            self.smoothed_rtt,
            self.bytes_in_flight,
            self.cwnd
        ]
    def write_then_reset_values( self ):
        self.csv_io.writerow( self.csv_row() )
        self.reset_values()

    def process(self, file_name):
        try:
            with open(file_name) as json_file:
                data = json.load(json_file)
                # for key in data:
                #    print(key + ": " + str(len(data[key])))
                if 'traces' in data:
                    traces   = data['traces']
                    start_ts = 0
                    for trace in traces:
                        if 'events' in trace:
                            for event in trace['events']:
                                event_type = event[2]
                                data       = event[3]
                                rel_time   = event[0] 
 

                                # at UDP level
                                # L4S switch works on each datagram
                                # => we will create a CSV row for each datagram
                                # write data to file and reset the counters
                                #
                                # As datagram_reeived is the first event in its event chain, e.g., datagram_received, packet_received, ...
                                # => we write only when we visited other events in the chain
                                # => we write previous when we see the new datagram_received

                                # this is to collect data
                                if event_type == "datagram_received" or event_type == "datagram_sent":
                                    #a new event is comming, report the last datagram_received event
                                    if self.is_packet_sent == "false":
                                        self.write_then_reset_values()

                                    #In picoquic, relative_time is timestamp of very first log event reported.
                                    # as we are interested in only the events below, so we shift the relative_time
                                    if start_ts == 0:
                                        start_ts = rel_time

                                    self.is_packet_sent    = "true" if event_type == "datagram_sent" else "false"
                                    self.udp_payload_size  = fetch( data, ["byte_length"] )
                                    self.relative_time     = rel_time - start_ts
                                #https://www.ietf.org/id/draft-ietf-quic-qlog-quic-events-03.html#name-metrics_updated
                                elif event_type == "metrics_updated":
                                    self.bytes_in_flight += fetch( data, ["bytes_in_flight"] )
                                    self.cwnd            += fetch( data, ["cwnd"] )
                                    self.latest_rtt      += fetch( data, ["latest_rtt"] )
                                    self.min_rtt         += fetch( data, ["min_rtt"] )
                                    self.smoothed_rtt    += fetch( data, ["smoothed_rtt"] )
                                
                                #https://www.ietf.org/id/draft-ietf-quic-qlog-quic-events-03.html#name-datagrams_received
                                #datagram_sent is at the end of its event chain
                                if event_type == "datagram_sent":
                                    self.write_then_reset_values()

        except Exception as e:
            traceback.print_exc()
            print("Cannot load <" + file_name + ">, error: " + str(e));
            return False
# To test, use file sample/small.qlog or sample/big.qlog

if len(sys.argv) == 3:
    qlog_file = sys.argv[1]
    csv_file  = sys.argv[2]
else:
    print("Usage: " + sys.argv[0] + " qlog_file csv_file")
    exit(-1)

print( qlog_file )

qs = qlogExtract( open(csv_file, "w") )
qs.process( qlog_file )
