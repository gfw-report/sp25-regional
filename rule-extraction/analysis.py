#!/usr/bin/env python3

import sys
import getopt
import glob
import csv

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from one or more files (or from standard input if no file is given),
extracts the second whitespace-delimited field from each line, counts its occurrences,
and then outputs the token, count, and percentage in CSV format.
Options:
  -h, --help            Show this help message.
  -o, --out             Write output to file (default: stdout).
  -b, --binary          Read input as binary (default: False).

Example:
  {program} results/censored-block-rules-california_*_result.txt > output.csv
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

def process_lines(files, binary=False):
    """Reads each line from the provided files, extracts the second field and counts it."""
    counts = {}
    total = 0
    for f in files:
        for line in f:
            if binary:
                # Decode binary input as UTF-8 (replace errors)
                line = line.decode('utf-8', errors='replace')
            line = line.strip()
            if not line:
                continue
            fields = line.split()
            if len(fields) < 2:
                continue
            token = fields[1]
            counts[token] = counts.get(token, 0) + 1
            total += 1
    return counts, total

def main():
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
        elif o in ("-o", "--out"):
            output_file = open(a, 'a+')
        elif o in ("-b", "--binary"):
            binary_input = True

    # Read through input files and process lines to count tokens from the second field.
    files_gen = input_files(args, binary=binary_input)
    counts, total = process_lines(files_gen, binary=binary_input)

    # Sort tokens by count in descending order.
    sorted_tokens = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    # Create a CSV writer to output the results.
    # use TSV
    writer = csv.writer(output_file, delimiter='\t')
    # Write CSV header.
    writer.writerow(["token", "count", "percentage"])

    for token, count in sorted_tokens:
        percentage = (count / total * 100) if total > 0 else 0
        # Format the percentage to two decimal places.
        writer.writerow([token, count, f"{percentage:.2f}"])

    if output_file is not sys.stdout:
        output_file.close()

if __name__ == '__main__':
    main()
