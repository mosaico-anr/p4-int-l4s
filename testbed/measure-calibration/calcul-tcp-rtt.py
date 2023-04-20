#!/usr/bin/python
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script parses the data.csv in each test configuration and renders a graph
#

import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
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



def read_data(file_name = "data.csv", ts_col="timestamp", cols=[]):
    '''
    Read data from a csv file. For each line in the csv, extract only the fields naming in `cols`
    return a dict whose keys are timestamp
    '''
    reader = csv.DictReader( open( file_name ), delimiter= ',', )
    
    dic={}
    keys=["total"]

    for row in reader:
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
            if i in row:
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
                    item[i][k] = calcul( cols[i], item[i][k] )
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

def avg(dic, x, index, key):
    '''
    Get a "column" in the dic
    '''
    ret = 0
    counter = 0
    for i in x:
        #print(i)
        #print(dic)
        if i in dic and key in dic[i][index]:
            #print(dic[i])
            ret += dic[i][index][key]
            counter += 1
    if counter == 0:
        return 0
    return int( ret/counter )

if len(sys.argv) != 2:
    print("Usage: {0} file.csv\n".format( sys.argv[0]))
    sys.exit(1)

FILE_PATH = sys.argv[1]
print("Processing {0}".format( FILE_PATH ))


COLS={
    #key : function of calcul
    "meta.packet_index": "COUNT",
    "meta.packet_len" : "SUM",
    "quic_ietf.spin_bit": "SUM", 
    "quic_ietf.rtt": "AVG",
    "int.hop_latencies": "AVG",
    "int.hop_queue_occups": "AVG",
    "int.hop_l4s_mark": "SUM",
    # LL does not drop packets => always zero
    #"int.hop_l4s_drop": "SUM",
    "int.mark_probability": "AVG"
}

dic, keys = read_data( FILE_PATH, cols=COLS )
minX=0
maxX=0

print("number of avail ticks: {0}".format(len(dic)) )
# get min and max timestamp
for i in dic:
    val = dic[i]["meta.packet_index"]
    #ignore leading zero
    if maxX == 0 and val == 0:
        continue
        
    i = int(i)
    
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
    print("axis Ox is not available")
    sys.exit(0)


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
for col in COLS:
    ax = axs[counter]
    counter += 1
    color = 0
    for key in keys:
        label = "{0} (avg: {1})".format( key, avg(dic, x, col, key))
        ax.plot( xDate, get(dic, x, col, key), label=label, color=COLORS[ color ] )
        color += 1
    ax.set_title( "{0} ({1} of each 10 millisecond))".format( col, COLS[col] ))
    ax.grid()
    ax.legend(loc="upper left")

# Save as pdf
#plt.savefig( "{0}-{1}-pps.pdf".format(FILE_NAME, TS_COL_INDEX), dpi=60, format='pdf', bbox_inches='tight')
output =  "{0}.png".format(FILE_PATH)
print("write to {0}".format( output ))
plt.savefig( output, dpi=70, format='png', bbox_inches='tight')

#if os.environ.get('DISPLAY','') != '':
#    plt.show()
