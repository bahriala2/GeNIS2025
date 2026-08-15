# Article 1 — GeNIS 2025
# La source de l'article est GeNIS_benchmark_article.docx (Word natif).
# La chaîne LaTeX est archivée dans legacy-latex/ et n'est plus maintenue.
#
#   make preview  : rend le .docx en PDF puis en images de pages, pour relecture
#   make figures  : régénère les figures depuis article1_results.json
#   make clean    : supprime les fichiers de rendu

DOCX = GeNIS_benchmark_article.docx

.PHONY: preview figures clean

preview: $(DOCX)
	soffice --headless --norestore --convert-to pdf $(DOCX)
	pdftoppm -jpeg -r 80 $(basename $(DOCX)).pdf page
	@echo "pages rendues : $$(ls page-*.jpg | wc -l)"

figures:
	python3 regen_en.py
	python3 regen_fig6.py
	python3 regen_fig13_cicids2017.py

clean:
	rm -f $(basename $(DOCX)).pdf page-*.jpg
