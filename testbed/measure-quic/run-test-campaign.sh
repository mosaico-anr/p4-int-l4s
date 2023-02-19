#!/bin/bash -x
# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#


# directory which contain this script
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# script to be run when the l4s switch is started successfully
export TEST_SCRIPT="$SCRIPT_PATH/start-monitoring.sh"

ROUND_ID=5
ROUND_NOTE="LL traffic is classified by using ECN==1"

DATA_DIR="$SCRIPT_PATH/round-$ROUND_ID"
rm -rf   "$DATA_DIR"
mkdir -p "$DATA_DIR"

cat <<EOF > "$DATA_DIR/README.md"
This campgaign of test was starting at $(date).
Each test result is in a folder whose name uses this format: \`flowA--flowB--date \`,
in which \`flowA\` and \`flowB\` has: \`type-bandwidth-start_time-duration\`
- \`type\`: either \`legit\` (legitime traffic) or \`unrespECN\`
- \`bandwidth\`: limit bandwidth at the client side in Kbps. Set to 0Kbps to unlimit.
- \`start_time\`: the client sleeps X seconds before sending request
- \`duration\`: the duration of request sent by the client before being stopped
$ROUND_NOTE
EOF

# read configurations to an array
declare -a LINES=()
while read -r line; do
	echo $line
	#ignore lines starting with #
	[[ "$line" =~ ^#.*$ ]] && continue
	LINES+=("$line")
	#break
done <<EOF
# configuration parameters use the following format:
# config A; config B
# bw,type,start,duration;bw,type,start,duration
#
# 5 Mbps = 5000 Kbps
5000,legit,0,120;5000,legit,0,120
5000,legit,0,120;5000,unrespECN,0,120
5000,legit,0,120;5000,legit,15,60
5000,legit,0,120;5000,unrespECN,15,60
#
# 10 Mbps
10000,legit,0,120;10000,legit,0,120
10000,legit,0,120;10000,legit,15,60
10000,legit,0,120;10000,unrespECN,15,60
10000,legit,0,120;10000,unrespECN,0,120
#
# 15 Mbps
15000,legit,0,120;15000,legit,0,120
15000,legit,0,120;15000,legit,15,60
15000,legit,0,120;15000,unrespECN,15,60
15000,legit,0,120;15000,unrespECN,0,120
#
# 20 Mbps
20000,legit,0,120;20000,legit,0,120
20000,legit,0,120;20000,legit,15,60
20000,legit,0,120;20000,unrespECN,15,60
20000,legit,0,120;20000,unrespECN,0,120
#
# 30 Mbps
30000,legit,0,120;30000,legit,0,120
30000,legit,0,120;30000,legit,15,60
30000,legit,0,120;30000,unrespECN,15,60
30000,legit,0,120;30000,unrespECN,0,120
#
# 50 Mbps
50000,legit,0,120;50000,legit,0,120
50000,legit,0,120;50000,legit,15,60
50000,legit,0,120;50000,unrespECN,15,60
50000,legit,0,120;50000,unrespECN,0,120
#
# unlimited
0,legit,0,120;0,legit,0,120
0,legit,0,120;0,legit,15,60
0,legit,0,120;0,unrespECN,15,60
0,legit,0,120;0,unrespECN,0,120
#
EOF

# now process each configuration
for line in "${LINES[@]}"
do
	echo "$line"

	IFS=';' read -r cfgA cfgB <<<"$line"
	IFS=',' read -r bwA typeA startA durationA <<<"$cfgA"
	IFS=',' read -r bwB typeB startB durationB <<<"$cfgB"
	
	#export the varilabes to transfer the parameters to the scripts to be executed
	export BANDWIDTH_A=$bwA
	export TYPE_A=$typeA
	export START_TIME_A=$startA
	export DURATION_A=$durationA
	export FILE_SIZE_A=2000
	
	export BANDWIDTH_B=$bwB
	export TYPE_B=$typeB
	export START_TIME_B=$startB
	export DURATION_B=$durationB
	export FILE_SIZE_B=2000
	
	if [[ "$IS_INITIALIZED" == "" ]]; then
		export IS_INITIALIZED=YES
		unset NO_COMPILE_P4
	else
		# we do not need to recompile P4 code each iteration
		export NO_COMPILE_P4=true
	fi
	
	cd "$SCRIPT_PATH/../"
	pwd
	
	date
	
	rm -rf log
	mkdir log
	
	( ./setup-testbed.sh 2>&1 ) |tee log/script.log

	mv log "$DATA_DIR/$typeA-bw_${bwA}Kbps-start_${startA}s-duration_${durationA}s--$typeB-bw_${bwB}Kbps-start_${startB}s-duration_${durationB}s--$(date +%Y%m%d-%H%M%S)"
	
	#break
	
	sleep 30
done