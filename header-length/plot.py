#!/usr/bin/env python3

import getopt
import sys
import glob

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json

import common

FIGSIZE = (common.COLUMNWIDTH, 2.0)

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""
Usage: {program} [FILENAME...]
This script reads from JSONL files and plots a CDF. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: figure.pdf)
  -n, --no-show         do not show the plot, just save as file

Example:
  {program} input.jsonl --out figure.pdf
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args, binary=False):
    STDIN =  sys.stdin.buffer if binary else sys.stdin
    MODE = 'rb' if binary else 'r'
    if not args:
        yield STDIN
    else:
        for arg in args:
            if arg == "-":
                yield STDIN
            else:
                for path in glob.glob(arg):
                    with open(path, MODE) as f:
                        yield f

def aggregate_header_length_counts(tcp_pkts_column):
    lengths, counts = [], []
    for entry in tcp_pkts_column.dropna():
        if isinstance(entry, dict):
            for length, value in entry.items():
                if 'count' in value:
                    lengths.append(int(length))  # Convert header length to integer
                    counts.append(value['count'])
    return lengths, counts

def calculate_cdf_by_length(lengths, counts):
    # Sort by header length and calculate cumulative distribution
    sorted_indices = np.argsort(lengths)
    sorted_lengths = np.array(lengths)[sorted_indices]
    sorted_counts = np.array(counts)[sorted_indices]
    cumulative_counts = np.cumsum(sorted_counts)
    cdf = cumulative_counts / cumulative_counts[-1]
    return sorted_lengths, cdf

if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:n", ["help", "out=", "no-show"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False

    # Read data from input files
    data = []
    for f in input_files(args):
        for line in f:
            data.append(json.loads(line))

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Ensure the relevant columns exist
    if 'tcp_pkts_2' in df.columns and 'tcp_pkts_3' in df.columns:
        # Aggregate header lengths and counts for tcp_pkts_2 and tcp_pkts_3
        lengths_2, counts_2 = aggregate_header_length_counts(df['tcp_pkts_2'])
        lengths_3, counts_3 = aggregate_header_length_counts(df['tcp_pkts_3'])

        # Calculate the total number of packets for TCP and TLS
        total_tcp_packets = sum(counts_2)
        total_tls_packets = sum(counts_3)

        # Report the total counts using eprint()
        eprint(f"Total TCP packets: {total_tcp_packets}")
        eprint(f"Total TLS packets: {total_tls_packets}")

        # Calculate the number of packets with header length 20 for both TCP and TLS
        tcp_packets_with_length_20 = sum(count for length, count in zip(lengths_2, counts_2) if length == 20)
        tls_packets_with_length_20 = sum(count for length, count in zip(lengths_3, counts_3) if length == 20)

        # Calculate the percentage of packets with header length 20
        tcp_percentage_length_20 = (tcp_packets_with_length_20 / total_tcp_packets) * 100 if total_tcp_packets > 0 else 0
        tls_percentage_length_20 = (tls_packets_with_length_20 / total_tls_packets) * 100 if total_tls_packets > 0 else 0

        # Report the percentages using eprint()
        eprint(f"Percentage of TCP packets with header length 20: {tcp_percentage_length_20:.2f}%")
        eprint(f"Percentage of TLS packets with header length 20: {tls_percentage_length_20:.2f}%")



        # Calculate CDF for both sets of lengths and counts
        sorted_lengths_2, cdf_2 = calculate_cdf_by_length(lengths_2, counts_2)
        sorted_lengths_3, cdf_3 = calculate_cdf_by_length(lengths_3, counts_3)

        # Plotting
        fig = plt.figure(figsize=FIGSIZE)
        ax = plt.axes()
        ax.plot(sorted_lengths_2, cdf_2, label='TCP packets', marker='.', linestyle='-', markersize=5)
        ax.plot(sorted_lengths_3, cdf_3, label='TLS packets', marker='x', linestyle='--', markersize=5)

        # Labels and Title
        ax.set_xlabel('TCP Header Length (bytes)')
        ax.set_ylabel('CDF')
        ax.set_title('CDF of Header Lengths in TCP packets and TLS packets')
        ax.legend()

        # Remove PDF metadata
        metadata = (
            {"CreationDate": None, "Creator": None, "Producer": None}
            if output_filename.endswith(".pdf")
            else None
        )

        fig.subplots_adjust(left=0.11, bottom=0.22, right=0.99, top=0.98)
        if output_filename:
            fig.savefig(output_filename, dpi=300, metadata=metadata)

        if show_plot:
            plt.show()
    else:
        eprint("The required columns 'tcp_pkts_2' and 'tcp_pkts_3' are not present in the data.")
