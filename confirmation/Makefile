PYTHON = python3

ALL = \
	client-to-sink-server-data-matrix.pdf\
	only-censored-inside-out.txt\
	only-censored-outside-in.txt \
	data.csv \



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

client-to-sink-server-data-matrix.pdf: confirmation-heatmap.py data.csv
	$(PYTHON) $^ --out "$@"

data.csv: ./to_generate_matrix_data.sh 
	./to_generate_matrix_data.sh ./data > "$@"

./data/inside-out.sorted.txt: ./data/inside-out.txt
	sort $^ > $@

./data/outside-in.sorted.txt: ./data/outside-in.txt
	sort $^ > $@

only-censored-inside-out.txt: ./data/inside-out.sorted.txt ./data/outside-in.sorted.txt
	comm -23 $^ > $@

only-censored-outside-in.txt: ./data/inside-out.sorted.txt ./data/outside-in.sorted.txt
	comm -13 $^ > $@

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: