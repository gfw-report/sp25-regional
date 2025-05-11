#!/bin/bash

# This script parses the output of the rule extraction script and 
# generates a CSV file with the following columns: Domain, Rules
# The regex rules are defined by:
    # 1. youtube.com
    # 2. youtube.com.ZZZZ
    # 3. youtube.comZZZZ
    # 4. ZZZZ.youtube.com
    # 5. ZZZZyoutube.com
    # 6. ZZZZ.youtube.com.ZZZZ
    # 7. ZZZZ.youtube.comZZZZ
    # 8. ZZZZyoutube.com.ZZZZ
    # 9. ZZZZyoutube.comZZZZ

# Use the script like this:
# cat ../data/censored-sni-guangzhou_* | sort -u | python3 ../util/generate-test-domains.py | ./rule-parser.sh ./data/censored-block-rules-2023-12-02.txt 

# Check if the correct number of arguments are provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <checker_file>"
    exit 1
fi

checker_file=$1

awk -v checker_file="$checker_file" '
    BEGIN {
        # Load the checker file into an array
        while (getline line < checker_file) {
            checker[line] = 1
        }
    }

    # Store the base domain and variations
    {
        if (NR % 9 == 1) {
            base_domain = $0
            output = (checker[$0] ? "1" : "")
        } else {
            variation_index = NR % 9
            if ($0 in checker) {
                output = (output ? output "," variation_index : variation_index)
            }
        }
    }

    # Every 9 lines, output the results
    NR % 9 == 0 {
        if (output) {
            print base_domain " " output
        }
    }
' <(cat)
