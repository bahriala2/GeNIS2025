#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figures 5, 9, 10, 11, 14 et 18, redessinees sur la condition auditee CORRIGEE.

E7 a montre qu'IdleTime est un identifiant de fichier de capture ; E8 a refait
la campagne sans lui. Ces trois figures dependent de la condition auditee et
doivent donc etre redessinees. Les figures 9 (McNemar) et 11 (bootstrap) demandaient les matrices de
probabilites, qui font 380 Mo et ne peuvent pas quitter Colab. Elles n'en ont
pas besoin ici : e8quater y a fait le calcul et n'en a rapporte que le
resultat -- 45 valeurs de p, 45 corrigees, dix moyennes et dix intervalles,
sous "stats" dans e8_results.json.

La figure 14 est un cas mixte, et c'est pour ca qu'elle etait restee de cote.
Son axe vertical est le macro-F1 temporel, qui a change pour les neuf
detecteurs ; son axe horizontal est le debit, mesure sur 55 colonnes et pas
remesure. Laisser la figure telle quelle affichait neuf points a la mauvaise
hauteur, ce qui est pire qu'un axe dont la provenance est ecrite : la legende
nomme desormais la condition de chaque axe, comme le fait le tableau 10.
Elle n'avait par ailleurs aucun script de regeneration -- MAPPING.md la
listait comme un manque -- et en voici un.

Rien n'est recopie : chaque valeur vient de experiments/e8/e8_results.json,
condition "corrigee". Les colonnes full et clean de la figure 10 viennent de
article1_results.json et ne changent pas -- elles n'ont jamais utilise la
liste noire.

Sorties : paper/figures_manuscrit/figure{05,09,10,11,14,18}_*.png
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

# =========================================================================
# Figure 14 — cout d'inference contre qualite, protocole temporel
# =========================================================================
# Les deux axes viennent maintenant de la meme condition et de la meme
# session. Le debit est celui du protocole qui amortit reellement le surcout
# par appel -- celui que la legende du tableau 10 annoncait deja -- et les
# modeles Keras y ont ete mesures sous tf.device("/CPU:0").
E8C = json.loads((REPO / "experiments" / "e8" / "e8_results.json")
                 .read_text(encoding="utf-8"))["cout_deux_conditions"]
COUT = {m: E8C[f"{m}|corrigee"]["flux_s_amorti_10240"] for m in ORD}
PROFOND = {"ftt", "rnn", "cnn", "dnn"}
P14 = sorted(((COUT[m], run(m, "temporal")["macro_f1"], m)
              for m in ORD if m != "nb"), key=lambda t: -t[1])
# Decalages d'etiquette, en points. Le defaut place au-dessus a droite ; les
# exceptions sont les seuls points ou ca chevauchait un voisin ou le cadre.
DEC = {"logreg": (-8, 8, "right"), "rf": (8, -12, "left"),
       "dnn": (8, -12, "left"), "lightgbm": (-8, -12, "right"),
       "cnn": (8, 8, "left"), "rnn": (-8, -12, "right")}

# La figure remplace l'image d'origine EN PLACE dans le document, sous son nom
# de hachage : on garde donc ses 1803 x 1276 pixels, pour que l'extent declare
# dans le .docx reste juste et que rien ne soit etire.
fig, ax = plt.subplots(figsize=(1803 / 285, 1276 / 285))
for deb, q, m in P14:
    creux = m in PROFOND
    ax.scatter(deb, q, s=95 if creux else 105,
               marker="^" if creux else "o",
               color="#c23b34" if creux else "#4a72b0", zorder=3)
    dx, dy, ha = DEC.get(m, (8, 8, "left"))
    ax.annotate(m, (deb, q), textcoords="offset points", xytext=(dx, dy),
                ha=ha, fontsize=9.5, color="#3b4046")
ax.set_xscale("log")
ax.set_xlabel("CPU throughput (flows/s, batch 512, log scale)", fontsize=10)
ax.set_ylabel("macro-F1, temporal protocol", fontsize=10)
ax.set_title("Inference cost versus detection quality", fontsize=12)
ax.grid(alpha=.25, color="#c9cdd2")
ax.set_axisbelow(True)
qs = [q for _, q, _ in P14]
marge = (max(qs) - min(qs)) * .12
ax.set_ylim(min(qs) - marge, max(qs) + marge)
ax.scatter([], [], s=105, marker="o", color="#4a72b0", label="classical / tree")
ax.scatter([], [], s=95, marker="^", color="#c23b34", label="deep")
ax.legend(loc="lower right", fontsize=9.5, framealpha=.95)
plt.tight_layout()
plt.savefig(OUT / "figure14_cost_vs_quality.png", dpi=285)
plt.close()

# Les trois affirmations que porte la legende, recalculees et non recopiees :
# l'etendue du debit, l'ecart entre le meilleur et son voisin a haut debit, et
# la domination du DNN sur les deux axes.
etendue = max(d for d, _, _ in P14) / min(d for d, _, _ in P14)
tete = P14[0]
second = P14[1]
rapport = second[0] / tete[0]
d_dnn, q_dnn, _ = next(t for t in P14 if t[2] == "dnn")
domine = [m for d, q, m in P14 if d > d_dnn and q > q_dnn]
print(f"figure 14 : debit sur {etendue:.0f}x, soit "
      f"{len(str(int(etendue))) - 1} ordres de grandeur")
print(f"            {tete[2]} mene a {tete[1]:.4f}, {second[2]} a "
      f"{second[1] - tete[1]:+.4f} pour {rapport:.0f}x le debit")
print(f"            dnn domine sur les deux axes par : {domine}")

# =========================================================================
# Figures 9 et 11 — les deux tests apparies, sur la condition corrigee
# =========================================================================
ST = json.loads((REPO / "experiments" / "e8" / "e8_results.json")
                .read_text(encoding="utf-8"))["stats"]["corrigee"]
HOLM, BOOT = ST["mcnemar_holm"], ST["bootstrap"]

# --- 9 : McNemar apparie, correction de Holm ------------------------------
# Ordre par macro-F1 decroissant, comme la figure publiee : la lecture est
# "les meilleurs sont-ils separables entre eux ?", et elle demande que les
# meilleurs soient cote a cote.
M9 = sorted(BOOT, key=lambda m: -moy(m))
n9 = len(M9)


def holm(a, b):
    return HOLM.get(f"{a}|{b}", HOLM.get(f"{b}|{a}"))


ns = np.zeros((n9, n9))
for i, a in enumerate(M9):
    for j, b in enumerate(M9):
        if i != j:
            ns[i, j] = 1.0 if holm(a, b) >= .05 else 0.0
n_ns = int(ns.sum() // 2)

fig, ax = plt.subplots(figsize=(1486 / 285, 1653 / 285))
ax.imshow(np.where(np.eye(n9, dtype=bool), np.nan, ns),
          cmap=matplotlib.colors.ListedColormap(["#eaeef2", "#4a72b0"]),
          vmin=0, vmax=1)
for i in range(n9):
    for j in range(n9):
        if i != j and ns[i, j]:
            ax.text(j, i, "ns", ha="center", va="center", fontsize=8.5,
                    color="white")
ax.set_xticks(range(n9))
ax.set_xticklabels(M9, rotation=90, fontsize=9)
ax.set_yticks(range(n9))
ax.set_yticklabels(M9, fontsize=9)
ax.set_xticks(np.arange(-.5, n9), minor=True)
ax.set_yticks(np.arange(-.5, n9), minor=True)
ax.grid(which="minor", color="white", lw=1.4)
ax.tick_params(which="minor", length=0)
ax.grid(which="major", visible=False)
# La figure est etroite (5.2 in) et le sous-titre est long : sur une seule
# ligne il depassait le cadre a droite. On le coupe en deux.
ax.set_title(f"Saturation: {n_ns} model pairs are not distinguishable\n"
             "(McNemar, Holm-corrected, $\\alpha$ = 0.05;\n"
             "models ordered by macro-F1)", fontsize=10.5)
ax.legend(handles=[matplotlib.patches.Patch(color="#4a72b0",
                                            label="not distinguishable (p >= 0.05)"),
                   matplotlib.patches.Patch(color="#eaeef2",
                                            label="significantly different")],
          loc="upper center", bbox_to_anchor=(.5, -.22), ncol=2, fontsize=9,
          frameon=False)
plt.tight_layout()
plt.savefig(OUT / "figure09_mcnemar.png", dpi=285)
plt.close()
print(f"figure 9  : {n_ns} paires indistinguables sur "
      f"{n9 * (n9 - 1) // 2}")

# --- 11 : intervalles de confiance bootstrap ------------------------------
# Le bayesien naif est ecarte, comme dans la figure publiee : son intervalle
# est a 0.53 et ecraserait les neuf autres sur un point.
M11 = sorted((m for m in BOOT if m != "nb"),
             key=lambda m: BOOT[m]["macro_f1_mean"])
mu = [BOOT[m]["macro_f1_mean"] for m in M11]
lo = [mu[i] - BOOT[m]["macro_f1_ci95"][0] for i, m in enumerate(M11)]
hi = [BOOT[m]["macro_f1_ci95"][1] - mu[i] for i, m in enumerate(M11)]

fig, ax = plt.subplots(figsize=(1655 / 285, 964 / 285))
ax.errorbar(mu, range(len(M11)), xerr=[lo, hi], fmt="o", ms=6, capsize=3,
            lw=1.4, color="#4a72b0")
ax.set_yticks(range(len(M11)))
ax.set_yticklabels(M11, fontsize=10)
ax.set_xlabel("macro-F1 (95 % bootstrap CI, audited condition, seed 1)",
              fontsize=10)
ax.set_title("Stratified ranking: the top group is statistically "
             "indistinguishable", fontsize=11)
ax.grid(alpha=.3)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(OUT / "figure11_bootstrap_ci.png", dpi=285)
plt.close()
bas = min(BOOT[m]["macro_f1_ci95"][0] for m in M11)
print(f"figure 11 : {len(M11)} detecteurs, borne basse {bas:.4f} ({M11[0]})")

print("\nles six figures sont ecrites dans", OUT)
