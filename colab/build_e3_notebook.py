#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e3_calibration_residual.ipynb depuis e3_calibration_residual.py.

E3 etait un script, ce qui obligeait a le deposer sur Colab avant de pouvoir
l'appeler. C'est une marche de trop. Le notebook contient le meme code et se
lance comme E1 et E2.

Relancer ce script apres toute modification du .py.
"""
import json
from pathlib import Path

VERSION = "v2"
BUILD = "2026-08-13"
HERE = Path(__file__).resolve().parent
SRC = (HERE / "e3_calibration_residual.py").read_text(encoding="utf-8")
CORPS = SRC[SRC.index("def ece("):SRC.index("def main():")].rstrip()

CELLS = []
md = lambda s: CELLS.append({"cell_type": "markdown", "metadata": {},
                             "source": s.strip("\n").split("\n")})
code = lambda s: CELLS.append({"cell_type": "code", "execution_count": None,
                               "metadata": {}, "outputs": [],
                               "source": s.strip("\n").split("\n")})

md(f"""
# E3 : calibration sous les deux protocoles, et audit résiduel

> **Notebook {VERSION}, compilé le {BUILD}.** La cellule 1 réaffiche ce numéro.

**Où le lancer.** Ici, dans Colab, comme E1 et E2. La version précédente était un
script `.py`, ce qui obligeait à le déposer sur la machine avant de pouvoir l'appeler :
c'est ce qui échouait. Il n'y a plus de fichier à déposer.

**Aucun réentraînement.** Tout se calcule depuis ce que le pipeline a déjà écrit.

| Partie | Ce qu'elle mesure | Ce qu'elle lit |
|---|---|---|
| A | ECE, Brier, température et diagramme de fiabilité, sous le protocole **stratifié et temporel** | `probs/`, `frozen_splits_60s.npz`, `cache/slice60.npz` |
| B | corrélation, information mutuelle et doublons **entre** les 55 colonnes retenues | `cache/slice60.npz` |

**Pourquoi ces deux mesures.** « Calibration » figure dans le titre de l'article et n'est
mesurée que sous un protocole. Et le balayage mono-feature dit que chaque colonne retenue
prise **seule** ne porte pas de raccourci, sans rien dire de la redondance **entre** elles,
qui est précisément le mécanisme que l'article accuse l'attribution de manquer.

**Durée.** Quelques minutes. Aucun GPU nécessaire.
""")

code(r"""
# --- 1. Drive et verification des entrees ----------------------------------
E3_VERSION = "VERSION_PLACEHOLDER"; E3_BUILD = "BUILD_PLACEHOLDER"
print(f"E3 notebook {E3_VERSION}, compile le {E3_BUILD}\n")
import pathlib, json
from google.colab import drive
drive.mount("/content/drive")

SAVE = pathlib.Path("/content/drive/MyDrive/GeNIS/article1_final")

ATTENDU = {
    "article1_results.json": "les resultats de la campagne",
    "frozen_splits_60s.npz": "les indices de decoupage geles",
    "cache/slice60.npz":     "les etiquettes et la matrice de features",
    "cache/slice60_meta.json": "les noms de colonnes",
    "probs":                 "les probabilites par run",
}
print("=" * 70)
print(f"ENTREES SOUS {SAVE}")
print("=" * 70)
manque = []
for rel, quoi in ATTENDU.items():
    p = SAVE / rel
    if p.exists():
        n = len(list(p.glob("*.npz"))) if p.is_dir() else 1
        taille = (sum(f.stat().st_size for f in p.rglob("*")) if p.is_dir()
                  else p.stat().st_size) / 1e6
        print(f"   OK      {rel:<26} {n:>4} fichier(s)  {taille:8.1f} Mo   {quoi}")
    else:
        manque.append(rel)
        print(f"   ABSENT  {rel:<26} {'':>18}   {quoi}")

if manque:
    print("\n>>> Ce qui manque limite ce qui est calculable :")
    if "probs" in manque or "frozen_splits_60s.npz" in manque:
        print("    la partie A (calibration) sera sautee")
    if "cache/slice60.npz" in manque:
        print("    les parties A ET B seront sautees : le cache porte les etiquettes")
    print("\n    Ces fichiers sont produits par article1_pipeline.ipynb et vivent")
    print("    dans MyDrive/GeNIS/article1_final/. Si le dossier a ete deplace,")
    print("    corrigez SAVE ci-dessus.")
else:
    print("\n>>> tout est present, les deux parties sont calculables")
""")

code("# --- 2. Fonctions ----------------------------------------------------------\n"
     "import re, sys\nimport numpy as np\n\nW_IN, DPI = 6.698, 400\nBINS = 15\n\n"
     + CORPS)

md("""
## Partie A : calibration sous les deux protocoles

Le calage de température s'ajuste sur les probabilités de **validation** et s'évalue sur
celles de **test**, exactement comme dans le pipeline. Les deux protocoles sont traités de
la même façon, ce qui rend la comparaison lisible.

**Contrôle à faire en premier** : la colonne `strat_seed1` doit reproduire le Tableau 6 du
manuscrit. Si elle s'en écarte nettement, c'est que l'aller-retour par le logarithme des
probabilités stockées en float16 perd trop de précision, et il faudra faire réémettre les
logits par le pipeline plutôt que publier des valeurs dégradées.
""")

code(r"""
res = {"source": str(SAVE)}
partie_calibration(SAVE, res)
""")

md("""
## Partie B : audit résiduel conjoint

Ce que le balayage mono-feature ne dit pas. Un doublon exact parmi les colonnes **retenues**
serait un raccourci redondant que l'audit a laissé passer : c'est le contrôle qui ferme la
boucle de la contribution centrale de l'article.
""")

code(r"""
partie_residuel(SAVE, res)
""")

code(r"""
# --- Export ----------------------------------------------------------------
out = SAVE / "e3_results.json"
out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float),
               encoding="utf-8")
print("ecrit :", out)
print(f"   parties presentes : {', '.join(k for k in res if k != 'source')}")
print("\nA me renvoyer : e3_results.json")
""")

nb = {"cells": [dict(c, source=[l.replace("VERSION_PLACEHOLDER", VERSION)
                                .replace("BUILD_PLACEHOLDER", BUILD) for l in c["source"]])
                for c in CELLS],
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True}},
      "nbformat": 4, "nbformat_minor": 0}

out = HERE / f"e3_calibration_residual_{VERSION}.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{out.name} : {len(CELLS)} cellules "
      f"({sum(1 for c in CELLS if c['cell_type'] == 'code')} de code)")
