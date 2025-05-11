#!/usr/bin/env python3

import getopt
import sys
import glob

from matplotlib.ticker import ScalarFormatter
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


import common

FIGSIZE = (common.COLUMNWIDTH, 2.9)

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
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:ng:k:", ["help", "out=", "no-show", "gfw=", "henan="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    gfw_filename = None
    henan_filename = None
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

    if not gfw_filename and not henan_filename:
        eprint("Missing input files")
        usage()
        sys.exit(2)

    if gfw_filename:
        df = pd.read_csv(gfw_filename, header=None)
    else:
        df = pd.read_csv(henan_filename, header=None)

    df.columns = ['domain', 'category']

    # df['category'] = df['category'].fillna('Newly Observed Domain')
    df['category'] = df['category'].dropna()


    # Count the occurrences of each category
    category_counts = df['category'].value_counts()

    # Get the top 10 categories
    top_categories = category_counts.head(10)

    # Calculate the cumulative percentage for the top categories
    cumulative_percentage = top_categories.cumsum() / top_categories.sum() * 100

    # Sort categories by count
    sorted_categories = top_categories.sort_values(ascending=False)

    # Create a cumulative percentage series
    cumulative_percentage = sorted_categories.cumsum() / sorted_categories.sum() * 100

    # print a CSV with the top categories, their counts, and portions
    eprint("category,count,portion")
    for category, count in sorted_categories.items():
        portion = count / sorted_categories.sum() * 100
        eprint(f"{category},{count},{portion:.1f}")



    # Create the bar plot
    fig, ax1 = plt.subplots(figsize=FIGSIZE)

    # Bar plot
    sorted_categories.plot(kind='bar', color='blue', ax=ax1, width=0.5)
    ax1.set_ylabel('Censored domains')
    ax1.set_xlabel(None)

    # Invert axis and align the twin axis
    ax1.yaxis.tick_left()
    ax1.yaxis.set_label_position("left")
    ax1.set_xticks(range(0,len(top_categories)), top_categories)

    # Cumulative percentage line plot with twin axis
    ax2 = ax1.twinx()
    cumulative_percentage.plot(kind='line', color='orange', ax=ax2)
    ax2.set_ylabel('Cumulative percentage', color='orange')
    ax2.set_ylim(0, 100)  # Assuming percentage range is 0-100
    ax2.tick_params(axis='y', colors='orange')
    ax2.grid(False)

    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=55,ha='right')

    # plt.title('Censored Domains by Category by --')
    plt.tight_layout()


    # remove pdf metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_filename.endswith(".pdf")
        else None
    )

    fig.subplots_adjust(left=0.24, bottom=0.5, right=0.84, top=0.95)
    if output_filename:
        fig.savefig(output_filename,
                    dpi=300,
                    metadata={"CreationDate": None})

    if show_plot:
        plt.show()
