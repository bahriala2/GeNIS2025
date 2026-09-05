#!/usr/bin/env python3
"""Emit a vector PDF beside every manuscript figure, for the artwork upload.

Elsevier lists vector drawings first among the accepted artwork formats, and a
vector file has no pixel count to fall short of -- which matters here because
three of the twenty PNGs sit under the 1772-pixel minimum the guide sets for a
single-column bitmap.

The hook is Figure.savefig rather than plt.savefig, because the regeneration
scripts use both and Figure.savefig is what they both end up calling. Patching
it means the PDF is written from the same figure object at the same moment as
the PNG, so the two cannot drift apart -- which a separate rendering pass could
not guarantee.
"""
import hashlib
import pathlib
import runpy
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

REPO = pathlib.Path(__file__).resolve().parent.parent
PNG = REPO / "paper" / "figures_manuscrit"
VEC = REPO / "paper" / "submission" / "figures"
VEC.mkdir(parents=True, exist_ok=True)

AVANT = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(PNG.glob("figure*.png"))}

_orig = Figure.savefig
ecrits = []


def savefig(self, fname, *a, **k):
    _orig(self, fname, *a, **k)
    p = pathlib.Path(str(fname))
    if p.suffix.lower() == ".png" and p.name.startswith("figure"):
        k2 = {c: v for c, v in k.items() if c != "dpi"}
        cible = VEC / (p.stem + ".pdf")
        _orig(self, cible, *a, **k2)
        ecrits.append(cible.name)


Figure.savefig = savefig

SCRIPTS = ["regen_fig_concept.py", "regen_figures_2_6.py", "regen_fig_protocols.py",
           "regen_e8_figures.py", "regen_fig6.py", "regen_e2.py",
           "regen_e4.py", "regen_e4b.py", "regen_e4c.py"]

for s in SCRIPTS:
    chemin = REPO / "paper" / s
    if not chemin.exists():
        print("absent, ignore :", s)
        continue
    try:
        runpy.run_path(str(chemin), run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:                      # noqa: BLE001
        print("%s a echoue : %s" % (s, e))

APRES = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(PNG.glob("figure*.png"))}
bouge = sorted(n for n in AVANT if APRES.get(n) != AVANT[n])
if bouge:
    print("\nATTENTION, ces PNG du manuscrit ont change :", bouge)
    sys.exit(1)
print("\nPDF ecrits :", len(set(ecrits)))
print("PNG du manuscrit inchanges :", len(AVANT))
