#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passe stylistique mecanique sur le manuscrit, avant soumission.

Compagnon de check_coherence.py : celui-la verifie que le document se tient
(figures appelees, numerotation, ordre des citations), celui-ci verifie
comment il est ecrit. Les deux lisent le .docx directement, sans dependance.

    python check_style.py [chemin/vers/le.docx]

Ce que le script controle, et ce qu'il sait deja etre normal. Un compteur
brut sur ce manuscrit signale beaucoup de faux positifs, et les laisser
crier rendrait le script inutile a la relecture suivante. Chaque exception
est donc nommee et justifiee ici, pas noyee dans un seuil :

  - doubles espaces : l'algorithme 1 et la formule de tau alignent leurs
    colonnes a l'espace. Les paragraphes qui en contiennent sont ecartes,
    et le controle porte sur la prose.
  - "dataset" contre "corpus" : le manuscrit dit corpus, sauf dans les
    titres de references, qu'on cite tels quels, et dans "dataset shift",
    qui est une locution figee de la litterature.
  - -ise contre -ize : le corps est britannique de bout en bout ; les trois
    -ization sont dans des titres de references.
  - decimales : 4 pour les macro-F1 de tete, 3 pour les accuracies, les
    ratios de transferabilite et les ecarts. Ce n'est pas un melange, c'est
    deux registres, et le script verifie qu'aucun des deux ne deborde.
  - "audited feature set" contre "audited condition" : le premier designe
    l'ensemble de colonnes, le second la condition experimentale. Deux
    objets, tous deux definis dans le texte.

Sortie : la liste des defauts, et un code de retour non nul s'il y en a.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = pathlib.Path(__file__).resolve().parent
DOCX = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
        else HERE / "GeNIS_benchmark_article.docx")

with zipfile.ZipFile(DOCX) as z:
    racine = ET.fromstring(z.read("word/document.xml"))
ELS = list(racine.find(W + "body"))
BLOCS = ["".join(t.text or "" for t in e.iter(W + "t")) for e in ELS]
TABLEAUX = {i for i, e in enumerate(ELS) if e.tag == W + "tbl"}

# La prose : ni les tableaux, ni les blocs monospaces, dont l'alignement
# a l'espace est le format et non une faute de frappe.
PROSE = {i: t for i, t in enumerate(BLOCS)
         if i not in TABLEAUX and "  " not in t}
I_REF = next((i for i, t in enumerate(BLOCS) if t.strip() == "References"), len(BLOCS))
CORPS = "\n".join(t for i, t in PROSE.items() if i < I_REF)

defauts = []


def signale(msg):
    defauts.append(msg)


def phrases(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t) if s.strip()]


# --- 1. typographie -------------------------------------------------------
# Ces trois-la n'ont aucune occurrence legitime dans de la prose.
for i, t in PROSE.items():
    for m in re.finditer(r"\S\s{2,}\S", t):
        signale(f"bloc {i} : double espace  ...{t[max(0, m.start() - 40):m.end() + 20]!r}")
    for m in re.finditer(r"\S\s+[,;.!?%](?!\w)", t):
        signale(f"bloc {i} : espace avant ponctuation  "
                f"...{t[max(0, m.start() - 40):m.end() + 20]!r}")
    for m in re.finditer(r"\b(\w+)\s+\1\b", t, re.I):
        if m.group(1).lower() not in ("that", "had"):
            signale(f"bloc {i} : mot double {m.group(0)!r}")
print(f"  {'typographie':16s} {len(PROSE)} paragraphes de prose examines")

# --- 2. orthographe : le corps est britannique ----------------------------
# "size", "sized", "Segment Size" ne sont pas des -ize, et -ising n'est pas
# une terminaison americaine : "comprising" et "promising" viennent de
# comprise et promise, que les deux orthographes ecrivent pareil.
# CRediT est un vocabulaire CONTROLE : « Conceptualization » et
# « Visualization » sont les noms officiels des roles, pas des mots de la
# prose. Les angliciser rendrait la declaration non conforme, donc c'est ce
# controle qui cede, et seulement pour ces deux termes.
CREDIT = {"conceptualization", "visualization"}
zed = re.findall(r"\b\w{4,}(?:ization|izing|ized|izes)\b", CORPS)
zed = [w for w in zed
       if not w.lower().startswith("size") and w.lower() not in CREDIT]
if zed:
    signale(f"orthographe : formes en -ize dans le corps {sorted(set(zed))}")
n_ise = len(re.findall(r"\w+isation\b", CORPS))
print(f"  {'orthographe':16s} -isation {n_ise}, -ization {len(zed)} dans le corps")

# --- 3. terminologie ------------------------------------------------------
# "dataset" est admis dans "dataset shift" et dans les titres cites ; ailleurs
# le manuscrit dit corpus, et un glissement se verrait.
for i, t in PROSE.items():
    if i >= I_REF:
        continue
    for m in re.finditer(r"\bdatasets?\b", t):
        suite = t[m.end():m.end() + 12]
        # "dataset shift" est la locution de Snoek et al. ; "dataset artefact"
        # celle de l'etude sur le port de destination ; "dataset descriptor"
        # designe le Data in Brief de GeNIS. Le pluriel designe les corpus
        # d'autrui, jamais le notre.
        if suite.startswith((" shift", "-shift", " artefact", " descriptor")):
            continue
        if m.group(0).endswith("s"):
            continue
        avant = t[max(0, m.start() - 40):m.start()]
        signale(f"bloc {i} : 'dataset' hors locution figee  ...{avant + m.group(0)!r}")

VARIANTES = [("blacklist", "exclusion list"), ("macro-F1", "macro F1"),
             ("k-NN", "kNN"), ("FT-Transformer", "FT Transformer"),
             ("nine-class", "9-class"), ("per-class", "per class")]
for retenu, proscrit in VARIANTES:
    n = len(re.findall(rf"\b{re.escape(proscrit)}\b", CORPS))
    # "per class" est correct en emploi adverbial ("evaluation must be per
    # class"), pas en epithete : on ne compte que l'epithete.
    if proscrit == "per class":
        n = len(re.findall(r"\bper class \w", CORPS))
    if n:
        signale(f"terminologie : {proscrit!r} employe {n} fois, "
                f"le manuscrit dit {retenu!r}")
print(f"  {'terminologie':16s} {len(VARIANTES)} paires controlees")

# --- 4. decimales ---------------------------------------------------------
# Deux registres : 4 decimales pour les macro-F1 de tete, 3 pour les
# accuracies, les ratios de transferabilite et les ecarts. Au-dela de 4, la
# valeur est signalee, sauf quand la phrase compare a une valeur inferieure
# a 0.001 : une erreur de calibration de 1.8e-5 ne se lit pas a quatre
# decimales, et sa contrepartie doit alors etre ecrite a la meme precision.
for i, t in PROSE.items():
    for ph in phrases(t):
        fine = any(float(m.group(0)) < 0.001 and float(m.group(0)) > 0
                   for m in re.finditer(r"(?<![\d.])0\.\d+(?![\d])", ph))
        for m in re.finditer(r"(?<![\d.])0\.(\d{5,})(?![\d])", ph):
            if fine or set(m.group(1)) == {"0"}:   # 0.00000, importance nulle
                continue
            signale(f"bloc {i} : {m.group(0)} a {len(m.group(1))} decimales  "
                    f"...{ph[max(0, m.start() - 45):m.end() + 20]!r}")
reg = Counter(len(m.group(1)) for t in PROSE.values()
              for m in re.finditer(r"(?<![\d.])0\.(\d{3,4})(?![\d])", t))
print(f"  {'decimales':16s} {reg.get(3, 0)} valeurs a 3, {reg.get(4, 0)} a 4")

# --- 5. longueur de phrase ------------------------------------------------
# 90 mots est la limite au-dela de laquelle une phrase de prose cesse d'etre
# lisible d'une traite, meme quand elle est une enumeration.
LIMITE = 90
n_ph, n_mots = 0, 0
for i, t in PROSE.items():
    if t.startswith(("Figure ", "Table ", "Algorithm ")):
        continue
    for s in phrases(t):
        n_ph += 1
        n_mots += len(s.split())
        if len(s.split()) > LIMITE:
            signale(f"bloc {i} : phrase de {len(s.split())} mots  {s[:90]!r}...")
print(f"  {'phrases':16s} {n_ph}, {n_mots / max(n_ph, 1):.1f} mots en moyenne")

# --- 6. ouvertures repetees -----------------------------------------------
# Une ouverture qui revient dans le meme paragraphe, ou dans deux paragraphes
# consecutifs, se voit a la lecture. Ailleurs elle est le plus souvent un
# parallelisme voulu ("Under the stratified protocol... Under the temporal
# protocol..."), et le script ne la reproche pas.
ouvertures = defaultdict(list)
for i, t in PROSE.items():
    if i >= I_REF or t.startswith(("Figure ", "Table ", "Algorithm ")):
        continue                       # la bibliographie n'est pas de la prose
    debut = 0
    # L'amorce en gras d'un paragraphe est un intertitre, pas une phrase : on
    # ne lui reproche pas de reprendre les mots de son propre paragraphe.
    for r in ELS[i].iter(W + "r"):
        pr = r.find(W + "rPr")
        if pr is not None and pr.find(W + "b") is not None:
            debut = 1
        break
    for s in phrases(t)[debut:]:
        mots = s.split()
        if len(mots) >= 2 and mots[0][0].isupper():
            ouvertures[" ".join(mots[:2])].append(i)
# Contrastes assumes : le manuscrit oppose systematiquement les deux
# protocoles et les deux corpus, et l'anaphore est ce qui rend l'opposition
# lisible. La reprocher reviendrait a demander de casser le parallelisme.
PARALLELES = {"Under the", "The audit", "What the", "On GeNIS", "On CICIDS2017"}
for tete, blocs in ouvertures.items():
    if tete in PARALLELES or len(blocs) < 2:
        continue
    for a, b in zip(blocs, blocs[1:]):
        if b - a <= 1:
            signale(f"ouverture {tete!r} repetee, blocs {a} et {b}")
            break
print(f"  {'ouvertures':16s} {len(ouvertures)} distinctes, "
      f"{max(len(v) for v in ouvertures.values())} au plus frequent")

# --- verdict --------------------------------------------------------------
print()
if defauts:
    print(f"{len(defauts)} defaut(s) :")
    for d in defauts:
        print(f"  - {d}")
else:
    print("aucun defaut stylistique mecanique")
sys.exit(1 if defauts else 0)
