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

Les DOI sont déjà renseignés. Le dépôt Zenodo est publié depuis le 13 août 2026 :
DOI de concept `10.5281/zenodo.21910662`, cité par la section 10, et version 1.0.0
`10.5281/zenodo.21910663`.

**Attention** : la v1.0.0 en ligne ne contient pas cette arborescence. Elle a été
montée à la main en deux zips, `article1_final.zip` et `models.zip`, sans MANIFEST
ni README ni clone du dépôt. Zenodo interdisant de modifier des fichiers publiés,
déposer le zip que produit cette cellule créerait une **v2** avec un nouveau DOI de
version. Le DOI de concept, lui, suivrait automatiquement. Voir `ARCHIVE_README.md`
dans le dépôt pour ce que contient réellement la v1.0.0.
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

# DOI de concept : ne bouge jamais, c'est celui que cite la section 10.
ARCHIVE_DOI = "10.5281/zenodo.21910662"
# DOI de la version que ce zip deviendrait. La v1.0.0 publiee le 13 aout 2026
# est 10.5281/zenodo.21910663 et ne contient PAS cette arborescence : elle a
# ete montee a la main en deux zips. Zenodo interdit de modifier des fichiers
# publies, donc deposer ceci ferait une v2 avec un nouveau DOI de version.
ARCHIVE_VERSION_DOI = "[attribue a la publication de cette version]"
INCLUDE_CODE = True     # clone le depot GitHub dans code/
INCLUDE_E1   = True     # ajoute supplementary/ si le notebook E1 a tourne
DRY_RUN      = False    # True : affiche le plan sans rien copier

import argparse, hashlib, json, pathlib, shutil, time

{coeur}

_save = SAVE if "SAVE" in dir() else pathlib.Path(
    "/content/drive/MyDrive/GeNIS/article1_final")
_out = pathlib.Path("/content/zenodo"); _out.mkdir(parents=True, exist_ok=True)

_zip = build_archive(_save, _out, archive_doi=ARCHIVE_DOI,
                     version_doi=ARCHIVE_VERSION_DOI,
                     include_code=INCLUDE_CODE, include_e1=INCLUDE_E1,
                     dry_run=DRY_RUN)

if _zip:
    # copie sur Drive : le disque de la VM ne survit pas a la deconnexion
    _dest = pathlib.Path(_save).parent / pathlib.Path(_zip).name
    shutil.copy2(_zip, _dest)
    print(f"\\ncopie sur Drive : {{_dest}}")
    print("\\nEtapes suivantes :")
    print("  1. telecharger ce zip depuis Drive")
    print("  2. sur zenodo.org, ouvrir le record 10.5281/zenodo.21910663")
    print("     puis 'New version' : les fichiers publies ne sont pas modifiables")
    print("  3. deposer ce zip, publier ; un nouveau DOI de version est attribue")
    print("  4. le DOI de concept 10.5281/zenodo.21910662, cite par la section 10,")
    print("     pointera automatiquement vers cette nouvelle version")
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
