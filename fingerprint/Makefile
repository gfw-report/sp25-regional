PYTHON = python3

ALL = \
	cdf-response-time.pdf \
	cdf-response-time.png

# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them, created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY: \
	pcap\

.PHONY: all
all: $(ALL)

# henan.csv: parse.py pcap/henan*.pcap
# 	$(PYTHON) $^ > "$@"

# gfw.csv: parse.py pcap/gfw*.pcap
# 	$(PYTHON) $^ > "$@"

*.pdf *.png: .EXTRA_PREREQS += common.py

cdf-response-time.pdf: plot.py henan_delta.csv gfw_delta.csv
	$(PYTHON) plot.py --henan henan_delta.csv --gfw gfw_delta.csv --out "$@" --no-show --threshold 30

cdf-response-time.png: plot.py henan_delta.csv gfw_delta.csv
	$(PYTHON) plot.py --henan henan_delta.csv --gfw gfw_delta.csv --out "$@" --no-show --threshold 30

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
