PYTHON = python3

ALL = \
	censored-duration-henan.csv \
	censored-duration-gfw.csv \
	cdf-censored-duration-both.pdf \
	cdf-censored-duration-both.png \
	henan-domains-censored-less-than-21-days.txt \
	henan-domains-censored-less-than-51-days.txt \
	henan-domains-ever-censored.txt \
	gfw-domains-ever-censored.txt \



# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them, created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY:

.PHONY: all
all: $(ALL)

HENAN_FILES := $(wildcard ../data/censored-sni-guangzhou_*.txt)
GFW_FILES := $(wildcard ../data/censored-sni-california_*.txt)

censored-duration-henan.csv: censored-duration.py $(HENAN_FILES)
	$(PYTHON) $^ > "$@"

censored-duration-gfw.csv: censored-duration.py $(GFW_FILES)
	$(PYTHON) $^ > "$@"

henan-domains-censored-less-than-21-days.txt: censored-duration-henan.csv
	awk -F, 'NR>1 && $$2<21 {print $$1}' $^ > "$@"

henan-domains-censored-less-than-51-days.txt: censored-duration-henan.csv
	awk -F, 'NR>1 && $$2<51 {print $$1}' $^ > "$@"

henan-domains-ever-censored.txt: censored-duration-henan.csv
	awk -F, 'NR>1 {print $$1}' $^ > "$@"

gfw-domains-ever-censored.txt: censored-duration-gfw.csv
	awk -F, 'NR>1 {print $$1}' $^ > "$@"

cdf-censored-duration-both.png: cdf-of-duration-two-in-one.py censored-duration-henan.csv censored-duration-gfw.csv
	$(PYTHON) $< --gfw censored-duration-gfw.csv --henan censored-duration-henan.csv --out "$@" --no-show

cdf-censored-duration-both.pdf: cdf-of-duration-two-in-one.py censored-duration-henan.csv censored-duration-gfw.csv
	$(PYTHON) $< --gfw censored-duration-gfw.csv --henan censored-duration-henan.csv --out "$@" --no-show

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: