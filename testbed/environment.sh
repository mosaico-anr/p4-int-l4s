#!/bin/bash -x
set -x

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

#. "$SCRIPT_PATH/environment-param-virtualbox.sh" 
. "$SCRIPT_PATH/environment-param-bare-metal.sh" 

function run-on-host(){
	if [ $# -lt 2 ]; then
		echo "Request at least 2 parameters: hostname command-to-run"
		return 1
	else
		hostname=$1
		shift
	
		# specific processing for server
		if [[ "$hostname" == "x" ]]; then
			hostname="192.168.0.235"
			ssh -o StrictHostKeyChecking=accept-new -i /home/montimage/.ssh/id_rsa montimage@$hostname -- sudo ip netns exec server "$@"
		else
			ssh -o StrictHostKeyChecking=accept-new -i /home/montimage/.ssh/id_rsa montimage@$hostname -- "$@"
		fi
	fi
}

function run-on-all-endhost(){
	MACHINES=($CLIENT_A_CTRL $CLIENT_B_CTRL $SERVER_A_CTRL $SERVER_B_CTRL)

	for hostname in ${MACHINES[@]}; do
		run-on-host $hostname "$@"
	done
}


function now(){
	date +%Y%m%d-%H%M%S
}

function log(){
	echo "$(now) " "$@"
}


function config_sw(){
	tee -a log/config.log | /usr/local/bin/simple_switch_CLI "$@" | tee -a log/config.log
}
