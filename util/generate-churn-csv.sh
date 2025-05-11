#!/bin/bash

# Run ./util/generate-churn-csv.sh ./data/ > ./daily-total-and-churn/data.csv
# in the root directory of the repository to generate a CSV file for the churn graph

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 path/to/data/files"
    exit 1
fi


dir=$1 # This is where the files are read from
tmp_folder="/tmp/foo" # Define tmp folder path


echo "Censor,Timestamp,Domain Count,Added,Dropped"

mkdir -p $tmp_folder # Ensure tmp folder exists

for file in $(ls $dir/*.txt | sort); do

    full_filename=$(basename "$file")
    filename="${full_filename%.txt}"

    timestamp=$(echo $filename | cut -d'_' -f 2)
    censor=$(echo $filename | cut -d'-' -f 3 | cut -d'_' -f1)

    case $censor in
    "california")
        censor="GFW"
        ;;
    "guangzhou")
        censor="Henan Firewall"
        ;;
    esac

    curr_file_domains="/tmp/${censor}_${timestamp}_curr_domains.txt"
    sort "$file" | uniq > "$curr_file_domains"

    domain_count=$(wc -l < "$curr_file_domains" | tr -d ' ')
 
    added=0
    dropped=0
    prev_ts=$(date -d "$timestamp -1 day" +"%Y-%m-%d")
    prev_file_domains="/tmp/${censor}_${prev_ts}_curr_domains.txt"
    if [ -f "$prev_file_domains" ]; then
        #echo "Comparing $prev_file_domains and $curr_file_domains"
        added_domains=$(comm -13 "$prev_file_domains" "$curr_file_domains")
        dropped_domains=$(comm -23 "$prev_file_domains" "$curr_file_domains")

        added=$(echo "$added_domains" | wc -l | tr -d ' ')
        dropped=$(echo "$dropped_domains" | wc -l | tr -d ' ')

        # Save churn data to unique files
        #echo "$added_domains" > "$tmp_folder/${censor}_${timestamp}_added.txt"
        #echo "$dropped_domains" > "$tmp_folder/${censor}_${timestamp}_dropped.txt"
    fi

    echo "$censor,$timestamp,$domain_count,$added,$dropped"
    #rm "$curr_file_domains"
done

# Cleanup
rm -f /tmp/*_curr_domains.txt
