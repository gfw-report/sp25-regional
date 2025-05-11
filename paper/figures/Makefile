.PYTHON = python3

ROOT_DIR := ../..

ALL = \
	cdf-response-time.pdf\
	cdf-ranking.pdf\
	venn-diagram-accumulated.pdf\
	censored-domains-over-time-all.pdf\
	gfw-categorized.pdf\
	henan-categorized.pdf\
	rule-extraction.pdf\
	client-to-sink-server-data-matrix.pdf\
	header-length.pdf\
	cdf-censored-duration-both.pdf\


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

# The .PHONY here means to always run the rule, even if the target file
# already exists. The figures here do not have dependencies.
# Rather, we let the Makefile in the relevant directory to do
# the dependency checking.
.PHONY: cdf-response-time.pdf
cdf-response-time.pdf:
	make -C $(ROOT_DIR)/fingerprint $@
	ln -sf $(ROOT_DIR)/fingerprint/$@ .

.PHONY: cdf-ranking.pdf
cdf-ranking.pdf:
	make -C $(ROOT_DIR)/ranking $@
	ln -sf $(ROOT_DIR)/ranking/$@ .

.PHONY: venn-diagram-accumulated.pdf
venn-diagram-accumulated.pdf:
	make -C $(ROOT_DIR)/zones/ $@
	ln -sf $(ROOT_DIR)/zones/$@ .

.PHONY: censored-domains-over-time-all.pdf
censored-domains-over-time-all.pdf:
	make -C $(ROOT_DIR)/daily-total-and-churn $@
	ln -sf $(ROOT_DIR)/daily-total-and-churn/$@ .

.PHONY: henan-categorized.pdf
henan-categorized.pdf:
	make -C $(ROOT_DIR)/categorization $@
	ln -sf $(ROOT_DIR)/categorization/$@ .

.PHONY: gfw-categorized.pdf
gfw-categorized.pdf:
	make -C $(ROOT_DIR)/categorization $@
	ln -sf $(ROOT_DIR)/categorization/$@ .

.PHONY: rule-extraction.pdf
rule-extraction.pdf:
	make -C $(ROOT_DIR)/rule-extraction $@
	ln -sf $(ROOT_DIR)/rule-extraction/$@ .

.PHONY: client-to-sink-server-data-matrix.pdf
client-to-sink-server-data-matrix.pdf:
	make -C $(ROOT_DIR)/confirmation $@
	ln -sf $(ROOT_DIR)/confirmation/$@ .

.PHONY: header-length.pdf
header-length.pdf:
	make -C $(ROOT_DIR)/header-length $@
	ln -sf $(ROOT_DIR)/header-length/$@ .

.PHONY: cdf-censored-duration-both.pdf
cdf-censored-duration-both.pdf:
	make -C $(ROOT_DIR)/censorship-duration $@
	ln -sf $(ROOT_DIR)/censorship-duration/$@ .

.PHONY: clean
clean:
	for file in $(ALL); do \
		if [ -h "$$file" ]; then \
			rm -f `readlink -f $$file`; \
			rm -f $$file; \
		fi; \
	done

.DELETE_ON_ERROR:
