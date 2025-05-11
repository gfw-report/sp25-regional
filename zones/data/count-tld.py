#!/usr/bin/env python3

import sys
import getopt
import glob

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads domains from files and write the count of TLDs to output. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file
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

    output_file = sys.stdout
    binary_input = False
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_file = open(a, 'a+')
        if o == "-b" or o == "--binary":
            binary_input = True

    tld_count = dict()
    for f in input_files(args, binary=binary_input):
        for line in f:
            line = line.strip()
            if not line:
                continue
            tld = ".".join(line.split(".")[1:])
            if tld in tld_count:
                tld_count[tld] += 1
            else:
                tld_count[tld] = 1

    # print the tld_count dict as a CSV, with the TLDs sorted by count
    for tld, count in sorted(tld_count.items(), key=lambda x: x[1], reverse=True):
        print(f"{tld},{count}", file=output_file)
    output_file.close()