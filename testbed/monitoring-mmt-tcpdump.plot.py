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
import matplotlib.colors as mcolors
import matplotlib.dates as md

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



def read_csv(file_name = "data.csv"):
    '''
    Read CSV into an array
    '''
    reader = csv.DictReader( open( file_name ), delimiter= ',', )
    data = []
    for row in reader:
        data.append( row )
    return data


def process_data(data, ts_col="timestamp", cols=[]):
    '''
    Read data from a csv file. For each line in the csv, extract only the fields naming in `cols`
    return a dict whose keys are timestamp
    '''
    # end-to-end latency: either tcp.rtt or quic_ietf.rtt
    global LATENCY_FIELD
    dic={}
    keys=["total"]

    #max of 4 bytes
    MAX_PROBABILITY = 0xFFFFFFFF

    
    # for each row in the csv file
    for row in data:
        # round the timestamp to millisecond
        ts = int(float(row[ts_col])*TICKS_PER_SECOND)

        # initialize
        if ts not in dic:
            dic[ts]={}

        item = dic[ts]
    
        #remember timestamp
        item[ts_col] = ts


        #for each metric we want to process:
        #  we will create an array for each metric
        #   then append the value into the array
        #  The array will be used later to calculate MEAN, MEDIAN, etc
        #group elements in an array
        
        for i in cols:
            #for the first time => init the array
            if i not in item:
                item[i] = {"total": []}

            val = -1
            if i in row:
                val = int(row[i])

            # ignore zero value that represent a "not available" avlue
            if val == -1:
                continue
            
            #key = "{0} -> {1}".format( row["src-ip"], row["dst-ip"] )
            key = "{0}:{1} -> {2}:{3}".format( row["src-ip"], row["src-port"], row["dst-ip"], row["dst-port"] )
            #key = "{0}:{1} -> {2}:{3}".format( row["ip.src"], row["udp.src_port"], row["ip.dst"], row["udp.dest_port"] )
            # remember the set of keys
            if key not in keys:
                keys.append( key )

            if key not in item[i]:
                item[i][key] = []

            item[i][key].append( val )
            item[i]["total"].append( val )

        # special traitement for w0-latency: delais total en excluant le delais de la file faible latence
        
        #first time: init the array

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
    if len( arr ) == 0:
        return {
            "mean"  : 0,
            "median": 0,
            "sum"   : 0,
            "max"   : 0
        }
        
    return {
        "mean"  : round( np.mean( arr ), 2),
        "median": round( np.median( arr ), 2),
        "sum"   : np.sum( arr ),
        "max"   : np.max( arr )
    }


if len(sys.argv) != 2:
    print("Usage: {0} file.csv\n".format( sys.argv[0]))
    sys.exit(1)

FILE_PATH = sys.argv[1]
print("Processing {0}".format( FILE_PATH ))

DATA = read_csv( FILE_PATH )


COLS={
    #key : function of calcul
    "index":         {"fun": "COUNT", "label": "throughput",    "unit": "packets/ms"},
    "packet-len" :   {"fun": "SUM",   "label": "bandwidth",     "unit": "bytes/ms"},
    "total-delay":   {"fun": "AVG",   "label": "total-delay",   "unit": "microseconds"},
    "queue-delay":   {"fun": "AVG",   "label": "queue-latency", "unit": "microseconds"},
    "queue-occups":  {"fun": "AVG",   "label": "queue-occups",  "unit": "packets"},
    "step-mark":     {"fun": "SUM",   "label": "step-mark",     "unit": "packets"},
    "mark-proba":    {"fun": "AVG",   "label": "mark-proba",    "unit": "percentage"}
}

dic, keys = process_data( DATA, cols=COLS )
minX=0
maxX=0

print("number of avail ticks: {0}".format(len(dic)) )
print(keys)
# get min and max timestamp
for i in dic:
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
#if maxX - minX > 70*TICKS_PER_SECOND:
#    #maxX = minX + 60*TICKS_PER_SECOND
#    None
## 60 seconds
#elif maxX - minX > 60*TICKS_PER_SECOND:
#    maxX = minX + 60*TICKS_PER_SECOND
## 30 second
#elif maxX - minX > 30*TICKS_PER_SECOND:
#    maxX = minX + 30*TICKS_PER_SECOND
#else:
#    # print("axis Ox is not available")
#    None


# x Axis is a range from min - max
x = range(int(minX), int(maxX))
xDate = [ datetime.fromtimestamp(ts*1.0/TICKS_PER_SECOND) for ts in range(0, int(maxX-minX))]

print("number of ticks to draw: {0}".format(len(x)) )

number_of_plots = len(COLS)*len(keys)
plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (30,2*number_of_plots )
# space between subplot
#plt.rcParams['figure.constrained_layout.use'] = True
#plt.subplots_adjust( hspace=100 )
# number of y ticks
plt.locator_params(axis='y', nbins=5)
#plt.rcParams['axes.titlepad'] = -14 #push title down (inside the chart) 

#global x_cl, x_ll
fig,axs=plt.subplots( number_of_plots  )

xfmt = md.DateFormatter('%M:%S')

counter=0
COLORS=["black", "red", "blue", "magenta", "pink", "green", "purple", "brown", "gray", "olive", "cyan", "plum", "violet" ]
#COLORS=mcolors.TABLEAU_COLORS

last_col=""
result = {}
for col in COLS:
    color = 0
    result[col] = {}

    for key in keys:

        stat_val = stats(dic, x, col, key)
        stat_val["unit"] = COLS[col]["unit"]
        result[col][key] = stat_val

        #do not draw total, but only each flow
        #if key == "total":
        #    continue

        ax = axs[counter]
        counter += 1


        label = "{0} (mean={1}, median={2} {3})".format( key, stat_val["mean"], stat_val["median"], COLS[col]["unit"])
        ax.plot( xDate, get(dic, x, col, key), label=label, color=COLORS[ color ] )
        

        #draw title only on the first plot in the serie
        if color == 0:
            ax.set_title( "{0} ({1} - {2} of each 10 millisecond))".format( col,  COLS[col]["label"], COLS[col]["fun"] ))
        ax.grid()
        ax.legend(loc="upper left")
        ax.xaxis.set_major_formatter(xfmt)
        
        xticks = ax.xaxis.get_major_ticks()
        xticks[0].label1.set_visible(False) #hide the first ax tick
        #xticks[-1].label1.set_visible(False) #hide the last ax tick
        ax.margins(x=0,y=0)

        #repeat color
        color += 1
        if color >= len(COLORS):
            color = 0
            

# Save as pdf
#plt.savefig( "{0}-{1}-pps.pdf".format(FILE_NAME, TS_COL_INDEX), dpi=60, format='pdf', bbox_inches='tight')
output =  "{0}.png".format(FILE_PATH)
print("write to {0}".format( output ))
plt.savefig( output, dpi=70, format='png', bbox_inches='tight')

#if os.environ.get('DISPLAY','') != '':
#    plt.show()


print(result["packet-len"])
#print("{0}".format( json.dumps(result, indent=2 )))

print("\n")

def _round(val):
    return ('%.3f' % (val))
    #return round(val, n)

# FILE_PATH = ".../unrespECN-bw_50Mbps-duration_60s--20230322-124338/data.csv"
match = re.search(r"(?P<type>(unrespECN|iperf3|legit))-bw_(?P<bw>\d+)Mbps-duration_(?P<duration>\d+)s", FILE_PATH)

# if we cannot guess the traffic type and limited bandwidth
if not match:
    match = {"type": "?", "bw": "?"}

#      |    0       |     1     |     2      |   3  |   4      |    5           |     6        |         7         |        8        |     9          |     10        |     11      |  12     |
print("|traffic type|lim bw-Mbps|mean bw-Mbps|  dura-s|# stepmark|mean lq delay-ms|med lq dlay-ms|mean w0 lq delay-ms|med w0 lq dlay-ms|mean tot dlay-ms|med tot dlay-ms|mean pkt-byte|# packets|")
print("|{0:>11} |{1:>10} |{2:>11} |{3:>5} |{4:>9} |{5:>15} |{6:>13} |{7:>18} |{8:>16} |{9:>15} |{10:>14} |{11:>13}|{12:>8} |".format(
    match["type"],
    match["bw"],
    _round( result["packet-len"]["total"]["mean"] * 8 * TICKS_PER_SECOND / 1000000),
    _round( (maxX - minX) / TICKS_PER_SECOND ),
    result["step-mark"]["total"]["sum"],
    _round(result["queue-delay"]["total"]["mean"]   / 1000),
    _round(result["queue-delay"]["total"]["median"] / 1000),
    
    _round((result["total-delay"]["total"]["mean"]  - result["queue-delay"]["total"]["mean"] )   / 1000),
    _round((result["total-delay"]["total"]["median"]- result["queue-delay"]["total"]["median"] ) / 1000),
    
    _round(result["total-delay"]["total"]["mean"]   / 1000),
    _round(result["total-delay"]["total"]["median"] / 1000),
    _round(result["packet-len"]["total"]["sum"] / result["index"]["total"]["sum"]),
    result["index"]["total"]["sum"]
))
print("\n")

