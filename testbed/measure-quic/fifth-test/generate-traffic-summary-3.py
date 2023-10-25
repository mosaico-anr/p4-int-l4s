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
 
"""param.json
{
	"server":       "10.0.1.13",
	"client":       "10.0.0.13",
	"bandwidth":    "1 Mbps",
	"power-attack": 0.1,
	"flows":        [{"type":"unrespECN", "start_time": 30, "duration": 60, "serer_port": 10000},{"type":"cl_legit", "start_time": 0, "duration": 120, "serer_port": 2000}]
}
"""

def get_flow_param(filepath):
    try:
       with open( filepath ) as f:
           conf = json.load(f)
           flows = conf["flows"]
           types = dict()
           for flow in flows:
               t = flow["type"]
               if not t in types:
                  types[t] = 0
               types[t] += 1
           ret = ""
           for t in types:
               ret = "{0} {1}*{2}".format(ret, types[t], t)
           return ret
    except Exception as e:
       print("Cannot process file {0}: {1}".format(filepath, e))
       return ""

output = open(FILE_PATH + "/traffic-summary.txt", "w")

def log(msg):
    global output
    print(msg)
    output.write("{0}\n".format(msg))

log("|testId |lim-Mbps|power|mean bw-Mbps|  dura-s|# stepmark|% stepmark|mean lq delay-ms|med lq dlay-ms|mean w0 lq delay-ms|med w0 lq dlay-ms|mean tot dlay-ms|med tot dlay-ms|mean pkt-byte|# packets| flow types")

filenames=[]
for filename in glob.iglob(FILE_PATH + '/**/script.log', recursive=True):
    filenames.append( filename )

REGEX = r"(?P<id>\d+)-bw_(?P<bw>\d+)Mbps-power_(?P<power>\d+(\.\d+)?)"

def _sort( s ):
    match = re.search(REGEX, s )

    # if we cannot guess the traffic type and limited bandwidth
    if not match:
        return ""
    return int(match["id"])


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

    line =  line[26:-1]
    #v = [float(i) for i in v]

    #additional space for "duration"
    space = ""
    if line.find("|", 13) == 20:
        space = " "

    flow_param = get_flow_param( os.path.dirname(filename) + "/param.json" ) 

    log("|{5:>6} |{0:>7} |{1:>4} |{2}|{3}{4}|{6}".format( match["bw"], match["power"], line[0:12], space, line[13:-1], match["id"], flow_param ))
    
output.close()
print("\n")

