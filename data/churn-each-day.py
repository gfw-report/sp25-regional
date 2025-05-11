#!/usr/bin/env python3

import os
import re
import sys
import json
from datetime import date
import tldextract  # pip install tldextract
import getopt

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DATA_DIR = "."  # Change to the directory containing your .txt files if needed

# FILENAME_REGEX will be set based on command-line flag
FILENAME_REGEX = None

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def parse_date_from_filename(filename):
    """
    Parse a date from filenames based on FILENAME_REGEX.
    Return a date object or None if no match.
    """
    global FILENAME_REGEX
    match = FILENAME_REGEX.match(filename)
    if match:
        year, month, day = map(int, match.groups())
        return date(year, month, day)
    return None

def read_domains_from_file(filepath):
    """
    Read the file line by line, stripping whitespace.
    Return a set of domain names (skip blank lines).
    """
    domains = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                domain = line.strip()
                if domain:
                    domains.add(domain)
    except Exception as e:
        eprint(f"Error reading {filepath}: {e}")
    return domains

def domain_sort_key(domain):
    """
    Given a domain, return a tuple (suffix, domain, subdomain) to sort
    by TLD/secondary TLD first, then primary domain, then subdomain.

    e.g. "www.google.co.uk" => suffix="co.uk", domain="google", subdomain="www"
    """
    extracted = tldextract.extract(domain)
    return (extracted.suffix, extracted.domain, extracted.subdomain)

def usage():
    prog = sys.argv[0]
    print(f"Usage: {prog} --henan | --gfw")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    # Parse command-line arguments for mode: --henan or --gfw
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["henan", "gfw"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()

    mode = None
    for o, a in opts:
        if o == "--henan":
            mode = "henan"
        elif o == "--gfw":
            mode = "gfw"

    if mode is None:
        eprint("Error: Must specify either --henan or --gfw")
        usage()

    # Set FILENAME_REGEX based on the mode
    global FILENAME_REGEX
    if mode == "henan":
        FILENAME_REGEX = re.compile(r"^censored-sni-guangzhou_(\d{4})-(\d{2})-(\d{2})\.txt$")
    elif mode == "gfw":
        FILENAME_REGEX = re.compile(r"^censored-sni-california_(\d{4})-(\d{2})-(\d{2})\.txt$")

    # 1. Find all relevant files and map them to dates
    all_files = os.listdir(DATA_DIR)
    date_to_file = {}

    for fname in all_files:
        parsed_date = parse_date_from_filename(fname)
        if parsed_date:
            full_path = os.path.join(DATA_DIR, fname)
            date_to_file[parsed_date] = full_path

    # 2. Sort the days by date
    sorted_days = sorted(date_to_file.keys())

    if not sorted_days:
        eprint("No matching files found. Exiting.")
        sys.exit(1)

    # 3. Read domains for each day
    day_to_domains = {}
    for d in sorted_days:
        day_to_domains[d] = read_domains_from_file(date_to_file[d])

    # 4. Compare each day’s domains with the previous day and build JSON output
    output = {}
    previous_domains = None

    for current_day in sorted_days:
        date_str = current_day.strftime("%Y-%m-%d")
        current_domains = day_to_domains[current_day]
        if previous_domains is None:
            # For the first day, consider all domains as "added"
            added = current_domains
            removed = set()
        else:
            added = current_domains - previous_domains
            removed = previous_domains - current_domains

        output[date_str] = {
            "number_added": len(added),
            "number_removed": len(removed),
            "domain_added": sorted(list(added), key=domain_sort_key),
            "domain_removed": sorted(list(removed), key=domain_sort_key)
        }

        previous_domains = current_domains

    # 5. Output JSON to stdout
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
