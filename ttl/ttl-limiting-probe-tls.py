import os
import time
import argparse
from scapy.all import *
from scapy.layers.tls.handshake import TLSClientHello
from scapy.layers.tls.extensions import TLS_Ext_ServerName, ServerName
from scapy.layers.tls.record import TLS
from scapy.layers.inet import IP, TCP

def send_syn_and_client_hello(ip_address, hostname, ttl=64, dst_port=443):
    print(f"TTL {ttl}: Starting sniffing before sending packets...")
    sniff_thread = AsyncSniffer(filter=f"src {ip_address}", store=True)
    sniff_thread.start()
    time.sleep(0.1) 
    
    src_port = 45000 # FixeD srcport
    
    ip_layer = IP(dst=ip_address, ttl=ttl)
    tcp_syn = TCP(sport=src_port, dport=dst_port, flags='S', seq=1000) 
    syn_packet = ip_layer / tcp_syn
    
    send(syn_packet, verbose=False)
    
    time.sleep(1)  
    
    # Capture the SYN-ACK response to set the correct acknowledgment number
    # syn_ack = sniff(filter=f"tcp and src {ip_address} and dst port {src_port}", count=1, timeout=2)
    
    # Don't wait for synack
    # if syn_ack and syn_ack[0].haslayer(TCP) and syn_ack[0][TCP].flags & 0x12:  # SYN-ACK flag
    #     ack_num = syn_ack[0][TCP].seq + 1  # Correct ACK number from SYN-ACK
    # else:
    #     print(f"TTL {ttl}: No SYN-ACK received, defaulting ACK number to 1")
    #     ack_num = 1  # Default if no SYN-ACK
    
    tcp_client_hello = TCP(sport=src_port, dport=dst_port, flags='PA', seq=1001, ack=1)
    
    sni = ServerName(servername=hostname)
    extensions = TLS_Ext_ServerName(servernames=[sni])
    
    cipher_suites = [0x1301, 0x1302, 0x1303, 0xc02b, 0xc02c, 0xc02f, 0xc030, 0xcca9, 0xcca8, 0xc013, 0xc014, 0x009c, 0x009d, 0x002f, 0x0035, 0x000a, 0x009f]
    
    client_random = os.urandom(32)
    
    client_hello = TLSClientHello(version=0x0303, gmt_unix_time=int(time.time()), random_bytes=client_random, ciphers=cipher_suites, ext=[extensions])
    
    tls_record = TLS(type=0x16, version=0x0301, msg=[client_hello])
    
    send(ip_layer / tcp_client_hello / tls_record, verbose=False)
    
    print(f"TTL {ttl}: Waiting for packets (timeout 5 seconds)...")
    time.sleep(5)
    sniff_thread.stop()
    
    responses = sniff_thread.results
    if responses:
        for packet in responses:
            print(f"TTL {ttl}: Received packet.")
            packet.show()
            if packet.haslayer(TCP) and packet[TCP].flags & 0x04:  # Check if RST flag is set
                print(f"TTL {ttl}: Received RST packet. Terminating sniffing.")
                return True
    else:
        print(f"TTL {ttl}: Timeout reached. No RST packet received.")
        return False

    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP and TLS probing script")
    parser.add_argument("ip_address", type=str, help="Target IP address")
    parser.add_argument("sni", type=str, help="SNI")
    args = parser.parse_args()
    
    for ttl in range(1, 64):  
        print(f"Running experiment with TTL = {ttl}")
        cont = send_syn_and_client_hello(args.ip_address, args.sni, ttl)
        print("--------------------------------------")
        if cont:
            break
