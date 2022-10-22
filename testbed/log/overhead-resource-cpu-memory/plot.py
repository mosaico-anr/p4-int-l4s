import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from matplotlib import pyplot as plt

import numpy as np
import csv, sys
import matplotlib
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D
import glob


x_len = 300

def read(file_name):
    reader = csv.reader( open( file_name ), delimiter= ' ', skipinitialspace=True)
    #index 1: CPU%
    #index 2: Real memory (MB)
    data = [ row  for row in reader]
    #return the last 300 elements
    data = data[-x_len:]
    
    print( file_name )
    print( data[0] )

    data = [ [float(row[1]), float(row[2])]  for row in data]
    return data


def load_data(is_int):
    file_names = glob.glob("./cpu_mem_int_{0}_pid_*.txt".format( is_int ))
    data = []
    for file_name in file_names:
        d = read( file_name )
        if len(data) == 0 :
            data = d
        else:
            for i in range(0,x_len):
                for j in range(0,2):
                    data[i][j] += d[i][j]


    # avg value
    nb = len(file_names)
    #2 CPU => max value = 200%
    data = [ [r[0]/nb/2, r[1]/nb] for r in data]


    return data


data_int_yes   = load_data("yes")
data_int_false = load_data("false")

x = range(0, x_len+1)

def get( data, index ):
    ret = []
    for i in range(0,x_len):
        ret.append( data[i][ index ] )
    
    #duplicate the last element to get 301th element
    # => to be able to show the last tick of ax
    ret.append(ret[-1])
    return ret



plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (8,5.2)
plt.tight_layout()
plt.locator_params(axis='y', nbins=5) 

#global x_cl, x_ll
fig,ax1=plt.subplots()

ax1.plot( x, get(data_int_yes, 0),    linewidth=1.5, color = 'b', label="CPU - with INT" )
ax1.plot( x, get(data_int_false, 0) , linewidth=1.5, color = 'r', label="CPU - without INT", linestyle=(0, (5, 0.5)) )
ax1.set_ylabel("CPU usage (%)")


ax2=ax1.twinx()
ax2.plot( x, get(data_int_yes, 1),    linewidth=1.5, color = '#5C2A9D', marker='.',markevery=10, label="Memory - with INT" )
ax2.plot( x, get(data_int_false, 1) , linewidth=1.5, color = 'green', marker='4',markevery=10, label="Memory - without INT" )
ax2.set_ylabel("Real Memory (MB)")


ax1.set_xlabel( "(b) Average of CPU and Memory Usage", fontsize=16 )

#ax2.set_ylabel('bandwidth (Mbps)')
#if log_scale:
#    ax1.set_yscale('log')
 
# defining display layout
plt.xticks(range(0,x_len+1,60))
ax1.set_xticklabels([0, 60, 120, 180, 240, "300 (s)"])

ax1.grid()
ax1.legend(loc="lower left")
ax2.legend(loc="lower right")

# Save as pdf
plt.savefig( "cpu_memory.pdf", dpi=60, format='pdf', bbox_inches='tight')

def avg( data, index):
    return np.average( get(data, index) )

print("avg of INT: CPU {0}, memory: {1}".format( avg(data_int_yes, 0), avg(data_int_yes, 1 )))
print("avg of no INT: CPU {0}, memory: {1}".format( avg(data_int_false, 0), avg(data_int_false, 1 )))
