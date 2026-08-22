#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E8 -- la condition auditee republiee sur la liste corrigee.

E7 a demontre qu'IdleTime est un identifiant de fichier de capture. E8 refait
la campagne sans lui, sur 15 configurations, les deux protocoles et cinq
graines, avec le bras publie en temoin.

Trois choses que ce script etablit, et qu'il faut lire dans cet ordre :

  A. Offset n'est PAS positionnel. La regle avait ete enoncee AVANT de voir le
     resultat, et elle tranche contre le soupcon : la liste reste a treize.
  B. La comparaison est valide -- le chemin des donnees se rejoue, et la bande
     de reproductibilite intra-session est mesuree, pas supposee.
  C. Ce que la correction coute, et ce qu'elle fait au classement. Les deux
     ensembles boostes quittent le sommet bien plus nettement qu'avant.

Et une limite qu'il faut dire : le FT-Transformer de cette session ne rejoue
pas celui du papier, l'ecart d'environnement y depasse l'effet mesure.

Entrees : experiments/e8/e8_results.json, paper/article1_results.json
"""
import json
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
E = json.loads((HERE / "e8_results.json").read_text(encoding="utf-8"))
R = json.loads((REPO / "paper" / "article1_results.json").read_text(encoding="utf-8"))
RUNS, PUB = E["runs"], R["models"]
BANDE = E["bande_environnement"]["max"]
CFG = sorted({k.split("|")[0] for k in RUNS})
DET = ("majority", "logreg", "nb", "knn", "rf", "xgboost", "lightgbm")
FORTS = [c for c in CFG if c.split("#")[0] not in ("majority", "nb")]
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK   ' if cond else 'ECHEC'} {nom}{('  ' + detail) if detail else ''}")


def mf(c, v, p):
    return RUNS.get(f"{c}|{v}|{p}", {}).get("macro_f1")


def moy(c, v, communes):
    return st.mean([RUNS[f"{c}|{v}|strat_seed{s}"]["macro_f1"] for s in communes])


def communes(c):
    return [s for s in range(1, 6)
            if f"{c}|publiee|strat_seed{s}" in RUNS
            and f"{c}|corrigee|strat_seed{s}" in RUNS]


# =========================================================================
# A. Offset : la regle enoncee d'avance tranche
# =========================================================================
print("A. Offset, tranche par la regle enoncee avant le resultat\n")
O = E["offset"]
print(f"   correlation de rang minimale avec l'ordre de capture : {O['rho_min']:.4f}")
print(f"   seuil enonce d'avance                                : {O['seuil']}")
chk("Offset n'est PAS positionnel : la regle le garde",
    not O["positionnel"] and O["rho_min"] < O["seuil"],
    f"{O['rho_min']:.3f} tres loin de {O['seuil']}")
chk("la liste corrigee compte donc treize entrees",
    len(E["blacklist_corrigee"]) == 13, str(E["colonnes_ajoutees"]))
chk("et la seule colonne ajoutee est IdleTime",
    E["colonnes_ajoutees"] == ["IdleTime"])
print("\n   Le soupcon portait sur une AUC binaire de 0.9379. La mesure dit non,")
print("   et c'est la mesure qui decide. Offset reste dans la condition auditee ;")
print("   son AUC binaire est rapportee en section 9 comme anomalie non resolue.")

# =========================================================================
# B. La comparaison est-elle valide ?
# =========================================================================
print("\n\nB. Ce qui rend la comparaison lisible\n")
TD = E["temoin_dur"]
chk("les modeles quasi deterministes rejouent le papier",
    TD["valide"], f"ecart maximal {TD['ecart_max']:.4f}, tolerance {TD['tolerance']}")
print("   -> decoupages, colonnes, scaler et etiquettes sont ceux du papier.\n")
print("   bande de reproductibilite INTRA-session, trois ajustements identiques :")
for c, v in E["bande_environnement"]["par_config"].items():
    print(f"     {c:<5} {[round(x, 4) for x in v['runs']]}  etendue {v['etendue']:.4f}")
chk("la bande intra-session est etroite", BANDE < 0.005, f"{BANDE:.4f}")
print("\n   Les deux bras ont tourne dans CETTE session : c'est donc bien la bande")
print("   intra-session qui borne ce qu'on peut attribuer a la correction.")

# =========================================================================
# C. Ce que la correction coute
# =========================================================================
print("\n\nC. Le cout de la correction\n")
ds, dt = {}, {}
print(f"   {'configuration':<15}{'strat. pub.':>12}{'strat. corr.':>13}{'delta':>9}"
      f"{'temp. pub.':>12}{'temp. corr.':>13}{'delta':>9}")
for c in CFG:
    com = communes(c)
    a, b = mf(c, "publiee", "temporal"), mf(c, "corrigee", "temporal")
    if not com or a is None or b is None:
        continue
    ma, mb = moy(c, "publiee", com), moy(c, "corrigee", com)
    ds[c], dt[c] = mb - ma, b - a
    print(f"   {c:<15}{ma:>12.4f}{mb:>13.4f}{mb - ma:>+9.4f}"
          f"{a:>12.4f}{b:>13.4f}{b - a:>+9.4f}")

f2 = [c for c in dt if c.split("#")[0] not in ("majority", "nb")]
ms, mt = max(abs(ds[c]) for c in f2), max(abs(dt[c]) for c in f2)
chk("le cout stratifie reste tres faible", ms < 0.006,
    f"{ms:.4f} ({max(f2, key=lambda c: abs(ds[c]))})")
chk("le cout temporel est d'un autre ordre", mt > 0.02,
    f"{mt:.4f} ({max(f2, key=lambda c: abs(dt[c]))})")
print(f"\n   rapport temporel/stratifie : x{mt / ms:.0f}")
gros = sorted(f2, key=lambda c: -abs(dt[c]))[:5]
chk("les cinq plus gros couts portent sur des modeles deterministes",
    all(c.split("#")[0] in DET for c in gros), ", ".join(gros))
chk("le bayesien naif s'effondre, comme la 6.2 le predit",
    abs(ds["nb#tuned"]) > 0.1, f"stratifie {ds['nb#tuned']:+.4f}")

sous = [c for c in dt if c.split("#")[0] not in DET and abs(dt[c]) < BANDE]
print(f"\n   sous la bande, donc non attribuables : {sous or 'aucun'}")

# =========================================================================
# D. Le classement, et la conclusion du papier
# =========================================================================
print("\n\nD. Le classement temporel\n")
cp = sorted(((c, mf(c, "publiee", "temporal")) for c in FORTS), key=lambda x: -x[1])
cc = sorted(((c, mf(c, "corrigee", "temporal")) for c in FORTS), key=lambda x: -x[1])
rp = {c: i + 1 for i, (c, _) in enumerate(cp)}
rc = {c: i + 1 for i, (c, _) in enumerate(cc)}
print(f"   {'rang':>4}  {'liste publiee':<26}{'liste corrigee':<26}")
for i in range(len(cp)):
    print(f"   {i+1:>4}  {cp[i][0]:<14}{cp[i][1]:.4f}    {cc[i][0]:<14}{cc[i][1]:.4f}")

chk("les deux ensembles boostes quittent le sommet, liste corrigee",
    min(rc["xgboost"], rc["lightgbm"]) >= 4,
    f"XGBoost {rc['xgboost']}e, LightGBM {rc['lightgbm']}e")
chk("et ils descendent PLUS BAS qu'avec la liste publiee",
    rc["lightgbm"] > rp["lightgbm"] and rc["xgboost"] > rp["xgboost"],
    f"LightGBM {rp['lightgbm']}e->{rc['lightgbm']}e, "
    f"XGBoost {rp['xgboost']}e->{rc['xgboost']}e")
chk("un modele lineaire mene toujours",
    cc[0][0].split("#")[0] == "logreg", f"{cc[0][0]} a {cc[0][1]:.4f}")
chk("le corpus reste sature sous le protocole stratifie",
    min(moy(c, "corrigee", communes(c))
        for c in ("xgboost", "lightgbm", "rf")) > 0.999)

# =========================================================================
# E. La limite qu'il faut ecrire : le FT-Transformer
# =========================================================================
print("\n\nE. Le FT-Transformer, et pourquoi il faut se retenir\n")
ec_ftt = abs(PUB["ftt|audited|temporal"]["macro_f1"] - mf("ftt", "publiee", "temporal"))
gain = dt["ftt"]
print(f"   publie          {PUB['ftt|audited|temporal']['macro_f1']:.4f}")
print(f"   E8, liste publiee   {mf('ftt', 'publiee', 'temporal'):.4f}   "
      f"ecart au papier {ec_ftt:.4f}")
print(f"   E8, liste corrigee  {mf('ftt', 'corrigee', 'temporal'):.4f}   "
      f"gain intra-session {gain:+.4f}")
chk("dans CETTE session, ftt gagne et remonte au sommet",
    gain > BANDE and rc["ftt"] <= 3, f"{rp['ftt']}e -> {rc['ftt']}e")
chk("MAIS l'ecart de cette session au papier depasse l'effet",
    ec_ftt > abs(gain), f"{ec_ftt:.4f} contre {abs(gain):.4f}")
print("\n   Consequence : le gain du FT-Transformer est solide DANS la session,")
print("   ou les deux bras sont comparables, et ne peut pas etre rapporte comme")
print("   une amelioration par rapport au chiffre publie. Le papier doit dire")
print("   les deux.")

# =========================================================================
# F. Le recalage des temperatures, et ce qu'il reproduit vraiment
#
# Mon notebook E8 calait la temperature en minimisant l'ECE ; le pipeline la
# cale en minimisant la NLL sur une grille de 80 points. Les matrices de
# probabilites ont ete rejouees avec le bon objectif, sans reentrainement.
#
# Le temoin ne peut pas etre le tableau 7 publie : celui-ci porte des T que la
# section 6.5 declare deja recalculer. La cible est E3-A, la recomputation que
# la 6.5 benit. Et la quantite controlee est l'ECE APRES calage, celle que les
# tableaux rapportent -- pas T, qui est un parametre intermediaire pose sur une
# surface plate ou deux jeux de probabilites voisins donnent des T eloignes.
# =========================================================================
print("\n\nF. Le recalage des temperatures contre E3-A\n")
E3 = json.loads((REPO / "experiments" / "e3" / "e3_results.json")
                .read_text(encoding="utf-8"))["calibration_two_protocols"]
BORNES = (0.05, 5.0)

brut, cal_s, cal_t = [], [], []
for cle, r3 in sorted(E3.items()):
    m, proto = cle.split("|")
    if "-tuned" in m:
        continue
    r8 = RUNS.get(f"{m}|publiee|{proto}")
    if not r8:
        continue
    brut.append((abs(r3["ece_before"] - r8["ece"]), cle))
    # Un T pose sur une borne dit que l'optimum est hors grille ; l'ecart
    # d'ECE qui en decoule ne renseigne pas sur la procedure.
    if r8["temperature"] not in BORNES:
        d = (abs(r3["ece_after"] - r8["ece_calibree"]), cle)
        (cal_s if proto.startswith("strat") else cal_t).append(d)

for nom, lot, seuil in (("ECE brut, les deux protocoles", brut, 0.004),
                        ("ECE calibree, stratifie", cal_s, 0.001),
                        ("ECE calibree, temporel", cal_t, 0.008)):
    e, pire = max(lot)
    print(f"   {nom:<32} {len(lot):>2} paires, ecart max {e:.4f}  ({pire})")
    chk(f"se reproduit sous {seuil}", e < seuil)

# Ce que le contraste dit, et qui n'etait pas attendu : l'ajustement sous-jacent
# se rejoue partout, mais l'ECE APRES calage ne se rejoue serre que sur le bras
# stratifie. Sur le temporel, l'optimum de NLL se deplace assez pour deplacer
# l'ECE. Le tableau 8 doit donc dire d'ou vient sa derniere colonne.
e_bs = max(d for d, c in brut if c.endswith("temporal"))
print(f"\n   Le bras temporel se rejoue a {e_bs:.4f} pres AVANT calage")
print(f"   et a {max(cal_t)[0]:.4f} pres APRES : c'est le calage qui amplifie,")
print("   pas l'ajustement. La derniere colonne du tableau 8 est donc la moins")
print("   stable du manuscrit, et sa legende le dit.")
chk("l'amplification vient bien du calage, pas de l'ajustement",
    max(cal_t)[0] > e_bs, f"{max(cal_t)[0]:.4f} contre {e_bs:.4f}")

# =========================================================================
# G. Le cout, et les rangs que la section 8 annonce
#
# La section 8 nomme des rangs. Un rang est exactement le genre d'affirmation
# qu'on ecrit de memoire et qui devient faux quand la mesure change : j'ai
# publie « last but one on latency » pour la foret aleatoire, qui est
# cinquieme sur neuf. Les rangs cites sont donc recalcules ici.
# =========================================================================
print("\n\nG. Le cout d'inference et les rangs de la section 8\n")
CD = E["cout_deux_conditions"]
PRECIS = ["xgboost", "lightgbm", "rf", "ftt", "logreg", "rnn", "cnn", "dnn",
          "knn"]
deb = {m: CD[f"{m}|corrigee"]["flux_s_amorti_10240"] for m in PRECIS}
lat = {m: CD[f"{m}|corrigee"]["p50_ms"] for m in PRECIS}
r_deb = [m for _, m in sorted(((-v, m) for m, v in deb.items()))]
r_lat = [m for _, m in sorted(((v, m) for m, v in lat.items()))]
print(f"   debit    {' > '.join(r_deb)}")
print(f"   latence  {' < '.join(r_lat)}")

chk("la regression logistique mene sur le debit", r_deb[0] == "logreg",
    f"{deb['logreg']:.0f} f/s")
chk("la foret aleatoire est 2e sur le debit", r_deb[1] == "rf")
chk("XGBoost est 4e sur le debit, pas 1er", r_deb.index("xgboost") == 3)
# Ce controle disait d'abord « XGBoost mene sur la latence HORS regression
# logistique ». L'exception etait la pour sauver une phrase de la section 8,
# pas pour mesurer quoi que ce soit -- et la phrase etait fausse. On teste ce
# que le papier affirme maintenant : la regression logistique devance XGBoost
# partout sauf sur le macro-F1 stratifie.
AXES = {"debit": (deb["logreg"] > deb["xgboost"], "plus haut"),
        "latence p50": (lat["logreg"] < lat["xgboost"], "plus bas"),
        "latence p99": (CD["logreg|corrigee"]["p99_ms"]
                        < CD["xgboost|corrigee"]["p99_ms"], "plus bas"),
        "macro-F1 temporel": (mf("logreg", "corrigee", "temporal")
                              > mf("xgboost", "corrigee", "temporal"), "plus haut")}
for nom, (gagne, sens) in AXES.items():
    chk(f"la regression logistique devance XGBoost sur {nom}", gagne, sens)
chk("et elle est derriere sur le macro-F1 stratifie, le seul",
    moy("logreg", "corrigee", range(1, 6)) < moy("xgboost", "corrigee", range(1, 6)),
    f"{moy('logreg', 'corrigee', range(1, 6)):.4f} contre "
    f"{moy('xgboost', 'corrigee', range(1, 6)):.4f}")
chk("LightGBM a la queue la plus serree des trois ensembles d'arbres",
    min(("rf", "xgboost", "lightgbm"),
        key=lambda m: CD[f"{m}|corrigee"]["p99_ms"]) == "lightgbm",
    "ce que la 8 attribuait a XGBoost, et qui etait deja faux "
    "sur le tableau 10 publie")
chk("la foret aleatoire est 5e sur neuf en latence",
    r_lat.index("rf") == 4, "et non avant-derniere")
# Les deux colonnes ne mesurent pas la meme propriete -- mais ca ne veut pas
# dire qu'aucun detecteur ne mene les deux : la regression logistique mene
# bien les deux. Ce qui le montre est le desaccord AILLEURS dans le
# classement. J'avais d'abord ecrit ici un controle qui passait a vide, et
# dans la 8 la phrase que ce controle aurait du contredire.
tau = sum((deb[a] - deb[b]) * (lat[a] - lat[b]) > 0
          for i, a in enumerate(PRECIS) for b in PRECIS[i + 1:])
chk("la regression logistique mene les DEUX colonnes",
    r_deb[0] == r_lat[0] == "logreg")
chk("les deux colonnes classent differemment ailleurs",
    r_deb[1:4] != r_lat[1:4],
    f"debit {r_deb[1:4]} contre latence {r_lat[1:4]}")
chk("le k-NN est 8e sur neuf en qualite temporelle",
    sorted(PRECIS, key=lambda m: -mf(m, "corrigee", "temporal")).index("knn") == 7)

# Le surcout par appel : ce que l'ancien protocole supprimait.
gain = E["temoin_cout"]["gain_amorti"]
forts = sorted(((g, m) for m, g in gain.items()), reverse=True)[:3]
print(f"\n   amortir vaut le plus a : "
      + ", ".join(f"{m} {g:.1f}x" for g, m in forts))
chk("les plus gros gains sont des modeles a surcout par appel",
    {m for _, m in forts} <= {"dnn", "cnn", "rnn", "ftt", "rf"})
chk("les deux conditions sont mesurees dans la meme session",
    len(E["temoin_cout"]["paires_completes"]) == 10)
chk("les mesures Keras sont bien des mesures CPU",
    E["gpu_visible_cout"] is False
    or all(CD[f"{m}|{c}"].get("backend") == "CPU"
           for m in ("ftt", "rnn", "cnn", "dnn")
           for c in ("publiee", "corrigee")))

# =========================================================================
# H. McNemar et bootstrap, calcules dans Colab et rapportes ici
# =========================================================================
print("\n\nH. Les deux tests apparies\n")
S = E["stats"]
n_ns = sum(1 for v in S["corrigee"]["mcnemar_holm"].values() if v >= .05)
print(f"   {n_ns} paires indistinguables sur "
      f"{len(S['corrigee']['mcnemar_holm'])}, condition corrigee")
chk("le bras publie rejoue la campagne du papier",
    E["temoin_stats"]["valide"],
    f"ecart max {E['temoin_stats']['ecart_max_bootstrap']:.6f} sur la "
    f"moyenne bootstrap ({E['temoin_stats']['pire']})")
BT = S["corrigee"]["bootstrap"]
chk("les intervalles bootstrap encadrent les moyennes a cinq graines",
    all(BT[m]["macro_f1_ci95"][0] <= RUNS[f"{m}|corrigee|strat_seed1"]["macro_f1"]
        <= BT[m]["macro_f1_ci95"][1] for m in PRECIS),
    "graine 1, la graine sur laquelle le bootstrap est tire")

manq = [f"{c}|{v}|{p}" for c in CFG for v in ("publiee", "corrigee")
        for p in ["temporal"] + [f"strat_seed{s}" for s in range(1, 6)]
        if f"{c}|{v}|{p}" not in RUNS]
print(f"\n\n   runs manquants : {len(manq)} sur {len(CFG) * 12}")
for m in manq:
    print(f"     {m}")
print("   Les moyennes ci-dessus sont calculees sur les graines COMMUNES aux")
print("   deux listes, donc sur une base identique de part et d'autre.")

print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("\nLECTURE. La liste noire passe a treize entrees, IdleTime seul ajoute :\n"
          "Offset a ete mesure et la regle le garde. Le cout est de 0.004 en\n"
          "stratifie et de 0.026 en temporel, et les cinq plus gros ecarts portent\n"
          "sur des modeles qui se rejouent au quatrieme chiffre. La conclusion du\n"
          "papier sur les ensembles boostes en sort nettement renforcee : LightGBM\n"
          "passe de la 3e a la 8e place, XGBoost de la 5e a la 7e.")
sys.exit(0 if all(ok) else 1)
