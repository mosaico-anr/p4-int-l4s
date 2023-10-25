ID="./"
# remove picoquic logs
find $ID -name qlog -exec rm -rf '{}' \;
# remove graph whose size > 500K. We can be regenerated by ../monitoring-mmt-tcpdump.plot.sh
find $ID -type f -name "*.png" -size "+500k" -delete
# remove pcap files
find $ID -type f -name "pcap.tar.gz" -delete
# delete conf of MMT
find $ID -type f -name "mmt-probe.conf" -delete
