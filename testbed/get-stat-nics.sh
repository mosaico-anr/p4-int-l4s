#!/bin/bash

declare -A RX TX

function log(){
	printf "  %2d.  %-20s rx=%12d   tx=%12d\n" "$@"
}

declare -A NICS

count=0
for i in $(ls -d /sys/class/net/* | sort); do
	# i = /sys/class/net/enp0s10
	NICS+=([$count]=$(basename $i) )
	count=$((count+1))
done

function get_stat(){
	date
	
	for ((i=0;i<count;i++)); do
		NIC="${NICS[$i]}"
		rx=$(cat /sys/class/net/$NIC/statistics/rx_packets)
		tx=$(cat /sys/class/net/$NIC/statistics/tx_packets)
		
		log $i $NIC $rx $tx
		
		RX[$i]=$rx
		TX[$i]=$tx
	done
}


# initial stats
get_stat

OLD_RX=("${RX[@]}")
OLD_TX=("${TX[@]}")

function ctrl_c() {
	echo
	get_stat
	echo
	echo "Difference:"
	for ((i=0;i<count;i++)); do
		NIC="${NICS[$i]}"
		rx=$(expr "${RX[$i]}" - "${OLD_RX[$i]}")
		tx=$(expr "${TX[$i]}" - "${OLD_TX[$i]}")
		log $i $NIC $rx $tx
	done
	echo "bye"
}

echo "press Ctrl+C to stop"
trap ctrl_c INT

sleep 3600