# Article 1 — GeNIS 2025
# make pdf   : compile main.pdf (pdflatex + bibtex, 3 passes)
# make docx  : construit la version Word NATIVE (docx-js, sans pandoc)
#              tex2struct.py extrait la structure, build_docx.js ecrit l'OOXML
# make all   : les deux
# make clean : supprime les fichiers intermediaires

.PHONY: all pdf docx preview clean check

all: pdf docx

pdf: main.pdf

main.pdf: main.tex references.bib $(wildcard tables/*.tex) $(wildcard figures/*.pdf)
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

docx: GeNIS_benchmark_article.docx

GeNIS_benchmark_article.docx: content.json build_docx.js $(wildcard figures/*.png)
	node build_docx.js

content.json: main.tex main.bbl tex2struct.py $(wildcard tables/*.tex)
	python3 tex2struct.py

# rendu de controle : convertit le .docx en PDF puis en images de pages
preview: GeNIS_benchmark_article.docx
	soffice --headless --norestore --convert-to pdf GeNIS_benchmark_article.docx
	pdftoppm -jpeg -r 80 GeNIS_benchmark_article.pdf page

check: main.pdf
	@echo "erreurs   : $$(grep -c '^! ' main.log)"
	@echo "overfull  : $$(grep -c 'Overfull .hbox' main.log)"
	@echo "cite/ref  : $$(grep -cE 'LaTeX Warning: (Citation|Reference)' main.log)"

clean:
	rm -f main.aux main.log main.out main.blg main.bbl main_word.tex
	rm -f GeNIS_benchmark_article.pdf page-*.jpg
