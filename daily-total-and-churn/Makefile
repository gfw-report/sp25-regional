PYTHON = python3

ROOT_DIR := ..

ALL = \
	censored-domains-over-time-all.pdf\
	censored-domains-over-time-all.png\
	censored-domains-over-time-all-with-breaks.pdf\
	censored-domains-over-time-all-with-breaks.png\


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

.PHONY: cdf-response-time.pdf
../data/churn-by-day-gfw.json:
	make -C $(ROOT_DIR)/fingerprint $@
	ln -sf $(ROOT_DIR)/fingerprint/$@ .

.PHONY: churn-by-day-henan.json
churn-by-day-henan.json:
	make -C $(ROOT_DIR)/data $@
	ln -sf $(ROOT_DIR)/data/$@ .

.PHONY: churn-by-day-gfw.json
churn-by-day-gfw.json:
	make -C $(ROOT_DIR)/data $@
	ln -sf $(ROOT_DIR)/data/$@ .

censored-domains-over-time-all.pdf: plot-one.py churn-by-day-gfw.json churn-by-day-henan.json
	$(PYTHON) ./plot-one.py --gfw churn-by-day-gfw.json --henan churn-by-day-henan.json --gaps 2024-03-04-2024-10-08 --gap-width 30.0 --no-show --out "$@"

censored-domains-over-time-all.png: plot-one.py churn-by-day-gfw.json churn-by-day-henan.json
	$(PYTHON) ./plot-one.py --gfw churn-by-day-gfw.json --henan churn-by-day-henan.json --gaps 2024-03-04-2024-10-08 --gap-width 30.0 --no-show --out "$@"

censored-domains-over-time-all-with-breaks.pdf: plot-one.py churn-by-day-gfw.json churn-by-day-henan.json
	$(PYTHON) ./plot-one.py --gfw churn-by-day-gfw.json --henan churn-by-day-henan.json --gaps 2024-03-04-2024-10-08 --breaks 2025-01-11-2025-01-16 --gap-width 30.0 --no-show --out "$@"

censored-domains-over-time-all-with-breaks.png: plot-one.py churn-by-day-gfw.json churn-by-day-henan.json
	$(PYTHON) ./plot-one.py --gfw churn-by-day-gfw.json --henan churn-by-day-henan.json --gaps 2024-03-04-2024-10-08 --breaks 2025-01-11-2025-01-16 --gap-width 30.0 --no-show --out "$@"

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR:
