PYTHON = python3
SHELL = /bin/bash

ALL = \
	cdf-ranking.pdf \
	cdf-ranking.png \
	henan.csv \
	gfw.csv \
	henan-less-than-21-days.csv \
	henan-less-than-51-days.csv \

# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them{28..30}crea s filtered and reduced versions of th2m{1..8}created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY: \
	data\

.PHONY: all
all: $(ALL)



henan.csv: ../lists/top-1m-2023-08-16-tranco.csv 
	cat ../censorship-duration/henan-domains-ever-censored.txt | sort -u > temp_domains.txt
	echo "domain,ranking" > "$@"
	join -t, -1 2 -2 1 <(sort -t, -k2 $(word 1,$^)) temp_domains.txt >> "$@"
	rm temp_domains.txt

gfw.csv: ../lists/top-1m-2023-08-16-tranco.csv 
	cat ../censorship-duration/gfw-domains-ever-censored.txt | sort -u > temp_domains.txt
	echo "domain,ranking" > "$@"
	join -t, -1 2 -2 1 <(sort -t, -k2 $(word 1,$^)) temp_domains.txt >> "$@"
	rm temp_domains.txt

henan-less-than-21-days.csv: ../lists/top-1m-2023-08-16-tranco.csv 
	cat ../censorship-duration/henan-domains-censored-less-than-21-days.txt | sort -u > temp_domains.txt
	echo "domain,ranking" > "$@"
	join -t, -1 2 -2 1 <(sort -t, -k2 $(word 1,$^)) temp_domains.txt >> "$@"
	rm temp_domains.txt

henan-less-than-51-days.csv: ../lists/top-1m-2023-08-16-tranco.csv 
	cat ../censorship-duration/henan-domains-censored-less-than-51-days.txt | sort -u > temp_domains.txt
	echo "domain,ranking" > "$@"
	join -t, -1 2 -2 1 <(sort -t, -k2 $(word 1,$^)) temp_domains.txt >> "$@"
	rm temp_domains.txt


cdf-ranking.pdf: plot.py gfw.csv henan.csv henan-less-than-21-days.csv henan-less-than-51-days.csv
	$(PYTHON) plot.py --henan henan.csv --gfw gfw.csv --henan-second henan-less-than-21-days.csv --henan-third henan-less-than-51-days.csv --out "$@" --no-show





.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
