#!/bin/bash

set -x
set -e

cd "$(dirname "$0")" || exit 1

# Check if the directory parameter is provided
if [ -z "$1" ]; then
    echo "Usage: $0 directory"
    exit 1
fi

# Assign the directory parameter
base_dir="$1"

# Check if the provided directory exists and is a directory
if [ ! -d "$base_dir" ]; then
    echo "Error: Directory $base_dir does not exist."
    exit 1
fi

# Define the list of cities and their corresponding regions
cities=("beijing" "shanghai" "guangzhou" "chengdu" "chongqing" "nanjing" "zhengzhou" "singapore" "seattle")
regions=("Beijing" "Shanghai" "Guangdong" "Sichuan" "Chongqing" "Jiangsu" "Henan" "Singapore" "U.S.")

# Get the total number of regions
region_count=${#regions[@]}

# Function to map a city to its corresponding region
get_region() {
    local city="$1"
    for ((i=0; i<${#cities[@]}; i++)); do
        if [ "${cities[$i]}" = "$city" ]; then
            echo "${regions[$i]}"
            return
        fi
    done
    # Return the city name if no region is found
    echo "$city"
}

# Print the CSV header with regions
echo -n ","
echo "${regions[@]}" | sed 's/ /,/g'

# Initialize an array to hold the rows
rows=()

# Variable to hold the U.S. row
us_row=""

# Loop over each directory inside the base directory
for dir in "$base_dir"/*/; do
    # Skip directories containing "singapore" in their name
    if [[ "$dir" == *"singapore"* ]]; then
        continue
    fi

    # Get the directory name without trailing slash and base path
    dir_name=$(basename "${dir%/}")

    # Map the directory name to its region if applicable
    dir_region=$(get_region "$dir_name")

    # Initialize a counter to track the city index
    index=0

    # Initialize a variable to hold the row
    row="${dir_region},"

    # Loop through each city and collect the count for each one
    for city in "${cities[@]}"; do
        # Construct the file pattern
        pattern="${dir}10k_sni_censorship_${city}_ts_0*"

        # Check if files matching the pattern exist
        if ls $pattern 1> /dev/null 2>&1; then
            # Count unique occurrences for each city
            count=$(grep "TLS,EOF" $pattern 2>/dev/null | cut -d, -f2 | sort -u | wc -l)
        else
            count=0
        fi

        # Append the count to the row
        row="${row}${count}"

        # Increment the index
        index=$((index + 1))

        # Add a comma if it's not the last region
        if [ "$index" -lt "$region_count" ]; then
            row="${row},"
        fi
    done

    # If the dir_region is "U.S.", save the row to us_row
    if [ "$dir_region" = "U.S." ]; then
        us_row="$row"
    else
        # Otherwise, add the row to rows array
        rows+=("$row")
    fi
done

# Print all rows except the U.S. row
for r in "${rows[@]}"; do
    echo "$r"
done

# Print the U.S. row last
if [ -n "$us_row" ]; then
    echo "$us_row"
fi
