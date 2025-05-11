#!/usr/bin/env python3

import sys
import getopt
import glob

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import common

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from files and write output. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: client-to-sink-server-data-matrix.pdf)
  -b, --binary          read input as binary (default: False)

Example:
  {program} < input.txt > output.txt
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
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:b", ["help", "out=", "binary"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "client-to-sink-server-data-matrix.pdf"
    binary_input = False
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-b" or o == "--binary":
            binary_input = True

    # concatenate all the dataframes to df
    df = pd.concat((pd.read_csv(f) for f in input_files(args, binary=binary_input)), ignore_index=True)

    # Rename the first column to 'Client Location'
    df.rename(columns={df.columns[0]: 'Clients'}, inplace=True)
    # Reordering columns to place Seattle and Singapore side by side
    # df = df[["Client Location", "Beijing", "Guangzhou", "Shanghai", "Seattle", "Singapore"]]

    # Plotting the corrected data with a blue and orange color scheme
    fig, ax = plt.subplots(figsize=(common.COLUMNWIDTH, 3.5))

    heatmap = sns.heatmap(df.set_index('Clients'),
    annot=True, fmt="d", cbar=False, cmap="Oranges",
    linewidth=0.5,linecolor="black", ax=ax)


    for _, spine in ax.spines.items():
        spine.set_visible(True)
        # set the color of the frame
        spine.set_color('black')

    xlabel = plt.xlabel('Servers', labelpad=5, loc='left')  # Moves x-axis label to the left corner
    xlabel.set_rotation(360 - 45)
    ax.xaxis.set_label_position('top')
    plt.gca().xaxis.set_label_coords(-0.15, 1.1)



    ylabel = plt.ylabel('Clients', rotation=0, fontweight='bold', loc='top')  # Moves y-axis label to the top
    ylabel.set_rotation(360 - 45)
    plt.gca().yaxis.set_label_coords(-0.15, 1.00)


    heatmap.xaxis.set_ticks_position('top')
    plt.xticks(rotation=90, ha='center')
    plt.yticks(rotation=0)

    # plt.show()
    metadata = (
            {"CreationDate": None, "Creator": None, "Producer": None}
            if output_filename.endswith(".pdf")
            else None
        )

    fig.subplots_adjust(left=0.23, bottom=0.0, right=0.99, top=0.80)
    if output_filename:
        fig.savefig(output_filename,
                    dpi=300,
                    metadata={"CreationDate": None})
