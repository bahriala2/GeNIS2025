#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle final : la liste noire produite par le SEUL audit imbrique.

La demande est legitime et c'est la derniere qui porte sur l'experimentation :
la campagne publiee a ete entrainee sur une liste noire selectionnee avec de
l'information de test (section 4.3 le dit). L'audit imbrique, lui, tient
entierement dans la partition d'entrainement. Il faut donc montrer que la
liste qu'il produit *seul* soutient les memes conclusions.

Ce script montre quelque chose de plus fort qu'une simple concordance : sous
la regle que l'audit imbrique porte lui-meme, la liste qu'il produit EST la
liste publiee, colonne pour colonne. Le controle demande n'est pas un
reentrainement, c'est une identite -- et toute la campagne publiee est deja
ce controle.

Comme une identite peut sembler trop commode, le script encadre aussi les
deux lectures degradees de l'audit imbrique, toutes deux deja entrainees dans
E4c, et verifie que les conclusions principales tiennent sous les trois.

Entrees, toutes committees :
  experiments/e4a/e4abis_results.json   l'audit imbrique
  paper/article1_results.json           la campagne publiee
  experiments/e4c/e4c_results.json      les listes alternatives, reentrainees
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
N = json.loads((HERE / "e4abis_results.json").read_text(encoding="utf-8"))["nested"]
R = json.loads((REPO / "paper" / "article1_results.json").read_text(encoding="utf-8"))
C = json.loads((REPO / "experiments" / "e4c" / "e4c_results.json")
               .read_text(encoding="utf-8"))
A, M = R["audit"], R["models"]
P_MAX, K = A["chance"], A["rule"]["min_acc_x_chance"]
PUB = sorted(f for f in A["blacklist"] if f in N)
MODS = ["logreg", "nb", "knn", "rf", "xgboost", "lightgbm", "dnn", "cnn", "rnn"]
FORTS = [m for m in MODS if m != "nb"]
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK ' if cond else 'ECHEC'}  {nom}{('  ' + detail) if detail else ''}")


# =========================================================================
# A. La liste que l'audit imbrique produit seul
# =========================================================================
# Le filtre de predictivite est le meme que dans la regle publiee : une
# colonne doit etre individuellement predictive pour etre candidate.
elig = [f for f in N if N[f]["strat"] > K * P_MAX]
srt = sorted(elig, key=lambda f: N[f]["tau"])
taus = [N[f]["tau"] for f in srt]
# La coupure : le plus grand ecart du classement. C'est la regle que la
# section 4.3 enonce, et elle ne connait pas le nombre 8.
ecarts = sorted(((taus[i + 1] - taus[i], i + 1) for i in range(len(taus) - 1)),
                reverse=True)
gmax, rang = ecarts[0]
LISTE_1 = sorted(srt[:rang])

print("A. La liste produite par le seul audit imbrique\n")
print(f"   {len(elig)} colonnes eligibles sur {len(N)} comportementales")
print(f"   plus grand ecart du classement : {gmax:.4f}, apres le rang {rang}")
print(f"   liste obtenue ({len(LISTE_1)}) : {LISTE_1}")
print(f"   liste publiee ({len(PUB)}) : {PUB}\n")
chk("la coupure tombe apres le rang 8 sans qu'on le lui dise", rang == 8)
chk("IDENTITE : la liste imbriquee est la liste publiee", LISTE_1 == PUB)
chk("le seuil litteral tau < 0.50 n'exclut rien sur l'imbrique",
    min(taus) > 0.50, f"minimum {min(taus):.4f}")

print("\n   les cinq plus grands ecarts, pour situer la marge :")
for g, k in ecarts[:5]:
    print(f"     apres le rang {k:>2} : {g:.4f}"
          + ("   <-- retenu" if k == rang else ""))
marge = gmax / ecarts[1][0]
chk("le plus grand ecart devance nettement le suivant",
    marge > 1.15, f"{gmax:.4f} contre {ecarts[1][0]:.4f}, rapport {marge:.2f}")

# =========================================================================
# B. Les deux lectures degradees, deja entrainees dans E4c
# =========================================================================
# Une identite peut sembler trop commode : on encadre. Couper au deuxieme
# ecart donne les six colonnes de duree, qui sont la variante tau040 de E4c ;
# appliquer le seuil litteral ne donne rien, qui est la variante clean.
LISTE_2 = sorted(srt[:ecarts[1][1]])
print("\n\nB. Les deux lectures degradees de l'audit imbrique\n")
chk("couper au deuxieme ecart donne la variante tau040 de E4c",
    LISTE_2 == sorted(C["variantes"]["tau040"]), f"{len(LISTE_2)} colonnes")
chk("le seuil litteral donne la variante clean de E4c",
    C["variantes"]["clean"] == [])


def val(var, m, proto):
    if var == "tau050":                      # la campagne publiee
        return M[f"{m}|audited|{proto}"]["macro_f1"]
    return C["runs"][f"{m}|{var}|{proto}"]["macro_f1"]


print()
for proto, lab in (("strat_seed1", "stratifie"), ("temporal", "temporel")):
    d2 = {m: val("tau040", m, proto) - val("tau050", m, proto) for m in MODS}
    d3 = {m: val("clean", m, proto) - val("tau050", m, proto) for m in MODS}
    m2 = max(abs(d2[m]) for m in FORTS)
    m3 = max(abs(d3[m]) for m in FORTS)
    print(f"   {lab:10s} ecart max hors bayesien naif : "
          f"lecture 2 {m2:.4f} ({max(FORTS, key=lambda m: abs(d2[m]))}), "
          f"lecture 3 {m3:.4f} ({max(FORTS, key=lambda m: abs(d3[m]))})")
    chk(f"{lab} : lecture 2 sous 0.01", m2 < 0.01)
    chk(f"{lab} : lecture 3 sous 0.025", m3 < 0.025)

# =========================================================================
# C. Les conclusions principales, sous les trois lectures
# =========================================================================
print("\n\nC. Ce que les conclusions deviennent sous les trois lectures\n")

# 1. le corpus est sature sous le protocole stratifie
for var in ("tau050", "tau040", "clean"):
    v = [val(var, m, "strat_seed1") for m in ("xgboost", "lightgbm", "rf")]
    chk(f"sature en stratifie ({var}) : les trois ensembles >= 0.9999",
        min(v) >= 0.9999, f"min {min(v):.4f}")

# 2. les ensembles boostes quittent le sommet sous le protocole temporel
for var in ("tau050", "tau040", "clean"):
    cls = sorted(((m, val(var, m, "temporal")) for m in FORTS), key=lambda kv: -kv[1])
    pos = {m: i + 1 for i, (m, _) in enumerate(cls)}
    chk(f"boostes hors du podium temporel ({var})",
        min(pos["xgboost"], pos["lightgbm"]) >= 4,
        f"XGBoost {pos['xgboost']}e, LightGBM {pos['lightgbm']}e")

# 3. la calibration se degrade d'ordres de grandeur sous le protocole temporel
for var in ("tau040", "clean"):
    r = [C["runs"][f"{m}|{var}|temporal"]["ece"]
         / C["runs"][f"{m}|{var}|strat_seed1"]["ece"] for m in FORTS]
    med = sorted(r)[len(r) // 2]
    chk(f"ECE temporel >> ECE stratifie ({var})", min(r) > 1 and med > 10,
        f"mediane x{med:.0f}, min x{min(r):.0f}, max x{max(r):.0f}")

# 4. ce qui bouge, et qu'il faut dire : l'ordre DANS le groupe de tete
print()
for var, lab in (("tau050", "lecture 1"), ("tau040", "lecture 2"),
                 ("clean", "lecture 3")):
    cls = sorted(((m, val(var, m, "temporal")) for m in FORTS), key=lambda kv: -kv[1])
    print(f"   ordre temporel, {lab:10s} : " + " > ".join(m for m, _ in cls[:5]))
tete = set()
for var in ("tau050", "tau040", "clean"):
    cls = sorted(((m, val(var, m, "temporal")) for m in FORTS), key=lambda kv: -kv[1])
    tete |= {m for m, _ in cls[:3]}
chk("le groupe de tete permute mais reste dans un ensemble reduit",
    len(tete) <= 5, f"{sorted(tete)}")

print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("\nLECTURE : la liste noire issue du seul audit imbrique est la liste\n"
          "publiee. Le controle demande est donc satisfait par la campagne\n"
          "elle-meme, et les deux lectures degradees, deja entrainees, laissent\n"
          "les conclusions principales intactes.")
sys.exit(0 if all(ok) else 1)
