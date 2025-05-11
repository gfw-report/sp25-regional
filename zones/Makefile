PYTHON = python3
SHELL = /bin/bash

DATA_FOLDER ?= ./data


# Final target files
ALL = \
	venn-diagram-accumulated.pdf \
	./data/henan-zone-files-blocklist.txt \
	./data/gfw-zone-files-blocklist.txt \
	./data/henan-zone-files-blocklist.txt.xz \
	./data/gfw-zone-files-blocklist.txt.xz



.PHONY: all
all: $(ALL)

./data/henan-zone-files-blocklist.txt.xz: ./data/test-2023-52-2024-07-weekly/zones-censored-sni-guangzhou*.txt ./data/test-2024-11-2025-04-monthly/zones-censored-sni_guangzhou*.txt
	sort -u  $^ | xz - > $@

./data/gfw-zone-files-blocklist.txt.xz: ./data/test-2023-52-2024-07-weekly/zones-censored-sni-california*.txt ./data/test-2024-11-2025-04-monthly/zones-censored-sni_california*.txt
	sort -u $^ | xz - > $@

./data/henan-zone-files-blocklist.txt: ./data/henan-zone-files-blocklist.txt.xz
		xzcat $< > $@

./data/gfw-zone-files-blocklist.txt: ./data/gfw-zone-files-blocklist.txt.xz
		xzcat $< > $@

venn-diagram-accumulated.pdf: ../util/graphs/venn_diagram.py  ./data/henan-zone-files-blocklist.txt ./data/gfw-zone-files-blocklist.txt
		$(PYTHON) $(word 1,$^) --gfw ./data/gfw-zone-files-blocklist.txt --henan ./data/henan-zone-files-blocklist.txt --out venn-diagram-accumulated.pdf --no-show;

.PHONY: clean
clean:
		rm -f $(ALL)
