#!/bin/bash
BW=10
if [[ "$1" != "" ]]; then
   BW=$1
fi

echo "Generate mahimahi trace of $BW Mbps to ${BW}Mbps.txt"

yes $BW | ./mm-rate-to-events.pl | head -n 500 > "${BW}Mbps.txt"
