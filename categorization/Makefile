PYTHON = python3
SHELL = /bin/bash

ALL = \
	gfw-categorized.pdf \
	henan-categorized.pdf \
	overlap-categorized.pdf \

# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them, created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY: \

.PHONY: all
all: $(ALL)

gfw-categorized.pdf: plot.py gfw-blacklist-categorized.csv
	$(PYTHON) plot.py --gfw gfw-blacklist-categorized.csv --out "$@" --no-show

henan-categorized.pdf: plot.py henan-blacklist-categorized.csv
	$(PYTHON) plot.py --henan henan-blacklist-categorized.csv --out "$@" --no-show

overlap-categorized.pdf: plot.py overlap_categorized.csv
	$(PYTHON) plot.py --henan overlap_categorized.csv --out "$@" --no-show

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
