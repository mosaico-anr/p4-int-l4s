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


file_name = sys.argv[1]

output_dir = file_name + ".out"

if not os.path.exists( output_dir ):
    os.mkdir( output_dir )

reader = csv.reader( open( file_name ))
data = [row for row in reader if row[0] == "999"]

unit=1000
unit=1 #1second
time_from =  5*unit
duration  = 300*unit
init=0

# update timestamp
for row in data:
    row[3] = int(float(row[3]) * unit)
    if init==0 :
        init = row[3]+time_from

    #specific for UDP
    # change its IP source to be classified as unresponsive ECN traffic
    l = len(row)-1
    if row[l].startswith("99."):
        if row[ l ] == "99.178.376.658" or row[ l ] == "99.178.376.0":
            row[6] = "10.0.0.12"
        row[l] = 0 #avoid error when convertint to float

    for i in range(8, len(row)):
        row[i] = float(row[i])
        # ECN
        if i == 17 and row[i] > 1:
            row[i] -= 2
    row[3] -= init

client_server_ips = ["10.0.0.11", "10.0.0.12", "10.0.1.11", "10.0.1.12"]
data = [row for row in data
    if  row[4] in ["int","tot"]          # interested reports
    and row[3] >= 0 and row[3] <= duration # testing duration
    and row[6] in client_server_ips      # interested clients and servers
    and row[7] in client_server_ips
    ]


ll_egress = [row for row in data if row[4] == "int" and row[6] == "10.0.0.11" and row[7] == "10.0.1.11" ]
cl_egress = [row for row in data if row[4] == "int" and row[6] == "10.0.0.12" and row[7] == "10.0.1.12" ]


ll_igress = [row for row in data if row[4] == "tot" and row[6] == "10.0.0.11" and row[7] == "10.0.1.11" ]
cl_igress = [row for row in data if row[4] == "tot" and row[6] == "10.0.0.12" and row[7] == "10.0.1.12" ]



def group_by_time( arr ):
    dic = {}
    for r in arr:
        for i in range(8, len(r)):
            r[i] = float(r[i])
        
        time=r[3]
        if time in dic:
            old = dic[time]

            for i in range(8, len(r)):
                old[i] += r[i]
        else:
            dic[time] = r
    arr = []
    for time in dic:
        arr.append(dic[time])
    arr = sorted(arr, key=lambda x: int(x[3]))
    #print( arr[0:10] )
    return arr

ll_egress     = group_by_time(ll_egress)
cl_egress     = group_by_time(cl_egress)
ll_igress = group_by_time(ll_igress)
cl_igress = group_by_time(cl_igress)

print( len(ll_egress), len(cl_egress), len(ll_igress), len(cl_igress) )

#length = min( len(ll_egress), len(cl_egress), len(ll_igress), len(cl_igress) )
#ll_egress=ll_egress[0:length]
#cl_egress=cl_egress[0:length]
#ll_igress=ll_igress[0:length]
#cl_igress=cl_igress[0:length]
# test only LL traffic
#cl_egress=ll_egress
#cl_igress=ll_igress

def get(a, index=3):
    return [row[ index ] for row in a]

def cum( a, index=-1 ):
    tot = 0
    result = []
    if index >= 0:
        for i in range(0, len(a) ):
            tot += a[i][index]
            result.append( tot )

    else:
        for i in range(0, len(a) ):
            tot += a[i]
            result.append( tot )
    #print(result)
    return result

def diff( a1, a2, i1, i2 ):
    result = []
    for i in range(0, len(a1)):
        v1 = a1[i]
        v2 = a2[i]
        # must be the same timestamp
        if v1[3] != v2[3]:
            print("Error ", v1, v2)
            return
        result.append( v1[i1] - v2[i2] )
    print(result)
    return result


def log_pkt( prefix, cl_egress, ll_egress ):
    print( prefix, "ll_egress = ", ll_egress, ", cl_egress = ", cl_egress, ", total = ", ll_egress+cl_egress)

log_pkt("ingress: ", cum(cl_igress, 9)[-1], cum(ll_igress, 9)[-1] )
log_pkt("egress:  ", cum(cl_egress, 10)[-1],    cum(ll_egress, 10)[-1] )



plt.rcParams['axes.xmargin'] = 0
plt.rcParams["figure.figsize"] = (8,5)
plt.tight_layout()
plt.locator_params(axis='y', nbins=5) 

x_cl = get( cl_egress )
x_ll = get( ll_egress )

def draw(file_name, y_label, y_cl, y_ll, x_cl=x_cl, x_ll=x_ll, label_cl="CL traffic", label_ll="LL traffic", log_scale=False):
    #global x_cl, x_ll
    x_ll=range(0,len(y_ll))
    x_cl=range(0,len(y_cl))
    
    fig,ax1=plt.subplots()
    
    ax1.plot( x_cl, y_cl, linewidth=2,  color = 'b', label=label_cl, linestyle=(1,(8,1)) )
    ax1.plot( x_ll, y_ll, linewidth=2,  color = 'r', label=label_ll, linestyle='-' )

    # giving labels to the axises
    #ax1.set_xlabel('time (s)')
    #ax1.set_ylabel( y_label )
    #we use xlabel  as title at the bottom
    ax1.set_xlabel( y_label, fontsize=16 )
    
    #ax2.set_ylabel('bandwidth (Mbps)')
    #if log_scale:
    #    ax1.set_yscale('log')
     
    # defining display layout
    plt.xticks(range(0,duration+1,60))
    ax1.set_xticklabels([0, 60, 120, 180, 240, "300 (s)"])
    
    plt.grid()
    plt.legend(loc="upper right")

    # Save as pdf
    plt.savefig( output_dir + "/" + file_name, dpi=60, format='pdf', bbox_inches='tight')

def hist(file_name, y_label,  y_cl, y_ll, label_cl="CL traffic", label_ll="LL traffic", xlim_min=0, xlim_max=0, bins=2000, unit="ms/packet" ):
    
    fig, ax = plt.subplots()

    ax.hist( y_cl, histtype='step', bins=bins, density=True, cumulative=True, label=label_cl, linewidth=2, color='blue', linestyle='--')
    ax.hist( y_ll, range=(0,99.9), histtype='step', bins=bins, density=True, cumulative=True, label=label_ll, linewidth=2, color='red')

    if xlim_min == 0:
        xlim_min = min(min( y_cl ), min(y_ll))
    if xlim_max == 0:
        xlim_max = max(max( y_cl ), max(y_ll))-1
        
    ax.set_xlim(xlim_min, xlim_max)
    #ax.set_ylim(0, 1)
    ax.set_xlabel( y_label, fontsize=16 )
    ax.grid()
    
    # modify the last x label
    a=ax.get_xticks().tolist()
    a = [int(v) for v in a]
    a[-2]= '{0} ({1})'.format( a[-2], unit )
    print(a)
    ax.set_xticklabels(a)
    ax.set_yticklabels( [0, 20, 40, 60, 80, 100] )

    #ax.legend()
    # Create new legend handles but use the colors from the existing ones
    handles, labels = ax.get_legend_handles_labels()
    new_handles = [Line2D([], [], c=h.get_edgecolor(), linestyle=h.get_linestyle()) for h in handles]

    plt.legend(handles=new_handles, labels=labels, loc="lower right",)

    plt.savefig( output_dir + "/" + file_name, dpi=60, format='pdf', bbox_inches='tight')

def share(file_name, y_label, y_cl, y_ll, bins=1000):
    #global x_cl, x_ll
    if len(y_ll) != len(y_cl):
        print "Error"

    x = range(0, len(y_ll) )
    y = []
    for i in x:
        if y_ll[i] != 0 and y_cl[i] != 0:
            y.append( y_ll[i] / y_cl[i] )
        else:
            y.append(1)
    fig,ax=plt.subplots()
    
    #ax.hist( y, histtype='step', bins=bins, density=True, cumulative=True, linewidth=1, color='blue')
    ax.plot( x, cum(y), linewidth=2,  color = 'green' )

    ax.set_xlabel( y_label, fontsize=16 )
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 300)
    plt.text(50, 250, 'CL traffic')
    plt.text(250, 50, 'LL traffic')
    
    ax.set_xticklabels([0, 50, 100, 150, 200, 250, "300 (s)"])
    ax.set_yticklabels([0, 50, 100, 150, 200, 250, "300 (s)"])
    
    #plt.xticks(range(0,duration+1,60))
    plt.grid()
    #plt.legend(loc="upper right")

    # Save as pdf
    plt.savefig( output_dir + "/" + file_name, dpi=60, format='pdf', bbox_inches='tight')


draw( "bandwidth-egress.pdf",   "(a) Egress bandwidth (Mbps)", 
    [row[9]*8/1000000.0 for row in cl_egress], [row[9]*8/1000000.0 for row in ll_egress] )
share( "bandwidth-egress-share.pdf",   "(d) Balance egress rate (LL/CL)", 
    [row[9]*8/1000000.0 for row in cl_egress], [row[9]*8/1000000.0 for row in ll_egress] )
    
draw( "throughput-egress.pdf",  "Egress throughput (pps)", 
    get(cl_egress, 10), get(ll_egress, 10))

draw( "queue-delay.pdf", "(b) Queue delay (ms/packet/s)", 
    [row[8]/row[10] for row in cl_egress], [row[8]/row[10] for row in ll_egress], log_scale=True )
hist( "queue-delay-hist.pdf", "(e) Queue delay distribution (%)", 
    [row[8]/row[10] for row in cl_egress], [row[8]/row[10] for row in ll_egress], xlim_max=0)
    
draw( "queue-occup.pdf", "(c) Queue occupancy (packets/s)",
    [row[13]/row[10] for row in ll_egress], [row[13]/row[10] for row in cl_egress] )

hist( "queue-occup-hist.pdf", "(f) Queue occupancy distribution (%)",
    [row[13]/row[10] for row in ll_egress], [row[13]/row[10] for row in cl_egress], xlim_max=0, unit='packets' )

draw( "tcp-cwr.pdf", "(f) TCP CWR signal (pps)",
    get(cl_egress, 16), get(ll_egress, 16) )


draw( "l4s-mark-cum.pdf",  "total marked packets", 
    cum( cl_egress, 11), cum(ll_egress, 11) )
draw( "l4s-mark.pdf",  "(c) Marked packets (pps)", 
    get( cl_egress, 11), get(ll_egress, 11) )

draw( "l4s-drop.pdf",  "Total dropped packets", 
    cum( cl_egress, 12), cum(ll_egress, 12) )

draw( "l4s-mark-drop.pdf",  "L4S marked and dropped packets", 
    cum(ll_egress, 11), cum(ll_egress, 12),  label_cl="LL mark", label_ll="LL drop" )


draw( "bandwidth-ingress.pdf",   "(a) Ingress bandwidth (Mbps)",     
    [int(row[8])*8/1000000.0 for row in cl_igress], [int(row[8])*8/1000000.0 for row in ll_igress] )

draw( "throughput-ingress.pdf", "Ingress throughput (pps)", 
    get(cl_igress, 9), get(ll_igress, 9))


# difference between igress and egress
# not in the same timestamp
#draw( "drop-ingress-egress-throughput.pdf", "dropped throughput (pps)", 
#    diff(cl_igress, cl_egress, 9, 10), diff(ll_igress, ll_egress, 9, 10))
#draw( "drop-ingress-egress-total.pdf", "total dropped (pps)", 
#    cum(diff(cl_igress, cl_egress, 9, 10)), cum(diff(ll_igress, ll_egress, 9, 10)))
