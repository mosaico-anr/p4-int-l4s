#!/bin/bash -x
# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#

# This script is to measure QUIC traffic
#
# Parameters are set via environment variables
# - info of the connection client_a -- server_a:
#    + BANDWIDTH  : bandwidth limited at the switch in Mbps
#    + TYPE       : "legit" or "unrespECN" or "iperf3"
#    + FILE_SIZE  : size of file to be downloaded, in MB

# we want to use clientA--serverA pair or clientB--serverB pair
# when using iperf3: we use clientB--serverB pair as they have tcp-prague by default
if [[ "$TYPE" == "iperf3" ]]; then
	#### Server B -- client B
	# data plane: generate traffic
	SERVER_DATA=$SERVER_B
	CLIENT_DATA=$CLIENT_B
	
	# control plane: to access to VMs to execute commands
	SERVER_CTRL=$SERVER_B_CTRL
	CLIENT_CTRL=$CLIENT_B_CTRL
	
	SERVER_IFACE=$SERVER_B_IFACE
	CLIENT_IFACE=$CLIENT_B_IFACE
else

	### server A -- client A
	# data plane
	SERVER_DATA=$SERVER_A
	CLIENT_DATA=$CLIENT_A
	# control plane: to access to VMs to execute commands
	SERVER_CTRL=$SERVER_A_CTRL
	CLIENT_CTRL=$CLIENT_A_CTRL
	
	SERVER_IFACE=$SERVER_A_IFACE
	CLIENT_IFACE=$CLIENT_A_IFACE
fi

# maximum 600 seconds
#export DURATION=600

export FILE_SIZE=1000
# create a dummy files with a given size on a given host
function create-dummy-files-on-servers(){
	run-on-host "$SERVER_CTRL" truncate -s "${FILE_SIZE}MB" "picoquic/picoquic/server_files/index-${FILE_SIZE}MB.htm"
}

# this script will: delete all previous qdisc setup
# no parameter
# example:
#  reset-qdisc-off-all-vms
function reset-qdisc-off-all-vms(){
	run-on-host $CLIENT_CTRL tc qdisc del dev $CLIENT_IFACE root
	run-on-host $SERVER_CTRL tc qdisc del dev $SERVER_IFACE root
}

date
set -x

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# load predefined environment variables
. "$SCRIPT_PATH/../environment.sh"
MMT_CONFIG_FILE="$SCRIPT_PATH/mmt-probe.conf"

. "$SCRIPT_PATH/pre-process-mmt-csv.sh" 


LOG_DIR="$PWD/log"
mkdir -p -- $LOG_DIR

# port of UDP on which QUIC uses
TCP_OR_UDP_PORT=4433

# current parameters
function print-parameters(){
cat <<EOF
{
	"SERVER":     "$SERVER_DATA",
	"CLIENT":     "$CLIENT_DATA",
	"bandwidth":  "$BANDWIDTH Mbps",
	"type":       "$TYPE",
	"file-size":  "$FILE_SIZE MB"
}
EOF
}

# copy a qlog file from a VM, then extract necessaire info
# usage: copy-qlog $CLIENT_CTRL
function copy-qlog(){
	HOST_CTRL=$1
	HOST_DATA=$2
	output="$HOST_DATA.qlog"

	log "copy qlog file from $HOST_DATA to $output"
	cd -- "$LOG_DIR"
	
	# copy to the local machine
	( run-on-host "$HOST_CTRL" "cat picoquic/picoquic/*qlog" ) > "$output"
	
	# if we have the content
	# As the log of picoquic can be either in .qlog or .log file.
	#   thus we check whether it is in .qlog
	# Checks if file has size greater than 0
	if [[ -s "$output" ]]; then
		#if this is .qlog, we extract the info
		#python "$SCRIPT_PATH/qlog-reader.py" "$output" "$output.csv"
		echo "no qlog"
	else
		#remove the empty file
		rm -rf -- "$output"
		output="$HOST_DATA.log"
		#somehow, picoquic does not generate .qlog but log
		( run-on-host "$HOST_CTRL" "cat picoquic/picoquic/*.log" ) > "$output"
	fi
	
	# compress to reduce storage space
	tar -czf "$output.tar.gz" "$output"
	#clean qlog files on this local machine and on the remote host
	rm -rf -- "$output"
}

function get-qlogs(){
	copy-qlog "$CLIENT_CTRL" "$CLIENT_DATA"
	copy-qlog "$SERVER_CTRL" "$SERVER_DATA"
}

function start-picoquic-servers(){
	log "run picoquic servers"
	#clean old log files
	run-on-host "$SERVER_CTRL" "rm -rf picoquic/picoquic/*log; rm -rf picoquic/picoquic/screenlog*"
	#on SERVER_CTRL A
	duration=$((DURATION+10))
	run-on-host "$SERVER_CTRL" "cd picoquic/picoquic && screen -S hn -L -dm timeout $duration ./launchquic.sh srv l4s $TCP_OR_UDP_PORT $TYPE_A verbose"
}


function start-picoquic-clients-and-wait-for-finish(){
	log "begin picoquic clients"
	#clean old log files
	run-on-host "$CLIENT_CTRL" "rm -rf picoquic/picoquic/*log; rm -rf picoquic/picoquic/screenlog*"
	
	sleep 5
	run-on-host "$CLIENT_CTRL" "cd picoquic/picoquic && screen -S hn -L -dm timeout $DURATION ./launchquic.sh cli $SERVER_DATA $TCP_OR_UDP_PORT $TYPE $FILE_SIZE verbose"
	
	sleep $DURATION
	sleep 5

	run-on-host "$CLIENT_CTRL" "cat picoquic/picoquic/screenlog*"
	run-on-host "$SERVER_CTRL" "cat picoquic/picoquic/screenlog*"

	log "end picoquic clients"
}


function start-iperf3-servers(){
	log "configuration $SERVER_CTRL VM"
	run-on-host "$SERVER_CTRL" "rm -rf /tmp/screenlog*"
	# activate tcp-prage
	run-on-host $SERVER_CTRL sudo sysctl -w net.ipv4.tcp_congestion_control=prague
	# Enable Accurate ECN
	run-on-host $SERVER_CTRL sudo sysctl -w net.ipv4.tcp_ecn=3
	
	log "start iperf3 $SERVER_CTRL"
	duration=$((DURATION+10))
	run-on-host "$SERVER_CTRL" "cd /tmp/ && screen -S hn -L -dm timeout $duration iperf3 -s --one-off --port $TCP_OR_UDP_PORT"
}


function start-iperf3-clients-and-wait-for-finish(){
	#clean old log files
	run-on-host "$CLIENT_CTRL" "rm -rf /tmp/screenlog*"
	
	log "configuration iperf3 $CLIENT_CTRL VM"
	
	run-on-host $CLIENT_CTRL sudo sysctl -w net.ipv4.tcp_congestion_control=prague
	run-on-host $CLIENT_CTRL sudo sysctl -w net.ipv4.tcp_ecn=3
	
	log "begin iperf3 clients"
	
	sleep 5
	
	run-on-host "$CLIENT_CTRL" "cd /tmp/ && screen -S hn -L -dm iperf3 -c $SERVER_DATA  --set-mss 1500 --length 1500 --time $DURATION --port $TCP_OR_UDP_PORT"
	
	sleep $DURATION
	sleep 5

	#print execution logs of iperf3 CLIENT_CTRL and SERVER_CTRL,
	run-on-host "$CLIENT_CTRL" "cat /tmp/screenlog*; rm -rf /tmp/screenlog*"
	run-on-host "$SERVER_CTRL" "cat /tmp/screenlog*; rm -rf /tmp/screenlog*"

	log "end iperf3 clients"
}


function limit-bandwidth(){
	# the P4 switch will read "./mahimahi.txt"
	cp "$SCRIPT_PATH/../mahimahi/${BANDWIDTH}Mbps.txt" "$SCRIPT_PATH/../mahimahi.txt"
	cp "$SCRIPT_PATH/../mahimahi/${BANDWIDTH}Mbps.txt" "$LOG_DIR"
	# syntax: set_egress_mahimahi port_num pps
	# ==> the pps parameter will no be taken into account as it is determined by the "mahimahi.txt" file
	echo "set_egress_mahimahi 1 ${BANDWIDTH}000" | config_sw
	echo "set_egress_mahimahi 2 ${BANDWIDTH}000" | config_sw
	sleep 2
}

log "start experiment"

# to verify which processes are running
ps aux
run-on-host "$SERVER_CTRL" ps aux
run-on-host "$CLIENT_CTRL" ps aux
#run-on-all-endhost ps aux

log "$(print-parameters)"
print-parameters > "$LOG_DIR/param.json"

limit-bandwidth

if [[ "$TYPE" == "iperf3" ]]; then
	start-iperf3-servers
	start-iperf3-clients-and-wait-for-finish
else 
	create-dummy-files-on-servers
	start-picoquic-servers
	start-picoquic-clients-and-wait-for-finish
	get-qlogs
fi

log "end experiment"