#!/usr/bin/env python3

import sys
import getopt
import glob

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads domain names from files and write the domain names to test in order to extract the regex rules. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file
  -r, --random          the random string for appending or prepending to the domain (default: ZZZZ)

Example:
  Generate testing domains for the censored domain youtube.com:
    {program} <<<youtube.com
        youtube.com
        youtube.com.ZZZZ
        youtube.comZZZZ
        ZZZZ.youtube.com
        ZZZZyoutube.com
        ZZZZ.youtube.com.ZZZZ
        ZZZZ.youtube.comZZZZ
        ZZZZyoutube.com.ZZZZ
        ZZZZyoutube.comZZZZ

  Create a pipelie to generate and test domains:
    grep TLS,EOF 1m.csv | cut -d, -f2 | {program} | ./snicensor
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args, binary=False):
    STDIN =  sys.stdin.buffer if binary else sys.stdin
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

def generate_domain(base_domain, random_str):
    # Rule 0 censored_domain
    # Rule 1 censored_domain{.rnd_str}
    # Rule 2 censored_domain{rnd_str}
    # Rule 3 {rnd_str.}censored_domain
    # Rule 4 {rnd_str}censored_domain
    # Rule 5 {rnd_str.}censored_domain{.rnd_str}
    # Rule 6 {rnd_str.}censored_domain{rnd_str}
    # Rule 7 {rnd_str}censored_domain{.rnd_str}
    # Rule 8 {rnd_str}censored_domain{rnd_str}
    yield base_domain
    yield f"{base_domain}.{random_str}"
    yield f"{base_domain}{random_str}"
    yield f"{random_str}.{base_domain}"
    yield f"{random_str}{base_domain}"
    yield f"{random_str}.{base_domain}.{random_str}"
    yield f"{random_str}.{base_domain}{random_str}"
    yield f"{random_str}{base_domain}.{random_str}"
    yield f"{random_str}{base_domain}{random_str}"


if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:r:", ["help", "out=", "random="])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_file = sys.stdout
    random_str = "ZZZZ"
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_file = open(a, 'a+')
        if o == "-r" or o == "--random":
            random_str = a

    for f in input_files(args):
        for line in f:
            base_domain = line.strip()
            if not base_domain:
                continue
            for domain in generate_domain(base_domain, random_str):
                print(domain, file=output_file)
    output_file.close()
