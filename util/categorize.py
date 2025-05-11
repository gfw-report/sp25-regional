#!/usr/bin/env python3

"""Look up categories of websites and write a CSV file.
"""

import sys
import argparse
import textwrap
import csv
import time

import requests
from bs4 import BeautifulSoup


# def usage(f=sys.stdout):
#     return f"""\
# Example:

# {sys.argv[0]} < domains.txt > categories.csv 2> errors.txt
# {sys.argv[0]} domains.txt --dictionary dict.csv > categories.csv 2> errors.txt
# """

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args):
    if not args:
        yield sys.stdin
    else:
        for arg in args:
            if arg == "-":
                yield sys.stdin
            else:
                with open(arg) as f:
                    yield(f)

def lookup(url):
    # first look up in local dict
    category = category_dict.get(url, None)
    if category:
        eprint("Cached:", url, category)
        return category

    # if non-existing, look up online
    # time.sleep(1)
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    # }

    # do a HTTP POST request to FortiGuard with parameter: url=google.com&webfilter_search_form_submit=submit&ver=9
    try:
        # page = requests.post("https://www.fortiguard.com/webfilter", headers=headers, data={
        #     'url': url,
        #     'webfilter_search_form_submit': 'submit',
        #     'ver': '9'
        # })

        url = f"https://api.cloudflare.com/client/v4/radar/ranking/domain/{url}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": ""
        }
        page = requests.get(url, headers=headers) 

    except requests.exceptions.ConnectionError as err:
        eprint("Failed to request:", err)
        return None

    if page.status_code != 200:
        eprint(f"{url},{page.status_code}")
        return False
    
    # if page.status_code == 429: # too many requests
    #     eprint(f"{url},{page.status_code}")
    #     return False

    # soup = BeautifulSoup(page.content, 'html.parser')
    # meta_tag = soup.find('meta', attrs={'name': 'description', 'property': 'description'})

    # if meta_tag is None:
        # return None

    data = page.json()
    categories = ','.join([x['name'] for x in data['result']['details_0']['categories']])

    # category = meta_tag['content'].replace('Category: ', '')
    #eprint(category)
    return categories


# global variable
category_dict = {}

if __name__ == '__main__':
    parse = argparse.ArgumentParser(description=__doc__,
                                    # usage=usage()
                                    )
    parse.add_argument('--dictionary', default='', help="path to a local category dictionary")
    #parse.add_argument('--input-files', default=[], nargs='+', help="path to input files ('-' for stdin)")
    args, remaining_args = parse.parse_known_args()

    if args.dictionary:
        with open(args.dictionary, mode='r') as f:
            d = csv.reader(f)
            category_dict = {rows[0]: rows[1] for rows in d}

    w = csv.DictWriter(sys.stdout, lineterminator="\n", fieldnames=["url", "category"])
    w.writeheader()
    # get the arguemtns that are not options


    for f in input_files(remaining_args):
        for line in f:
            url = line.strip()
            if not url:
                continue
            category = lookup(url)
            if category:
                # cache
                category_dict[url] = category

                w.writerow(dict(
                    url = url,
                    category = category
                ))
                sys.stdout.flush()
