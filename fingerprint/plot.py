#!/usr/bin/env python3

import getopt
import sys
import glob

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import common

FIGSIZE = (common.COLUMNWIDTH, 2.0)

# Read packets from CSV.
WANTED_COLUMNS = [
    "tcp_flags",
    "is_legit",
]

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from CSV files and plot . With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: figure.pdf)
  -n, --no-show         do not show the plot, just save as file
  -g, --gfw             GFW CSV file
  -k, --henan           Henan Firewall CSV file
  -t, --threshold       max second threshold of delay to be considered as a valid (default: 30)

Example:
  {program} --gfw gfw.csv --henan henan.csv --out figure.pdf
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


if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:ng:k:t", ["help", "out=", "no-show", "gfw=", "henan=", "threshold="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    gfw_filename = None
    henan_filename = None
    threshold = 30
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False
        if o == "-g" or o == "--gfw":
            gfw_filename = a
        if o == "-k" or o == "--henan":
            henan_filename = a
        if o == "-t" or o == "--threshold":
            threshold = int(a)

    if not gfw_filename or not henan_filename:
        eprint("Missing input files")
        usage()
        sys.exit(2)

    gfw_df = pd.read_csv(gfw_filename, usecols=['delta'])
    henan_df = pd.read_csv(henan_filename, usecols=['delta'])

    # filter any row's delta that is greater than 30 s
    gfw_df = gfw_df[gfw_df['delta'] < threshold]
    henan_df = henan_df[henan_df['delta'] < threshold]

    # convert delta to milliseconds
    gfw_df['delta'] = gfw_df['delta'] * 1000
    henan_df['delta'] = henan_df['delta'] * 1000

    eprint("GFW")
    eprint(gfw_df['delta'].describe())
    eprint("---------------------------")
    eprint("Henan")
    eprint(henan_df['delta'].describe())

    fig = plt.figure(figsize=FIGSIZE)
    ax = plt.axes()
    # ax.margins(0, 0)
    #ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(50))

    # plot CDF with seaborn
    ax = sns.ecdfplot(data=gfw_df, x='delta', label='GFW')
    ax = sns.ecdfplot(data=henan_df, x='delta', label='Henan Firewall')

    # show legend
    ax.legend()

    # make the y-axis percentage
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:,.0%}'.format(x) for x in vals])

    ax.set(xlim=(0, 40))

    ax.set(xlabel="Time Difference: ClientHello Sent to RST Received (ms)")
    ax.set(ylabel="")

    # remove pdf metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_filename.endswith(".pdf")
        else None
    )

    fig.subplots_adjust(left=0.12, bottom=0.22, right=0.92, top=0.95)
    if output_filename:
        fig.savefig(output_filename,
                    dpi=300,
                    metadata={"CreationDate": None})

    if show_plot:
        plt.show()
