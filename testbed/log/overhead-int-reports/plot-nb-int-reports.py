import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from matplotlib import pyplot as plt

import math 
import numpy as np
import csv, sys
import matplotlib
from matplotlib.lines import Line2D
import random

traffic_type = {
    "LL traffic": "0",
    "CL traffic": "1"
}

report_type = {
    "No filter" : "int",
    "Event-based filter": "cond",
    "Query-based filter": "query"
}

duration  = 300
time_from =  5
def load_data( file_name ):
    print file_name
    init=0

    with open( file_name, 'r' ) as input_file:
        csv_reader = csv.reader(input_file)
        data = [row for row in csv_reader]
        
        x = 0
        for row in data:
            if row[0] != '999' and row[0] != '1000':
                continue
            row[3] = int( float(row[3] ))
            if init==0 :
                init = row[3]+time_from
            row[3] -= init

        data = [row for row in data if row[3] >= 0 and row[3] <= duration ]
        return data;

data = load_data("data.csv")

#group by time
group = {}
for row in data:
    time = row[3]
    if time in group:
        group[time].append( row )
    else:
        group[time] = [row]

total   = []
latency = []
occups  = []

x = range(0, duration+1)

tt = 0
tl = 0
to = 0

for i in x:
    t = 0
    l = 0
    o = 0
    data = group[i]
    for row in data:
        #same timestamp
        if row[4] == "int":
            t += 1
        elif row[4] == "latency":
            l += 1
        elif row[4] == "occups":
            o += 1
    tt += t
    tl += l
    to += o

    total.append( t )
    latency.append( l )
    occups.append( o )

print("total",   tt)
print("latency", tl )
print("occups",  to)

plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (8,5)
plt.tight_layout()
plt.locator_params(axis='y', nbins=5) 




fig,ax=plt.subplots()
    

ax.plot( x, total,   linewidth=2.75, marker="",  color = 'r', label="#Reports of each INT packet", linestyle='-.' )
ax.plot( x, latency, linewidth=1, marker="",  color = 'b', label="#Event-based reports of queue latency", linestyle='-' )
ax.plot( x, occups,  linewidth=1.75, marker="",  color = 'green', label="#Event-based reports of queue occupancy", linestyle=(0,(10,0.75)) )

# modify the last x label
#a=ax.get_xticks().tolist()
#a[1]='change'
plt.xticks(range(0,duration+1,60))
ax.set_xticklabels([0, 60, 120, 180, 240, "300 (s)"])

#ax.set_yscale('log')
ax.set_xlabel( "(c) Number of INT reports per second", fontsize=16 )
#plt.text(300, 300, "300 (second)")


plt.grid()
plt.legend(loc="upper left")

# Save as pdf
plt.savefig( "nb-int-reports.pdf", dpi=60, format='pdf', bbox_inches='tight')
