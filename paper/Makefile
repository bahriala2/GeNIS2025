# Article 1 — GeNIS 2025
# make pdf   : compile main.pdf (pdflatex + bibtex, 3 passes)
# make docx  : construit la version Word a partir de main.tex + main.bbl
# make all   : les deux
# make clean : supprime les fichiers intermediaires

.PHONY: all pdf docx clean check

all: pdf docx

pdf: main.pdf

main.pdf: main.tex references.bib $(wildcard tables/*.tex) $(wildcard figures/*.pdf)
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

docx: GeNIS_benchmark_article.docx

GeNIS_benchmark_article.docx: main.tex main.bbl make_docx.py
	python3 make_docx.py

check: main.pdf
	@echo "erreurs   : $$(grep -c '^! ' main.log)"
	@echo "overfull  : $$(grep -c 'Overfull .hbox' main.log)"
	@echo "cite/ref  : $$(grep -cE 'LaTeX Warning: (Citation|Reference)' main.log)"

clean:
	rm -f main.aux main.log main.out main.blg main.bbl main_word.tex
