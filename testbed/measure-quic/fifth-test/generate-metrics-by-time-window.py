#!/usr/bin/python3
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script parses the data.csv in each test configuration, then extract the necessaire metrics then write the result to another csv
#
# TCP rtt is calculated based on tsval and tsecr values
#
import os, csv, sys, json
import tarfile, tempfile
import numpy as np
# a period of time
TIME_WINDOW = 33000 #33 milliseconds

#do nothing
def proc_same( val ):
    return val

#convert to integer
def proc_int( val ):
    return int(val)

# convert nanosecond to microsecond
def proc_nsms( val ):
    return round(int(val) / 1000)

def proc_prob( val ):
    #max of 4 bytes
    MAX_PROBABILITY = 0xFFFFFFFF
    #percentage
    return round(int(val) * 100 / MAX_PROBABILITY)

def proc_ecn( val ):
    val = int(val)
    #whether the ECN is marked
    if val == 2 or val == 3:
        return 1
    return 0

#map from MMT  metrics to the required metrics
MAP = {
    "int.hop_egress_times" : {"pre_proc": proc_nsms, "label": "egress-ts"},
    "int.hop_ingress_times": {"pre_proc": proc_nsms, "label": "igress-ts"},
    "ip.src"               : {"pre_proc": proc_same, "label": "src-ip"},
    "ip.dst"               : {"pre_proc": proc_same, "label": "dst-ip"},
    "udp.src_port"         : {"pre_proc": proc_int,  "label": "src-port"},
    "udp.dest_port"        : {"pre_proc": proc_int,  "label": "dst-port"},
    "meta.packet_len"      : {"pre_proc": proc_int,  "label": "bytes-sent"},
    "int.hop_latencies"    : {"pre_proc": proc_int,  "label": "queue-delay"},
    "int.hop_queue_occups" : {"pre_proc": proc_int,  "label": "queue-occups"},
    "int.mark_probability" : {"pre_proc": proc_prob, "label": "mark-proba"},
    "int.hop_l4s_mark"     : {"pre_proc": proc_int,  "label": "step-marks"},
    "int.hop_l4s_drop"     : {"pre_proc": proc_int,  "label": "nb-l4s-drops"},
    "ip.ecn"               : {"pre_proc": proc_ecn,  "label": "ecn-marks"},
    #quic_ietf.rtt is in microsecond
    "quic_ietf.rtt"        : {"pre_proc": proc_int,  "label": "total-delay"},
    "int.hop_queue_ids"    : {"pre_proc": proc_int,  "label": "queue-id"},
}

def read_csv( filepath ):
    '''
    Read CSV into an array
    '''
    reader = csv.DictReader( open(filepath, "r"), delimiter= ',', )
    data = []
    for row in reader:
        data.append( row )
    return data

def pre_process_data(data):
    '''
    Map data from MMT metrics to the required metrics
    '''

    new_data = []

    #max of 4 bytes
    MAX_PROBABILITY = 0xFFFFFFFF

    
    index = 0
    # for each row in the csv file
    for row in data:
        # empty IP? MMT may report ARP packet
        if row["ip.src"] == "" or row["ip.dst"] == "":
            continue

        new_row = {}
        #map from MMT value to the required value
        for i in MAP:
            if not i in row:
                print("raw data does not contain '{0}' metric".format( i ))
                sys.exit( 1 )
                
            v = MAP[i]
            new_row[v["label"]] = v["pre_proc"]( row[i] )

        if new_row["igress-ts"] >= new_row["egress-ts"]:
            print(" --> invalid data: igress-ts >= egress-ts")
            print( new_row )
            print( row )
            sys.exit( 6 )
        new_data.append( new_row )

    return new_data

def _sort( v ):
    return v["egress-ts"]


# get column of an array
def extract_column(data, key):
    arr = []
    for r in data:
        arr.append( r[key] ) 
    return arr

def get_flow_key( row ):
    key = "{0}:{1} -> {2}:{3}".format( row["src-ip"], row["src-port"], row["dst-ip"], row["dst-port"] )
    return key

def _round( val):
    return ('%.2f' % (val))

def get_metrics( group ):
    dic = {}
    
    # group packets by flow
    for row in group:
        # group by 4 tuples: IP src/dst + Port src/dst
        key = get_flow_key( row )
        
        if key not in dic:
            dic[ key ] = []
        dic[key].append( row )
    
    data = []
    # for each flow
    for key in dic:
        arr = dic[key]
        
        # generate a row which contains metrics of a flow
        row = {}
        # metrics to be keeped the same values
        for i in ["src-ip", "dst-ip", "src-port", "dst-port", "queue-id"]:
            row[i] = extract_column( arr, i)[0] #first value

        # metrics to cumulate
        for i in ["bytes-sent", "step-marks", "nb-l4s-drops", "ecn-marks" ]:
            row[i] = np.sum( extract_column( arr, i) )

        # metrics to get avg and median
        for i in ["queue-delay", "total-delay", "mark-proba", "queue-occups"]:
            column = extract_column( arr, i)
            row["{0}-avg".format(i)]    = _round(np.average( column ))
            row["{0}-median".format(i)] = _round(np.median( column ))

        # number of packets is the number of rows
        row["nb-packets"] = len( extract_column( arr, "src-ip"))
        
        #timestamp of this flow
        #row["igress-ts"]  = np.min( extract_column( arr, "igress-ts") ) #first igress
        row["egress-ts"]  = np.max( extract_column( arr, "egress-ts") ) #last egress

        data.append( row )

    return data

FIELDS = {"window-id": True, 'queue-size-CL': True, 'queue-size-LL': True}
def get_all_packets_in_queues( data, start_time, end_time ):
    '''
    Get all packets that are present in the queues (LL or CL) in the interval [start_time, end_time)
    '''
    group = []
    for row in data:
        if row["igress-ts"] <= end_time and row["egress-ts"] >= start_time:
            group.append( row )
        
    nb_ll = 0
    nb_cl = 0
    dic = {}
    for row in group:
        if row["queue-id"] == 1:
            nb_ll += 1
        else:
            nb_cl += 1

        key = get_flow_key( row )
        FIELDS[key] = 1
        #init
        if key not in dic:
            dic[ key ] = 0
        # count the packet for this flow
        dic[key] += 1
    #nb_pkts_in_queue = len( group )
    
    #remember statistic of queues at this window
    dic["queue-size-LL"] = nb_ll
    dic["queue-size-CL"] = nb_cl
    return dic

QUEUE_STAT=[]
def process_data( data ):
    T0 = data[0]["egress-ts"]
    
    new_data = []
    
    #index of this window
    window_id = 0;
    group = [] #contain packets in this window
    # start and end time of this window
    start_time = T0
    end_time   = TIME_WINDOW + start_time
    
    # for each packet
    for i in range(0, len(data)):
        # test first 1000 rows
        #if i > 1000:
        #    break
        
        row = data[i]
        
        if row["egress-ts"] < end_time:
            group.append( row )
        else:
            if len(group) == 0:
                #print(" --> empty traffic in window {0}-th".format( ts))
                None
            else: #got a window
                #calculate the metrics in this window
                new_rows = get_metrics( group )
                
                # calculate the rate of occupancy of each flow in this window
                queue = get_all_packets_in_queues( data, start_time, end_time )
                queue["window-id"] = window_id
                QUEUE_STAT.append( queue ) #remember this stat

                for new_row in new_rows:
                    #1. append synthetic metrics
                    new_row["window-id"] = window_id;
                    # set time to relative
                    new_row["egress-ts"] -= T0
                    #debit
                    debit = new_row["bytes-sent"] * 8.0 # to number of bit
                    debit = debit / (TIME_WINDOW / 1000.0 / 1000) # per second
                    debit = debit / (1000 * 1000) # to Mega bit
                    new_row["debit"] = _round(debit)
                    # bandwidth rate wrt the limit
                    new_row["occupation"] = int(debit * 100 / LIM_BANDWIDTH)
                    
                    # 2. append metrics which are parameter
                    flow_param = get_flow_param(new_row["src-port"], new_row["dst-port"] )
                    new_row["traffic-type"] = flow_param["type"]
                    if new_row["traffic-type"] == "unrespECN":
                        new_row["power-attack"] = PARAM["power-attack"]
                    else:
                        new_row["power-attack"] = 0

                    #3. append queue info
                    key = get_flow_key( new_row )
                    if key not in queue:
                        print( " --> not found stats of queue concerning flow {0} in window {1}-th which has {2} outgoing packets".format( key, ts, len(group) ))
                        print(start_time, end_time)
                        print(new_rows)
                        print(group)
                        print( queue )
                        sys.exit( 5 )

                    # copy info
                    else:
                        new_row["nb-pkt-in-queue"] = queue[key]
                        for j in ["queue-size-LL", "queue-size-CL"]:
                            new_row[j] = queue[j]

                    new_data.append( new_row )

            # reset counter, group
            window_id += 1
            group = []
            start_time = end_time
            end_time  += TIME_WINDOW

    return new_data;


def load_parameter( filepath ):
    with open( filepath ) as f:
        return json.load(f)
    return {}

# get flow parameter from src or dst ports
def get_flow_param( src_port, dst_port=0 ):
    flows = PARAM["flows"]
    for f in flows:
        port = f["serer_port"]
        if port == src_port or port == dst_port:
            return f
    print("Not found parameters of flow having src-port={0} and dst-port={1}".format( src_port, dst_port ))
    sys.exit( 2 )

def fail_if_a_flow_is_less_than_60s( data ):
    '''
    
    '''
    flows = {}
    for row in data:
        key = get_flow_key( row )
        ts  = row["egress-ts"]
        #init
        if key not in flows:
            flows[ key ] = {"min": ts, "max": ts}
        else:
            # count the packet for this flow
            f = flows[ key ]
            if f["min"] > ts:
                f["min"] = ts 
            if f["max"] < ts:
                f["max"] = ts 

    count = 0
    for key in flows:
        f = flows[key]
        duration = f["max"] - f["min"] #micro second
        duration = duration / (1000*1000)  #to second
        print( " --> flow {0} has {1} seconds".format( key, _round(duration) ))
        if duration < 50:
            count += 1
    if count > 0:
        print( " --> {0} flows are less than 50 seconds. EXIT".format( count ))
        sys.exit( 7 )

############# Main processing ##################

if len(sys.argv) != 2:
    print("\nUsage: python3 {0} directory-of-an-experiment".format( sys.argv[0]))
    print("   Ex: python3 {0} third-test/round-1/1-bw_1Mbps-power_0.1-flows_unrespECN.0.60.10000--20230719-203649/\n".format( sys.argv[0]))
    sys.exit(1)

DIR_PATH = sys.argv[1]
print("Processing {0}".format( DIR_PATH ))

filepath = os.path.join(DIR_PATH, "param.json")
if not os.path.isfile( filepath ): 
    print(" --> not found param.json")
    sys.exit(3)

PARAM = load_parameter( filepath )
lim_bandwidth = PARAM["bandwidth"] #10 Mbps
LIM_BANDWIDTH = int( lim_bandwidth.split(" ")[0] )
print(" --> limited bandwidth {0} Mbps".format( LIM_BANDWIDTH ))


data = None
filepath = os.path.join(DIR_PATH, "data.csv" )
# try to read data from tar.gz file, then write data to a tmp file
if os.path.isfile( filepath ): 
    data = read_csv( filepath )
    print(" --> read csv from {0}".format( filepath ))
else:
    filepath = os.path.join(DIR_PATH, "data.csv.tar.gz" )
    if os.path.isfile( filepath ): 
        tar = tarfile.open( filepath, "r:gz")
        for member in tar.getmembers():
            f = tar.extractfile(member)
            content = f.read()
            f.close()
            # write content to a temporary file
            tmp = tempfile.NamedTemporaryFile()
            tmp.write( content )
            data = read_csv( tmp.name )
            print(" --> read csv from {0}".format( filepath ))
            tmp.close() # close the file, it will be removed
            break
if data == None:
    print(" --> not found neither data.csv nor data.csv.tar.gz")
    sys.exit(3)


data  = pre_process_data( data )
#sort data by timestamp
data.sort( key=_sort )
data  = process_data( data )
fail_if_a_flow_is_less_than_60s( data )

output_filename = os.path.join(DIR_PATH, "synthesis_data.csv" )
print(" --> writing to {0}".format( output_filename ))
with open(output_filename, 'w') as f:
    fieldnames = data[0].keys()

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows( data ) 

# statistic of data in flow
output_filename = os.path.join(DIR_PATH, "queue_data.csv" )
print(" --> writing to {0}".format( output_filename ))
with open(output_filename, 'w') as f:
    fieldnames = FIELDS.keys()

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows( QUEUE_STAT ) 

