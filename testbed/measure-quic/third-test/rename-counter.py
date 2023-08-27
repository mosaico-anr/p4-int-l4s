#!/usr/bin/python3
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This code reset the counter of each test to start from 1

import sys, glob, re, os

if len(sys.argv) != 2:
    print("\nUsage: python3 {0} directory-of-an-experiments".format( sys.argv[0]))
    print("   Ex: python3 {0} ./round-3/\n".format( sys.argv[0]))
    sys.exit(1)


DIR_PATH = sys.argv[1]

REGEX = r"(?P<counter>(\d+))-bw_(?P<other>([^/]+))$"
filenames=[]
for filename in glob.iglob(DIR_PATH + '/*', recursive=False):
    if not os.path.isdir( filename ): 
        continue
    # FILE_PATH = ".../unrespECN-bw_50Mbps-duration_60s--20230322-124338/data.csv"
    match = re.search(REGEX, filename )

    # if we cannot guess the traffic type and limited bandwidth
    if not match:
        continue
    filenames.append( filename )

# sort by conter
def _sort( s ):
    match = re.search(REGEX, s )
    return int(match["counter"])

filenames.sort( reverse=False, key=_sort )

for i in range(0, len(filenames)):
    filename = filenames[i]
    match = re.search(REGEX, filename )
    new_filename = os.path.join( DIR_PATH, "{0}-bw_{1}".format( (i+1), match["other"]))
    if new_filename != filename:
        print( "rename \n - from: {0}\n - to  : {1}".format( filename, new_filename  ))
        os.rename( filename, new_filename )
