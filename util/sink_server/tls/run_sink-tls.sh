#!/bin/bash

cd "$(dirname "$0")" || exit

sudo tcpdump not port 22 -Uw "$(hostname)-%m-%d-%H-%M.pcap" -G 3600 -Z root &

./sink-tls -p 443 -timeout 5s -out server.out -log server.log

sudo pkill tcpdump
