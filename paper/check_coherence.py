#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle de coherence interne du manuscrit, avant soumission.

Ce que ce script attrape, et qu'une relecture humaine laisse passer :

  - une figure ou un tableau dont la legende existe mais qu'aucune phrase
    n'appelle. C'est arrive : la figure 4 est entree dans le document sans
    qu'aucun paragraphe ne la convoque, et personne ne l'a vu en relisant.
  - une numerotation qui saute un rang, ou deux legendes portant le meme
    numero, ce qui arrive apres toute renumerotation.
  - un objet dont la legende precede de loin sa premiere citation.
  - un ordre de premiere citation bibliographique qui n'est pas croissant,
    ce que le style numerique d'Elsevier impose.
  - une reference jamais citee, ou une citation sans reference.

Le script lit le .docx directement, sans dependance : il decompresse
word/document.xml et le parcourt.

    python check_coherence.py [chemin/vers/le.docx]

Sortie : la liste des anomalies, et un code de retour non nul s'il y en a.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = pathlib.Path(__file__).resolve().parent
DOCX = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "GeNIS_benchmark_article.docx"

with zipfile.ZipFile(DOCX) as z:
    racine = ET.fromstring(z.read("word/document.xml"))
corps = racine.find(W + "body")
BLOCS = ["".join(t.text or "" for t in e.iter(W + "t")) for e in corps]
TEXTE = " ".join(BLOCS)

anomalies = []


def signale(msg):
    anomalies.append(msg)


# --- 1. figures et tableaux ----------------------------------------------
# "Figure 17a" est une citation de la figure 17 : le suffixe de panneau ne
# doit pas empecher la detection, faute de quoi on croit la figure orpheline.
for genre in ("Figure", "Table", "Algorithm"):
    legendes, citations = {}, {}
    for i, t in enumerate(BLOCS):
        m = re.match(rf"{genre} (\d+)\.", t)
        if m:
            n = int(m.group(1))
            if n in legendes:
                signale(f"{genre} {n} : deux legendes (blocs {legendes[n]} et {i})")
            legendes[n] = i
        for m in re.finditer(rf"\b{genre} (\d+)[a-z]?\b", t):
            n = int(m.group(1))
            if not re.match(rf"{genre} {n}\.", t):
                citations.setdefault(n, i)

    if not legendes:
        continue
    attendu = list(range(1, max(legendes) + 1))
    manquants = [n for n in attendu if n not in legendes]
    if manquants:
        signale(f"{genre} : numeros sans legende {manquants}")
    ordre = [legendes[n] for n in sorted(legendes)]
    if ordre != sorted(ordre):
        signale(f"{genre} : les legendes ne se suivent pas dans l'ordre du document")
    for n in sorted(legendes):
        if n not in citations:
            signale(f"{genre} {n} : legende presente, jamais appelee dans le texte")
        elif citations[n] > legendes[n] + 3:
            signale(f"{genre} {n} : appelee (bloc {citations[n]}) bien apres sa "
                    f"legende (bloc {legendes[n]})")
    for n in citations:
        if n not in legendes:
            signale(f"{genre} {n} : citee dans le texte, aucune legende")
    print(f"  {genre:9s} {len(legendes)} legendes, "
          f"{len(citations)} appelees dans le texte")

# --- 2. bibliographie ----------------------------------------------------
i_ref = next((i for i, t in enumerate(BLOCS) if t.strip() == "References"), None)
if i_ref is None:
    signale("section References introuvable")
else:
    entrees = sorted(int(m.group(1)) for t in BLOCS[i_ref:]
                     for m in [re.match(r"\s*\[(\d+)\]", t)] if m)
    corps_txt = " ".join(BLOCS[:i_ref])
    ordre_cit = []
    for m in re.finditer(r"\[([\d,\s–-]+)\]", corps_txt):
        for part in m.group(1).replace("–", "-").split(","):
            part = part.strip()
            bornes = part.split("-")
            try:
                rng = (range(int(bornes[0]), int(bornes[1]) + 1)
                       if len(bornes) == 2 else [int(part)])
            except ValueError:
                continue
            for n in rng:
                if n not in ordre_cit:
                    ordre_cit.append(n)
    if entrees != list(range(1, len(entrees) + 1)):
        signale(f"bibliographie : numerotation non continue, {entrees}")
    jamais = sorted(set(entrees) - set(ordre_cit))
    if jamais:
        signale(f"bibliographie : references jamais citees {jamais}")
    fantomes = sorted(set(ordre_cit) - set(entrees))
    if fantomes:
        signale(f"bibliographie : citations sans entree {fantomes}")
    if ordre_cit != sorted(ordre_cit):
        recul = [(ordre_cit[i], ordre_cit[i + 1]) for i in range(len(ordre_cit) - 1)
                 if ordre_cit[i + 1] < ordre_cit[i]]
        signale(f"bibliographie : ordre de premiere citation non croissant, "
                f"premiers reculs {recul[:5]}")
    print(f"  {'References':9s} {len(entrees)} entrees, "
          f"{len(ordre_cit)} citees, ordre de premiere citation "
          f"{'croissant' if ordre_cit == sorted(ordre_cit) else 'NON CROISSANT'}")

# --- 3. sections ---------------------------------------------------------
titres = [t for t in BLOCS if re.match(r"^\d+\.\s+\S", t)]
nums = [int(t.split(".")[0]) for t in titres]
if nums != list(range(1, len(nums) + 1)):
    signale(f"sections : numerotation {nums}")
print(f"  {'Sections':9s} {len(nums)} de premier niveau")

# --- verdict --------------------------------------------------------------
print()
if anomalies:
    print(f"{len(anomalies)} anomalie(s) :")
    for a in anomalies:
        print(f"  - {a}")
else:
    print("aucune anomalie de coherence interne")
sys.exit(1 if anomalies else 0)
