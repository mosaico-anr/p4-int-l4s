#!/bin/bash


# The interface facing the clients
export IFACE="enp0s8"
# The interface facing the servers
export REV_IFACE="enp0s9"
# The interface to export INT reports
export MON_IFACE="enp0s10"
# The IP prefix of the servers
export SERVER_NET="10.0.1.1/24"
export CLIENT_NET="10.0.0.1/24"
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
	MACHINES=($CLIENT_A $CLIENT_B $SERVER_A $SERVER_B)

	for hostname in ${MACHINES[@]}; do
		run-on-host $hostname "$@"
	done
}


function now(){
	date +%Y%m%d-%H%M%S
}
