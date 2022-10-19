import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from matplotlib import pyplot as plt

import numpy as np
import csv, sys
import matplotlib

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
plt.rcParams["figure.figsize"] = (8,4)
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

plt.yticks([0,1000,2000,3000,4000])
ax.set_ylim([0, 4500]) #min,max y


ax.legend()
plt.grid()
# Save as pdf
plt.savefig( "rtt-with-without-int-boxplot.pdf", dpi=60, format='pdf', bbox_inches='tight')
