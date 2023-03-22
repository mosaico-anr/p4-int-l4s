#!/bin/bash -x

set -x

# The interface facing the clients
export IFACE="enp0s8"
# The interface facing the servers
export REV_IFACE="enp0s9"
# The interface to export INT reports
export MON_IFACE="enp0s10"
# The IP prefix of the servers
export SERVER_NET="10.0.1.0/24"
export CLIENT_NET="10.0.0.0/24"
# Client and servers addresses
export SERVER_A="10.0.1.11"
export SERVER_B="10.0.1.12"
export CLIENT_A="10.0.0.11"
export CLIENT_B="10.0.0.12"

# The interface on both clients connected to the aqm/router (to apply mixed rtt)
export CLIENT_A_IFACE="enp0s8"
export CLIENT_B_IFACE="enp0s8"
# Server interfaces that might need to be tuned (e.g., offload, ...)
export SERVER_A_IFACE="enp0s8"
export SERVER_B_IFACE="enp0s8"

export MMT_IP="10.0.30.2"
export MMT_IFACE="enp0s8"



# control plane:
export SERVER_A_CTRL="192.168.1.104"
export SERVER_B_CTRL="192.168.1.105"
export CLIENT_A_CTRL="192.168.1.100"
export CLIENT_B_CTRL="192.168.1.103"



function run-on-host(){
	if [ $# -lt 2 ]; then
		echo "Request at least 2 parameters: hostname command-to-run"
		return 1
	else
		hostname=$1
		shift
		ssh -i /home/montimage/.ssh/id_rsa montimage@$hostname -- "$@"
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
