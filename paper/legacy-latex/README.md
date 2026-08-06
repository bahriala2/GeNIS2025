# Chaîne LaTeX : archivée

Le fichier Word `paper/GeNIS_benchmark_article.docx` est la **source unique** de
l'article depuis août 2026. Ce dossier conserve la chaîne LaTeX telle qu'elle était
au moment de l'abandon, et **elle n'est plus tenue à jour** : `main.tex` s'arrête à
9 figures et 8 tables, alors que le Word en compte 13 et 11, et il ignore la
normalisation corrigée du hasard (τ*), les tables 10 et 11, et la déclaration
d'usage de l'IA générative.

| Fichier | Rôle |
|---|---|
| `main.tex` | Article, format elsarticle (état gelé, obsolète) |
| `main.bbl`, `references.bib` | Bibliographie à 25 entrées (le Word en a 27) |
| `tables/` | Fragments de tableaux LaTeX |
| `figures/` | Versions PDF des figures, pour `\includegraphics` |
| `main.pdf` | Dernier PDF compilé (41 pages) |
| `regenerate_tables.py` | Régénérait les fragments depuis `article1_results.json` |

Ne rien reprendre d'ici sans comparer au Word : les chiffres et les formulations
ont divergé.
