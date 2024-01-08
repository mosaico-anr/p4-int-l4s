#!/bin/bash -x
# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#

# This script is to measure QUIC traffic



# data plane: generate traffic
SERVER_DATA_IP=$SERVER_C
CLIENT_DATA_IP=$CLIENT_C

# control plane: to access to VMs to execute commands
SERVER_CTRL_IP=$SERVER_C_CTRL
CLIENT_CTRL_IP=$CLIENT_C_CTRL

date
set -x
#set -e


SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
MMT_CONFIG_FILE="$SCRIPT_PATH/mmt-probe.conf"

# load predefined environment variables
. "$SCRIPT_PATH/../environment.sh"
. "$SCRIPT_PATH/pre-process-mmt-csv.sh" 


LOG_DIR="$SCRIPT_PATH/../log"
mkdir -p -- $LOG_DIR

# port of UDP on which QUIC uses
TCP_OR_UDP_PORT=4433
FILE_SIZE=1000

# get_nic_stat 10.0.0.1 enp0s8 tx_packets
# get_nic_stat 10.0.0.1 enp0s8 tx_bytes
# get_nic_stat 10.0.0.1 enp0s8 rx_packets
# get_nic_stat 10.0.0.1 enp0s8 rx_bytes

function get_nic_stat(){
	HOST=$1
	NIC=$2
	STAT=$3
	run-on-host "$HOST" cat /sys/class/net/$NIC/statistics/$STAT
}

function get_picoquic_path(){
	flow_type=$1
	# depending on flow type, we start different client or server
	picoquic_path=""
	if [[ "$flow_type" == "unrespECN" ]]; then
		picoquic_path="picoquic/picoquic-unrespECN"
	elif [[ "$flow_type" == "cl_legit" ]]; then
		picoquic_path="picoquic/picoquic-classic-legit"
	elif [[ "$flow_type" == "ll_legit" ]]; then
		picoquic_path="picoquic/picoquic-legit"
	elif [[ "$flow_type" == "iperf" ]]; then
		picoquic_path=""
	else
		echo "Does not support flow type: $flow_type" > /dev/stderr
		exit 0
	fi
	echo $picoquic_path
}

function copy_log(){
	flow_type=$1
	picoquic_path=$(get_picoquic_path $flow_type)
	
	mkdir -p "$LOG_DIR/qlog/$flow_type"
	run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && tar -czf - *.qlog *.log " > "$LOG_DIR/qlog/$flow_type"/server.tar.gz
	run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && tar -czf - *.qlog *.log " > "$LOG_DIR/qlog/$flow_type"/client.tar.gz
	
	# delete log files
	run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && rm -rf *.qlog *.log "
	run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && rm -rf *.qlog *.log "
}

# directory to contain semaphore files to remember whenther to rebuild picoquic client/servers
# ==> delete this folder to trigger the rebuild
REBUILD_SEM_DIR="/tmp/rebuild"
mkdir -p "$REBUILD_SEM_DIR"

# Inverse value of POWER_ATTACK
function get_power_attack(){
	POWER="$1"
	case $POWER in
		"1")
			echo "0"
			;;
		"0.9")
			echo "0.1"
			;;
		"0.8")
			echo "0.2"
			;;
		"0.5")
			echo "0.5"
			;;
		"0.2")
			echo "0.8"
			;;
		"0.1")
			echo "0.9"
			;;
		"0")
			echo "1"
			;;
		*)
			echo "Unsupport POWER_ATTACK: $POWER" | tee > /dev/stderr
			exit 2
	esac
}

function rebuild_attacker(){
	picoquic_path=$(get_picoquic_path unrespECN)
	echo "Rebuild attack client and server using power_attack=$POWER_ATTACK"
	LAST_POWER_ATTACK=$(cat $REBUILD_SEM_DIR/unrespECN)
	if [[ "$LAST_POWER_ATTACK" == "$POWER_ATTACK" ]]; then
		echo "power attack has not changed since last built ==> do not rebuild picoquic"
	else
		printf "$POWER_ATTACK" > $REBUILD_SEM_DIR/unrespECN
		POWER_ATTACK_VAL=$(get_power_attack "$POWER_ATTACK")
		run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh srv l4s unrespECN $POWER_ATTACK_VAL; git diff)"
		run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh cli l4s unrespECN $POWER_ATTACK_VAL; git diff)"
	fi
}


function rebuild_ll_legit(){
	picoquic_path=$(get_picoquic_path ll_legit)
	file="$REBUILD_SEM_DIR/ll_legit"
	echo "Rebuild ll legit client and server"
	if [[ -f  "$file" ]]; then
		echo "$file is existing ==> do not rebuild picoquic"
	else
		date > "$file"
		run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh srv l4s legit; git diff)"
		run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh cli l4s legit; git diff)"
	fi
}

function rebuild_cl_legit(){
	picoquic_path=$(get_picoquic_path cl_legit)
	file="$REBUILD_SEM_DIR/cl_legit"
	echo "Rebuild cl legit client and server"
	if [[ -f  "$file" ]]; then
		echo "$file is existing ==> do not rebuild picoquic"
	else
		date > "$file"
		run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh srv classic legit; git diff)"
		run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && (rm -rf build; ./rebuild-picoquic.sh cli classic legit; git diff)"
	fi
}

function start_flow()(
	local index=$1
	local flow_type=$2
	local start_time=$3
	local duration=$4
	local port=$5
	echo "Start new flow $@"
	
	picoquic_path=$(get_picoquic_path $flow_type)

	screen_name="$flow_type-$port"
	# ensure no script is running
	run-on-host "$SERVER_CTRL_IP" "screen -X -S svr-$screen_name stuff '^C'"
	run-on-host "$SERVER_CTRL_IP" "screen -X -S cli-$screen_name stuff '^C'"

	server_duration=$((duration+10))
	date
	sleep "$start_time"
	echo "Start new flow $@"
	# create new data file to download, then start server
	run-on-host "$SERVER_CTRL_IP" truncate -s "${FILE_SIZE}MB" "$picoquic_path/server_files/index-${FILE_SIZE}MB.htm"
	run-on-host "$SERVER_CTRL_IP" "cd $picoquic_path && screen -S svr-$screen_name -L -Logfile /tmp/hn/$screen_name -dm timeout --signal=9 $server_duration ./start_picoserver.sh $port"
	sleep 2 #wait for the server
	# start client
	run-on-host "$CLIENT_CTRL_IP" "cd $picoquic_path && screen -S cli-$screen_name -L -Logfile /tmp/hn/$screen_name -dm timeout --signal=9 $duration ./build/picoquic_sample client $SERVER_DATA_IP $port /tmp/ index-${FILE_SIZE}MB.htm"
	date
)

function start-flows-and-wait-to-finish(){
	declare -a FLOWS_CFG=()
	max_duration=0
	index=0
	IFS=";" read -ra CONF <<<"$TRAFFIC_TYPES"
	for conf in "${CONF[@]}"
	do
		((index+=1))

		echo " - $index starting $conf"
		
		#ignore emtpy line
		[[ "$conf" == "" ]] && continue
		
		#parse the parameter
		IFS="," read -r flow_type start_time duration port <<<"$conf"
		if [[ "$flow_type" == "" || "$start_time" == "" || "$duration" == "" || "$port" == "" ]]; then
			echo "Incorrect configuration: '$conf'"
			exit 1 
		fi
	
		[[ $start_time == ?(-)+([0-9]) ]] || (echo "start_time is not a number: $conf" && exit 1)
		[[ $duration == ?(-)+([0-9]) ]]   || (echo "duration is not a number: $conf"   && exit 1)

		# remeber the configuration
		FLOWS_CFG+=("{\"type\":\"$flow_type\", \"start_time\": $start_time, \"duration\": $duration, \"server_port\": $port}")
		
		#start the flow
		( start_flow "$index" "$flow_type" "$start_time" "$duration" "$port" ) &
		
		#total time a flow needs
		timeout=$((start_time+duration+10))
		#get time tobe sleeped
		max_duration=$((timeout>max_duration? timeout : max_duration))
	done
	date
	
	# current parameters
	cat > "$LOG_DIR/param.json" <<EOF
{
	"server":       "$SERVER_DATA_IP",
	"client":       "$CLIENT_DATA_IP",
	"bandwidth":    "$BANDWIDTH Mbps",
	"power-attack": $POWER_ATTACK,
	"flows":        [$(IFS=, ; echo "${FLOWS_CFG[*]}")]
}
EOF
	
	# wait for all flows terminate
	date
	echo "sleep $max_duration to wait for all flows"
	sleep $max_duration
	date
	echo "terminated all flows"
}




log "start experiment"
date

# to verify which processes are running
ps auxf
run-on-host "$SERVER_CTRL_IP" ps auxf
run-on-host "$CLIENT_CTRL_IP" ps auxf
#run-on-all-endhost ps aux

#clean old log files
run-on-host "$SERVER_CTRL_IP" "rm -rf /tmp/hn; mkdir /tmp/hn"
run-on-host "$CLIENT_CTRL_IP" "rm -rf /tmp/hn; mkdir /tmp/hn"

# rebuild picoquic of attacker only to update the attack_power
rebuild_attacker
rebuild_cl_legit
rebuild_ll_legit

	# print stat of NIC
NIC=enp0s8
run-on-host "$SERVER_CTRL_IP" ifconfig $NIC
run-on-host "$CLIENT_CTRL_IP" ifconfig $NIC
# get number of packets, bytes sent and received by server, clients
SERVER_TX_PACKETS_BEGIN=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" tx_packets)
SERVER_RX_PACKETS_BEGIN=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" rx_packets)
CLIENT_TX_PACKETS_BEGIN=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" tx_packets)
CLIENT_RX_PACKETS_BEGIN=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" rx_packets)

SERVER_TX_BYTES_BEGIN=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" tx_bytes)
SERVER_RX_BYTES_BEGIN=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" rx_bytes)
CLIENT_TX_BYTES_BEGIN=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" tx_bytes)
CLIENT_RX_BYTES_BEGIN=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" rx_bytes)

date
start-flows-and-wait-to-finish

run-on-host "$SERVER_CTRL_IP" ifconfig $NIC
run-on-host "$CLIENT_CTRL_IP" ifconfig $NIC
	
SERVER_TX_PACKETS_END=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" tx_packets)
SERVER_RX_PACKETS_END=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" rx_packets)
CLIENT_TX_PACKETS_END=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" tx_packets)
CLIENT_RX_PACKETS_END=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" rx_packets)

SERVER_TX_BYTES_END=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" tx_bytes)
SERVER_RX_BYTES_END=$(get_nic_stat "$SERVER_CTRL_IP" "$NIC" rx_bytes)
CLIENT_TX_BYTES_END=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" tx_bytes)
CLIENT_RX_BYTES_END=$(get_nic_stat "$CLIENT_CTRL_IP" "$NIC" rx_bytes)

cat <<EOF | tee "$LOG_DIR/stat_nic.json"
{
"server_tx_packets": $((SERVER_TX_PACKETS_END - SERVER_TX_PACKETS_BEGIN)),
"client_rx_packets": $((CLIENT_RX_PACKETS_END - CLIENT_RX_PACKETS_BEGIN)),

"client_tx_packets": $((CLIENT_TX_PACKETS_END - CLIENT_TX_PACKETS_BEGIN)),
"server_rx_packets": $((SERVER_RX_PACKETS_END - SERVER_RX_PACKETS_BEGIN)),

"server_tx_bytes": $((SERVER_TX_BYTES_END - SERVER_TX_BYTES_BEGIN)),
"client_rx_bytes": $((CLIENT_RX_BYTES_END - CLIENT_RX_BYTES_BEGIN)),

"client_tx_bytes": $((CLIENT_TX_BYTES_END - CLIENT_TX_BYTES_BEGIN)),
"server_rx_bytes": $((SERVER_RX_BYTES_END - SERVER_RX_BYTES_BEGIN))
}
EOF

echo "Execution log of clients:"
# print out the output screens
run-on-host "$CLIENT_CTRL_IP" "cat /tmp/hn/*"
echo "Execution log of servers:"
run-on-host "$SERVER_CTRL_IP" "cat /tmp/hn/*"

copy_log "unrespECN"
copy_log "cl_legit"
copy_log "ll_legit"

date
log "end experiment"