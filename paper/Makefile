PDFLATEX = pdflatex -halt-on-error -file-line-error -interaction=nonstopmode -synctex=1
PDFLATEX_FAST = pdflatex -draftmode -halt-on-error -file-line-error -interaction=nonstopmode
BIBTEX = bibtex

ROOT_DIR = ..

MAIN = main
SUBMISSION = submission
DIFF = diff

#FIGURES = figures/*.pdf figures/*.tex

$(MAIN).pdf: \
	$(MAIN).tex preamble.tex \
	$(MAIN).bib censor.bib $(FIGURES) \
	IEEEtran.cls

%.pdf: %.tex
	rm -f "$*.aux" "$*.bbl"
	$(PDFLATEX) -draftmode "$*"
	$(BIBTEX) "$*"
	$(PDFLATEX) -draftmode "$*"
	$(PDFLATEX) "$*"
	

# Generate a diff.tex file using latexdiff
$(DIFF).tex: $(SUBMISSION).tex $(MAIN).tex
	latexdiff --exclude-textcmd="caption" $(SUBMISSION).tex $(MAIN).tex | \
	sed '/\\RequirePackage\[normalem\]{ulem}/d' > $(DIFF).tex


# Compile the diff file to PDF
$(DIFF).pdf: $(DIFF).tex $(MAIN).bib censor.bib
	rm -f "$(DIFF).aux" "$(DIFF).bbl"
	$(PDFLATEX_FAST) $(DIFF)
	$(BIBTEX) $(DIFF)
	$(PDFLATEX_FAST) $(DIFF)
	$(PDFLATEX) $(DIFF)


censor.bib:
	wget -O $@ "https://raw.githubusercontent.com/NullHypothesis/censorbib/refs/heads/master/references.bib"

figures/*.pdf:
	make -C figures

figures/*.tex:
	make -C figures

.PHONY: clean
clean:
	rm -rf $(addprefix main,.aux .ent .log .pdf .bbl .blg .out)
	rm -rf $(addprefix diff,.aux .log .pdf .out .toc .tex)

.DELETE_ON_ERROR:
