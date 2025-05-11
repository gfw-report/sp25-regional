#!/bin/bash

cd "$(dirname "$0")" || exit

date=$(date +%F_%H-%M-%S)

# set max open file to a large number
ulimit -n 50000

DST_NAME="sfo-1"
DST_IP="1.1.1.1"
MIN_DSTPORT=10000
MAX_DSTPORT=65000

INPUT_FILE='top-1m-2023-08-16-tranco.csv'
OUTPUT_FILE="1m_sni_censorship_${DST_NAME}_${date}.csv"

# use tcpdump to capture the traffic associate with the destination IP
sudo tcpdump -Uw "wall_behind_wall_${DST_NAME}_${date}.pcap" host "$DST_IP" &
PID_TCPDUMP=$!

cut -d, -f2 "$INPUT_FILE" | ./sincensor -dip "$DST_IP" -p "${MIN_DSTPORT}-${MAX_DSTPORT}" -timeout 6s -worker 10 -out "$OUTPUT_FILE"

sudo pkill -P "$PID_TCPDUMP"
