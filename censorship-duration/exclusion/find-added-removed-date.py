#!/usr/bin/env python3

import sys
import getopt
import glob
import json
import csv

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [OPTIONS] [DOMAIN_FILE...]
This script reads a list of domains from files or stdin and two churn JSON files.
It outputs a CSV with columns: domain,gfw_added,gfw_removed,henan_added,henan_removed.

Options:
  -h, --help            show this help
  -o, --out FILE        write CSV output to FILE (default: stdout)
  --churn-gfw FILE      specify the churn JSON file for GFW (required)
  --churn-henan FILE    specify the churn JSON file for Henan (required)
  -b, --binary          read input as binary (default: False)

Example:
  {program} --churn-gfw gfw.json --churn-henan henan.json < domains.txt > output.csv
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

def load_churn_file(churn_file_path, binary=False):
    mode = 'rb' if binary else 'r'
    with open(churn_file_path, mode) as f:
        content = f.read()
        if binary:
            content = content.decode('utf-8')
        return json.loads(content)

if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:b", ["help", "out=", "binary", "churn-gfw=", "churn-henan="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_file = sys.stdout
    binary_input = False
    churn_gfw_path = None
    churn_henan_path = None

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--out"):
            output_file = open(a, 'w')
        elif o in ("-b", "--binary"):
            binary_input = True
        elif o == "--churn-gfw":
            churn_gfw_path = a
        elif o == "--churn-henan":
            churn_henan_path = a

    if not churn_gfw_path or not churn_henan_path:
        eprint("Error: Both --churn-gfw and --churn-henan options are required")
        usage()
        sys.exit(1)

    # Load churn JSON files.
    try:
        churn_gfw_data = load_churn_file(churn_gfw_path, binary=binary_input)
    except Exception as e:
        eprint("Error loading churn-gfw file:", e)
        sys.exit(1)

    try:
        churn_henan_data = load_churn_file(churn_henan_path, binary=binary_input)
    except Exception as e:
        eprint("Error loading churn-henan file:", e)
        sys.exit(1)

    # Build lookup dictionaries for each churn file.
    gfw_added = {}
    gfw_removed = {}
    henan_added = {}
    henan_removed = {}

    # Process GFW churn data.
    for date, data in churn_gfw_data.items():
        for domain in data.get("domain_added", []):
            if domain not in gfw_added:
                gfw_added[domain] = date
        for domain in data.get("domain_removed", []):
            if domain not in gfw_removed:
                gfw_removed[domain] = date

    # Process Henan churn data.
    for date, data in churn_henan_data.items():
        for domain in data.get("domain_added", []):
            if domain not in henan_added:
                henan_added[domain] = date
        for domain in data.get("domain_removed", []):
            if domain not in henan_removed:
                henan_removed[domain] = date

    # Read domain list from input files or stdin.
    domains = []
    for f in input_files(args, binary=binary_input):
        for line in f:
            line = line.strip()
            if not line:
                continue
            if binary_input and isinstance(line, bytes):
                line = line.decode('utf-8')
            domains.append(line)

    # Write CSV output.
    csv_writer = csv.writer(output_file)
    csv_writer.writerow(["domain", "gfw_added", "gfw_removed", "henan_added", "henan_removed"])
    for domain in domains:
        csv_writer.writerow([
            domain,
            gfw_added.get(domain, ""),
            gfw_removed.get(domain, ""),
            henan_added.get(domain, ""),
            henan_removed.get(domain, "")
        ])

    if output_file is not sys.stdout:
        output_file.close()
