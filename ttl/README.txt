# Run this from the vm in ChinaVPS to generate results.
# Henan Firewall
1) sudo sysctl -w net.ipv4.tcp_timestamps=0
2) python3 ttl-limiting-probe-tls.py 1.1.1.1 mos011.com > ttl-henan.txt

# GFW
1) sudo sysctl -w net.ipv4.tcp_timestamps=1
2) python3 ttl-limiting-probe-tls.py 2.2.2.2 youtube.com > ttl-gfw.txt
