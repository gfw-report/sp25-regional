PYTHON = python3

ALL = \
	header-length.pdf \

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

header-length.pdf: plot.py header_len.jsonl
	$(PYTHON) $^ --out "$@" --no-show

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
