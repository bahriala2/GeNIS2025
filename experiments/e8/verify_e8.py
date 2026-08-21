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
