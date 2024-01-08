#!/bin/bash

for dir in ./round-*
do
   echo $dir
   python3 generate-traffic-summary-3.py "$dir"
   echo
done
