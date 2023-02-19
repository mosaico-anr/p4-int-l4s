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


def read_data(file_name = "data.csv", ts_col="timestamp", cols=[]):
    '''
    Read data from a csv file. For each line in the csv, extract only the fields naming in `cols`
    return a dict whose keys are timestamp
    '''
    reader = csv.DictReader( open( file_name ), delimiter= ',', )
    
    dic={}
    
    for row in reader:
        # round the timestamp to second
        ts = int(float(row[ts_col]))

        # initialize
        if ts not in dic:
            dic[ts]={}

        item = dic[ts]
    
        #remember timestamp
        item[ts_col] = ts

        for i in cols:
            if i in row:
                val = int(row[i])
                if i in item:
                    item[i] += val
                else:
                    item[i]  = val
            else:
                item[i] = 0
    return dic

def get(dic, x, index):
    '''
    Get a "column" in the dic
    '''
    ret = []
    for i in x:
        #print(i)
        if i in dic:
            #print(dic[i])
            ret.append( dic[i][index] )
        else:
            ret.append( 0 )
    return ret

def avg(dic, x, index):
    '''
    Get a "column" in the dic
    '''
    ret = 0
    for i in x:
        #print(i)
        if i in dic:
            #print(dic[i])
            ret += dic[i][index]
    return int( ret/len(x) )

if len(sys.argv) != 2:
    print("Usage: {0} file.csv\n".format( sys.argv[0]))
    sys.exit(1)

FILE_PATH = sys.argv[1]
print("Processing {0}".format( FILE_PATH ))


COLS = ["meta.packet_len","quic_ietf.spin_bit","int.hop_latencies","int.hop_queue_occups","int.hop_l4s_mark","int.hop_l4s_drop"]

dic = read_data( FILE_PATH, cols=COLS )
minX=0
maxX=0

# get min and max timestamp
for i in dic:
    i = int(i)
    if maxX == 0:
        minX = i
        maxX = i
    else:
        if i > maxX :
            maxX = i
        if i < minX :
            minX = i

# x Axis is a range from min - max
x = range(minX,maxX)
xDate = [ datetime.fromtimestamp(ts) for ts in x]


plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (10,3*len(COLS) )
# space between subplot
plt.rcParams['figure.constrained_layout.use'] = True
plt.subplots_adjust( hspace=5 )
# number of y ticks
plt.locator_params(axis='y', nbins=5) 

#global x_cl, x_ll
fig,axs=plt.subplots( len(COLS)  )

for i in range( len(COLS) ):
    ax = axs[i]
    ax.plot( xDate, get(dic, x, COLS[i]), label=COLS[i], color="black" )
    ax.set_title( "{0} (total) -- (avg={1})".format( COLS[i], avg(dic, x, COLS[i]), ))
    ax.grid()

# Save as pdf
#plt.savefig( "{0}-{1}-pps.pdf".format(FILE_NAME, TS_COL_INDEX), dpi=60, format='pdf', bbox_inches='tight')
output =  "{0}.png".format(FILE_PATH)
print("write to {0}".format( output ))
plt.savefig( output, dpi=70, format='png', bbox_inches='tight')
