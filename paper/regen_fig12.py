#!/usr/bin/env python3
"""Redraw figure 12 as vector, from the released campaign.

The figure was the last of the twenty with no vector version, and it sits below
the 1772-pixel minimum Elsevier sets for a single-column bitmap. It was thought
unrecoverable because the runs it plots -- LightGBM at 5, 10 and 30 seconds --
are not among the 154 of the main campaign. They are in the same file, under the
`intervals` key, which an earlier inspection missed by truncating the key list.

Construction, as the caption states it: the mean over seeds 1 to 3 at 5, 10 and
30 s, and seed 1 alone at 60 s. Every cell of the published heat map is asserted
below, so this file cannot drift from the figure the article shows.

The manuscript's own PNG is deliberately left alone: the article is submitted,
and its embedded images should stay bit-for-bit what the journal received. This
writes only the artwork file, which completes the set at twenty of twenty.
"""
import json
import pathlib
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "submission" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

R = json.loads((HERE / "article1_results.json").read_text(encoding="utf-8"))
IV, MO = R["intervals"], R["models"]

CLASSES = ["benign", "bruteforce-ftp", "bruteforce-smb", "bruteforce-ssh",
           "dos-hulk", "dos-icmp", "dos-pushack", "dos-slowloris", "dos-udp"]
COLONNES = ["5", "10", "30", "60"]


def cellule(interval, classe):
    if interval == "60":
        return MO["lightgbm|audited|strat_seed1"]["per_class_f1"][classe]
    return st.mean(IV[interval]["runs"][f"lightgbm|seed{s}"]["per_class_f1"][classe]
                   for s in (1, 2, 3))


G = np.array([[cellule(c, k) for c in COLONNES] for k in CLASSES])

# --- les valeurs que la figure publiee affiche, au millieme -----------------
PUBLIEE = {
    "5":  [1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000],
    "10": [0.973, 0.685, 0.986, 0.881, 0.993, 0.997, 0.999, 0.998, 0.999],
    "30": [1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000],
    "60": [1.000, 0.999, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000],
}
for j, c in enumerate(COLONNES):
    for i, k in enumerate(CLASSES):
        assert abs(round(G[i, j], 3) - PUBLIEE[c][i]) < 5e-4, (c, k, G[i, j])

# Ce que la 6.4 lit dans la figure, et qui doit rester vrai.
_ftp10 = [IV["10"]["runs"][f"lightgbm|seed{s}"]["per_class_f1"]["bruteforce-ftp"]
          for s in (1, 2, 3)]
assert sorted(round(v, 3) for v in _ftp10) == [0.056, 0.999, 1.0], _ftp10
assert round(st.mean(_ftp10), 3) == 0.685
# Toute cellule sous 0.99 est dans la colonne des 10 s, et la legende le dit.
assert {COLONNES[j] for i, j in zip(*np.where(G < 0.99))} == {"10"}

fig, ax = plt.subplots(figsize=(7.4, 5.2))
im = ax.imshow(G, cmap="viridis", vmin=0.60, vmax=1.00, aspect="auto")
ax.set_xticks(range(len(COLONNES)), [f"{c} s" for c in COLONNES])
ax.set_yticks(range(len(CLASSES)), CLASSES)
ax.set_xlabel("flow aggregation interval")
ax.set_title("Per-family detectability across aggregation intervals")
for i in range(len(CLASSES)):
    for j in range(len(COLONNES)):
        ax.text(j, i, f"{G[i, j]:.3f}", ha="center", va="center",
                color="white" if G[i, j] < 0.78 else "black", fontsize=9)
ax.set_xticks(np.arange(-.5, len(COLONNES), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(CLASSES), 1), minor=True)
ax.grid(which="minor", color="0.85", linewidth=.6)
ax.tick_params(which="minor", length=0)
fig.colorbar(im, ax=ax, label="per-class F1 (LightGBM, audited)")
fig.tight_layout()

cible = OUT / "figure12_intervals_per_class.pdf"
fig.savefig(cible)
fig.savefig(cible.with_suffix(".png"), dpi=320)
print("ecrit :", cible.name, "et son PNG de controle")
print("grille reproduite, %d cellules verifiees contre la figure publiee"
      % G.size)
