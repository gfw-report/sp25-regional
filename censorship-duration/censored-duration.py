#!/usr/bin/env python3

import sys
import getopt
import glob
import csv
from collections import Counter

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from files containing newline-separated domains and writes a CSV output with columns: domain, count.
With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file
  -b, --binary          read input as binary (default: False)

Example:
  {program} < input.txt > output.csv
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args, binary=False):
    STDIN = sys.stdin.buffer if binary else sys.stdin
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

    output_file = sys.stdout
    binary_input = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        if o in ("-o", "--out"):
            output_file = open(a, 'a+')
        if o in ("-b", "--binary"):
            binary_input = True

    # Use a counter to keep track of each domain's frequency.
    counter = Counter()

    for f in input_files(args, binary=binary_input):
        for line in f:
            if binary_input:
                line = line.decode('utf-8', errors='ignore')
            line = line.strip()
            if not line:
                continue
            counter[line] += 1

    # Write the results as CSV.
    writer = csv.writer(output_file)
    writer.writerow(["domain", "count"])
    for domain, count in counter.items():
        writer.writerow([domain, count])

    output_file.close()
