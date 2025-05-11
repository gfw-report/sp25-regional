PYTHON = python3


CITIES := california guangzhou

DATA_FOLDER ?= ./data
DATES := $(shell ls $(DATA_FOLDER) | grep -oE '\d{4}-\d{2}-\d{2}' | sort -u)

# Aggregate files for each date
AGGREGATED_FILES := $(foreach city,$(CITIES),$(foreach date,$(DATES),$(DATA_FOLDER)/aggregated_$(city)_$(date).csv))
# AGGREGATED_FILES := $(foreach date,$(DATES),$(DATA_FOLDER)/aggregated_$(date).csv)

# Files to generate after processing
PROCESSED_FILES := $(AGGREGATED_FILES:$(DATA_FOLDER)/aggregated_%.csv=censored-block-rules-%.txt) rule-extraction.pdf

# Final target files
ALL := $(PROCESSED_FILES) \
		gfw-rule-count.tsv \
		henan-rule-count.tsv \

.PHONY: all
all: $(ALL)

# Rule to aggregate files
$(DATA_FOLDER)/aggregated_%.csv:
		@echo Aggregating files for $*
		@{ \
				set -e; \
				date=$$(echo $* | cut -d '_' -f2); \
				city=$$(echo $* | cut -d '_' -f1); \
				echo "Date: $$date"; \
				file_pattern="$(DATA_FOLDER)/1m_sni_block_rules_"$$date"_*_$$city.csv"; \
				echo "File pattern: $$file_pattern"; \
				for file in $$file_pattern; do \
						if [ -f "$$file" ]; then \
								echo "Concatenating file: $$file"; \
								cat "$$file" >> $@; \
						else \
								echo "No files found matching $$file_pattern"; \
								echo "" >> $@; \
						fi; \
				done; \
		}

# Rule for processing aggregated files
censored-block-rules-%.txt: $(DATA_FOLDER)/aggregated_%.csv
		grep TLS,EOF $< | cut -d, -f2 | sort -u > "$(DATA_FOLDER)/$@"

rule-extraction.pdf: ./results/censored-block-rules-guangzhou*.txt ./results/censored-block-rules-california*.txt
	$(PYTHON) plot.py --no-show --guangzhou './results/censored-block-rules-guangzhou*.txt' --california './results/censored-block-rules-california*.txt' --out "$@"

gfw-rule-count.tsv: analysis.py results/censored-block-rules-california_*_result.txt
	$(PYTHON) $^ > "$@"

henan-rule-count.tsv: analysis.py results/censored-block-rules-guangzhou_*_result.txt
	$(PYTHON) $^ > "$@"

.PHONY: clean
clean:
		rm -f $(AGGREGATED_FILES) $(PROCESSED_FILES)

.DELETE_ON_ERROR:
