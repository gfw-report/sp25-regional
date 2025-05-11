#!/usr/bin/env python3

import sys
import os
import glob
from collections import defaultdict

def extract_tlds(domain):
    parts = domain.split('.')
    if len(parts) < 2:
        return None, None  # Invalid domain

    root = '.' + parts[-1]  # Example: ".com"
    full_tld = '.'.join(parts[-2:]) if len(parts) > 2 else root  # Example: "com.pk", "co.uk"

    return root, full_tld



def getfiles(pattern):
    directory = os.getcwd()


    domains = set()
    # First pass to get the set of domains
    files = glob.glob(os.path.join(directory, pattern))
    for file_path in files:
        with open(file_path, 'r') as f:
            for domain in f.readlines():
                domains.add(domain.strip())

    data = defaultdict(list)
    # Second pass build data
    files = sorted(glob.glob(os.path.join(directory, pattern)), key=os.path.basename)
    for file_path in files:
        print(file_path)
        with open(file_path, 'r') as f:
            day_domains = set()
            for domain in f.readlines():
                day_domains.add(domain.strip())
            # Those in today get a 1, otherwise 0
            for d in day_domains:
                data[d].append(1)
            for d in domains - day_domains:
                data[d].append(0)

    return data


gfw = getfiles('censored-sni-california*')
henan = getfiles('censored-sni-guangzhou*')


def savedata(fname, data):
    with open(fname, 'w') as f:
        for d, v in sorted(data.items(), key=lambda x: (extract_tlds(x[0])[0], extract_tlds(x[0])[1], x[0], sum(x[1])), reverse=True):
            f.write('% 30s    ' % d)
            f.write(''.join(['%d' % x for x in v]))
            f.write('\n')

savedata('gfw-day-by-day-check.txt', gfw)
savedata('henan-day-by-day-check.txt', henan)
