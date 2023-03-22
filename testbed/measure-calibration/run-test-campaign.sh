#!/bin/bash -x
# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#


# directory which contain this script
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# script to be run when the l4s switch is started successfully
export TEST_SCRIPT="$SCRIPT_PATH/start-monitoring.sh"

ROUND_ID=2
# we can modify LL traffic classification in the lines 194-202 in "state parse_ipv4" of switch-l4s.p4
ROUND_NOTE="Limit traffic at the egress ports of the P4 switch using Mahimahi"

DATA_DIR="$SCRIPT_PATH/round-$ROUND_ID"
rm -rf   "$DATA_DIR"
mkdir -p "$DATA_DIR"

#remember of the current configuration of the switch
cp $SCRIPT_PATH/../switch-l4s.p4 $SCRIPT_PATH/../int.p4 $DATA_DIR

cat <<EOF > "$DATA_DIR/README.md"
This campgaign of test was starting at $(date).
Each test result is in a folder whose name uses this format: \`type-bandwidth-duration\`
- \`type\`: either \`legit\` (legitime traffic) or \`unrespECN\` or \`iperf3\`
- \`bandwidth\`: limit bandwidth at the client side in Mbps.
- \`duration\`: the duration of request sent by the client before being stopped
$ROUND_NOTE
EOF

for duration in 60 30
do
	for bw in 5 10 20 50 100
	do
		for type in legit unrespECN iperf3 
		do
			#export the varilabes to transfer the parameters to the scripts to be executed
			export BANDWIDTH=$bw
			export TYPE=$type
			export DURATION=$duration
			
			
			if [[ "$IS_INITIALIZED" == "" ]]; then
				export IS_INITIALIZED=YES
				unset NO_COMPILE_P4
			else
				# we do not need to recompile P4 code each iteration
				export NO_COMPILE_P4=true
			fi
			
			# go up one level to setup testbed
			cd "$SCRIPT_PATH/../"
			pwd
			
			date
			
			rm -rf log
			mkdir log
			
			( ./setup-testbed.sh 2>&1 ) |tee log/script.log

			mv log "$DATA_DIR/$type-bw_${bw}Mbps-duration_${duration}s--$(date +%Y%m%d-%H%M%S)"
			
			#break 3
			
			sleep 10
		done
		#break 2
	done
done