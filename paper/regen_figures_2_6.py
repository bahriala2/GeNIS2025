#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figures 2 et 6, les deux dernieres qui n'avaient aucun script.

MAPPING.md les listait comme un manque, et la liste des contributions de la
section 1 promet « the scripts regenerating every figure and table ». Deux
figures sans script rendaient cette phrase fausse.

Les redessiner a aussi corrige trois erreurs que les images portaient :

  - figure 2, la note de bas de figure annonce 5 029 flux benins de test. Le
    plus petit taux de faux positifs non nul de toute la campagne vaut
    exactement 1/5030, donc la partition en contient 5 030, ce que la legende
    et les sections 4.5 et 9 disaient deja ;
  - figure 2, le titre arrondissait la part des floods a 87.3 % quand les deux
    autres parts sont donnees au centieme, si bien que les trois sommaient a
    100.04 ;
  - figure 6, IdleTime etait dessine dans la couleur « retained ». C'est la
    treizieme entree de la liste noire depuis la section 9. Il porte
    desormais sa propre marque, parce qu'il est exclu par un critere que ni
    l'un ni l'autre des deux autres ne couvre.

Sorties : paper/figures_manuscrit/figure{02,06}_*.png
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "figures_manuscrit"
OUT.mkdir(exist_ok=True)

A = json.loads((HERE / "article1_results.json").read_text(encoding="utf-8"))
CNT = A["slice60"]["class_counts"]
N = A["slice60"]["n"]
# DPI fixe la GEOMETRIE : les figsize sont ecrits en pixels divises par lui,
# donc le changer ne change pas le nombre de pixels rendus. Il en faut un
# second pour la resolution de sortie.
DPI = 285
# Elsevier demande 300 dpi au moins pour une figure mixte trait et
# demi-teinte. La figure 6 occupe 5.76 pouces de large dans le document, ou
# ses 1678 pixels ne faisaient que 291 dpi effectifs. A 320 en sortie elle en
# fait 327, et le rapport hauteur/largeur ne bouge pas, donc l'etendue posee
# dans le document reste valable.
DPI_OUT = 320

VERT, BLEU, ROUGE = "#4b9c5a", "#4a72b0", "#c23b34"

# =========================================================================
# Figure 2 — distribution naturelle des classes
# =========================================================================
FAM = {c: ("benign" if c == "benign"
           else "brute force" if c.startswith("bruteforce-")
           else "volumetric DoS") for c in CNT}
COUL = {"benign": VERT, "brute force": BLEU, "volumetric DoS": ROUGE}
parts = {f: sum(v for c, v in CNT.items() if FAM[c] == f) for f in COUL}
ordre = sorted(CNT, key=CNT.get)

# Le nombre de flux benins de test se DEDUIT et ne se recopie pas : le plus
# petit taux de faux positifs non nul de la campagne en est l'inverse exact.
fprs = [r["binary"]["fpr"] for k, r in A["models"].items()
        if k.endswith("|audited|strat_seed1") and r["binary"]["fpr"] > 0]
n_benin_test = round(1 / min(fprs))
pas = 100 / n_benin_test

fig, ax = plt.subplots(figsize=(1867 / DPI, 1214 / DPI))
ax.barh(range(len(ordre)), [CNT[c] for c in ordre],
        color=[COUL[FAM[c]] for c in ordre], height=.72)
for i, c in enumerate(ordre):
    ax.text(CNT[c] * 1.08, i, f"{CNT[c]:,}".replace(",", " ")
            + f"  ({100 * CNT[c] / N:.2f}%)", va="center", fontsize=9.5,
            color="#25292e")
ax.set_xscale("log")
ax.set_yticks(range(len(ordre)))
ax.set_yticklabels(ordre, fontsize=10)
ax.set_xlim(1e3, 4e5)
ax.set_xlabel("60-second flows (log scale)", fontsize=11)
ax.set_title("Natural class distribution of the 60-second slice\n"
             + ", ".join(f"{f} {100 * parts[f] / N:.2f}%"
                         for f in ("volumetric DoS", "benign", "brute force")),
             fontsize=12)
ax.grid(axis="x", alpha=.3)
ax.set_axisbelow(True)
ax.legend(handles=[matplotlib.patches.Patch(color=COUL[f], label=f)
                   for f in ("benign", "brute force", "volumetric DoS")],
          loc="lower right", fontsize=10)
fig.text(.5, .025,
         f"The 20% test partition holds {n_benin_test:,}".replace(",", "\u00a0")
         + f" benign flows, so a single false positive is" + "\n"
         + f"{pas:.4f} percentage points, and every false-positive rate" + "\n"
         + "reported in this paper is an integer multiple of that step.",
         ha="center", fontsize=9.2, color="#4a4f55")
plt.tight_layout(rect=[0, .135, 1, 1])
plt.savefig(OUT / "figure02_class_distribution.png", dpi=DPI_OUT)
plt.close()
print(f"figure 2  : {n_benin_test} flux benins de test, pas de {pas:.4f} point")
print("            parts " + ", ".join(f"{f} {100 * parts[f] / N:.2f}%"
                                       for f in parts)
      + f"  (somme {sum(100 * v / N for v in parts.values()):.2f})")

# =========================================================================
# Figure 6 — l'attribution ne separe pas les raccourcis du signal
# =========================================================================
TT = {r["feature"]: r for r in A["audit"]["transfer_table"]}
BL8 = set(A["audit"]["blacklist"]) & set(TT)          # les huit du rapport
ID = "IdleTime"
PLANCHER = 3e-5

fig, ax = plt.subplots(figsize=(1678 / DPI, 1322 / DPI))
ax.axvspan(1e-5, 1e-4, color=ROUGE, alpha=.05)
for feat, r in TT.items():
    imp = max(r["importance"], PLANCHER)
    acc = r["acc seule (stratifie)"]
    if feat == ID:
        ax.scatter(imp, acc, s=150, marker="D", color="#7a3fa0", zorder=4)
    elif feat in BL8:
        ax.scatter(imp, acc, s=130, color=ROUGE, alpha=.85, zorder=3)
    else:
        ax.scatter(imp, acc, s=90, color=BLEU, alpha=.75, zorder=2)

pmax = max(CNT.values()) / N
ax.axhline(3 * pmax, ls="--", color="#7d848c", lw=1.2)
ax.text(1.2e-5, 3 * pmax + .012, "predictivity filter (3x)", fontsize=9.5,
        color="#7d848c")
ax.axhline(pmax, ls=":", color="#7d848c", lw=1.2)
ax.text(1.2e-5, pmax + .012, "majority-class rate", fontsize=9.5,
        color="#7d848c")
ax.text(1.2e-5, .155, "importance below $10^{-4}$", fontsize=9.5, color=ROUGE)
ax.annotate(ID, (TT[ID]["importance"], TT[ID]["acc seule (stratifie)"]),
            textcoords="offset points", xytext=(-10, 14), ha="right",
            fontsize=10.5, color="#7a3fa0")

# Les deux annotations que la legende de la figure promet au lecteur : le
# paquet des six colonnes identiques, et la paire que l'attribution classe au
# meme endroit alors que la regle en exclut une et garde l'autre.
_DUP = ["Dur", "RunTime", "Mean", "Sum", "Min", "Max"]
assert len({TT[f]["acc seule (stratifie)"] for f in _DUP}) == 1
ax.annotate("6 numerically\nidentical columns",
            (PLANCHER, TT["Dur"]["acc seule (stratifie)"]),
            textcoords="offset points", xytext=(34, -26), fontsize=10,
            color=ROUGE,
            arrowprops=dict(arrowstyle="-", color=ROUGE, lw=1))
_A, _B = "SIntPktMax", "DstBytes"
# Placee en coordonnees d'axes : en points depuis le nuage, elle sortait du
# cadre et repoussait le titre.
ax.annotate(f"{_A} (excluded, {TT[_A]['acc seule (stratifie)']:.3f}) and\n"
            f"{_B} (retained, {TT[_B]['acc seule (stratifie)']:.3f}) are\n"
            "ranked identically by attribution",
            xy=(PLANCHER, TT[_B]["acc seule (stratifie)"]),
            xycoords="data", xytext=(.40, .985), textcoords="axes fraction",
            ha="left", va="top", fontsize=9.5, color="#3b4046",
            arrowprops=dict(arrowstyle="-", color="#7d848c", lw=1,
                            connectionstyle="arc3,rad=0.2"))
ax.set_xscale("log")
ax.set_xlim(1e-5, 1)
ax.set_ylim(0, 1.03)
ax.set_xlabel("permutation importance (accuracy drop, log scale; values below\n"
              "$3\\times10^{-5}$, including exact zeros, are drawn on the left "
              "edge)", fontsize=11)
ax.set_ylabel("single-feature accuracy, stratified split", fontsize=11)
ax.set_title("Attribution importance does not separate shortcuts from signal",
             fontsize=11.5)
ax.grid(alpha=.3)
ax.set_axisbelow(True)
ax.legend(handles=[
    plt.Line2D([], [], ls="", marker="o", ms=9, color=BLEU, label="retained"),
    plt.Line2D([], [], ls="", marker="o", ms=10, color=ROUGE,
               label="excluded by the transferability rule"),
    plt.Line2D([], [], ls="", marker="D", ms=9, color="#7a3fa0",
               label="excluded by the capture-file test")],
    loc="lower right", fontsize=9.5)
plt.tight_layout()
plt.savefig(OUT / "figure06_importance_vs_transferability.png",
            dpi=DPI_OUT)
plt.close()
nuls = sum(1 for r in TT.values() if r["importance"] == 0)
print(f"figure 6  : {len(TT)} colonnes, {len(BL8)} exclues par la regle, "
      f"{nuls} a importance exactement nulle")
print(f"            {ID} : importance {TT[ID]['importance']:.4f}, "
      f"exactitude {TT[ID]['acc seule (stratifie)']:.4f}")
