#!/usr/bin/python3
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This code  print folder which contains "queue_data.csv.tar.gz"

import sys, glob, re, os
import subprocess

if len(sys.argv) != 2:
    print("\nUsage: python3 {0} directory-of-an-experiments".format( sys.argv[0]))
    print("   Ex: python3 {0} ./round-3/\n".format( sys.argv[0]))
    sys.exit(1)


DIR_PATH = sys.argv[1]

REGEX = r"(?P<counter>(\d+))-bw_(?P<other>([^/]+))$"
filenames = []
for filename in glob.iglob(DIR_PATH + '/*', recursive=False):
    if not os.path.isdir( filename ): 
        continue

    # FILE_PATH = ".../unrespECN-bw_50Mbps-duration_60s--20230322-124338/data.csv"
    match = re.search(REGEX, filename )

    # if we cannot guess the traffic type and limited bandwidth
    if not match:
        continue

    if not os.path.isfile( os.path.join( filename, "queue_data.csv.tar.gz")):
        filenames.append( filename )

filenames.sort()
for f in filenames:
    print( "rm {0}".format(f ))
    subprocess.run(["rm", "-rf", "--", f])
    
