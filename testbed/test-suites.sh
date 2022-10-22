source ./environment.sh
DELAY=1ms

set -

function hn-start-mmt(){
	# start mmt to monitor
	rm 16*.csv

	(
	# defautl: INT
	mmt-probe -c ./mmt-probe-int.conf 2>&1  &
	# iface on clients to get total traffic
	mmt-probe -c ./mmt-probe-tot.conf 2>&1  &
	) > log/mmt-probes.log &
	tcpdump -i enp0s10 -w /tmp/enp0s10.pcap &
}

function hn-stop-mmt(){
	killall -2 mmt-probe
	killall -2 tcpdump
	sleep 1
	tar -czf log/enp0s10.pcap.tar.gz /tmp/enp0s10.pcap
	cat 16*data*.csv > log/data.csv
	rm 16*data*.csv
}

function hn-stop-all-test(){
	run-on-all-endhost sudo killall -9 iperf3
	sleep 2
	run-on-all-endhost screen -XS hn2 quit
}


function hn-run-test-using-iperf(){
	if [[ "$#" -lt "3" ]]; then
		echo "Need 3 parameters: bandwidth-a bandwidth-b test-duration"
		return
	fi

	hn-start-mmt &
	sleep 2
	
	
	BANDWIDTH_A=$1
	BANDWIDTH_B=$2
	TIME=$3
	
	run-on-host $CLIENT_A screen -S hn -dm iperf3 -c $SERVER_A --set-mss 1400 --length 1400 --time 600 --bandwidth $BANDWIDTH_A
	run-on-host $CLIENT_B screen -S hn -dm iperf3 -c $SERVER_B --set-mss 1400 --length 1400 --time 600 --bandwidth $BANDWIDTH_B
	run-on-host $CLIENT_B screen -S hn -dm iperf3 -c $SERVER_B --set-mss 1400 --length 1400 --time 600 --bandwidth $BANDWIDTH_B --port 22223
	
	
	sleep $TIME
	sleep 5
	hn-stop-mmt
	hn-stop-all-test
	killall -2 simple_switch

	sleep 2

	mv log "log-l4s/log-${BANDWIDTH_A}bps-${BANDWIDTH_B}bps-${TIME}s-delay$DELAY-$4-$(now)"
	#exit 0
}

function hn-setup-prague-cubic(){
	run-on-host $CLIENT_A sudo sysctl -w net.ipv4.tcp_congestion_control=prague
	run-on-host $SERVER_A sudo sysctl -w net.ipv4.tcp_congestion_control=prague
# Enable/disable ECN on corresponding clients/servers
	run-on-host $CLIENT_A sudo sysctl -w net.ipv4.tcp_ecn=3
	run-on-host $SERVER_A sudo sysctl -w net.ipv4.tcp_ecn=3
		
	run-on-host $CLIENT_B sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
	run-on-host $SERVER_B sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
	
	run-on-host $CLIENT_B sudo sysctl -w net.ipv4.tcp_ecn=0
	run-on-host $SERVER_B sudo sysctl -w net.ipv4.tcp_ecn=0
}

function hn-setup-traffic-iperf-on-server(){
	hn-stop-all-test
	#clean up tc rule
	run-on-host $CLIENT_A sudo tc qdisc del dev $CLIENT_A_IFACE root
	run-on-host $CLIENT_B sudo tc qdisc del dev $CLIENT_B_IFACE root
	run-on-host $SERVER_A sudo tc qdisc del dev $SERVER_A_IFACE root
	run-on-host $SERVER_B sudo tc qdisc del dev $SERVER_B_IFACE root
	
	run-on-host $CLIENT_A sudo tc qdisc change dev $CLIENT_A_IFACE root netem delay  $DELAY
	run-on-host $CLIENT_B sudo tc qdisc change dev $CLIENT_B_IFACE root netem delay  $DELAY
	run-on-host $SERVER_A sudo tc qdisc change dev $SERVER_A_IFACE root netem delay  $DELAY
	run-on-host $SERVER_B sudo tc qdisc change dev $SERVER_B_IFACE root netem delay  $DELAY
	

	hn-setup-prague-cubic

	#start iperf server
	# --one-off: after the client finishes the test, the server shuts itself down.
	run-on-host $SERVER_A screen -S hn -dm iperf3 -s --one-off 
	run-on-host $SERVER_B screen -S hn -dm iperf3 -s --one-off
	run-on-host $SERVER_B screen -S hn2 -dm iperf3 -s --port 22223 --one-off
}

BW=4M
function hn-run-abnormal-traffic-iperf-on-server(){
	
	hn-setup-traffic-iperf-on-server
	
	#start another iperf server
	run-on-host $SERVER_A screen -S hn2 -dm iperf3 -s --port 22222 --one-off
	sleep 1
	run-on-host $CLIENT_A screen -S hn2 -dm iperf3 -c $SERVER_A --bandwidth $BW  --set-mss 1400 --length 1400 --time 600 --port 22222 --udp
	
	hn-run-test-using-iperf $BW $BW 310 abnormal-prague-udp-cubic-cubic-delay-$DELAY
}

function hn-run-abnormal-2-traffic-iperf-on-server(){
	
	hn-setup-traffic-iperf-on-server
	
	#start another iperf server
	run-on-host $SERVER_A screen -S hn2 -dm iperf3 -s --port 22222 --one-off
	sleep 1
	run-on-host $CLIENT_A screen -S hn2 -dm iperf3 -c $SERVER_A --bandwidth 12M  --set-mss 1400 --length 1400 --time 600 --port 22222 --udp
	
	hn-run-test-using-iperf $BW $BW 310 abnormal-prague-udp-12Mbps-cubic-cubic-delay-$DELAY
}

function hn-run-normal-traffic-iperf-on-server(){
	
	hn-setup-traffic-iperf-on-server
	
	#start another iperf server
	run-on-host $SERVER_A screen -S hn2 -dm iperf3 -s --port 22222 --one-off
	sleep 1
	run-on-host $CLIENT_A screen -S hn2 -dm iperf3 -c $SERVER_A --bandwidth $BW  --set-mss 1400 --length 1400 --time 600 --port 22222
	
	hn-run-test-using-iperf $BW $BW 310 normal-prague-cubic-cubic-delay-$DELAY
}

function test-latency(){
	CLIENT_IP=$1
	SERVER_IP=$2
	PKT_SIZE=$3
	NB_ITERATION=10000
	scp client-server/client montimage@$CLIENT_IP:
	scp client-server/server montimage@$SERVER_IP:
	run-on-host $SERVER_IP screen -S hn -dm ./server 22222
	run-on-host $CLIENT_IP "./client $SERVER_IP 22222 $PKT_SIZE $NB_ITERATION > data.csv"
	
	TARGET="log-overhead/latency-overhead-$CLIENT_IP-$SERVER_IP-pkt-$PKT_SIZE-INT-$ENABLE_INT.csv"
	scp montimage@$CLIENT_IP:data.csv $TARGET
	tail -n1 $TARGET
}

function hn-run-test-overhead-latency(){
	hn-stop-all-test
	#compile code
	(cd client-server; make clean; make)
	run-on-host $CLIENT_A sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
	run-on-host $SERVER_A sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
	run-on-host $CLIENT_B sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
	run-on-host $SERVER_B sudo sysctl -w net.ipv4.tcp_slow_start_after_idle=0
	#disable ECN on corresponding clients/servers
	run-on-host $CLIENT_A sudo sysctl -w net.ipv4.tcp_ecn=0
	run-on-host $SERVER_A sudo sysctl -w net.ipv4.tcp_ecn=0
	run-on-host $CLIENT_B sudo sysctl -w net.ipv4.tcp_ecn=0
	run-on-host $SERVER_B sudo sysctl -w net.ipv4.tcp_ecn=0

	#clean up tc rule
	run-on-host $CLIENT_A sudo tc qdisc del dev $CLIENT_A_IFACE root
	run-on-host $CLIENT_B sudo tc qdisc del dev $CLIENT_B_IFACE root
	run-on-host $SERVER_A sudo tc qdisc del dev $SERVER_A_IFACE root
	run-on-host $SERVER_B sudo tc qdisc del dev $SERVER_B_IFACE root
	
	for PKT_SIZE in 100 200 500 1000
	do
		test-latency $CLIENT_A $SERVER_A $PKT_SIZE
		test-latency $CLIENT_B $SERVER_B $PKT_SIZE
	done
}

function hn-test-microburst(){
   #run-on-host $SERVER_A 'screen -S hn -dm  ./client-server/server 12345 '
   #run-on-host $CLIENT_A 'screen -S hn -dm  ./client-server/client-microburst 10.0.1.11 12345 50 5000'
   #run-on-host $CLIENT_A 'screen -S hn -dm sudo python client-server/send.py enp0s8 08:00:27:8f:c5:f3 10.0.1.11 4 1000 --timer=gtod'
   tcpdump -i enp0s8  -G 10 -w log/igress.pcap &
   tcpdump -i enp0s10 -G 10 -w log/egress.pcap &
   #start collector
   cp mmt-probe-microburst.conf log/
   (mmt-probe -c ./mmt-probe-microburst.conf 2>&1 ) > log/mmt-probe.log &
   (
      END=100
      #for ((i=1;i<=END;i++)); do
      while true ; do
         tc -s qdisc show dev enp0s8 | tr -d "\n" >> log/qdisc.txt
         echo "$i  $(date +%T.%3N)" >> log/qdisc.txt
         #sleep 0.003
      done
   )
   killall mmt-probe
   killall tcpdump

}

sleep 5
echo "start testing"
hn-test-microburst
exit 0

#hn-stop-all-test
#hn-run-normal-traffic-iperf-on-server
#hn-stop-all-test
#exit 0
#
#
#for i in $(seq 1 5); do
#	hn-stop-all-test
#	hn-run-normal-traffic-iperf-on-server
#	hn-stop-all-test
#	hn-run-abnormal-traffic-iperf-on-server
#	hn-stop-all-test
#	hn-run-abnormal-2-traffic-iperf-on-server
#	hn-stop-all-test
#done
#hn-run-test-overhead-latency

HISTORY_LOG="bash-history.log"
date >> $HISTORY_LOG
export HISTFILE=$HISTORY_LOG
export PS1='$(date) bash demo: '
set -x
