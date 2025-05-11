#!/usr/bin/env python3

import getopt
import sys
import glob

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common

FIGSIZE = (common.COLUMNWIDTH, 1.75)

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} --gfw FILE [--gfw FILE ...] --henan FILE [--henan FILE ...]
This script reads from CSV files containing domains and their censoring counts for two groups,
computes the CDF of the count values, and plots both CDFs on a single plot.
The CSV files must have two columns: domain, count.

Options:
  -h, --help            show this help
  -o, --out FILE        write output to file (default: figure.pdf)
  -n, --no-show         do not show the plot, just save as file
  --gfw FILE            CSV file for the GFW group (can be used multiple times)
  --henan FILE          CSV file for the Henan Firewall group (can be used multiple times)

Example:
  {program} --gfw gfw1.csv --gfw gfw2.csv --henan henan.csv --out figure.pdf
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(file_patterns, binary=False):
    STDIN = sys.stdin.buffer if binary else sys.stdin
    MODE = 'rb' if binary else 'r'
    if not file_patterns:
        return
    for arg in file_patterns:
        if arg == "-":
            yield STDIN
        else:
            for path in glob.glob(arg):
                with open(path, MODE) as f:
                    yield f

if __name__ == '__main__':
    try:
        opts, _ = getopt.gnu_getopt(sys.argv[1:], "ho:n", ["help", "out=", "no-show", "gfw=", "henan="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    gfw_patterns = []
    henan_patterns = []

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--out"):
            output_filename = a
        elif o in ("-n", "--no-show"):
            show_plot = False
        elif o == "--gfw":
            gfw_patterns.append(a)
        elif o == "--henan":
            henan_patterns.append(a)

    if not gfw_patterns and not henan_patterns:
        eprint("Error: Must provide at least one file for --gfw or --henan.")
        usage()
        sys.exit(1)

    # Read and concatenate CSV data for the GFW group.
    gfw_list = []
    for f in input_files(gfw_patterns):
        try:
            df = pd.read_csv(f)
            gfw_list.append(df)
        except Exception as ex:
            eprint("Error reading GFW file:", ex)
    if gfw_list:
        gfw_df = pd.concat(gfw_list, ignore_index=True)
        gfw_counts = gfw_df["count"].values
        gfw_sorted = np.sort(gfw_counts)
        gfw_cdf = np.arange(1, len(gfw_sorted) + 1) / len(gfw_sorted)
    else:
        gfw_sorted = None

    # Read and concatenate CSV data for the Henan Firewall group.
    henan_list = []
    for f in input_files(henan_patterns):
        try:
            df = pd.read_csv(f)
            henan_list.append(df)
        except Exception as ex:
            eprint("Error reading Henan file:", ex)
    if henan_list:
        henan_df = pd.concat(henan_list, ignore_index=True)
        henan_counts = henan_df["count"].values
        henan_sorted = np.sort(henan_counts)
        henan_cdf = np.arange(1, len(henan_sorted) + 1) / len(henan_sorted)
    else:
        henan_sorted = None

    # Compute the maximum x-axis value.
    max_x = max(gfw_sorted.max() if gfw_sorted is not None else 0,
                henan_sorted.max() if henan_sorted is not None else 0)

    # Output summary statistics for selected thresholds.
    thresholds = [x for x in range(1, int(max_x) + 1, 5)]
    for t in thresholds:
        parts = []
        if gfw_list:
            percent_gfw = np.mean(gfw_counts < t) * 100
            parts.append(f"{percent_gfw:.1f}% for GFW")
        if henan_list:
            percent_henan = np.mean(henan_counts < t) * 100
            parts.append(f"{percent_henan:.1f}% for Henan Firewall")
        eprint(f"Domains censored for less than {t} day{'s' if t != 1 else ''}: " + ", ".join(parts))

    # eprint the statistics for GFW and Henan Firewall, like average, median, and standard deviation
    if gfw_list:
        eprint(f"GFW: mean={gfw_counts.mean():.1f}, median={np.median(gfw_counts):.1f}, std={gfw_counts.std():.1f}")
    if henan_list:
        eprint(f"Henan Firewall: mean={henan_counts.mean():.1f}, median={np.median(henan_counts):.1f}, std={henan_counts.std():.1f}")

    # Create the plot.
    fig = plt.figure(figsize=FIGSIZE)
    ax = plt.axes()

    ax.margins(0, 0)
    ax.set_xlim(-5, max_x)
    ax.set_ylim(0, 1)

    if gfw_sorted is not None:
        ax.plot(gfw_sorted, gfw_cdf, marker='x', linestyle='-', label="GFW", markersize=2)
    if henan_sorted is not None:
        ax.plot(henan_sorted, henan_cdf, linestyle='-', label="Henan Firewall", markersize=2)

    ax.set(xlabel="Number of Days Censored", ylabel="CDF")
    ax.legend()
    ax.grid(True)

    fig.subplots_adjust(left=0.09, bottom=0.203, right=0.99, top=0.95)

    # Save the figure (remove PDF metadata if output is a PDF).
    fig.savefig(output_filename, dpi=300, metadata={"CreationDate": None})

    if show_plot:
        plt.show()
