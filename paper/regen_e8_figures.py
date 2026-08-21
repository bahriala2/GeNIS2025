#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figures 5, 10 et 18, redessinees sur la condition auditee CORRIGEE.

E7 a montre qu'IdleTime est un identifiant de fichier de capture ; E8 a refait
la campagne sans lui. Ces trois figures dependent de la condition auditee et
doivent donc etre redessinees. Ce sont les seules que l'on puisse refaire sans
les matrices de probabilites : les figures 9 (McNemar) et 11 (bootstrap) en
ont besoin, et la figure 14 attend la mesure de cout.

Rien n'est recopie : chaque valeur vient de experiments/e8/e8_results.json,
condition "corrigee". Les colonnes full et clean de la figure 10 viennent de
article1_results.json et ne changent pas -- elles n'ont jamais utilise la
liste noire.

Sorties : paper/figures_manuscrit/figure{05,10,18}_*.png
"""
import json
import pathlib
import statistics as st
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "figures_manuscrit"
OUT.mkdir(exist_ok=True)

R = json.loads((HERE / "article1_results.json").read_text(encoding="utf-8"))
E = json.loads((REPO / "experiments" / "e8" / "e8_results.json")
               .read_text(encoding="utf-8"))["runs"]
M = R["models"]
CN = R["slice60"]["classes"]
ORD = ["xgboost", "lightgbm", "rf", "ftt", "logreg", "rnn", "cnn", "dnn",
       "knn", "nb"]
NICE = {"xgboost": "XGBoost", "lightgbm": "LightGBM", "rf": "RF",
        "ftt": "FT-Tr.", "logreg": "LogReg", "rnn": "RNN", "cnn": "CNN",
        "dnn": "DNN", "knn": "$k$-NN", "nb": "NB"}


def run(m, proto):
    return E[f"{m}|corrigee|{proto}"]


def moy(m, proto="strat"):
    v = [E[f"{m}|corrigee|strat_seed{s}"]["macro_f1"] for s in range(1, 6)
         if f"{m}|corrigee|strat_seed{s}" in E]
    return st.mean(v)


# La condition auditee doit bien etre celle a treize colonnes.
assert run("xgboost", "strat_seed1")["n_features"] == 54, "pas la liste corrigee"

# =========================================================================
# Figure 5 — F1 par classe, condition auditee, graine 1
# =========================================================================
Mx = np.array([[run(m, "strat_seed1")["per_class_f1"][c] for m in ORD]
               for c in CN])
fig, ax = plt.subplots(figsize=(7.2, 3.8))
im = ax.imshow(Mx, aspect="auto", vmin=0, vmax=1, cmap="RdYlGn")
ax.set_xticks(range(len(ORD)))
ax.set_xticklabels([NICE[m] for m in ORD], rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(CN)))
ax.set_yticklabels(CN, fontsize=8)
for i in range(len(CN)):
    for j in range(len(ORD)):
        ax.text(j, i, f"{Mx[i, j]:.2f}", ha="center", va="center", fontsize=6.3,
                color="black" if Mx[i, j] > .35 else "white")
plt.colorbar(im, label="per-class F1")
ax.set_title("Per-class F1, audited condition (seed 1)", fontsize=10)
plt.tight_layout()
plt.savefig(OUT / "figure05_per_class_f1_audited.png", dpi=285)
plt.close()
print(f"figure 5  : minimum hors NB {Mx[:, :-1].min():.4f}")

# =========================================================================
# Figure 10 — macro-F1 par condition et protocole
# =========================================================================
# Cinq positions : full/strat, clean/strat, audite/strat (5 graines),
# clean/temporel, audite/temporel. Seules les colonnes auditees changent.
POS = ["full\n(strat.)", "clean\n(strat.)", "audited\n(strat., 5 seeds)",
       "clean\n(temporal)", "audited\n(temporal)"]
FORTS = [m for m in ORD if m != "nb"]
FAIBLES = ["nb", "majority"]


def serie(m):
    return [M[f"{m}|full|strat_seed1"]["macro_f1"],
            M[f"{m}|clean|strat_seed1"]["macro_f1"],
            moy(m),
            M.get(f"{m}|clean|temporal", {}).get("macro_f1", np.nan),
            run(m, "temporal")["macro_f1"]]


fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 4.2),
                             gridspec_kw={"width_ratios": [3.1, 1]})
a1.axvspan(-.4, 2.5, color="#4a72b0", alpha=.05)
a1.axvspan(2.5, 4.4, color="#c23b34", alpha=.05)
cmap = plt.get_cmap("tab10")
for k, m in enumerate(FORTS):
    v = serie(m)
    a1.plot(range(5), v, "o-", ms=5, lw=1.3, color=cmap(k % 10))
    a1.annotate(m, (4.06, v[-1]), fontsize=7.5, color=cmap(k % 10),
                va="center", annotation_clip=False)
bas = min(min(x for x in serie(m) if not np.isnan(x)) for m in FORTS)
a1.set_ylim(bas - .004, 1.0015)
a1.set_xlim(-.4, 4.4)
a1.set_xticks(range(5))
a1.set_xticklabels(POS, fontsize=8)
a1.set_ylabel("macro-F1")
a1.set_title("(a) supervised detectors (zoom)", fontsize=10)
a1.grid(alpha=.25, lw=.5)
a1.text(1.0, bas - .0025, "stratified protocol", color="#4a72b0", fontsize=8,
        ha="center")
a1.text(3.5, bas - .0025, "temporal protocol", color="#c23b34", fontsize=8,
        ha="center")
for m, col in zip(FAIBLES, ("#dd8452", "#8c8c8c")):
    a2.plot(range(5), serie(m), "o-", ms=4, lw=1.2, color=col, label=m)
a2.set_ylim(0, .8)
a2.set_xticks(range(5))
a2.set_xticklabels(["f/s", "c/s", "a/s", "c/t", "a/t"], fontsize=8)
a2.set_title("(b) weak baselines", fontsize=10)
a2.legend(fontsize=8)
a2.grid(alpha=.25, lw=.5)
fig.suptitle("Model ranking across feature conditions and evaluation "
             "protocols (60 s slice)", fontsize=11)
plt.tight_layout(rect=[0, 0, 1, .95])
plt.savefig(OUT / "figure10_conditions_protocols.png", dpi=285)
plt.close()
print(f"figure 10 : plancher du panneau (a) {bas:.4f}")

# =========================================================================
# Figure 18 — F1 par classe sous le protocole temporel
# =========================================================================
# Les detecteurs sont ordonnes par macro-F1 temporel decroissant : c'est cet
# ordre qui a change le plus avec la correction.
ORD_T = sorted(FORTS, key=lambda m: -run(m, "temporal")["macro_f1"])
Mt = np.array([[run(m, "temporal")["per_class_f1"][c] for c in CN]
               for m in ORD_T])
fig, ax = plt.subplots(figsize=(7.35, 5.55))
im = ax.imshow(Mt, aspect="auto", vmin=.80, vmax=1.0, cmap="RdYlGn")
ax.set_xticks(range(len(CN)))
ax.set_xticklabels(CN, rotation=35, ha="right", fontsize=8)
ax.set_yticks(range(len(ORD_T)))
ax.set_yticklabels(ORD_T, fontsize=8)
ax.set_xticks(np.arange(-.5, len(CN), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(ORD_T), 1), minor=True)
ax.grid(which="minor", color="white", lw=1.4)
ax.tick_params(which="minor", length=0)
seuil = np.percentile(Mt, 8)
for i in range(len(ORD_T)):
    for j in range(len(CN)):
        v = Mt[i, j]
        gras = v <= seuil
        ax.text(j, i, f"{v:.3f}".lstrip("0") if v < 1 else "1.000",
                ha="center", va="center", fontsize=7.4,
                weight="bold" if gras else "normal",
                color="white" if v < .87 else "black")
plt.colorbar(im, label="per-class F1 (scale clipped at 0.80)")
ax.set_title("Per-class F1 under the temporal protocol, audited condition\n"
             "the differences the stratified protocol hides", fontsize=10)

def _avant():
    """Ce que valaient, sous la liste publiee, les cellules qui tombent ici.

    La phrase est CALCULEE et non affirmee : la premiere version que j'avais
    ecrite disait que toutes ces cellules etaient au-dessus de 0.93 avant la
    correction, et c'etait faux pour l'une d'elles.
    """
    bas = [(m, c) for m in ORD_T
           for c, v in run(m, "temporal")["per_class_f1"].items() if v < .93]
    if not bas:
        return ""
    av = [E[f"{m}|publiee|temporal"]["per_class_f1"][c] for m, c in bas]
    n = sum(1 for v in av if v > .93)
    mot = {12: "twelve", 11: "eleven", 10: "ten", 9: "nine", 8: "eight",
           7: "seven", 6: "six", 5: "five", 4: "four", 3: "three"}
    return (f"Under the published blacklist {mot.get(n, str(n))} of these "
            f"{mot.get(len(bas), str(len(bas)))} cells sat above 0.93.")


# La note du bas se calcule. Sous la liste corrigee la perte ne se disperse
# plus : elle se concentre sur deux classes, et le dire est le resultat.
libres = [c for k, c in enumerate(CN)
          if Mt[:, k].min() > .995 and np.ptp(Mt[:, k]) < .002]
plats = sorted((Mt[i, j], ORD_T[i], CN[j])
               for i in range(len(ORD_T)) for j in range(len(CN)))
pire = plats[0]
# Une classe "dure" est celle ou PLUSIEURS detecteurs tombent, pas celle ou
# un seul trebuche : sans ce comptage, la note appelait "concentration" une
# liste de cinq classes dont deux ne portaient qu'un incident.
tombe = {c: sorted((m for v, m, cc in plats if cc == c and v < .93),
                   key=ORD_T.index) for c in CN}
dures = [c for c in CN if len(tombe[c]) >= 3]
isoles = [(tombe[c][0], c) for c in CN if len(tombe[c]) == 1]
perdants = sorted({m for c in dures for m in tombe[c]}, key=ORD_T.index)


def _et(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


note = ((f"{_et(libres)} are free for every detector. " if libres else "")
        + "The loss concentrates on "
        + f"{_et(dures)}, where {_et(perdants)} all fall below 0.93"
        + (f"; elsewhere only {_et([f'{m} on {c}' for m, c in isoles])} "
           f"drop{'s' if len(isoles) == 1 else ''} that far. "
           if isoles else ". ")
        + f"The lowest cell is {pire[1]} on {pire[2]} ({pire[0]:.3f}), "
        + f"against {Mt[0].min():.3f} for the leading detector's worst class. "
        + _avant())
fig.text(.5, .045, "\n".join(textwrap.wrap(note, 108)), ha="center",
         fontsize=8.2, color="#25292e")
plt.tight_layout(rect=[0, .13, 1, 1])
plt.savefig(OUT / "figure18_per_class_f1_temporal.png", dpi=285)
plt.close()
print(f"figure 18 : ordre temporel {ORD_T}")
print(f"            cellule la plus basse {pire[1]} / {pire[2]} = {pire[0]:.4f}")
print("\nles trois figures sont ecrites dans", OUT)
