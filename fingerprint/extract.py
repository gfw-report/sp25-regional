#!/usr/bin/env python
# coding: utf-8

import dpkt
import socket
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob

def is_from_firewall(ip):
    """
    Check if the source IP is one of the known firewall addresses.
    Since dpkt stores IP addresses in binary, we convert them to strings.
    """
    src_ip = socket.inet_ntoa(ip.src)
    return src_ip == '1.1.1.1' or src_ip == '2.2.2.2'

def get_session_key(ip, tcp):
    """
    Generate a unique session key for a TCP session.
    The key is a tuple consisting of sorted source and destination IP addresses 
    and sorted source and destination ports.
    """
    src_ip = socket.inet_ntoa(ip.src)
    dst_ip = socket.inet_ntoa(ip.dst)
    ips = tuple(sorted([src_ip, dst_ip]))
    ports = tuple(sorted([tcp.sport, tcp.dport]))
    return ips + ports

def extract_psh_rst_data_dpkt(filename):
    """
    """
    sessions = {}  # Container for session information.
    
    with open(filename, 'rb') as f:
        try:
            pcap = dpkt.pcap.Reader(f)
        except Exception as e:
            print("Error reading pcap file:", filename, e)
            return []
        
        for ts, buf in pcap:
            # Parse the Ethernet frame.
            try:
                eth = dpkt.ethernet.Ethernet(buf)
            except Exception:
                continue
            
            # Process only IP packets.
            if not isinstance(eth.data, dpkt.ip.IP):
                continue
            ip = eth.data
            
            # Process only TCP packets.
            if ip.p != dpkt.ip.IP_PROTO_TCP:
                continue
            tcp = ip.data
            
            # Obtain a unique session key.
            session_key = get_session_key(ip, tcp)
            if session_key not in sessions:
                sessions[session_key] = {
                    'last_psh': None,
                    'latest_rst': None,
                    'psh_data': None,
                    'psh_seq': None,
                    'psh_ack': None,
                    'rst_seq': None,
                    'rst_ack': None
                }
            
            # Process PSH packet: flag 0x08 (TH_PUSH).
            if tcp.flags & dpkt.tcp.TH_PUSH:
                # Update if this packet has a later timestamp.
                if sessions[session_key]['last_psh'] is None or ts > sessions[session_key]['last_psh']:
                    sessions[session_key]['last_psh'] = ts
                    sessions[session_key]['psh_data'] = tcp.data    # Save TCP payload.
                    sessions[session_key]['psh_seq'] = tcp.seq      # Save TCP sequence number.
                    sessions[session_key]['psh_ack'] = tcp.ack      # Save TCP acknowledgment number.
            
            # Process RST packet: flag 0x04 (TH_RST).
            if tcp.flags & dpkt.tcp.TH_RST:
                # Only consider RST packets from the designated firewall.
                if not is_from_firewall(ip):
                    continue
                if sessions[session_key]['latest_rst'] is None or ts > sessions[session_key]['latest_rst']:
                    sessions[session_key]['latest_rst'] = ts
                    sessions[session_key]['rst_seq'] = tcp.seq      # Save TCP sequence number.
                    sessions[session_key]['rst_ack'] = tcp.ack      # Save TCP acknowledgment number.
    
    # Prepare a list of results for sessions that have both PSH and RST packets.
    results = []
    for key, times in sessions.items():
        last_psh = times['last_psh']
        latest_rst = times['latest_rst']
        psh_data = times['psh_data']
        # Only include sessions where both PSH and RST exist and RST occurs at/after PSH.
        if last_psh is not None and latest_rst is not None and latest_rst >= last_psh and psh_data is not None:
            # Linux will drop a connection if the RST’s ack number exactly equals:
            # the PSH packet’s sequence number plus the length of its payload.
            expected_rst_ack = times['psh_seq'] + len(psh_data)
            # If the RST’s ack does not match, it means Linux would ignore that reset.
            if times['rst_ack'] != expected_rst_ack:
                continue  # Skip this stream.
            diff_seconds = float(latest_rst - last_psh)  # Time difference in seconds.
            results.append({
                'time_diff': diff_seconds,
                'psh_data': psh_data,
                'psh_seq': times['psh_seq'],
                'psh_ack': times['psh_ack'],
                'rst_seq': times['rst_seq'],
                'rst_ack': times['rst_ack'],
                'file_name': filename
            })
    return results


guangzhou_files = glob.glob('../pcap/1m_sni_censorship_guangzhou-1_ts_0_2023-*-*.pcap')
california_files = glob.glob('../pcap/1m_sni_censorship_california-1_ts_1_2023-*-*.pcap')

psh_rst_data_henan = []
psh_rst_data_gfw = []

# Process Guangzhou files (e.g., Henan Firewall traffic).
for filename in guangzhou_files:
    print(f"Processing file: {filename}")
    psh_rst_data_henan.extend(extract_psh_rst_data_dpkt(filename))

# Process California files (e.g., GFW traffic).
for filename in california_files:
    print(f"Processing file: {filename}")
    psh_rst_data_gfw.extend(extract_psh_rst_data_dpkt(filename))

# For plotting, extract the time differences.
time_diffs_henan = [entry['time_diff'] for entry in psh_rst_data_henan]
time_diffs_gfw = [entry['time_diff'] for entry in psh_rst_data_gfw]

# Create DataFrames including all desired fields.
df_henan = pd.DataFrame({
    'delta': time_diffs_henan,
    # 'psh_data': [entry['psh_data'] for entry in psh_rst_data_henan],
    # 'psh_seq': [entry['psh_seq'] for entry in psh_rst_data_henan],
    # 'psh_ack': [entry['psh_ack'] for entry in psh_rst_data_henan],
    # 'rst_seq': [entry['rst_seq'] for entry in psh_rst_data_henan],
    # 'rst_ack': [entry['rst_ack'] for entry in psh_rst_data_henan],
    'file_name': [entry['file_name'] for entry in psh_rst_data_henan]
})
df_gfw = pd.DataFrame({
    'delta': time_diffs_gfw,
    # 'psh_data': [entry['psh_data'] for entry in psh_rst_data_gfw],
    # 'psh_seq': [entry['psh_seq'] for entry in psh_rst_data_gfw],
    # 'psh_ack': [entry['psh_ack'] for entry in psh_rst_data_gfw],
    # 'rst_seq': [entry['rst_seq'] for entry in psh_rst_data_gfw],
    # 'rst_ack': [entry['rst_ack'] for entry in psh_rst_data_gfw],
    # 'file_name': [entry['file_name'] for entry in psh_rst_data_gfw]
})

# -------------------------------
# Plotting the ECDF
# -------------------------------
# sns.set_style('whitegrid')
# ax = sns.ecdfplot(data=df_henan, x='time_diff', label='Henan Firewall', log_scale=(True))
# ax = sns.ecdfplot(data=df_gfw, x='time_diff', label='GFW', log_scale=(True))
# ax.set(xlim=(None, 1))
# plt.title('CDF of Time Difference (PSH to RST) in Seconds')
# plt.xlabel('Seconds')
# plt.ylabel('CDF')
# plt.legend()
# plt.show()


# Save the DataFrames to CSV files for further analysis if needed.
df_henan.to_csv('henan_delta.csv', index=False)
df_gfw.to_csv('gfw_delta.csv', index=False)
