#!/usr/bin/env python3

import sys
import getopt
import os
import glob
from collections import defaultdict
from datetime import datetime, timedelta

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [options]

This script processes domain files in the current directory and outputs day-by-day check data
for two sets of files:
  - GFW data: files matching pattern "censored-sni-california*"
  - Henan data: files matching pattern "censored-sni-guangzhou*"

Options:
  --gfw-out=FILE      Output file for GFW data (default: stdout)
  --henan-out=FILE    Output file for Henan data (default: stdout)
  -h, --help          Show this help message and exit.
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def extract_tlds(domain):
    parts = domain.split('.')
    if len(parts) < 2:
        return None, None  # Invalid domain
    root = '.' + parts[-1]  # e.g., ".com"
    full_tld = '.'.join(parts[-2:]) if len(parts) > 2 else root  # e.g., "co.uk"
    return root, full_tld

def safe_extract_tlds(domain):
    root, full_tld = extract_tlds(domain)
    return (root if root is not None else "", full_tld if full_tld is not None else "")

def getfiles(pattern):
    directory = os.getcwd()
    domains = set()
    # First pass: collect all domains from matching files
    files = glob.glob(os.path.join(directory, pattern))
    for file_path in files:
        with open(file_path, 'r') as f:
            for domain in f.readlines():
                domains.add(domain.strip())

    data = defaultdict(list)
    # Second pass: process files day by day
    files = sorted(glob.glob(os.path.join(directory, pattern)), key=os.path.basename)
    if not files:
        return data  # No matching files found
    files_prefix = files[0].split('_')[0]
    start_date = files[0].split('_')[-1].split('.')[0]
    end_date = files[-1].split('_')[-1].split('.')[0]

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1  # +1 to include end_date

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        file_path = f"{files_prefix}_{current_date.strftime('%Y-%m-%d')}.txt"
        try:
            with open(file_path, 'r') as f:
                day_domains = set(line.strip() for line in f.readlines())
                # Domains present on this day get a 1; absent get a 0
                for d in day_domains:
                    data[d].append(1)
                for d in domains - day_domains:
                    data[d].append(0)
        except Exception:
            for d in domains:
                data[d].append(0)
    return data

def savedata_handle(handle, data):
    # Sort by TLD parts, domain name, then by the sum of daily marks (in descending order)
    for d, v in sorted(
        data.items(),
        key=lambda x: (safe_extract_tlds(x[0])[0], safe_extract_tlds(x[0])[1], x[0], sum(x[1])),
        reverse=True
    ):
        handle.write('% 30s    ' % d)
        handle.write(''.join(['%d' % x for x in v]))
        handle.write('\n')

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h", ["help", "gfw-out=", "henan-out="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    # Default output: stdout
    gfw_out_handle = sys.stdout
    henan_out_handle = sys.stdout

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o == "--gfw-out":
            if a != "-" and a != "":
                gfw_out_handle = open(a, 'w')
            else:
                gfw_out_handle = sys.stdout
        elif o == "--henan-out":
            if a != "-" and a != "":
                henan_out_handle = open(a, 'w')
            else:
                henan_out_handle = sys.stdout

    # Process GFW data
    gfw_data = getfiles("censored-sni-california*")
    if gfw_out_handle == sys.stdout:
        savedata_handle(sys.stdout, gfw_data)
    else:
        savedata_handle(gfw_out_handle, gfw_data)

    # Process Henan data
    henan_data = getfiles("censored-sni-guangzhou*")
    if henan_out_handle == sys.stdout:
        savedata_handle(sys.stdout, henan_data)
    else:
        savedata_handle(henan_out_handle, henan_data)

    # Close file handles if they are not stdout
    if gfw_out_handle != sys.stdout:
        gfw_out_handle.close()
    if henan_out_handle != sys.stdout and henan_out_handle != gfw_out_handle:
        henan_out_handle.close()

if __name__ == '__main__':
    main()
