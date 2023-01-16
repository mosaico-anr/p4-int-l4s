# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.

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

traffic_type = {
    "LL traffic": "10.0.0.11-10.0.1.11",
    "CL traffic": "10.0.0.12-10.0.1.12"
}

int_type = {
    "without INT": "no",
    "with INT": "yes"
}

pkt_size = [100, 200, 500, 1000]

def load_data( file_name ):
    print file_name
    with open( file_name, 'r' ) as input_file:
        csv_reader = csv.reader(input_file)
        rows = [row for row in csv_reader]
        #exclude the first and the last rows (header and result)
        rows = rows[1:-1]
        result = [ int(row[3]) for row in rows ]
        return result;

result = {}

for i in int_type:
    result[i] = []
    for t in traffic_type:
        val = [];
        for pkt in pkt_size:
            data = load_data( "latency-overhead-{0}-pkt-{1}-INT-{2}.csv".format( 
                traffic_type[t], pkt, int_type[i] ) )
            val += data
            
        val = np.array( val )
        #p = np.percentile(data, 50) # return 50th percentile, e.g median.
        #p = np.median( data )
        #p = [np.percentile(data, 0), np.percentile(data, 25), np.average(data), np.percentile(data, 75), np.percentile(data, 100)]
        #print p
        #result[i].append( p )
        print np.average( val )
        result[i].append( val ) 

ticks = traffic_type.keys()
print ticks

def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)


plt.rcParams['axes.xmargin'] = 0.2
plt.rcParams["figure.figsize"] = (8,5)
plt.tight_layout()


l = result.keys()

data_a = result[ l[0] ]
data_b = result[ l[1] ]

#print data_a
#print data_b

fig, ax = plt.subplots()

width=0.6
bpl = ax.boxplot(data_a, positions=np.array(xrange(len(data_a)))*2.0+width/2+0.1, sym='', widths=width)
bpr = ax.boxplot(data_b, positions=np.array(xrange(len(data_b)))*2.0-width/2-0.1, sym='', widths=width)
set_box_color(bpl, 'red') # colors are from http://colorbrewer2.org/
set_box_color(bpr, 'blue')

# draw temporary red and blue lines and use them to create a legend
ax.plot([], c='red',  label=l[0])
ax.plot([], c='blue', label=l[1])


# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('RTT of packets (microsecond)')


plt.xticks(xrange(0, len(ticks)*2, 2), ticks)
plt.xlim(-2, len(ticks)*2)

ax.set_yticks([0,1000,2000,3000,4000])
ax.set_ylim([0, 4500]) #min,max y

ax.grid()
ax.legend()

# Save as pdf
plt.savefig( "rtt-with-without-int-boxplot.pdf", dpi=60, format='pdf', bbox_inches='tight')


def plot_cdf(ax, data, **kwargs):
    ax.hist(data, **kwargs)

fig, ax = plt.subplots()

#plot_cdf(ax, data_a, label=l[0], color='r', linewidth=1)
#plot_cdf(ax, data_b, label=l[1], color='b', linewidth=1)

colors = {
    "with INT" : ["blue", "red"],
    "without INT": ["green", "orange"]
}

linestyles = {
    "with INT" : [(0,(5,5)), "-."],
    "without INT": [ (1,(8,2)), '-']
}


for i in l:
    for j in range(0, len(ticks)):
        label = ticks[j] + " - " + i
        print label
        ax.hist( result[i][j], histtype='step', bins=2000, density=True, cumulative=True, label=label, linewidth=2, color=colors[i][j], linestyle=linestyles[i][j])


ax.set_xlim(2200, 4250)
#ax.set_ylim(0, 1)
#ax.set_ylabel("(a) RTT Probability")
ax.set_xlabel( "(a) RTT distribution (%)", fontsize=16 )
ax.grid()

# modify the last x label
a=ax.get_xticks().tolist()
a = [int(v) for v in a]
a[-1]= '{0} ($\mu$s)'.format( a[-1] )
ax.set_xticklabels(a)
ax.set_yticklabels( [0, 20, 40, 60, 80, 100] )

#ax.legend()
# Create new legend handles but use the colors from the existing ones
handles, labels = ax.get_legend_handles_labels()
new_handles = [Line2D([], [], c=h.get_edgecolor(), linestyle=h.get_linestyle()) for h in handles]


plt.legend(handles=new_handles, labels=labels, loc="lower right",)
#plt.legend( labels=labels, loc="lower right",)

plt.savefig( "rtt-with-without-int-histogram.pdf", dpi=30, format='pdf', bbox_inches='tight')
