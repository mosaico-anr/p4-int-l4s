#!/bin/bash -x

# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.


set -x

if [ "$EUID" -ne 0 ]
	then echo "Please run as root"
	exit
fi

# by default, enable INT
if [ -z "$ENABLE_INT" ]; then
	export ENABLE_INT=yes
fi



#JSON file to run
FILE="switch-l4s.json"
if [[ "$#" == "1" ]]; then
	FILE="$1"
fi


# clear old compiled file
#rm *.json *.p4i
##compile code
#cat <<EOF | parallel -j 3
#	p4c  --target  bmv2  --arch  v1model  switch-l4s.p4
#	p4c  --target  bmv2  --arch  v1model  switch-int.p4
#	p4c  --target  bmv2  --arch  v1model  switch-forward.p4
#EOF


if [ $? != 0 ]
then
  echo "Could not compile P4" >&2
  exit 1
fi

source environment.sh

# clean log folder
mkdir -p log  2> /dev/null

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


export CLIENT_A_MAC=$(get-remote-mac $CLIENT_A $CLIENT_A_IFACE)
export CLIENT_B_MAC=$(get-remote-mac $CLIENT_B $CLIENT_B_IFACE)

export SERVER_A_MAC=$(get-remote-mac $SERVER_A $SERVER_A_IFACE)
export SERVER_B_MAC=$(get-remote-mac $SERVER_B $SERVER_B_IFACE)

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
run-on-host $CLIENT_A sudo ip route add $SERVER_NET via $IFACE_IP
run-on-host $CLIENT_B sudo ip route add $SERVER_NET via $IFACE_IP
run-on-host $SERVER_A sudo ip route add $CLIENT_NET via $REV_IFACE_IP
run-on-host $SERVER_B sudo ip route add $CLIENT_NET via $REV_IFACE_IP

# Disable offload
run-on-host $CLIENT_A sudo ethtool -K $CLIENT_A_IFACE tso off gso off gro off tx off
run-on-host $CLIENT_B sudo ethtool -K $CLIENT_A_IFACE tso off gso off gro off tx off
run-on-host $SERVER_A sudo ethtool -K $SERVER_A_IFACE tso off gso off gro off tx off
run-on-host $SERVER_B sudo ethtool -K $SERVER_B_IFACE tso off gso off gro off tx off

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
sysctl -w net.ipv4.tcp_ecn=0

function create-virtual-nic(){
	NIC_1=$1
	MAC_1=$2
	NIC_2=$3
	MAC_2=$4

	ip link add name $NIC_1 type veth peer name $NIC_2
	config-nic $NIC_1
	config-nic $NIC_2
	ip link set dev $NIC_1 address $MAC_1
	ip link set dev $NIC_2 address $MAC_2
	ifconfig $NIC_1 up
	ifconfig $NIC_2 up
}

B1_IFACE=veth_b1
B2_IFACE=veth_b2
B1_IFACE_MAC=00:00:00:00:00:01
B2_IFACE_MAC=00:00:00:00:00:02


function create-dummy-nic(){
	NIC=$1
	MAC=$2
	ip link add name $NIC type dummy
	config-nic $NIC
	ip link set dev $NIC address $MAC
	ifconfig $NIC up
}

#create-virtual-nic "$B1_IFACE" "$B1_IFACE_MAC" "$B2_IFACE" "$B2_IFACE_MAC"

modprobe dummy
#use MON_IFACE and a dummy NIC
B1_IFACE=$MON_IFACE
B2_IFACE=veth
B1_IFACE_MAC=$MON_IFACE_MAC
B2_IFACE_MAC=00:00:00:00:00:0b

#create-dummy-nic $B2_IFACE $B2_IFACE_MAC


B1_IFACE=$MON_IFACE
B2_IFACE=$MON_IFACE
B1_IFACE_MAC=$MON_IFACE_MAC
B2_IFACE_MAC=$MON_IFACE_MAC

# increate MTU of Monitoring IFACE to be able to contain additional data for INT
ip link set $B1_IFACE mtu 2000
ip link set $B1_IFACE mtu 2000

SW_A_B_PORT=9091
SW_B_C_PORT=9092

SIMPLE_SWITCH=simple_switch
function create-switch(){
	NIC_1=$1
	NIC_2=$2
	THRIFT_PORT=$3
	ID=$4
	# remove the first 4 parameters
	shift ; shift ; shift ; shift
	
	echo "$(now) Creating a bridge using simple_switch: $@"
	#/home/montimage/github/behavioral-model/targets/simple_switch/simple_switch   --pcap  --log-console --log-level debug  -i 1@veth_a -i 2@veth_b --thrift-port 9090 $FILE &
	#DEBUG="--log-file log/sw-$ID.log  --log-level debug --pcap $LOG/" 
	#disable debug
	#DEBUG=""
	$SIMPLE_SWITCH $DEBUG --device-id $ID -i 1@$NIC_1 -i 2@$NIC_2 --thrift-port $THRIFT_PORT "$@"
	echo "$(now) simple_switch $ID returned code: $?"
	#/usr/local/bin/simple_switch "$@"
}

function monitor_cpu_memory(){
   PID=$1
   FILE_NAME="log/cpu_mem_int_${ENABLE_INT}_pid_${PID}"
   #/home/montimage/.local/bin/psrecord "$PID" --plot $FILE_NAME.png --log $FILE_NAME.txt --duration 300 --interval 1 --include-children
   /home/montimage/.local/bin/psrecord "$PID" --log $FILE_NAME.txt --duration 320 --interval 1 --include-children
}

#tcpdump -i enp0s10 -w log/enp0s10.pcap &

# ensure no switch is running
killall simple_switch

# Betrand modified simple_switch to support L4S
SIMPLE_SWITCH="/home/montimage/bertrand-behavioral-model/targets/simple_switch/simple_switch --queue 2  --ll_queue 64 --BE_queue 128"
create-switch $IFACE   "$B1_IFACE"   "$SW_A_B_PORT" "1" switch-l4s.json 2>&1 1> log/sw-1-simple.log &
(monitor_cpu_memory $!) &
#SIMPLE_SWITCH=/home/montimage/github-behavioral-model/targets/simple_switch/simple_switch
#create-switch $IFACE   "$B1_IFACE"   "$SW_A_B_PORT" "1" switch-int.json 2>&1 1> log/sw-1-simple.log &
# Here we do not use L4S => use "standard" simple_switch to avoid debug messages
SIMPLE_SWITCH=/home/montimage/github-behavioral-model/targets/simple_switch/simple_switch
create-switch "$B2_IFACE" $REV_IFACE "$SW_B_C_PORT" "2" switch-int.json 2>&1 1> log/sw-2-simple.log &


#wait for simple_switch
sleep 2

function config_sw_ab(){
	tee -a log/config-$SW_A_B_PORT.log | /usr/local/bin/simple_switch_CLI --thrift-port "$SW_A_B_PORT" "$@"
}
function config_sw_bc(){
	tee -a log/config-$SW_B_C_PORT.log | /usr/local/bin/simple_switch_CLI --thrift-port "$SW_B_C_PORT" "$@"
}
#table_add ipv4_lpm ipv4_forward 192.168.109.214 => 00:00:00:00:00:a0 00:00:00:00:00:a1  1

#IP forwarding
# Syntax:
# ip_dst => ip_host mac_src mac_dst egress_port

# config le switch A-B
cat <<EOF  | config_sw_ab
table_set_default ipv4_lpm drop

table_add ipv4_lpm ipv4_forward $CLIENT_A => $IFACE_MAC $CLIENT_A_MAC    1
table_add ipv4_lpm ipv4_forward $CLIENT_B => $IFACE_MAC $CLIENT_B_MAC    1
table_add ipv4_lpm ipv4_forward $SERVER_A => $B1_IFACE_MAC $B2_IFACE_MAC 2
table_add ipv4_lpm ipv4_forward $SERVER_B => $B1_IFACE_MAC $B2_IFACE_MAC 2
EOF

cat <<EOF | config_sw_bc
table_set_default ipv4_lpm drop

table_add ipv4_lpm ipv4_forward $CLIENT_A => $B2_IFACE_MAC $B1_IFACE_MAC  1
table_add ipv4_lpm ipv4_forward $CLIENT_B => $B2_IFACE_MAC $B1_IFACE_MAC  1
table_add ipv4_lpm ipv4_forward $SERVER_A => $REV_IFACE_MAC $SERVER_A_MAC 2
table_add ipv4_lpm ipv4_forward $SERVER_B => $REV_IFACE_MAC $SERVER_B_MAC 2
EOF


# L4S
cat <<EOF | config_sw_ab
table_add select_PI2_param set_PI2_param => 1342 13421 15000 14
table_add select_L4S_param set_L4S_param => 5000 3000 0 1500 21
EOF

if [[ "$ENABLE_INT" == "yes" ]]; then
# CONFIGURE In-band network telemetry
# enable INT
# => set switch ID
cat <<EOF | config_sw_ab
table_add tb_int_config_transit set_transit => 1
EOF

cat <<EOF | config_sw_bc
table_add tb_int_config_transit set_transit => 2
EOF

#cat <<EOF | simple_switch_CLI
#table_add swtrace add_swtrace => 1
#EOF

# set source
# ip_src ip_dst port_src port_dst => max_hop hop_md_length inst_mask priority
cat <<EOF | config_sw_ab
table_add tb_int_config_source set_source $CLIENT_A&&&0xFFFFFF00 5001&&&0x0000 $SERVER_A&&&0xFFFFFF00 5001&&&0x0000 => 4 10 0xFFFF 0
EOF

#cat <<EOF | config_sw_bc
#table_add tb_int_config_source set_source 10.0.10.1&&&0xFFFFFF00 5001&&&0x0000 10.0.20.0&&&0xFFFFFF00 5001&&&0x000 => 4 10 0x0000 0
#EOF

# set sink node
# egress_port => sink_reporting_port
# sent INT reports to the sink_reporting_port is currently not supported
# the INT data packet will be copied using mirroring via mirroring_add command
cat <<EOF | config_sw_ab
table_add tb_int_config_sink set_sink 1 => 3
EOF
cat <<EOF | config_sw_bc
table_add tb_int_config_sink set_sink 2 => 3
EOF

fi

# mirroring port
# mirroring_add <mirror_id> <egress_port>
# mirror_id is defined by in int.p4:
#   const bit<32> REPORT_MIRROR_SESSION_ID = 500;
#cat <<EOF | config_sw_bc
#mirroring_add 500 3
#EOF

# ping does not reply when having this
#  set_egress_mahimahi 2 33


#simple_switch_CLI --thrift-port $THRIFT_PORT
# config_sw_ab
bash --noprofile --rcfile ./test-suites.sh
# put simple_siwtch to forground
#fg

killall -2 simple_switch

sleep 2


mv log "log-$(date +%s)"
