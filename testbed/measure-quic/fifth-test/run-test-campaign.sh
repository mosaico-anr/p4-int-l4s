#!/bin/bash -x
# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#

set -x

# directory which contain this script
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# script to be run when the l4s switch is started successfully
export TEST_SCRIPT="$SCRIPT_PATH/start-monitoring.sh"

LOG_DIR="$SCRIPT_PATH/../log"
mkdir -p -- $LOG_DIR


# limit the outing bandwidth of router using Mahimahi
function limit-bandwidth(){
	BANDWITH=$1
	
	# the P4 switch will read "./mahimahi.txt"
	# no limited
	if [[ "$BANDWITH" == "0" ]]; then
		rm -rf "$SCRIPT_PATH/../mahimahi.txt"
	else
		# the P4 switch will read "./mahimahi.txt"
		cp "$SCRIPT_PATH/../mahimahi/${BANDWIDTH}Mbps.txt" "$SCRIPT_PATH/../mahimahi.txt"
		# remember the config file by copying it into "log" folder
		cp "$SCRIPT_PATH/../mahimahi/${BANDWIDTH}Mbps.txt" "$LOG_DIR"
	fi
}

# list_include_item "10 11 12" "2"
function list_include_item {
	local list="$1"
	local item="$2"
	if [[ $list =~ (^|[[:space:]])"$item"($|[[:space:]]) ]] ; then
		# yes, list include item
		result=0
	else
		result=1
	fi
	return $result
}

# rebuild the picoquic clients and servers
#rm -rf /tmp/rebuild

# read configurations to an array
declare -a TRAFFIC_CFG=()
while read -r line; do
	#ignore lines starting with #
	[[ "$line" =~ ^#.*$ ]] && continue
	#ignore empty line
	[[ "$line" == "" ]] && continue

	TRAFFIC_CFG+=("$line")
	#break
done <<EOF
# configuration parameters use the following format:
# config A; config B;
# type,start,duration,server-port;type,start,duration,server-port;...
#
# Example: "unrespECN,30,60,10000;cl_legit,0,120,4430"
#1 flux attaquant; 1 flux classique légitime
# - flux attaquant starts at 30th second, and keeps during 60 seconds, thus it will be stopped at 90th second.
# - flux cl legitime starts immediately, and keeps during 120 seconds
#
# 3x 1/0
unrespECN,0,60,10000
cl_legit,0,60,2000
ll_legit,0,60,3000
#
# 2x 1/1
unrespECN,30,60,10000;cl_legit,0,120,2000
unrespECN,30,60,10000;ll_legit,0,120,3000
#
# 2x 1/2
unrespECN,30,60,10000;cl_legit,0,120,2000;ll_legit,0,120,3000
unrespECN,30,60,10000;ll_legit,0,120,3000;ll_legit,0,120,3001
#
# 2x 1/5
unrespECN,30,60,10000;cl_legit,0,120,2000;cl_legit,0,120,2001;cl_legit,0,120,2002;ll_legit,0,120,3000;ll_legit,0,120,3001
unrespECN,30,60,10000;ll_legit,0,120,3000;ll_legit,0,120,3001;ll_legit,0,120,3002;ll_legit,0,120,3003;ll_legit,0,120,3004
#
# 2x 1/10
unrespECN,30,60,10000;cl_legit,0,120,2000;cl_legit,0,120,2001;cl_legit,0,120,2002;cl_legit,0,120,2003;cl_legit,0,120,2004;ll_legit,0,120,3000;ll_legit,0,120,3001;ll_legit,0,120,3002;ll_legit,0,120,3003;ll_legit,0,120,3004
unrespECN,30,60,10000;ll_legit,0,120,3000;ll_legit,0,120,3001;ll_legit,0,120,3002;ll_legit,0,120,3003;ll_legit,0,120,3004;ll_legit,0,120,3005;ll_legit,0,120,3006;ll_legit,0,120,3007;ll_legit,0,120,3008;ll_legit,0,120,3009
#
EOF

# 1. round ID
# for each round
for ROUND_ID in 2 3 4 5 6
do

DATA_DIR="$SCRIPT_PATH/round-$ROUND_ID"
rm -rf   "$DATA_DIR"
mkdir -p "$DATA_DIR"

# index of the current test => to count number of tests
TEST_INDEX=0

#remember of the current configuration of the switch
cp $SCRIPT_PATH/../switch-l4s.p4 $SCRIPT_PATH/../int.p4 $DATA_DIR

cat <<EOF > "$DATA_DIR/README.md"
This campgaign of test was starting at $(date).
Each test result is in a folder whose name uses this format: \`type-bandwidth-duration-nb_clients-nb_servers\`
- \`type\`: either \`cl_legit\` (classic legitime traffic), \`ll_legit\` (ll legitime traffic) or \`unrespECN\`
- \`bandwidth\`: limit bandwidth at the client side in Mbps. 0 == unlimited
- \`power\`: the power of attack
EOF

# 2 - parameter: Limit bandwidth
# limit bandwidth of output traffic of the router
for bw in 1 2 5 10
do

# 3 - parameter: Power attack
# power of attack
for power_attack in 0.1 0.2 0.5 1
do

# 4 - parameter: flows' configurations
# now process each configuration
for traffic_types in "${TRAFFIC_CFG[@]}"
do
			TEST_INDEX=$((TEST_INDEX+1))
			
			# 8 sept: perform only the tests in the list
			#if [ "$ROUND_ID" == "1" ]; then
			#	#run only the tests which are in the list
			#	`list_include_item "101 104 113 114 145 150 157 158 163 167 49 62 82" "$TEST_INDEX"` || continue
			#fi

			echo "Start Test $TEST_INDEX: $traffic_types "
			#export the varilabes to transfer the parameters to the scripts to be executed
			export BANDWIDTH=$bw
			export TRAFFIC_TYPES=$traffic_types
			export POWER_ATTACK=$power_attack
			
			# need to do before starting the BMv2 switch
			limit-bandwidth $bw
			
			# we do not need to recompile P4 code each iteration
			if [[ "$IS_INITIALIZED" == "" ]]; then
				export IS_INITIALIZED=YES
				unset NO_COMPILE_P4
			else
				export NO_COMPILE_P4=true
			fi
			
			# go up one level to setup testbed
			cd "$SCRIPT_PATH/../"
			pwd
			
			date
			
			rm -rf log
			mkdir log
			
			# setup testbed, then run script $TEST_SCRIPT
			( ./setup-testbed.sh 2>&1 ) | tee log/script.log

			# move "log" to a folder whose name represents the tested parameters
			DIR_NAME=$(echo "bw_${bw}Mbps-power_${POWER_ATTACK}-flows_${TRAFFIC_TYPES}" | sed -r 's/[\.\$;,]+/\./g' | head -c 220) #avoid filename too long > 255 characters
			mv log "$DATA_DIR/${TEST_INDEX}-${DIR_NAME}--$(date +%Y%m%d-%H%M%S)"
			
			# sleep a little before going to the next test
			echo "End Test $TEST_INDEX: Sleep 10 seconds before going to the next test..."
			sleep 2
done #end traffic_types
#break 3
done #end power_attack
done #end bw
done #end round

