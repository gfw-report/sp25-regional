PYTHON = python3

ALL = \
	second-level-domain-changes-henan.csv.xz \
	second-level-domain-changes-gfw.csv.xz \
	churn-by-day-henan.json \
	churn-by-day-gfw.json \
	gfw-day-by-day-check.txt.xz \
	henan-day-by-day-check.txt.xz \

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

HENAN_FILES := $(wildcard censored-sni-guangzhou_*.txt)
GFW_FILES := $(wildcard censored-sni-california_*.txt)

henan-day-by-day-check.txt.xz: load-day-by-day.py | $(HENAN_FILES)
	$(PYTHON) $^ --henan-out - | xz > "$@"

gfw-day-by-day-check.txt.xz: load-day-by-day.py | $(GFW_FILES)
	$(PYTHON) $^ --gfw-out - | xz > "$@"

churn-by-day-henan.json: churn-each-day.py | $(HENAN_FILES)
	$(PYTHON) $^ --henan > "$@"

churn-by-day-gfw.json: churn-each-day.py | $(GFW_FILES)
	$(PYTHON) $^ --gfw > "$@"

second-level-domain-changes-henan.csv.xz: churn-each-day-second-level-domain.py henan-day-by-day-check.txt.xz
	xzcat henan-day-by-day-check.txt.xz | $(PYTHON) $< | xz > "$@"

second-level-domain-changes-gfw.csv.xz: churn-each-day-second-level-domain.py gfw-day-by-day-check.txt.xz
	xzcat gfw-day-by-day-check.txt.xz | $(PYTHON) $< | xz > "$@"


.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: