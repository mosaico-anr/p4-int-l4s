#!/usr/bin/python
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script parses the data.csv in each test configuration and renders a graph
#
# TCP rtt is calculated based on tsval and tsecr values
#
import re
import json
import os
import matplotlib as mpl
#if os.environ.get('DISPLAY','') == '':
    #print('no display found. Using non-interactive Agg backend')
mpl.use('Agg')

from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
import csv, sys
import matplotlib
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D
from datetime import datetime
import numpy as np

# number of ticks per second, e.g.,
# 100 => group by each 10 millisecond
TICKS_PER_SECOND=100.0

def calcul( func, arr ):
    if len(arr) == 0:
        return 0

    if func == "SUM":
        return np.sum( arr )
    elif func == "AVG":
        return np.average( arr )
    elif func == "COUNT":
        return len(arr)


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
    dic={}
    keys=["total"]

    #max of 4 bytes
    MAX_PROBABILITY = 0xFFFFFFFF
    for row in data:
        # round the timestamp to millisecond
        ts = int(float(row[ts_col])*TICKS_PER_SECOND)

        # initialize
        if ts not in dic:
            dic[ts]={}

        item = dic[ts]
    
        #remember timestamp
        item[ts_col] = ts

        #group elements in an array
        for i in cols:
            #for the first time => init the array
            if i not in item:
                item[i] = {"total": []}

            val = 0
            # specific traitment for TCP rtt
            if i == "tcp.rtt":
                val = get_tcp_rtt(row, data)
            elif i == "int.mark_probability":
                val = int(int(row[i])*100/ MAX_PROBABILITY)
            elif i in row:
                val = int(row[i])

            # ignore zero value that represent a "not available" avlue
            if val == 0:
                continue
            
            # empty IP?
            if row["ip.src"] == "" or row["ip.dst"] == "":
                continue

            key = "{0} -> {1}".format( row["ip.src"], row["ip.dst"] )
            # remember the set of keys
            if key not in keys:
                keys.append( key )

            if key not in item[i]:
                item[i][key] = []

            item[i][key].append( val )
            item[i]["total"].append( val )

    #get final value of each row
    for ts in dic:
        item = dic[ts]
        for i in cols:
            for k in keys:
                if( k in item[i] ):
                    item[i][k] = calcul( cols[i]["fun"], item[i][k] )
                else:
                    item[i][k] = 0

    return dic, keys

def get(dic, x, index, key):
    '''
    Get a "column" in the dic
    '''
    ret = []
    for i in x:
        #print(i)
        val = 0
        if i in dic and key in dic[i][index]:
            #print(dic[i])
            val = dic[i][index][key]
        ret.append( val )
    return ret

def stats(dic, x, index, key):
    '''
    Get a "column" in the dic
    '''
    arr = []
    for i in x:
        #print(i)
        #print(dic)
        if i in dic and key in dic[i][index]:
            #print(dic[i])
            arr.append( dic[i][index][key] )

    return {
        "mean"  : round( np.mean( arr ), 2),
        "median": round( np.median( arr ), 2),
        "sum"   : np.sum( arr )
    }


if len(sys.argv) != 2:
    print("Usage: {0} file.csv\n".format( sys.argv[0]))
    sys.exit(1)

FILE_PATH = sys.argv[1]
print("Processing {0}".format( FILE_PATH ))

DATA = read_csv( FILE_PATH )


COLS={
    #key : function of calcul
    "meta.packet_index":    {"fun": "COUNT", "unit": "packets"},
    "meta.packet_len" :     {"fun": "SUM",   "unit": "bytes"},
    "quic_ietf.spin_bit":   {"fun": "SUM",   "unit": "packets"}, 
    "quic_ietf.rtt":        {"fun": "AVG",   "unit": "microseconds"},
    "int.hop_latencies":    {"fun": "AVG",   "unit": "microseconds"},
    "int.hop_queue_occups": {"fun": "AVG",   "unit": "packets"},
    "int.hop_l4s_mark":     {"fun": "SUM",   "unit": "packets"},
    # LL does not drop packets => always zero
    #"int.hop_l4s_drop": "SUM",
    "int.mark_probability": {"fun": "AVG",   "unit": "percentage"}
}

LATENCY_FIELD="quic_ietf.rtt"

# use tcp
if is_tcp_data( DATA ):
    # remove QUIC or UDP
    # use list() to avoid "RuntimeError: dictionary changed size during iteration"
    # https://stackoverflow.com/questions/11941817
    for i in list(COLS):
        if i.startswith("quic") or i.startswith("udp"):
            del COLS[i]
    # add TCP
    COLS["tcp.rtt"] = {"fun": "AVG", "unit": "microseconds"}
    LATENCY_FIELD="tcp.rtt"

dic, keys = process_data( DATA, cols=COLS )
minX=0
maxX=0

print("number of avail ticks: {0}".format(len(dic)) )
# get min and max timestamp
for i in dic:
    val = dic[i]["meta.packet_index"]["total"]
    
    #ignore leading zero
    if maxX == 0 and val == 0:
        continue
        
    i = int(i)
    #init
    if maxX == 0:
        minX = i
        maxX = i
    else:
        if i > maxX :
            maxX = i
        if i < minX :
            minX = i

# limit distance between min-max
# 60 seconds

if maxX - minX > 60*TICKS_PER_SECOND:
    maxX = minX + 60*TICKS_PER_SECOND
# 30 second
elif maxX - minX > 30*TICKS_PER_SECOND:
    maxX = minX + 30*TICKS_PER_SECOND
else:
    # print("axis Ox is not available")
    None


# x Axis is a range from min - max
x = range(int(minX), int(maxX))
xDate = [ datetime.fromtimestamp(ts*1.0/TICKS_PER_SECOND) for ts in x]

print("number of ticks to draw: {0}".format(len(x)) )

plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (30,3*len(COLS) )
# space between subplot
#plt.rcParams['figure.constrained_layout.use'] = True
#plt.subplots_adjust( hspace=100 )
# number of y ticks
plt.locator_params(axis='y', nbins=5)
#plt.rcParams['axes.titlepad'] = -14 #push title down (inside the chart) 

#global x_cl, x_ll
fig,axs=plt.subplots( len(COLS)  )

counter=0
COLORS=["black", "red", "blue", "magenta"]

result = {}
for col in COLS:
    ax = axs[counter]
    counter += 1
    color = 0
    result[col] = {}

    for key in keys:
        stat_val = stats(dic, x, col, key)
        stat_val["unit"] = COLS[col]["unit"]
        result[col][key] = stat_val

        label = "{0} (mean={1}, median={2} {3})".format( key, stat_val["mean"], stat_val["median"], COLS[col]["unit"])
        ax.plot( xDate, get(dic, x, col, key), label=label, color=COLORS[ color ] )
        color += 1
    ax.set_title( "{0} ({1} of each 10 millisecond))".format( col, COLS[col]["fun"] ))
    ax.grid()
    ax.legend(loc="upper left")


# Save as pdf
#plt.savefig( "{0}-{1}-pps.pdf".format(FILE_NAME, TS_COL_INDEX), dpi=60, format='pdf', bbox_inches='tight')
output =  "{0}.png".format(FILE_PATH)
print("write to {0}".format( output ))
plt.savefig( output, dpi=70, format='png', bbox_inches='tight')

#if os.environ.get('DISPLAY','') != '':
#    plt.show()


#print("{0}".format( json.dumps(result, indent=2 )))


print("\n")

# FILE_PATH = ".../unrespECN-bw_50Mbps-duration_60s--20230322-124338/data.csv"
match = re.search(r"(?P<type>(unrespECN|iperf3|legit))-bw_(?P<bw>\d+)Mbps-duration_(?P<duration>\d+)s", FILE_PATH)

# if we cannot guess the traffic type and limited bandwidth
if not match:
    match = {"type": "?", "bw": "?"}

print("| traffic type | limited bw (Mbps) | mean bw (Mbps) | duration (s) | nb step mark | mean queue delay (ms) | median queue delay (ms) | mean total delay (ms) |")
print("| {0:>12} | {1:>17} | {2:>14} | {3:>12} | {4:>12} | {5:>21} | {6:>23} | {7:>21} |".format(
    match["type"],
    match["bw"],
    round( result["meta.packet_len"]["total"]["mean"] * 8 * TICKS_PER_SECOND / 1000000, 2),
    (maxX - minX) / TICKS_PER_SECOND,
    result["int.hop_l4s_mark"]["total"]["sum"],
    round(result["int.hop_latencies"]["total"]["mean"]   / 1000, 2),
    round(result["int.hop_latencies"]["total"]["median"] / 1000, 2),
    round(result[LATENCY_FIELD]["total"]["mean"] / 1000, 2),
))
print("\n")

