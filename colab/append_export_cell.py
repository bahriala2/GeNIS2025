#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Insere (ou remplace) la cellule d'export Zenodo a la fin de article1_pipeline.ipynb.

Le corps de la cellule est construit a partir de zenodo_export_cell.py, pour
qu'il n'existe qu'une seule source. Relancer ce script apres toute modification
de ce fichier.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
NB = HERE / "article1_pipeline.ipynb"
SRC = HERE / "zenodo_export_cell.py"
MARKER = "# 8.1 - Archive Zenodo"

MD = """
## 8. Archive Zenodo

Ce que la section 10 de l'article promet, rassemble en une arborescence unique,
avec le README que les relecteurs ouvrent en premier et un MANIFEST qui donne
pour chaque fichier sa taille, son empreinte SHA-256 et la cellule qui l'a
produit.

À lancer **une fois la campagne terminée**. La cellule affiche d'abord le plan et
les tailles, puis copie. Mettre `DRY_RUN = True` pour ne voir que le plan.

Deux exclusions volontaires : le cache `slice60.npz`, qui est une copie dérivée
du corpus et que les indices de découpage régénèrent, et le corpus lui-même,
déjà archivé sous `doi:10.5281/zenodo.14919237`.

Réservez le DOI sur Zenodo avant de lancer (*New upload* puis **Reserve DOI**) et
reportez-le dans `ARCHIVE_DOI` : il sera écrit dans le README de l'archive.
"""


def body():
    """Extrait de zenodo_export_cell.py ce qui doit vivre dans la cellule."""
    src = SRC.read_text(encoding="utf-8")
    debut = src.index("README = r\"\"\"")
    fin = src.index("def main():")
    coeur = src[debut:fin].rstrip()
    return f"""{MARKER} -------------------------------------------------
# Source : colab/zenodo_export_cell.py dans le depot. Ne pas editer ici,
# editer le fichier puis relancer colab/append_export_cell.py.

ARCHIVE_DOI = "[A COMPLETER : DOI reserve sur Zenodo]"
INCLUDE_CODE = True     # clone le depot GitHub dans code/
INCLUDE_E1   = True     # ajoute supplementary/ si le notebook E1 a tourne
DRY_RUN      = False    # True : affiche le plan sans rien copier

import argparse, hashlib, json, pathlib, shutil, time

{coeur}

_save = SAVE if "SAVE" in dir() else pathlib.Path(
    "/content/drive/MyDrive/GeNIS/article1_final")
_out = pathlib.Path("/content/zenodo"); _out.mkdir(parents=True, exist_ok=True)

_zip = build_archive(_save, _out, archive_doi=ARCHIVE_DOI,
                     include_code=INCLUDE_CODE, include_e1=INCLUDE_E1,
                     dry_run=DRY_RUN)

if _zip:
    # copie sur Drive : le disque de la VM ne survit pas a la deconnexion
    _dest = pathlib.Path(_save).parent / pathlib.Path(_zip).name
    shutil.copy2(_zip, _dest)
    print(f"\\ncopie sur Drive : {{_dest}}")
    print("\\nEtapes suivantes :")
    print("  1. telecharger ce zip depuis Drive")
    print("  2. le deposer sur le brouillon Zenodo ou le DOI a ete reserve")
    print("  3. auteurs avec ORCID, licence, type Software, related identifier")
    print("     'is supplement to' vers l'article une fois qu'il a un DOI")
    print("  4. publier AVANT la soumission : un DOI reserve n'est enregistre")
    print("     qu'a la publication du depot")
"""


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"]
             if not (c["cell_type"] == "code" and MARKER in "".join(c["source"]))
             and not (c["cell_type"] == "markdown" and "## 8. Archive Zenodo" in "".join(c["source"]))]
    retires = len(nb["cells"]) - len(cells)

    cells.append({"cell_type": "markdown", "metadata": {},
                  "source": MD.strip("\n").split("\n")})
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": body().strip("\n").split("\n")})
    nb["cells"] = cells
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{retires} ancienne(s) cellule(s) remplacee(s)")
    print(f"{len(cells)} cellules, la cellule d'export est la derniere")


if __name__ == "__main__":
    main()
