#!/usr/bin/env python3

import sys
import getopt
import glob

import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy as np
from matplotlib import pyplot as plt, ticker
import matplotlib.dates as mdates
import matplotlib

import common

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from a pickle data file and plot it. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: figs/responding-ips-over-time.pdfec)
  -n, --no-show         do not show the plot, just save as file
  -s, --start           bound on starting date of graph
  -l, --legend          show legend
  -e, --end             bound on ending date of graph

Example:
  {program} dat/data.pickle --out figs/responding-ips-over-time.pdf
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

def exclude(row):
    exclusion_ranges = [
            (pd.to_datetime('2024-01-03'), pd.to_datetime('2024-01-10')),
            # (pd.to_datetime('2024-01-27'), pd.to_datetime('2024-01-30')),
            # (pd.to_datetime('2023-09-12 02:00:00'), pd.to_datetime('2023-09-12 05:00:00')),
            # (pd.to_datetime('2023-09-13 10:00:00'), pd.to_datetime('2023-09-13 12:00:00')),
            # (pd.to_datetime('2023-09-13 18:00:00'), pd.to_datetime('2023-09-14 04:00:00')),
            # (pd.to_datetime('2023-10-05 07:00:00'), pd.to_datetime('2023-10-05 18:00:00')),
        ]
    for excl_range in exclusion_ranges:
        if row['Dates'] > excl_range[0] and row['Dates'] < excl_range[1]:
            row['Domain Count'] = np.nan
            row['Added'] = np.nan
            row['Dropped'] = np.nan
    return row


def custom_formatter(x, pos):
    if x >= 1000:
        return f'{int(x/1000)}k'
    return str(int(x))


def plot(df, output_file, enable_legend):
    register_matplotlib_converters()

    fig, ax = plt.subplots(
        figsize=(common.COLUMNWIDTH, 2.1)
    )
    fig.subplots_adjust(left=0.20, right=0.99, bottom=0.3, top=0.85)

    df = df.apply(exclude, axis=1)

    # df['Dates'] = df['Dates'].dt.tz_localize('US/Mountain')
    # df['Dates'] = df['Dates'].dt.tz_convert('Asia/Shanghai')

    # df['Control Count Smooth'] = df['Control Count'].rolling(window=24).mean()

    #  wc -l 2023-08-22-20-11-non-8888-wallbleed-based-on-answer-responding-ip-one-IP-per-24-subnet.txt
    #1130343 2023-08-22-20-11-non-8888-wallbleed-based-on-answer-responding-ip-one-IP-per-24-subnet.txt

    # ax.axhline(y=1130343, color='gray', linestyle='dashed', label='Total Monitored')
#    ax.plot(df['Dates'], df['Control Count Smooth'], label='Control Responses', color='o')
    ax.plot(df['Dates'], df['Domain Count'], color='b', label='Blocked Domains')
    # cutted
    # ax.bar(df['Dates'], df['Added'], color='g', width=0.3, label='Added')
    # ax.bar(df['Dates'], df['Dropped'], color='r', width=0.3, label='Removed')
    # ax.legend(bbox_to_anchor=[0.0, 0.55], loc='center left', prop={'size':6})
    # ax.legend(loc='best',prop={'size':6})
    if enable_legend == True:
        ax.legend(loc='upper center', bbox_to_anchor=(0.39, 1.3),
            ncol=3, fancybox=False, shadow=False, prop={'size': 8})

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(custom_formatter))

    # move legend above the plot
    # ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)

    # Ensure the DataFrame's 'Dates' column is sorted
    df.sort_values('Dates', inplace=True)

    # Explicitly set the range of dates for x-axis
    start_date = pd.to_datetime(df['Dates'].min())
    end_date = pd.to_datetime(df['Dates'].max())

    # Generate date range for ticks
    date_range = pd.date_range(start=start_date, end=end_date, freq='W')  # Daily frequency
    ax.set_xticks(date_range)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

    # rotate the xlables 90 degrees
    plt.xticks(rotation=90)

    # Format Counts
    # ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, pos: f"{y/1e6:,g} M".replace("-", "−")))

    # Set title and labels for axes
    ax.set(
        ylabel="Unique Domains",
    )

    # remove pdf metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_file.endswith(".pdf")
        else None
    )

    fig.savefig(output_file, dpi=300, metadata=metadata)


if __name__ == "__main__":
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:ns:e:", ["help", "out=", "no-show", 'firewall=', 'legend'])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "responding-ips-over-time.pdf"
    show_plot = True
    enable_legend = False
    firewall = "GFW"
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False
        if o == "-f" or o == "--firewall":
            firewall = a.strip()
        if o == "-l" or o == "--legend":
            enable_legend = True

    if len(args) > 3:
        eprint("Too many arguments")
        usage()
        sys.exit(2)

    for f in input_files(args, binary=True):
        df = pd.read_csv(f)
        df = df[df['Censor'] == firewall]
        df['Dates'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d').dt.normalize()
        # eprint(f"min_date: {df['Dates'].min()}")
        # eprint(f"max_date: {df['Dates'].max()}")
        # if start is not None:
            # df = df[(df['Dates'] > start)]
        # if end is not None:
            # df = df[(df['Dates'] < end)]
        df['Dropped'] = np.negative(df['Dropped'])
        df.set_index('Dates')

        plot(df, output_filename, enable_legend)

        if show_plot:
            plt.show()
