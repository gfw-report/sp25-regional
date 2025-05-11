#!/usr/bin/env python3

import getopt
import sys
import json
import re

from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.dates import MonthLocator, DateFormatter
from brokenaxes import brokenaxes

import common

FIGSIZE = (common.COLUMNWIDTH, 2.0)

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} --gfw <gfw.json> --henan <henan.json> [options]
This script reads two JSON files produced by the domain diff tool and plots the cumulative number of blocked domains.
Each JSON file should contain a dictionary with date keys. For each date, the JSON object should have:
  "number_added": <int>
  "number_removed": <int>
  "domain_added": [list of domains]
  "domain_removed": [list of domains]

Options:
  -h, --help            Show this help message
  -o, --out             Write the plot to file (default: figure.pdf)
  -n, --no-show         Do not display the plot, just save it
  --gfw <file>          Input JSON file for GFW
  --henan <file>        Input JSON file for Henan Firewall
  --start <YYYY-MM-DD>  Start date (inclusive); default is the earliest date in the data
  --end <YYYY-MM-DD>    End date (inclusive); default is the latest date in the data
  --gaps <spec>         Gap spec of the form YYYY-MM-DD-YYYY-MM-DD (both boundaries required)
  --gap-width <float>   (Unused in this broken‐axis version; use the gap spec to break the x–axis)
  --breaks <spec>       Small gaps in the data to be ignored (e.g., 2024-01-03-2024-01-10)
Example:
  {program} --gfw gfw.json --henan henan.json --start 2023-11-01 --end 2023-12-31 --gaps 2024-03-04-2024-10-08 --out plot.pdf
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def load_json_to_dataframe(filename):
    """
    Load the JSON file and convert its diff records into a DataFrame.
    The JSON file is expected to be a dict with keys as date strings.
    We compute a cumulative "Domain Count" for each date.
    For the first day, we treat the daily diff as having 0 additions/drops for plotting.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    records = []
    sorted_dates = sorted(data.keys())
    cumulative = None
    for i, d in enumerate(sorted_dates):
        dt = pd.to_datetime(d)
        day_data = data[d]
        added = day_data.get("number_added", 0)
        removed = day_data.get("number_removed", 0)
        if i == 0:
            cumulative = added
            records.append({
                "Timestamp": dt,
                "Domain Count": cumulative,
                "Added": 0,
                "Dropped": 0
            })
        else:
            cumulative = cumulative + added - removed
            records.append({
                "Timestamp": dt,
                "Domain Count": cumulative,
                "Added": added,
                "Dropped": removed
            })
    return pd.DataFrame(records)

def main():
    try:
        opts, _ = getopt.gnu_getopt(
            sys.argv[1:],
            "ho:nb:",
            ["help", "out=", "no-show", "gfw=", "henan=", "start=", "end=", "gaps=", "gap-width=", "breaks="]
        )
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    gfw_file = None
    henan_file = None
    start_date_str = None
    end_date_str = None
    gaps_str = None   # Gap spec (required format: YYYY-MM-DD-YYYY-MM-DD)
    breaks_str = None  # Small gaps in the data to be ignored (e.g., 2024-01-03-2024-01-10)
    # Note: --gap-width is not used in this broken-axis approach.

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--out"):
            output_filename = a
        elif o in ("-n", "--no-show"):
            show_plot = False
        elif o == "--gfw":
            gfw_file = a
        elif o == "--henan":
            henan_file = a
        elif o == "--start":
            start_date_str = a
        elif o == "--end":
            end_date_str = a
        elif o == "--gaps":
            gaps_str = a
        elif o == "--gap-width":
            pass  # In this broken-axis version, gap-width is not used.
        elif o == "--breaks":
            breaks_str = a


    if not gfw_file or not henan_file:
        eprint("Error: Both --gfw and --henan input files must be provided.")
        usage()
        sys.exit(2)

    # Load data.
    df_gfw = load_json_to_dataframe(gfw_file)
    df_henan = load_json_to_dataframe(henan_file)

    # Optional exclusion ranges.
    exclusion_ranges = [
        (pd.to_datetime('2024-01-03'), pd.to_datetime('2024-01-10')),
    ]
    def exclude(row):
        for start, end in exclusion_ranges:
            if start < row['Timestamp'] < end:
                row['Domain Count'] = np.nan
        return row

    df_gfw = df_gfw.apply(exclude, axis=1)
    df_henan = df_henan.apply(exclude, axis=1)

    # Apply start/end date filtering if specified.
    if start_date_str:
        start_dt = pd.to_datetime(start_date_str).normalize()
        df_gfw = df_gfw[df_gfw['Timestamp'] >= start_dt]
        df_henan = df_henan[df_henan['Timestamp'] >= start_dt]
    if end_date_str:
        end_dt = pd.to_datetime(end_date_str).normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        df_gfw = df_gfw[df_gfw['Timestamp'] <= end_dt]
        df_henan = df_henan[df_henan['Timestamp'] <= end_dt]

    # Determine overall date range.
    t0 = min(df_gfw['Timestamp'].min(), df_henan['Timestamp'].min())
    t3 = max(df_gfw['Timestamp'].max(), df_henan['Timestamp'].max())

    gap_specified = False
    if gaps_str:
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})$', gaps_str.strip())
        if not m:
            eprint(f"Error parsing gap spec '{gaps_str}': Format must be YYYY-MM-DD-YYYY-MM-DD.")
        else:
            gap_specified = True
            gap_start = pd.to_datetime(m.group(1))
            gap_end = pd.to_datetime(m.group(2))

    breaks_specified = False
    if breaks_str:
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})$', breaks_str.strip())
        if not m:
            eprint(f"Error parsing breaks spec '{breaks_str}': Format must be YYYY-MM-DD-YYYY-MM-DD.")
        else:
            breaks_specified = True
            break_start = pd.to_datetime(m.group(1))
            break_end = pd.to_datetime(m.group(2))

    if gap_specified:
        df_gfw_gapfree = df_gfw.copy()
        df_henan_gapfree = df_henan.copy()

        df_gfw_gapfree.loc[(df_gfw_gapfree['Timestamp'] > gap_start) & (df_gfw_gapfree['Timestamp'] < gap_end), 'Domain Count'] = np.nan
        df_henan_gapfree.loc[(df_henan_gapfree['Timestamp'] > gap_start) & (df_henan_gapfree['Timestamp'] < gap_end), 'Domain Count'] = np.nan

        # Use brokenaxes to split the timeline
        fig = plt.figure(figsize=(FIGSIZE))  # Adjust width for readability
        bax = brokenaxes(
            xlims=((t0, gap_start), (gap_end, t3)),
            hspace=0.05,
            wspace=0.05,
            despine=False,
        )

        # split the GFW data into two parts for plotting, before 2025-01-11 and after 2025-01-18
        if breaks_specified:
            break_start = pd.to_datetime(break_start)
            break_end = pd.to_datetime(break_end)

            df_gfw_gapfree_before = df_gfw[df_gfw['Timestamp'] < break_start]
            df_gfw_gapfree_after = df_gfw[df_gfw['Timestamp'] > break_end]
            line1 = bax.plot(df_gfw_gapfree_before['Timestamp'], df_gfw_gapfree_before['Domain Count'],
                    label='GFW', color='blue', linestyle='-', marker='x', markersize=2)
            line2 = bax.plot(df_gfw_gapfree_after['Timestamp'], df_gfw_gapfree_after['Domain Count'],
                    color='blue', linestyle='-', marker='x', markersize=2)


            df_henan_gapfree_before = df_henan[df_henan['Timestamp'] < break_start]
            df_henan_gapfree_after = df_henan[df_henan['Timestamp'] > break_end]
            line3 = bax.plot(df_henan_gapfree_before['Timestamp'], df_henan_gapfree_before['Domain Count'],
                    label='Henan Firewall', color='orange', linestyle='-', markersize=2)
            line4 = bax.plot(df_henan_gapfree_after['Timestamp'], df_henan_gapfree_after['Domain Count'],
                    color='orange', linestyle='-', markersize=2)

        else:
            bax.plot(df_gfw_gapfree['Timestamp'], df_gfw_gapfree['Domain Count'],
                    label='GFW', color='blue', linestyle='-', marker='x', markersize=2)
            bax.plot(df_henan_gapfree['Timestamp'], df_henan_gapfree['Domain Count'],
                    label='Henan Firewall', color='orange', linestyle='-', markersize=2)




        # bax.plot(df_gfw_gapfree['Timestamp'], df_gfw_gapfree['Domain Count'],
        #         label='GFW', color='blue', linestyle='-', marker='x', markersize=2)


        [x.remove() for x in bax.diag_handles]

        # Format x-axis date labels
        for ax in bax.axs:
            # e.g. Jan 1, '24
            ax.xaxis.set_major_formatter(DateFormatter('%b %d \n %Y'))
            # make it show the first day of the month

            ax.tick_params(axis='x', labelrotation=0, labelsize=10)
            ax.grid(True, axis='x', linestyle='--', alpha=0.3)


        # Add labels and legend
        # bax.set_xlabel("Date", labelpad=35)
        # bax.axs[0].xaxis.set_label_coords(0.5, -0.25)

        bax.set_ylabel("# of Blocked Domains")
        bax.legend(loc='upper left')
        bax.grid(True)



    else:
        # No gap specified: use a single continuous axis.
        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax.plot(df_henan['Timestamp'], df_henan['Domain Count'],
                label='Henan Firewall', linestyle='-', color='orange', markersize=2, marker='x')
        ax.plot(df_gfw['Timestamp'], df_gfw['Domain Count'],
                label='GFW', linestyle='-', color='blue', markersize=1)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.xticks(rotation=45)
        ax.set_xlim(t0, t3)
        ax.set_xlabel("Date")
        ax.set_ylabel("# of Blocked Domains")
        ax.legend()
        ax.grid(True)
        fig.tight_layout()

    metadata = ({"CreationDate": None, "Creator": None, "Producer": None}
                if output_filename.endswith(".pdf") else None)


    fig.subplots_adjust(left=0.18, bottom=0.16, right=0.98, top=0.97)
    # Keep it below the above line to avoid the worng positioning of //
    bax.draw_diags()

    if output_filename:
        fig.savefig(output_filename, dpi=300, metadata=metadata)
    if show_plot:
        plt.show()

if __name__ == '__main__':
    main()
