#!/usr/bin/env python3

import getopt
import sys
import glob

from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib_venn import venn2, venn3, venn2_circles, venn2_unweighted


import common

FIGSIZE = (common.COLUMNWIDTH, 2.0)

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

    if not gfw_filename or not henan_filename:
        eprint("Missing input files")
        usage()
        sys.exit(2)



    gfw_df = pd.read_csv(gfw_filename, header=None)
    henan_df = pd.read_csv(henan_filename, header=None)
    intersection = set(gfw_df[0].tolist()) & set(henan_df[0].tolist())


    fig = plt.figure(figsize=FIGSIZE)

    set1 = set(gfw_df[0].tolist())
    set2 = set(henan_df[0].tolist())

    v = venn2([set1, set2], ('GFW', 'Henan'))

    
    v.get_label_by_id('11').set_text(str(len(intersection)))

    # for text in v.set_labels:
        # text.set_fontsize(5)
    
    # for text in v.subset_labels:
        # text.set_fontsize(5)
        # text.set_position(position)



    # remove pdf metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_filename.endswith(".pdf")
        else None
    )

    fig.subplots_adjust(left=0.05, bottom=0.05, right=0.995, top=0.995)
    plt.title("Venn diagram of GFW and Henan")

    plt.annotate(format(int(v.get_label_by_id('100').get_text()), ',d' ), xy=v.get_label_by_id('100').get_position() - np.array([0, 0.00]), xytext=(-23,0),
             ha='center', textcoords='offset points', bbox=dict(boxstyle='round,pad=0.0', fc='none', edgecolor='none' ,alpha=0.1),
             )
    
    v.get_label_by_id('100').set_text('')

    plt.annotate(format(int(v.get_label_by_id('11').get_text()), ',d'), xy=v.get_label_by_id('11').get_position() - np.array([0, 0.00]), xytext=(-10,40),
             ha='center', textcoords='offset points', bbox=dict(boxstyle='round,pad=0.5', fc='none', edgecolor='none', alpha=0.1),
             arrowprops=dict(arrowstyle='<-', connectionstyle='arc3,rad=0.0',color='black'))
    
    v.get_label_by_id('11').set_text('')


    
    v.get_label_by_id('01').set_text(format(int(v.get_label_by_id('01').get_text()), ',d'))

    if output_filename:
        fig.savefig(output_filename,
                    dpi=300,
                    metadata={"CreationDate": None})


    if show_plot:
        plt.show()
