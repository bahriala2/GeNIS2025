#!/usr/bin/env python3
"""One-shot edit of the manuscript source for the transfer to Digital Engineering.

EAAI-26-28539 was not kept by Engineering Applications of Artificial
Intelligence and is transferred to Digital Engineering (Elsevier, ISSN
2950-550X). Five changes follow from that journal's Guide for Authors, read on
15 November 2026:

1. The abstract named "the contribution to artificial intelligence" and "the
   engineering application", a pairing EAAI requires and Digital Engineering
   does not. The sentence is rewritten (24 -> 21 words, abstract 250 -> 247).
2. The title page must give the full postal address of each affiliation.
3. The corresponding author's e-mail must be on the title page; it is published.
4. The AI disclosure section must carry the title the guide prescribes.
5. The text is in British English; one American form remains outside the
   reference titles, which are quoted as published and stay untouched.

The EAAI state stays recoverable from git (commit ed7800d and earlier).
Run once; it refuses to run twice because each old string must be found.
"""
import pathlib
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "GeNIS_benchmark_article.docx"

EDITS = [
    ("The contribution to artificial intelligence is a four-test feature-audit "
     "protocol, explicit rather than a leakage-free guarantee, and the "
     "engineering application is network intrusion detection.",
     "We contribute a four-test feature-audit protocol, explicit rather than a "
     "leakage-free guarantee, for evaluating learned intrusion detectors that "
     "protect digital infrastructure."),
    (" INSIGHT Lab, ISITCom, University of Sousse, Tunisia",
     " INSIGHT Lab, Higher Institute of Computer Science and Communication "
     "Technologies of Hammam Sousse (ISITCom), University of Sousse, "
     "Hammam Sousse 4011, Tunisia"),
    (" Corresponding author.",
     " Corresponding author. E-mail address: "
     "bahri.mohamedalaeddine@isitc.u-sousse.tn"),
    ("12. Declaration of generative AI in the writing process",
     "12. Declaration of generative AI and AI-assisted technologies in the "
     "manuscript preparation process"),
    ("supervised algorithms generalize from",
     "supervised algorithms generalise from"),
]


def texte(e):
    return "".join(t.text or "" for t in e.iter(W + "t"))


def remplacer(p, vieux, neuf):
    """Replace a string that may span several runs, keeping the first run's format."""
    plein = texte(p)
    k = plein.index(vieux)
    pos, reste = 0, neuf
    for t in p.iter(W + "t"):
        s_ = t.text or ""
        a, b = pos, pos + len(s_)
        pos = b
        if b <= k or a >= k + len(vieux):
            continue
        dd, ff = max(k, a) - a, min(k + len(vieux), b) - a
        t.text = s_[:dd] + reste + s_[ff:]
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        reste = ""


d = pathlib.Path(tempfile.mkdtemp())
with zipfile.ZipFile(SRC) as z:
    z.extractall(d)
doc = d / "word" / "document.xml"
brut = doc.read_text(encoding="utf-8")
tete = brut[brut.index("<w:document"):brut.index(">", brut.index("<w:document")) + 1]
for pfx, uri in re.findall(r'xmlns:([A-Za-z0-9]+)="([^"]+)"', tete):
    if not re.fullmatch(r"ns\d+", pfx):
        ET.register_namespace(pfx, uri)
arbre = ET.parse(doc)
body = arbre.getroot().find(W + "body")

for vieux, neuf in EDITS:
    vus = [p for p in body.iter(W + "p") if vieux in texte(p)]
    assert len(vus) == 1, (len(vus), vieux[:60])
    remplacer(vus[0], vieux, neuf)
    print("ok :", vieux[:60])

arbre.write(doc, encoding="UTF-8", xml_declaration=True)
xml = doc.read_text(encoding="utf-8")
i = xml.index("<w:document")
j = xml.index(">", i)
presentes = dict(re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', xml[i:j + 1]))
manquantes = [f'{k}="{v}"' for k, v in re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', tete)
              if k not in presentes]
if manquantes:
    doc.write_text(xml[:j] + " " + " ".join(manquantes) + xml[j:], encoding="utf-8")

tmp = SRC.with_suffix(".tmp.docx")
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(d.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(d).as_posix())
shutil.rmtree(d)
tmp.replace(SRC)

abstract = None
r = ET.fromstring(zipfile.ZipFile(SRC).read("word/document.xml"))
ps = [texte(p) for p in r.iter(W + "p")]
abstract = ps[ps.index("Abstract") + 1]
print("abstract :", len(abstract.split()), "words")
assert len(abstract.split()) <= 250
