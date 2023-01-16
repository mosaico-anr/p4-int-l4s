import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter

import numpy as np
import csv, sys
import matplotlib
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D
import glob
from datetime import datetime


x_len = 300

def read_qdisc_pfifo( file_name = "qdisc.txt" ):
    reader = csv.reader( open( file_name ), delimiter= ' ', skipinitialspace=True)
    data = [ row  for row in reader]
    #11: nb pkt
    #24: time
    data = [[ int(row[11]), datetime.strptime(row[24] + '000', '%H:%M:%S.%f')] for row in data  ]
    #data = data[0:10]
    # since number of pkt is cummulated
    # => need to get the difference
    last = data[0][0]
    data[0][0] = 0
    #data[0][1] = 0
    no_zero = 0
    for i in range(1, len(data)):
        tmp = data[i][0]
        data[i][0] -= last
        #data[i][1] = i
        last = tmp
        
        if data[i][0] != 0 and no_zero == 0:
            no_zero = i

    data = data[no_zero - 3 : ]
    index = 334
    #data = data[1940:1965]
    data = data[0:17]
    return data

def read_mmt(file_name = "data.csv"):
    reader = csv.reader( open( file_name ), delimiter= ',', skipinitialspace=True)
    
    #use only event-based report
    data = [ row  for row in reader if row[0] == "1000"]
    
    first_time = float( data[0][3] ) #
    # 8: ingress time = number of nanosecond since the BMv2 swith started
    #
    data = [ int(row[8]) for row in data]
    # to millisecond
    data = [ int(row/1000/1000) for row in data]
    #get interval
    data = [ row-data[0] for row in data]
    # count same time
    dict = {}
    for i in data:
        if i < 0 :
            print("error =========")
        if i in dict:
            dict[i] += 1
        else:
            dict[i] = 0
    last = data[-1]
    ret = []
    for i in range( last ):
        if i in dict:
            ret.append( [ dict[i], 
                datetime.utcfromtimestamp(first_time + i/1000.0 )
                #remove date, so that we have the same date as in qdisc data
                .replace(day=1, month=1, year=1900)] )
    
    return ret

def get(data, index):
    ret = []
    for i in range( len(data) ):
        ret.append( data[i][index] )
    return ret

def add_labels(line):
    x,y=line.get_data()
    labels=map(','.join,zip(map(lambda s: '%g'%s,x),map(lambda s: '%g'%s,y)))
    map(matplotlib.pyplot.text,x,y,labels)

def plot( data, out):
    plt.rcParams['axes.xmargin'] = 0
    plt.rcParams["figure.figsize"] = (8,5.2)
    plt.tight_layout()
    plt.locator_params(axis='y', nbins=5) 
    
    #global x_cl, x_ll
    fig,ax1=plt.subplots()
    
    ax1.plot( get(data, 1), get(data, 0), linewidth=1.5, color = 'b', label="tc", marker="o" )
    
    ax1.xaxis.set_major_formatter(DateFormatter("%H:%M:%S.%f"))
    # Save as pdf
    plt.savefig( out, dpi=60, format='pdf', bbox_inches='tight')

qdisc = read_qdisc_pfifo()
#print qdisc
plot( qdisc, "tc.pdf" )

begin = qdisc[0][1]
end   = qdisc[-1][1]

print( begin, end )

mmt = read_mmt()
mmt = [ row for row in mmt if row[1] >= begin and row[1] <= end ]

plot( mmt, "mmt.pdf" )


for i in range(len(mmt) ):
    mmt[i][0] *= 5

plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (8,5.2)
plt.tight_layout()
plt.locator_params(axis='y', nbins=5) 

#global x_cl, x_ll
fig,ax1=plt.subplots()

ax1.plot( get(qdisc, 1), get(qdisc, 0), linewidth=1.5, color = 'b', label="tc", marker='.' )
#add_labels(line)
ax1.plot( get(mmt, 1), get(mmt, 0), linewidth=1.5, color = 'r', label="tc", marker='' )

#ax1.xaxis_date()
#ax1.xaxis.set_major_formatter(DateFormatter("%S.%f"))
# Save as pdf
plt.savefig( "plot.pdf", dpi=60, format='pdf', bbox_inches='tight')
plt.show()