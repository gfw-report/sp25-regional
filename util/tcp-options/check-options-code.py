import os
import time
from scapy.all import *
from scapy.layers.tls.handshake import TLSClientHello
from scapy.layers.tls.extensions import TLS_Ext_ServerName, ServerName
from scapy.layers.tls.record import TLS
from scapy.layers.inet import IP, TCP

def send_syn(ip_address, dst_port=443):
    # Build the SYN packet
    ip_layer = IP(dst=ip_address)
    tcp_layer = TCP(sport=RandShort(), dport=dst_port, flags='S')
    syn_packet = ip_layer / tcp_layer
    # Send SYN and wait for SYN-ACK
    syn_ack = sr1(syn_packet, timeout=1)
    return syn_ack

def send_tls_client_hello(syn_ack, hostname):
    # Extract TCP session parameters
    ip_layer = IP(dst=syn_ack[IP].src)
    tcp_layer = TCP(sport=syn_ack[TCP].dport, dport=syn_ack[TCP].sport, flags='PA', seq=syn_ack[TCP].ack, ack=syn_ack[TCP].seq + 1,
                    options=[('NOP', None), ('MSS', 1460),('SAckOK', '')])

    # Server Name Indication Extension
    sni = ServerName(servername=hostname)
    extensions = TLS_Ext_ServerName(servernames=[sni])

    # Cipher Suites
    cipher_suites = [0x1301, 0x1302, 0x1303, 0xc02b, 0xc02c, 0xc02f, 0xc030, 0xcca9, 0xcca8, 0xc013, 0xc014, 0x009c, 0x009d, 0x002f, 0x0035, 0x000a, 0x009f]

    # Client Random
    client_random = os.urandom(32)

    # Create the ClientHello message
    client_hello = TLSClientHello(version=0x0303, gmt_unix_time=int(time.time()), random_bytes=client_random, ciphers=cipher_suites, ext=[extensions])

    # Encapsulate the ClientHello in a TLS Record
    tls_record = TLS(type=0x16, version=0x0301, msg=[client_hello])

    # Send the TLS ClientHello packet
    send(ip_layer / tcp_layer / tls_record)

if __name__ == "__main__":
    ip_address = '1.1.1.1'  # IP address to which the packet will be sent
    hostname = '011.com'  # Define the hostname you want to use in the SNI
    syn_ack_response = send_syn(ip_address)
    if syn_ack_response:
        send_tls_client_hello(syn_ack_response, hostname)
    else:
        print("No SYN-ACK received; the target might not be responding or port 443 is closed.")
