#!/usr/bin/python
# coding=utf-8
#
# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.
#
# This script merges the csv files into one

import csv

# load csv file into an array
def load( csv_file ):
    data = []
    with open(csv_file, "r") as io:
        csv_reader = csv.reader( io )
        for r in csv_reader:
            data.append( r )
    print(" - loaded {0}: {1} lines".format( csv_file, len(data) ))
    return data

int_csv = load("int.csv")
client  = load("client.csv")
server  = load("server.csv")

out = csv.writer( open("data.csv", "w"), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

line = min( len(int_csv), len(client), len(server))

print("min length: {0}".format( line ))

# header
out.writerow( int_csv[0] 
            #add prefix on client headers
            + ["client." + str(i) for i in client[0] ] 
            + ["server." + str(i) for i in server[0] ] 
        )
for i in range(1, line):
    out.writerow( int_csv[i] + client[i] + server[i] )
