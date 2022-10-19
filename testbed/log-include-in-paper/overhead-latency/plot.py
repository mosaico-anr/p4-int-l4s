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
        p = np.average( val )
        print p
        result[i].append( p ) 

labels = traffic_type.keys()
print labels

plt.rcParams['axes.xmargin'] = 0.2
plt.rcParams["figure.figsize"] = (8,4)
plt.tight_layout()

x = np.arange( len(labels) )  # the label locations
width = 0.2  # the width of the bars

l = result.keys()

fig, ax = plt.subplots()
rects2 = ax.bar(x - width/2, result[ l[1] ], width, label=l[1], color="blue")
rects1 = ax.bar(x + width/2, result[ l[0] ], width, label=l[0], color="red")

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('RTT of packets (microsecond)')
#ax.set_xticks(x, labels)
ax.set_ylim([0, 4500]) #min,max y
plt.xticks(x, labels)
plt.yticks([0,1000,2000,3000])
ax.legend()

#ax = plt.gca()
#ax.set_xlim([xmin, xmax])

# Not work
#ax.bar_label(rects1, padding=3)
#ax.bar_label(rects2, padding=3)
def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1*height,
                '%d' % int(height),
                ha='center', va='bottom')

autolabel( rects1 )
autolabel( rects2 )

plt.grid()
plt.legend(loc="upper right")

# Save as pdf
plt.savefig( "rtt-with-without-int.pdf", dpi=60, format='pdf', bbox_inches='tight')
