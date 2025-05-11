#!/usr/bin/env python3

import sys
import getopt
import glob

import seaborn as sns
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import rc
import matplotlib.dates as mdates

import common

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from a pickle data file and plot it. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: censored-domains-over-time.pdf)
  -n, --no-show         do not show the plot, just save as file

Example:
  {program} data.csv --out censored-domains-over-time.pdf
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

def plot(df, output_file):
    register_matplotlib_converters()

    grouped = df.groupby('Censor')

    # Create a subplot for each censor
    fig, axs = plt.subplots(nrows=len(grouped), figsize=(common.COLUMNWIDTH, 1.5 * len(grouped)), sharex=True)

    if len(grouped) == 1:
        axs = [axs]  # Ensure axs is iterable for a single group

    check = True
    for (city, group), ax in zip(grouped, axs):
        # Create a secondary y-axis for the line plot
        ax2 = ax.twinx()

        # # Bar plots on the primary y-axis
        ax.bar(group['Timestamp'], group['Added'], width=1, label='Domains Added', alpha=0.8, color='green')
        ax.bar(group['Timestamp'], group['Dropped'], width=1, label='Domains Removed', alpha=0.8, color='red')

        # Line plot on the secondary y-axis
        ax2.plot(group['Timestamp'], group['Domain Count'], label='Total Domains Blocked', color='blue')

        # Set labels for both y-axes


        # Set title and x-axis label
        ax.set_title(f"{city}")
        # ax.set_xlabel("Date")

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.tick_params(axis='x', rotation=45)
        plt.setp(ax.get_xticklabels(), ha="right", rotation=45)


        # # # Add legends
        if check == True:
            ax.set_ylabel("Daily Domains Added/Removed", color='green', loc='top')
            # ax2.yaxis.set_label_coords(-0.05, 1.355)
            check = False

        # ax.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5, alpha=0.7)
        ax.grid(True)
        ax2.grid(False)

        # Collect all handles and labels for the combined legend
        handles, labels = [], []
        for handle, label in zip(*ax.get_legend_handles_labels()):
            handles.append(handle)
            labels.append(label)
        for handle, label in zip(*ax2.get_legend_handles_labels()):
            handles.append(handle)
            labels.append(label)

    # Create one combined legend
    # ax.set_ylabel("Daily Domains Added/Removed", color='green')
    # ax2.set_ylabel("Total Domains Blocked", color='blue', loc='center')
    # ax2.legend(handles, labels, loc='upper center',bbox_to_anchor=(0.5, -1.0), ncol=3, fancybox=False)

    ax2.yaxis.set_label_coords(1.115, 1.25)


    # ax.legend(handles, labels, loc='upper right',fancybox=True)




    plt.tight_layout()
    # fig.subplots_adjust(left=0.18, bottom=0.56, right=0.84, top=0.5)
    fig.savefig(output_file, dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:n", ["help", "out=", "no-show"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "censored-domains-over-time.pdf"
    show_plot = True
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False

    if len(args) > 1:
        eprint("Too many arguments")
        usage()
        sys.exit(2)

    for f in input_files(args, binary=True):
        df = pd.read_csv(f)
        df['Dropped'] = np.negative(df['Dropped'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d').dt.normalize()
        df.set_index('Timestamp')


        # There was a problem in this date range
        start_date = pd.to_datetime('2024-01-04')
        end_date = pd.to_datetime('2024-01-09')

        # Use date slicing to drop rows

        mask = (df['Timestamp'] < start_date) | (df['Timestamp'] > end_date)
        df = df[mask]

        df = df[(df['Timestamp'] < pd.to_datetime('2024-01-28')) |  (pd.to_datetime('2024-01-28') > df['Timestamp'])]


        plot(df, output_filename)

        if show_plot:
            plt.show()
