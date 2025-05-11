PYTHON = python3

ALL = \
	censored-only-1-day-gfw.csv \
	censored-only-1-day-gfw-date.csv


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


censored-only-1-day-gfw.csv: ../censored-duration-gfw.csv
	awk -F, '$$2 == 1 {print}' ../censored-duration-gfw.csv > censored-only-1-day-gfw.csv

censored-only-1-day-gfw-date.csv: censored-only-1-day-gfw.csv find-added-removed-date.py ../../data/churn-by-day-gfw.json ../../data/churn-by-day-henan.json
	cut -d, -f1 censored-only-1-day-gfw.csv | $(PYTHON) find-added-removed-date.py --churn-gfw ../../data/churn-by-day-gfw.json --churn-henan ../../data/churn-by-day-henan.json > "$@"

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: