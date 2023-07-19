#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# load predefined environment variables
MMT_CONFIG_FILE="$SCRIPT_PATH/mmt-probe.conf"


# attributes to collect. They must be in syntax: proto.att_name as being defined by MMT
MMT_ATTRIBUTES=$(cat <<EOF
	"meta.packet_index",
	"meta.packet_len",
	"ip.src", 
	"ip.dst", 
	"ip.proto_tos", 
	"ip.ecn",
	"ip.identification", 
	"udp.src_port","udp.dest_port","udp.len",
	"tcp.src_port","tcp.dest_port","tcp.payload_len","tcp.seq_nb","tcp.ack_nb","tcp.tsval","tcp.tsecr",
	"quic_ietf.header_form",
	"quic_ietf.spin_bit",
	"quic_ietf.rtt",
	"int.hop_latencies", 
	"int.hop_queue_occups",
	"int.hop_ingress_times", 
	"int.hop_egress_times",
	"int.hop_l4s_mark", 
	"int.hop_l4s_drop",
	"int.hop_tx_utilizes"
EOF
)
# NOTE: override "hop_tx_utilizes" to carry "int.mark_probability"


# the "name" of the attributes above to show as CSV header.
# They can be any string as you want
MMT_ATTRIBUTES_HEADERS=$(
	# I temporarily use hop_tx_utilizes to carry info about mark_probability
	echo "$MMT_ATTRIBUTES" | sed --expression="s/int.hop_tx_utilizes/int.mark_probability/"
)
	
	
function combine-mmt-csv-files(){
	OUTPUT=$1
	HEADER=$(echo "report-id,probe-id,source,timestamp,report-name,int.hop_queue_ids,$MMT_ATTRIBUTES_HEADERS" | tr -d '"' | tr -d "\n" | tr -d "[:blank:]" )
	echo "$HEADER" > "$OUTPUT"

	for f in $(find . -name '1*.csv'); do
		echo " $f"
		#            only event reports
		cat "$f" | grep "^1000," >> "$OUTPUT"
		rm  -- "$f"
	done
}

function generate-monitor-config(){
	cat <<EOF
# Generated by script on $(date)
event-report int {
	enable = true
	# only capture UDP packet
	event  =  "int.hop_queue_ids"
	delta-cond = {}
	attributes = { $MMT_ATTRIBUTES }
	output-channel = {file}
}
EOF
}


function start-monitoring(){
	cd -- "$LOG"
	
	# start pcap dumping
	log "start pcap dump"
	FILTER="tcp or udp"
	
	# store only first 128 bytes that should be nought for ETH/IP/UDP/QUIC-header
	tcpdump --snapshot-length=128 -i "$IFACE"      -w "$IFACE-data.pcap"     "$FILTER" &
	tcpdump --snapshot-length=128 -i "$REV_IFACE"  -w "$REV_IFACE-data.pcap" "$FILTER" &
	# store only the first 176 bytes that should be enougth for ETH/IP/UDP/INT/QUIC-header
	tcpdump --snapshot-length=176 -i "$MON_IFACE"  -w "$MON_IFACE-int.pcap"  "$FILTER" &
	sleep 1

	# generate config file
	cp -- "$MMT_CONFIG_FILE" ./mmt-probe.conf
	generate-monitor-config >> mmt-probe.conf

	log "start mmt-probe"
	(mmt-probe -c ./mmt-probe.conf -i "$MON_IFACE" > mmt-probe.log 2>&1) &
	sleep 2
}



function stop-monitoring(){
	cd -- "$LOG"

	log "stop tcpdump and mmt-probe"
	killall --signal SIGINT tcpdump
	killall --signal SIGINT mmt-probe
	
	sleep 2

	tar -czf pcap.tar.gz "$IFACE-data.pcap" "$REV_IFACE-data.pcap" "$MON_IFACE-int.pcap"
	# test to run mmt offline
	#mmt-probe -t enp0s10-int.pcap
	
	rm "$IFACE-data.pcap" "$REV_IFACE-data.pcap" "$MON_IFACE-int.pcap"

	log "processing MMT files ..."
	combine-mmt-csv-files data.csv
	tar -czf data.csv.tar.gz data.csv
	
	# extract interested metrics from data.csv, then write to new_data.csv
	python3 "$SCRIPT_PATH/monitoring-mmt-tcpdump.processing.py" data.csv
	tar -czf new_data.csv.tar.gz new_data.csv
	
	#plot graph
	python3 "$SCRIPT_PATH/monitoring-mmt-tcpdump.plot.py" new_data.csv
	rm data.csv new_data.csv
}


# run directly
ACTION="$1"
if [[ "$ACTION" == "combine-mmt-csv-files" ]]; then
	combine-mmt-csv-files data.csv
fi