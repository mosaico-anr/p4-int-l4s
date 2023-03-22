#!/bin/bash -x

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
set -x

if [ "$EUID" -ne 0 ]
	then echo "Please run as root"
	exit
fi

# by default, enable INT
if [ -z "$ENABLE_INT" ]; then
	export ENABLE_INT=yes
fi



#P4 file to run
P4_FILE_PREFIX="switch-l4s"
#P4_FILE_PREFIX="switch-forward-clone"
if [[ "$#" == "1" ]]; then
	P4_FILE_PREFIX="$1"
fi

if [ "$NO_COMPILE_P4" == "" ]
then
	# clear old compiled file
	rm *.json *.p4i
	##compile code
	#cat <<EOF | parallel -j 3
	#	p4c  --target  bmv2  --arch  v1model  switch-l4s.p4
	#	p4c  --target  bmv2  --arch  v1model  switch-int.p4
	#	p4c  --target  bmv2  --arch  v1model  switch-forward.p4
	#EOF


	p4c  --target  bmv2  --arch  v1model  $P4_FILE_PREFIX.p4

	if [ $? != 0 ]
	then
	  echo "Could not compile P4" >&2
	  exit 1
	fi
else
	echo "No need to compile P4 code"
fi

source environment.sh

# clean log folder
export LOG="$SCRIPT_PATH/log"

mkdir -p "$LOG"  2> /dev/null

function get-mac(){
	iface=$1
	cat /sys/class/net/$iface/address
}

function get-remote-mac(){
	ip=$1
	iface=$2
	run-on-host $ip cat /sys/class/net/$iface/address
}

export IFACE_MAC=$(get-mac $IFACE)
# The interface facing the servers
export REV_IFACE_MAC=$(get-mac $REV_IFACE)
export MON_IFACE_MAC=$(get-mac $MON_IFACE)


export CLIENT_A_MAC=$(get-remote-mac $CLIENT_A_CTRL $CLIENT_A_IFACE)
export CLIENT_B_MAC=$(get-remote-mac $CLIENT_B_CTRL $CLIENT_B_IFACE)
                                                
export SERVER_A_MAC=$(get-remote-mac $SERVER_A_CTRL $SERVER_A_IFACE)
export SERVER_B_MAC=$(get-remote-mac $SERVER_B_CTRL $SERVER_B_IFACE)

#fixed in arp cache
#arp -s           10.0.0.3 00:00:00:00:00:a0
arp -s $SERVER_A $SERVER_A_MAC
arp -s $SERVER_B $SERVER_B_MAC
arp -s $CLIENT_A $CLIENT_A_MAC
arp -s $CLIENT_B $CLIENT_B_MAC

function get-ip(){
	iface=$1
	/sbin/ip -o -4 addr list $iface | awk '{print $4}' | cut -d/ -f1
}

IFACE_IP=$(get-ip $IFACE)
REV_IFACE_IP=$(get-ip $REV_IFACE)

# set route on clients/server
run-on-host $CLIENT_A_CTRL sudo route add -net $SERVER_NET gw  $IFACE_IP
run-on-host $CLIENT_B_CTRL sudo route add -net $SERVER_NET gw  $IFACE_IP
run-on-host $SERVER_A_CTRL sudo route add -net $CLIENT_NET gw  $REV_IFACE_IP
run-on-host $SERVER_B_CTRL sudo route add -net $CLIENT_NET gw  $REV_IFACE_IP

# Disable offload
run-on-host $CLIENT_A_CTRL sudo ethtool -K $CLIENT_A_IFACE tso off gso off gro off tx off
run-on-host $CLIENT_B_CTRL sudo ethtool -K $CLIENT_A_IFACE tso off gso off gro off tx off
run-on-host $SERVER_A_CTRL sudo ethtool -K $SERVER_A_IFACE tso off gso off gro off tx off
run-on-host $SERVER_B_CTRL sudo ethtool -K $SERVER_B_IFACE tso off gso off gro off tx off

# create new virtual NIC to test P4
#https://opennetworking.org/news-and-events/blog/getting-started-with-p4/
function config-nic(){
	NIC=$1

	ip link set $NIC mtu 1500
	ethtool -K $NIC tso off gso off gro off tx off
	sysctl net.ipv6.conf.$NIC.disable_ipv6=1
}

#to delete virtual NIC:
#ip link delete veth_a

config-nic $IFACE
config-nic $REV_IFACE

# disable ip forward
sysctl -w net.ipv4.ip_forward=0
#sysctl -w net.ipv4.tcp_ecn=3


# increate MTU of Monitoring IFACE to be able to contain additional data for INT
ip link set $MON_IFACE mtu 2000

function monitor_cpu_memory(){
   PID=$1
   FILE_NAME="log/cpu_mem_int_${ENABLE_INT}_pid_${PID}"
   #/home/montimage/.local/bin/psrecord "$PID" --plot $FILE_NAME.png --log $FILE_NAME.txt --duration 300 --interval 1 --include-children
   /home/montimage/.local/bin/psrecord "$PID" --log $FILE_NAME.txt --duration 320 --interval 1 --include-children
}

# ensure no switch is running
killall simple_switch

# Betrand modified simple_switch to support L4S
SIMPLE_SWITCH="/home/montimage/bertrand-behavioral-model/targets/simple_switch/simple_switch --queue 2  --ll_queue 64 --BE_queue 128"
# normal simple_switch
#SIMPLE_SWITCH="/usr/local/bin/simple_switch"

DEBUG="--log-file log/sw.log  --log-level info --pcap log/" 
#disable debug
DEBUG=""
($SIMPLE_SWITCH $DEBUG -i 1@$IFACE -i 2@$REV_IFACE -i 3@$MON_IFACE  $P4_FILE_PREFIX.json 2>&1 > log/sw-simple.log )&
SW_PID=$!
# change priority of the switch 
# Priority is a number in the range of -20 to 20. The higher the number, the lower the priority.
renice -n -10 -p $SW_PID
# bind the switch process to a cpu
taskset -c 0-4 -p $SW_PID

( monitor_cpu_memory $SW_PID ) &


#wait for simple_switch
sleep 2

#IP forwarding
# Syntax:
# ip_dst => ip_host mac_src mac_dst egress_port

# config le switch A-B
cat <<EOF  | config_sw
table_set_default ipv4_lpm drop

table_add ipv4_lpm ipv4_forward $CLIENT_A => $IFACE_MAC $CLIENT_A_MAC     1
table_add ipv4_lpm ipv4_forward $CLIENT_B => $IFACE_MAC $CLIENT_B_MAC     1
table_add ipv4_lpm ipv4_forward $SERVER_A => $REV_IFACE_MAC $SERVER_A_MAC 2
table_add ipv4_lpm ipv4_forward $SERVER_B => $REV_IFACE_MAC $SERVER_B_MAC 2
EOF


# L4S
cat <<EOF | config_sw
table_add select_PI2_param set_PI2_param => 1342 13421 15000 14
table_add select_L4S_param set_L4S_param => 5000 3000 0 1500 21
EOF

if [[ "$ENABLE_INT" == "yes" ]]; then
# CONFIGURE In-band network telemetry
# enable INT
# => set switch ID
cat <<EOF | config_sw
table_add tb_int_config_transit set_transit => 1
EOF

# set source
# ip_src ip_dst port_src port_dst => max_hop hop_md_length inst_mask priority
#cat <<EOF | config_sw
#table_add tb_int_config_source set_source $CLIENT_A&&&0xFFFFFF00 5001&&&0x0000 $SERVER_A&&&0xFFFFFF00 5001&&&0x0000 => 4 10 0xFFFF 0
#EOF

# do INT on any packet
cat <<EOF | config_sw
table_add tb_int_config_source set_source $CLIENT_A&&&0x00000000 5001&&&0x0000 $SERVER_A&&&0x00000000 5001&&&0x0000 => 4 10 0xFFFF 0
EOF

# set sink node
# egress_port => sink_reporting_port
# sent INT reports to the sink_reporting_port is currently not supported
# the INT data packet will be copied using mirroring via mirroring_add command
cat <<EOF | config_sw
table_add tb_int_config_sink set_sink 1 => 3
EOF



# mirroring port
# mirroring_add <mirror_id> <egress_port>
# mirror_id is defined by in int.p4:
#   const bit<32> REPORT_MIRROR_SESSION_ID = 1;
cat <<EOF | config_sw
mirroring_add 1 3
EOF

fi

# ping does not reply when having this
#  set_egress_mahimahi 2 33

# start mmt and tcpdump to capture and analyse traffic
. "$SCRIPT_PATH/monitoring-mmt-tcpdump.sh"

start-monitoring

#clear
echo "*******testbed is ready*******"

#simple_switch_CLI --thrift-port $THRIFT_PORT
# config_sw_ab

cd -- "$SCRIPT_PATH"

if [[ "$TEST_SCRIPT" == "" ]]; then
	# HN: either show a termnal or run a test-suite
	bash --noprofile --rcfile ./terminal.sh
	#bash ./test-suites.sh
else
	bash -x "$TEST_SCRIPT"
fi

# put simple_siwtch to forground
#fg

killall -2 simple_switch

sleep 2

stop-monitoring


#mv log "log-$(date +%s)"
