#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quatrieme verificateur : la prose dit-elle ce que les tableaux montrent ?

Les trois autres controlent le document. check_coherence.py verifie qu'il se
tient, check_style.py comment il est ecrit, check_layout.py ce qu'il donne une
fois pagine. Aucun ne peut voir qu'une phrase lit mal le tableau qu'elle cite,
et c'est la que les fautes se logent.

Ce que la relecture chiffre par chiffre a trouve, et qu'aucun des trois ne
pouvait attraper :

  - la 6.1 annoncait XGBoost a 1.0000 +/- 0.0000 la ou le tableau 2, juste
    au-dessus, affiche 0.9999 +/- 0.0001 ;
  - le tableau 13 donnait XGBoost « >= 0.9999 a tous les intervalles », alors
    que le minimum de ses vingt runs est 0.999789 ;
  - la 8 aplatissait le DNN a 30 s en « 0.85 », quand quatre graines sont vers
    0.849 et la cinquieme a 0.9879 -- ce que la 6.6 refuse explicitement de
    faire deux pages plus tot ;
  - la legende de la figure 15 comptait deux detecteurs sortant de sa bande ;
    il y en a quatre ;
  - la 6.3 attribuait au CNN une perte au reglage, alors que sa recherche
    n'a rien adopte et que son bras regle repete son bras par defaut.

Chaque controle ci-dessous recalcule une affirmation depuis les fichiers de
resultats. Un rang, un compte ou une borne est exactement ce qu'on ecrit de
memoire et qui devient faux des que la mesure change.

    python check_claims.py [chemin/vers/le.docx]

Sortie : la liste des ecarts, et un code de retour non nul s'il y en a.
"""
import json
import pathlib
import re
import statistics as st
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
DOCX = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
        else HERE / "GeNIS_benchmark_article.docx")

A = json.loads((HERE / "article1_results.json").read_text(encoding="utf-8"))
E8 = json.loads((REPO / "experiments" / "e8" / "e8_results.json")
                .read_text(encoding="utf-8"))
E5 = json.loads((REPO / "experiments" / "e5" / "e5_results.json")
                .read_text(encoding="utf-8"))["runs"]
E4B = json.loads((REPO / "experiments" / "e4b" / "e4b_results.json")
                 .read_text(encoding="utf-8"))
R8, CD, STA = E8["runs"], E8["cout_deux_conditions"], E8["stats"]["corrigee"]

with zipfile.ZipFile(DOCX) as z:
    BODY = ET.fromstring(z.read("word/document.xml")).find(W + "body")
ELS = list(BODY)


def txt(e):
    return "".join(t.text or "" for t in e.iter(W + "t"))


BLOCS = [txt(e) for e in ELS]
TABLEAUX = {}
for i, e in enumerate(ELS):
    if e.tag != W + "tbl":
        continue
    for j in range(i - 1, max(-1, i - 4), -1):
        m = re.match(r"Table (\d+)\.", BLOCS[j])
        if m:
            TABLEAUX[int(m.group(1))] = [
                [txt(tc).strip() for tc in tr.findall(W + "tc")]
                for tr in e.findall(W + "tr")]
            break

ecarts = []


def chk(nom, ok, detail=""):
    if not ok:
        ecarts.append(f"{nom}{('  ' + detail) if detail else ''}")
    print(f"  {'OK   ' if ok else 'ECART'} {nom}{('  ' + detail) if detail else ''}")


def prose(debut):
    """Le paragraphe qui commence par ce texte."""
    for t in BLOCS:
        if t.startswith(debut):
            return t
    raise LookupError(debut)


def cellule(n, ligne, col):
    """Une cellule d'un tableau, reperee par le libelle de sa ligne."""
    for r in TABLEAUX[n]:
        if r and r[0].strip() == ligne:
            return r[col].strip()
    raise LookupError(f"Table {n}, ligne {ligne!r}")


def moy(c, cond="corrigee"):
    return st.mean([R8[f"{c}|{cond}|strat_seed{s}"]["macro_f1"]
                    for s in range(1, 6)])


def tmp(c):
    return R8[f"{c}|corrigee|temporal"]["macro_f1"]


NOMS = {"XGBoost": "xgboost", "LightGBM": "lightgbm", "Random forest": "rf",
        "FT-Transformer": "ftt", "Logistic reg.": "logreg", "RNN": "rnn",
        "1D CNN": "cnn", "DNN": "dnn", "k-NN": "knn", "Naive Bayes": "nb",
        "Majority class": "majority"}

# =========================================================================
# A. Les tableaux calcules se rejouent depuis les fichiers de resultats
# =========================================================================
print("\nA. Les tableaux calcules contre leurs donnees\n")

for lab, c in NOMS.items():
    a = moy(c)
    dit = cellule(2, lab, 3)
    chk(f"tableau 2, {lab}, moyenne stratifiee",
        dit.startswith(f"{a:.4f}"), f"{dit!r} contre {a:.4f}")
chk("tableau 2, colonne temporelle",
    all(cellule(2, lab, 5) == f"{tmp(c):.4f}" for lab, c in NOMS.items()))

for lab, c in NOMS.items():
    if f"{c}|corrigee" not in CD:
        continue
    r = CD[f"{c}|corrigee"]
    chk(f"tableau 10, {lab}, debit",
        cellule(10, lab, 3).replace(" ", "").replace(" ", "")
        == f"{round(r['flux_s_amorti_10240']):d}",
        f"{cellule(10, lab, 3)!r}")

# Le tableau 6 porte soixante runs et aucune moyenne : chacun doit se
# retrouver tel quel dans les fichiers.
def run_int(iv, m, s):
    if iv == "60":
        return A["models"][f"{m}|audited|strat_seed{s}"]["macro_f1"]
    r = A["intervals"][iv]["runs"].get(f"{m}|seed{s}") or E5[f"{iv}|{m}|seed{s}"]
    return r["macro_f1"]


n6 = 0
for r in TABLEAUX[6][1:]:
    iv = r[0].replace(" s", "").strip()
    m = NOMS[r[1].strip()]
    for s in range(1, 6):
        if f"{run_int(iv, m, s):.4f}" != r[1 + s].strip():
            ecarts.append(f"tableau 6, {iv} s, {m}, graine {s}")
        n6 += 1
chk(f"tableau 6, les {n6} runs individuels", n6 == 60
    and not [x for x in ecarts if x.startswith("tableau 6")])

# =========================================================================
# B. Les rangs et les comptes que la prose annonce
#
# C'est la categorie qui pourrit en silence : un rang reste ecrit alors que
# la mesure sous lui a bouge.
# =========================================================================
print("\nB. Les rangs et les comptes de la prose\n")

PRECIS = ["xgboost", "lightgbm", "rf", "ftt", "logreg", "rnn", "cnn", "dnn",
          "knn"]
deb = {m: CD[f"{m}|corrigee"]["flux_s_amorti_10240"] for m in PRECIS}
lat = {m: CD[f"{m}|corrigee"]["p50_ms"] for m in PRECIS}
r_deb = sorted(PRECIS, key=lambda m: -deb[m])
r_lat = sorted(PRECIS, key=lambda m: lat[m])

p8 = prose("Since the leading models are statistically indistinguishable")
chk("la 6.7 place la regression logistique en tete du debit",
    r_deb[0] == "logreg" and "logistic regression dominates outright" in p8)
chk("la 6.7 place XGBoost quatrieme sur le debit",
    r_deb.index("xgboost") == 3 and "XGBoost fourth" in p8)
chk("la 6.7 n'attribue pas la latence la plus basse a XGBoost",
    not re.search(r"XGBoost leads on median latency", p8),
    f"la plus basse est {r_lat[0]}")

p1 = prose("Table 2 reports the nine-class benchmark")
chk("la 6.1 n'annonce pas XGBoost a 1.0000",
    "XGBoost and LightGBM reach macro-F1 1.0000" not in p1,
    f"sa moyenne est {moy('xgboost'):.4f}")
ns = [k for k, v in STA["mcnemar_holm"].items() if v >= .05]
chk(f"la 6.1 annonce {len(ns)} paires non significatives",
    f"{len(ns)} are not significantly different" in p1)
lr = {tuple(set(k.split("|")) - {"logreg"})[0] for k in ns if "logreg" in k}
for m in lr:
    nom = {"rnn": "the RNN", "cnn": "the CNN", "dnn": "the DNN"}[m]
    chk(f"la 6.1 cite {nom} comme non distinguable de la logistique",
        nom in p1)

# Les vingt runs d'intervalle de XGBoost : la borne annoncee doit tenir.
xg = [run_int(iv, "xgboost", s) for iv in ("5", "10", "30", "60")
      for s in range(1, 6)]
chk("le tableau 13 borne XGBoost au-dessus de son minimum reel",
    cellule(13, "XGBoost", 3).startswith("≥ 0.9998"),
    f"minimum reel {min(xg):.6f}, cellule {cellule(13, 'XGBoost', 3)!r}")

# Le bras regle : la recherche n'a rien adopte pour la plupart des modeles.
adopte = {m for m in A["hpo"] if A["hpo"][m].get("best_params")}
p3 = prose("Two observations qualify this")
chk("la 6.3 n'impute pas de perte au reglage a un modele sans reglage",
    "the CNN loses" not in p3,
    f"la recherche n'a adopte que pour {sorted(adopte)}")
d_dnn = moy("dnn#tuned") - moy("dnn")
chk("la 6.3 donne la bonne perte du DNN",
    f"{abs(d_dnn):.4f}" in p3, f"{d_dnn:+.4f}")

# =========================================================================
# C. Les legendes de figures qui comptent
# =========================================================================
print("\nC. Les legendes qui comptent des detecteurs\n")

ORI = ("o0.40", "o0.45", "o0.50", "o0.55", "o0.60")
M15 = ("logreg", "cnn", "rf", "rnn", "dnn", "knn", "lightgbm", "xgboost")
O = E4B["origines"]
sortent = [m for m in M15
           if any(O[f"{m}|{o}"]["macro_f1"] < 0.970 for o in ORI)]
f15 = prose("Figure 15. Macro-F1 at five rolling origins")
chk(f"la figure 15 compte {len(M15) - len(sortent)} detecteurs dans sa bande",
    f"{['zero', 'one', 'two', 'three', 'Four', 'five'][len(M15) - len(sortent)]}"
    " of them stay inside" in f15,
    f"en sortent : {sortent}")

cells = [v for m in PRECIS
         for v in R8[f"{m}|corrigee|strat_seed1"]["per_class_f1"].values()]
f5 = prose("Figure 5. Per-class F1 under the audited condition")
chk("la figure 5 donne sa cellule la plus basse", f"{min(cells):.4f}" in f5)
chk("la figure 5 ne compte pas onze detecteurs quand elle en montre dix",
    "Ten of the eleven detectors" not in f5)

f14 = prose("Figure 14. Inference cost against detection quality")
rap = round(deb["logreg"] / deb["ftt"])
chk("la figure 14 donne le bon rapport de debit",
    f"{rap:,}".replace(",", " ") in f14 or str(rap) in f14, f"{rap}")

# =========================================================================
# D. Les sections 1 a 6, ce que la seconde relecture y a trouve
# =========================================================================
print("\nD. Les affirmations des sections 1 a 6\n")

# Le bras regle : six detecteurs n'ont pas de configuration adoptee, et leur
# bras regle EST leur bras par defaut. Le dire « inerte » les confond avec
# ceux que la recherche a bel et bien touches.
INERTES = [c for c in ("xgboost", "lightgbm", "rf", "ftt", "rnn", "cnn")
           if c not in adopte]
p65 = prose("Hyperparameter tuning is similarly inert where it matters")
chk(f"la 6.5 dit que {len(INERTES)} detecteurs n'ont recu aucune configuration",
    "the search adopted no configuration at all for any of them" in p65,
    f"{INERTES}")
g_nb = moy("nb#tuned") - moy("nb")
chk("la 6.5 donne le bon gain du bayesien naif",
    f"{g_nb:+.4f}" in p65, f"{g_nb:+.4f}")

# Le calage sous protocole temporel : il ameliore les uns et aggrave les
# autres, et le compte doit suivre la mesure.
CAL = ("xgboost", "lightgbm", "rf", "ftt", "logreg", "rnn", "cnn", "dnn",
       "knn", "nb", "majority")
mieux = [m for m in CAL
         if R8[f"{m}|corrigee|temporal"]["ece_calibree"]
         < R8[f"{m}|corrigee|temporal"]["ece"]]
MOTS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven"]
pcal = prose("Temperature scaling is no longer inert under the temporal")
chk(f"la 6.5 compte {len(mieux)} ameliorations et {len(CAL) - len(mieux)} "
    "aggravations",
    f"improves {MOTS[len(mieux)]} of the eleven detectors and worsens "
    f"{MOTS[len(CAL) - len(mieux)]}" in pcal)
chk("la 6.5 ne dit plus que le calage repare le FT-Transformer",
    "repairs the FT-Transformer decisively" not in pcal,
    f"{R8['ftt|corrigee|temporal']['ece']:.4f} -> "
    f"{R8['ftt|corrigee|temporal']['ece_calibree']:.4f}")

# Les bornes de la 6.4. Une borne qui ne tient qu'a l'arrondi n'est pas une
# borne : la cellule DoS la plus basse de la figure 12 vaut 0.99287.
CL = A["slice60"]["classes"]
DOS = [c for c in CL if c.startswith("dos-")]


def lgbm(iv, s):
    return (A["intervals"][iv]["runs"].get(f"lightgbm|seed{s}")
            or E5[f"{iv}|lightgbm|seed{s}"])


bas = min(st.mean(lgbm(iv, s)["per_class_f1"][c] for s in (1, 2, 3))
          for iv in ("5", "10", "30") for c in DOS)
p12 = prose("Figure 12 resolves this by family")
m = re.search(r"never falling below (0\.\d+)", p12)
chk("la 6.4 borne les familles DoS sous leur minimum reel",
    m and float(m.group(1)) <= bas, f"minimum {bas:.5f}, borne {m.group(1)}")

fpr = max(lgbm("10", s)["binary"]["fpr"] for s in (1, 2, 4, 5))
p64 = prose("Table 6 gives the effect on detection")
chk("la 6.4 borne le FPR des quatre autres graines au-dessus du reel",
    f"{100 * fpr:.4f}%" in p64, f"{100 * fpr:.4f}%")

# Figure 2 : trois parts qui doivent sommer a 100 a la precision affichee.
cnt = A["slice60"]["class_counts"]
n = A["slice60"]["n"]
parts = {"dos": sum(v for k, v in cnt.items() if k.startswith("dos-")),
         "benign": cnt["benign"],
         "bf": sum(v for k, v in cnt.items() if k.startswith("bruteforce-"))}
f2 = prose("Figure 2. Class distribution of the 60-second slice")
aff = [float(x) for x in re.findall(r"(\d+\.\d+)%", f2)]
chk("les trois parts de la figure 2 somment a 100 comme affichees",
    abs(sum(aff[:3]) - 100) < 0.005, f"{aff[:3]} -> {sum(aff[:3]):.2f}")

# =========================================================================
print()
if ecarts:
    print(f"{len(ecarts)} ecart(s) entre la prose et les donnees :")
    for e in ecarts:
        print(f"  - {e}")
else:
    print("aucun ecart entre la prose, les tableaux et les donnees")
sys.exit(1 if ecarts else 0)
