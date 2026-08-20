#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle de mise en page, sur le document rendu.

Troisieme des trois verificateurs. check_coherence.py verifie que le
document se tient, check_style.py comment il est ecrit, celui-ci ce qu'il
donne une fois pagine -- ce qu'aucune lecture du XML ne montre.

Ce qu'il a attrape la premiere fois qu'il a tourne, et qu'aucun des deux
autres ne pouvait voir :

  - la legende de la figure 6 se coupait en deux entre les pages 15 et 16.
    Les legendes de figures n'avaient ni keepNext ni keepLines ; seules
    celles que edit_manuscript.py fabrique en avaient.
  - la legende du tableau 14 restait au bas d'une page dont le tableau
    etait a la suivante.

    python check_layout.py [chemin/vers/le.docx]

Il faut LibreOffice Writer (soffice) et PyMuPDF. Sans eux le script le dit
et sort sans rien affirmer : un controle qui ne peut pas tourner ne doit
pas se lire comme un controle passe.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = pathlib.Path(__file__).resolve().parent
DOCX = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
        else HERE / "GeNIS_benchmark_article.docx")

try:
    import pymupdf
except ImportError:
    sys.exit("PyMuPDF absent : pip install pymupdf")
if not shutil.which("soffice"):
    sys.exit("LibreOffice Writer absent : apt-get install libreoffice-writer")


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


# --- rendu ----------------------------------------------------------------
tmp = pathlib.Path(tempfile.mkdtemp(prefix="genis_layout_"))
subprocess.run(["soffice", "--headless", "--norestore",
                f"-env:UserInstallation=file://{tmp}/profile",
                "--convert-to", "pdf", "--outdir", str(tmp), str(DOCX)],
               check=True, capture_output=True, timeout=900)
pdf = tmp / (DOCX.stem + ".pdf")
if not pdf.exists():
    sys.exit(f"le rendu a echoue : {pdf} absent")
doc = pymupdf.open(pdf)
PAGES = [norm(p.get_text()) for p in doc]
LARG, HAUT = doc[0].rect.width, doc[0].rect.height

with zipfile.ZipFile(DOCX) as z:
    corps = ET.fromstring(z.read("word/document.xml")).find(W + "body")
BLOCS = ["".join(t.text or "" for t in e.iter(W + "t")) for e in corps]
sect = corps.find(W + "sectPr")
mg = sect.find(W + "pgMar")
MG_G, MG_D = int(mg.get(W + "left")) / 20, int(mg.get(W + "right")) / 20
MG_H, MG_B = int(mg.get(W + "top")) / 20, int(mg.get(W + "bottom")) / 20

defauts = []
print(f"  {'rendu':18s} {doc.page_count} pages de "
      f"{LARG / 72:.2f} x {HAUT / 72:.2f} in")

# --- 1. les legendes tiennent d'un bloc sur une page ----------------------
# Une legende coupee par un saut de page est le defaut que ce script existe
# pour attraper. On teste le premier et le dernier mot : le texte complet ne
# se retrouve pas toujours a l'identique dans l'extraction, a cause des
# caracteres speciaux (cases a cocher, exposants, espaces insecables).
legendes = [t for t in BLOCS if re.match(r"(Figure|Table|Algorithm) \d+\.", t)]
for leg in legendes:
    mots = norm(leg).split()
    debut, fin = " ".join(mots[:3]), " ".join(mots[-4:])
    pd = [i for i, pg in enumerate(PAGES) if debut in pg]
    # la fin doit etre cherchee A PARTIR de la page ou la legende commence :
    # une phrase de quatre mots se retrouve ailleurs dans le manuscrit, et la
    # chercher depuis le debut du document donnait un faux positif sur le
    # tableau 7, annonce comme commencant p25 et finissant p12.
    pf = [i for i, pg in enumerate(PAGES) if fin in pg and (not pd or i >= pd[0])]
    if not pd or not pf:
        defauts.append(f"legende introuvable dans le rendu : {debut}...")
    elif pd[0] != pf[0]:
        defauts.append(f"{debut}... commence p{pd[0] + 1} et finit p{pf[0] + 1}")
print(f"  {'legendes':18s} {len(legendes)} controlees")

# --- 2. une legende de tableau reste avec son tableau ---------------------
# La legende d'un tableau le precede : si elle tombe au bas d'une page, le
# tableau part a la suivante et le lecteur les voit separes.
for i, t in enumerate(BLOCS):
    m = re.match(r"Table (\d+)\.", t)
    if not m or i + 1 >= len(BLOCS):
        continue
    tbl = corps[i + 1]
    if tbl.tag != W + "tbl":
        continue
    entete = norm("".join(x.text or "" for x in tbl.iter(W + "t")))[:40]
    pl = next((k for k, pg in enumerate(PAGES) if norm(t)[:35] in pg), None)
    pt = next((k for k, pg in enumerate(PAGES) if entete and entete in pg), None)
    if pl is not None and pt is not None and pt != pl:
        defauts.append(f"Table {m.group(1)} : legende p{pl + 1}, tableau p{pt + 1}")

# --- 3. rien ne deborde des marges ----------------------------------------
# Au glyphe pres, et en tolerant 1 pt : une cesure en fin de ligne justifiee
# fait saillir le trait d'union, ce qui est de la typographie et non un
# defaut, et depend du moteur de rendu.
TOL = 1.0
for p in doc:
    for im in p.get_images(full=True):
        for r in p.get_image_rects(im[0]):
            if (r.x1 > LARG - MG_D + TOL or r.x0 < MG_G - TOL
                    or r.y1 > HAUT - MG_B + TOL or r.y0 < MG_H - TOL):
                defauts.append(f"p{p.number + 1} : une image sort des marges "
                               f"({r.width:.0f}x{r.height:.0f} pt)")
n_img = sum(len(p.get_images(full=True)) and
            len([1 for im in p.get_images(full=True) for _ in p.get_image_rects(im[0])])
            for p in doc)
print(f"  {'images':18s} {n_img} placees, aucune hors marges"
      if not defauts else f"  {'images':18s} {n_img} placees")

# --- 4. aucune page presque vide ------------------------------------------
# Une figure trop haute pour la place restante chasse le texte et laisse une
# page a moitie blanche, ce qu'un relecteur remarque.
for i, pg in enumerate(PAGES):
    if len(pg) < 700 and i < len(PAGES) - 1:
        defauts.append(f"p{i + 1} : {len(pg)} caracteres seulement, page presque vide")
print(f"  {'remplissage':18s} {min(len(p) for p in PAGES[:-1])} caracteres "
      f"sur la page la plus creuse")

# --- verdict --------------------------------------------------------------
print()
if defauts:
    print(f"{len(defauts)} defaut(s) de mise en page :")
    for d in defauts:
        print(f"  - {d}")
else:
    print("aucun defaut de mise en page")
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if defauts else 0)
