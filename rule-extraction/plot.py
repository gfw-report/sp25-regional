#!/usr/bin/env python3

import getopt
import sys
import glob

from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from upsetplot import UpSet
from upsetplot import from_memberships

from matplotlib import cm

import common

FIGSIZE = (common.COLUMNWIDTH, 2.0)



def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from CSV files and plot . With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: rule-extraction.pdf)
  -n, --no-show         do not show the plot, just save as file

Example:
  {program} --out figure.pdf
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
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:ng:c:", ["help", "out=", "no-show", "guangzhou=", "california="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "rule-extraction.pdf"
    show_plot = True
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False
        if o == "-g" or o == "--guangzhou":
            guangzhou_csv_files = glob.glob(a)
        if o == "-c" or o == "--california":
            california_csv_files = glob.glob(a)
            

    guanzhou_dataframes = []
    for csv_file in guangzhou_csv_files:
        dataframe = pd.read_csv(csv_file, sep=" ", header=None, names=["Domain", "Categories"])
        if not dataframe.empty:
            guanzhou_dataframes.append(dataframe)

    guangzhou_df = pd.concat(guanzhou_dataframes)
    guangzhou_df = guangzhou_df.drop_duplicates(subset=['Domain'])


    california_dataframes = []
    for csv_file in california_csv_files:
        dataframe = pd.read_csv(csv_file, sep=" ", header=None, names=["Domain", "Categories"])
        if not dataframe.empty:
            california_dataframes.append(dataframe)

    california_df = pd.concat(california_dataframes)
    california_df = california_df.drop_duplicates(subset=['Domain'])


    # Finding common domains
    common_domains = pd.merge(california_df, guangzhou_df, on='Domain')
    print(common_domains.head(50))





    guangzhou_df['city'] = 'Henan'
    california_df['city'] = 'GFW'

    df = pd.concat([guangzhou_df, california_df])

    domains_rules = [
    "domain",
    "domain.{rnd}",
    "domain{rnd}",
    "{rnd}.domain",
    "{rnd}domain",
    "{rnd}.domain.{rnd}",
    "{rnd}.domain{rnd}",
    "{rnd}domain.{rnd}",
    "{rnd}domain{rnd}",
    ]


    df['Categories'] = df['Categories'].astype(str)

    by_rule = from_memberships(df.Categories.str.split(",").apply(lambda x: [ 'Rule '+str(int(y))+': ' + domains_rules[int(y)-1] for y in x]), data=df)
    # UpSet(by_rule)

    # fig, axes = plt.subplots(figsize=FIGSIZE)

    fig = plt.figure(figsize=FIGSIZE)

    upset = UpSet(by_rule, min_subset_size=15, show_percentages=True, intersection_plot_elements=0,facecolor='black')

    # black and gray cm colors:

    upset.add_stacked_bars(
        by="city", title="Rule Combination Overlap", elements=5,colors=['#808080', '#000000']
    )
    upset.plot(fig=fig)

    # plt.legend(loc='upper left', fancybox=True)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.2, 0.3), borderpad=0.3)

    plt.legend(loc='upper center', bbox_to_anchor=(0.75, 1.15),
            ncol=1, fancybox=False, shadow=False, prop={'size': 10})

    # remove pdf metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_filename.endswith(".pdf")
        else None
    )


    fig.subplots_adjust(left=0.09, bottom=0.05, right=0.99, top=0.95)
    if output_filename:
        fig.savefig(output_filename,
                    dpi=300,
                    metadata={"CreationDate": None})

    if show_plot:
        plt.show()
