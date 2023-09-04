#!/bin/bash

dir="."
if [ "$#" -ge 1 ]; then
   dir="$1"
   shift
fi


echo "Processing files in $dir"

find "$dir/" -type d "$@" -name '*-bw_*' -print0 | xargs -0 -n1 -P16 python3 generate-metrics-by-time-window.py

# compress csv file
find "$dir/" -type f "$@" -name '*.csv' -print0 | xargs -0 -n1 -P16 -I % bash -c 'tar -czf %.tar.gz -C $(dirname %) $(basename %); rm %'
