# 
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#

from os import listdir
from os.path import isfile, join
import os, sys
import subprocess


PLOT_SCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "monitoring-mmt-tcpdump.plot.py")

def exec(args):
    return subprocess.run( args )


def visite(file_path):
    arr = []
    for f in os.listdir(file_path):
        arr.append( f )

    arr.sort()
    for f in arr:
        f = os.path.join( file_path, f )
        
        # we work only on directories, not files
        if not os.path.isdir( f ):
            continue

        csv_tar = os.path.join(f, "data.csv.tar.gz")
        csv_txt = os.path.join(f, "data.csv")

        # no data files are available
        if not os.path.exists( csv_tar ) and not os.path.exists( csv_txt ):
            visite( f )
            continue

        isUntar = False
        # no csv is available ==> untar
        if not os.path.exists( csv_txt ):
            isUntar = True
            exec(["tar", "-C", f, "-xf", csv_tar])

        if not os.path.exists( csv_txt ):
            print("not found {0}".format( csv_txt) )
            continue
        print("=====\n{0}".format(file_path))
        exec(["python3", PLOT_SCRIPT, csv_txt])

        # clear csv txt file
        if isUntar:
            #os.remove( csv_txt )
            None

if len(sys.argv) <= 1:
    print("Usage: {0} path-to-replot".format( sys.argv[0] ))
    sys.exit()

FILE_PATH = os.path.abspath( sys.argv[1] )
print("Processing {0}".format( FILE_PATH ))

visite( FILE_PATH )