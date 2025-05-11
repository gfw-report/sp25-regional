#!/usr/bin/env python3

import sys
import getopt
import glob
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [OPTIONS] [FILENAME...]
This script reads from files (or STDIN if none or '-' is given) containing domain history data,
processes the data to detect abrupt changes per TLD, and writes the analysis as CSV to stdout (or to a file).

Options:
  -h, --help                     show this help
  -o, --out=FILE                 write output to FILE (default: stdout)
  -b, --binary                   read input as binary (default: False)
  -s, --start-date=YYYY-MM-DD    first date in the dataset (default: 2023-11-05)
  -f, --filter-start-date=YYYY-MM-DD
                                 start date for filtering (default: 2023-11-21)
  -e, --filter-end-date=YYYY-MM-DD
                                 end date for filtering (default: 2024-03-03)
  -j, --jump-low=NUM             lower bound for jump detection (default: 10)
  -k, --jump-high=NUM            upper bound for jump detection (default: 80)
  -d, --drop-high=NUM            high threshold for drop detection (default: 50)
  -l, --drop-low=NUM             low threshold for drop detection (default: 10)
  -m, --min-domains=NUM          minimum number of domains per TLD to include (default: 10)

Example:
  {program} -s 2023-11-05 -f 2023-11-21 -e 2023-12-31 -j 10 -k 80 -d 50 -l 10 -m 10 < henan-day-by-day-check.txt > output.csv
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

def get_tld(domain):
    parts = domain.split(".")
    if len(parts) >= 3:
        return ".".join(parts[-2:])  # e.g., "co.uk", "org.uk"
    else:
        return parts[-1]  # e.g., "com", "net"

if __name__ == '__main__':
    # Default configuration values
    start_date_str = "2023-11-05"
    filter_start_date_str = "2023-11-21"
    filter_end_date_str = "2024-03-03"
    jump_low = 10
    jump_high = 80
    drop_high = 50
    drop_low = 10
    min_domains = 10
    binary_input = False
    output_file = sys.stdout

    # Parse command-line options
    try:
        opts, args = getopt.gnu_getopt(
            sys.argv[1:],
            "ho:bs:f:e:j:k:d:l:m:",
            ["help", "out=", "binary", "start-date=", "filter-start-date=", "filter-end-date=",
             "jump-low=", "jump-high=", "drop-high=", "drop-low=", "min-domains="]
        )
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--out"):
            output_file = open(a, 'a+')
        elif o in ("-b", "--binary"):
            binary_input = True
        elif o in ("-s", "--start-date"):
            start_date_str = a
        elif o in ("-f", "--filter-start-date"):
            filter_start_date_str = a
        elif o in ("-e", "--filter-end-date"):
            filter_end_date_str = a
        elif o in ("-j", "--jump-low"):
            jump_low = int(a)
        elif o in ("-k", "--jump-high"):
            jump_high = int(a)
        elif o in ("-d", "--drop-high"):
            drop_high = int(a)
        elif o in ("-l", "--drop-low"):
            drop_low = int(a)
        elif o in ("-m", "--min-domains"):
            min_domains = int(a)

    # Convert date strings to datetime objects
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        filter_start_date = datetime.strptime(filter_start_date_str, "%Y-%m-%d")
        filter_end_date = datetime.strptime(filter_end_date_str, "%Y-%m-%d")
    except ValueError as e:
        eprint("Error parsing dates:", e)
        sys.exit(1)

    # Calculate indices for slicing history lists
    start_index = (filter_start_date - start_date).days
    end_index = (filter_end_date - start_date).days + 1

    # Read all input lines from provided files or STDIN
    all_lines = []
    for f in input_files(args, binary=binary_input):
        for line in f:
            if binary_input:
                line = line.decode("utf-8", errors="replace")
            line = line.strip()
            if not line:
                continue
            all_lines.append(line)

    # Process the input lines to extract (domain, history)
    data = []
    for line in all_lines:
        parts = line.rsplit(maxsplit=1)
        if len(parts) == 2:
            domain, history = parts
            data.append((domain.strip(), history.strip()))

    if not data:
        eprint("No valid data found in input.")
        sys.exit(1)

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=["Domain", "History"])

    # Extract TLDs
    df["TLD"] = df["Domain"].apply(get_tld)

    # Convert history string to list of integers and slice by date indices
    df["History"] = df["History"].apply(lambda x: [int(c) for c in x])
    df["History"] = df["History"].apply(lambda x: x[start_index:end_index])

    # Aggregate by TLD: compute the mean blocked ratio per day for each TLD
    tld_stats = df.groupby("TLD")["History"].apply(lambda x: np.array(x.tolist()).mean(axis=0))

    # Count how many domains are under each TLD
    tld_counts = df.groupby("TLD")["Domain"].nunique()

    # Filter out TLDs that have more than the configured minimum number of associated domains
    filtered_tlds = tld_counts[tld_counts > min_domains].index

    # Keep only aggregated stats for TLDs that pass the filter
    filtered_tld_stats = {tld: history for tld, history in tld_stats.items() if tld in filtered_tlds}

    # Create a list of rows for each event we detect
    analysis_rows = []

    for tld, history in filtered_tld_stats.items():
        # Convert from ratio to absolute counts
        total_domains_for_tld = len(df[df["TLD"] == tld])
        absolute_counts = np.array(history) * total_domains_for_tld

        # Convert ratios to integer percentages
        percentages = (history * 100).astype(int)

        # Iterate through the days in the slice (starting from the second day)
        for i in range(1, len(percentages)):
            change_date = filter_start_date + timedelta(days=i)
            formatted_date = change_date.strftime("%Y-%m-%d")

            old_pct = percentages[i-1]
            new_pct = percentages[i]
            old_abs = int(absolute_counts[i-1])
            new_abs = int(absolute_counts[i])

            # Check conditions using the configurable thresholds
            if old_pct < jump_low and new_pct > jump_high:
                note = f"Addition of {tld}, Jump from {old_pct}% to {new_pct}%, {old_abs} to {new_abs}"
            elif old_pct >= drop_high and new_pct <= drop_low:
                note = f"Removal of {tld}, Drop from {old_pct}% to {new_pct}%, {old_abs} to {new_abs}"
            else:
                continue

            analysis_rows.append([
                tld,
                formatted_date,
                f"{old_pct}%",
                f"{new_pct}%",
                f"{old_abs}",
                f"{new_abs}",
                note
            ])

    # Convert the collected analysis into a DataFrame and sort by Date
    analysis_df = pd.DataFrame(
        analysis_rows,
        columns=["TLD", "Date", "Old Percentage", "New Percentage", "Old Number", "New Number", "Notes"]
    )
    analysis_df = analysis_df.sort_values(by="Date")

    # Output CSV results
    print(analysis_df.to_csv(index=False), file=output_file)

    # Only close the output file if it is not sys.stdout
    if output_file is not sys.stdout:
        output_file.close()
