#!/bin/bash

cd "$(dirname "$0")" || exit 1xsa

for file in ./data/censored-block-rules-guangzhou_*; do
    filename=$(basename "$file")
    output_file="./results/${filename%.*}_result.${filename##*.}"
	cat ../data/censored-sni-guangzhou_* | sort -u | python3 ../util/generate-test-domains.py | ./rule-parser.sh "$file" > $output_file
done


for file in ./data/censored-block-rules-california_*; do
    filename=$(basename "$file")
    output_file="./results/${filename%.*}_result.${filename##*.}"
	cat ../data/censored-sni-california_* | sort -u | python3 ../util/generate-test-domains.py | ./rule-parser.sh "$file" > $output_file
done