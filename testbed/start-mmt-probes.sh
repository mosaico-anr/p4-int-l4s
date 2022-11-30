#!/bin/bash

# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.


sudo rm 16*.csv
# defautl: INT
sudo mmt-probe -c mmt-probe-int.conf  &
# iface on clients to get total traffic
sudo mmt-probe -c mmt-probe-tot.conf

sudo killall mmt-probe

cat 16*.csv > log/data.csv
rm -f 16*.csv
