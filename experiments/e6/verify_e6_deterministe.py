#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6, second volet : le binning rendu deterministe sur GeNIS.

Le premier volet (reproduce_binning.py) a montre, sur des donnees
synthetiques et a decoupage fixe, que la construction des bins suffit a
produire la forme observee : des chutes discretes sur la classe la plus
rare. C'etait une preuve de suffisance, pas d'operation.

Ce volet est l'experience qui tranche, et elle tranche contre l'hypothese.
Cinq ajustements a 10 s, memes cinq decoupages que la campagne publiee,
subsample_for_bin porte au-dela de la taille du jeu d'entrainement -- la
grille d'histogramme devient deterministe et plus rien d'autre ne change.

Resultat : l'effondrement de la graine 3 disparait, et les graines 2 et 4
s'effondrent a sa place, la pire des deux nettement plus bas que l'original.
Le binning n'est donc pas la cause. Le candidat principal est elimine.

Entrees, toutes committees :
  experiments/e6/e6_deterministe_results.json   les cinq ajustements
  experiments/e5/e5_results.json                les cinq valeurs publiees
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
D = json.loads((HERE / "e6_deterministe_results.json").read_text(encoding="utf-8"))
E5 = json.loads((REPO / "experiments" / "e5" / "e5_results.json").read_text(encoding="utf-8"))

PUB = E5["table_macro_f1"]["10|lightgbm"]      # les cinq valeurs du tableau 6
REF = D["reference"]
DET = D["verdict"]["deterministe"]
GRAINES = ["1", "2", "3", "4", "5"]
SEUIL = 0.99                                    # en deca, un run est effondre
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK   ' if cond else 'ECHEC'} {nom}{('  ' + detail) if detail else ''}")


# =========================================================================
# A. L'experience est valide : l'environnement rejoue la campagne publiee
# =========================================================================
# Sans ce controle, toute difference entre les deux bras pourrait venir de
# l'environnement Colab plutot que du binning. Le temoin est la graine 1
# rejouee avec le binning d'origine.
print("A. Le temoin, qui rend la comparaison lisible\n")
tem = D["runs"]["temoin|ech"]["macro_f1"]
chk("le temoin rejoue la graine 1 publiee au dernier chiffre",
    tem == PUB["1"], f"{tem!r}")
chk("le notebook declare le temoin reproduit", D["verdict"]["temoin_reproduit"])
chk("le bloc de reference est le tableau 6, graine pour graine",
    all(REF[g] == PUB[g] for g in GRAINES))
chk("le temoin a bien tourne sans binning force",
    D["runs"]["temoin|ech"]["subsample_for_bin"] is None)

print("\n   les cinq valeurs publiees, pour memoire :")
for g in GRAINES:
    print(f"     graine {g} : {PUB[g]:.4f}" + ("   <-- effondrement" if PUB[g] < SEUIL else ""))

# =========================================================================
# B. Le binning a bien ete rendu deterministe
# =========================================================================
print("\n\nB. Le bras deterministe est bien deterministe\n")
det_runs = {g: D["runs"][f"det|seed{g}"] for g in GRAINES}
n_train = {r["n_train"] for r in det_runs.values()}
chk("les cinq ajustements portent sur le meme volume", len(n_train) == 1,
    f"{n_train.pop():,} lignes".replace(",", " "))
chk("subsample_for_bin depasse la taille du jeu d'entrainement pour les cinq",
    all(r["subsample_for_bin"] > r["n_train"] for r in det_runs.values()),
    f"{det_runs['1']['subsample_for_bin']:,}".replace(",", " "))
chk("le bras deterministe rend bien les macro-F1 du verdict",
    all(det_runs[g]["macro_f1"] == DET[g] for g in GRAINES))

# =========================================================================
# C. Le resultat : la liste des effondrements change, ils ne disparaissent pas
# =========================================================================
print("\n\nC. Ce que le binning deterministe fait, et ne fait pas\n")
av = sorted(g for g in GRAINES if REF[g] < SEUIL)
ap = sorted(g for g in GRAINES if DET[g] < SEUIL)
print(f"   {'graine':>7} {'publie':>10} {'deterministe':>14}")
for g in GRAINES:
    mark = ""
    if REF[g] < SEUIL and DET[g] >= SEUIL:
        mark = "   <-- guerit"
    elif REF[g] >= SEUIL and DET[g] < SEUIL:
        mark = "   <-- s'effondre"
    print(f"   {g:>7} {REF[g]:>10.4f} {DET[g]:>14.4f}{mark}")

chk("un seul effondrement avant, la graine 3", av == ["3"])
chk("l'effondrement de la graine 3 disparait", DET["3"] >= SEUIL,
    f"{REF['3']:.4f} -> {DET['3']:.4f}")
chk("mais deux autres apparaissent", ap == ["2", "4"])
chk("le notebook conclut au verdict mixte", D["verdict"]["conclusion"] == "mixte")
chk("VERDICT : le binning n'est pas la cause, il n'y a pas moins d'echecs",
    len(ap) >= len(av), f"{len(av)} avant, {len(ap)} apres")
chk("et le pire echec est nettement plus bas qu'avant",
    min(DET.values()) < min(REF.values()) - 0.3,
    f"{min(DET.values()):.4f} contre {min(REF.values()):.4f}")

# =========================================================================
# D. Les nouveaux echecs n'ont pas la signature de l'ancien
# =========================================================================
# La 6.4 decrivait l'echec publie par trois marques : degradation suivant la
# rarete, ROC-AUC qui tombe sans s'effondrer, ajustement 15 % plus long. Les
# deux nouveaux echecs n'en partagent qu'une seule.
print("\n\nD. La signature des nouveaux echecs\n")
sains = [g for g in GRAINES if DET[g] >= SEUIL]
t_sain = sum(det_runs[g]["fit_time_s"] for g in sains) / len(sains)
print(f"   {'graine':>7} {'macro-F1':>9} {'ROC-AUC':>9} {'FPR':>8} {'ajustement':>12}")
for g in GRAINES:
    r = det_runs[g]
    print(f"   {g:>7} {r['macro_f1']:>9.4f} {r['binary']['roc_auc']:>9.4f} "
          f"{r['binary']['fpr']:>8.4f} {r['fit_time_s']:>10.1f} s")

chk("la graine 2 perd l'ordonnancement, pas seulement le seuil",
    det_runs["2"]["binary"]["roc_auc"] < 0.55,
    f"ROC-AUC {det_runs['2']['binary']['roc_auc']:.4f}, quasi le hasard")
chk("et son taux de faux positifs explose",
    det_runs["2"]["binary"]["fpr"] > 0.9, f"{det_runs['2']['binary']['fpr']:.4f}")
chk("les classes rares tombent a zero, pas a une valeur basse",
    all(det_runs["2"]["per_class_f1"][c] == 0.0
        for c in ("bruteforce-ftp", "bruteforce-smb", "bruteforce-ssh")))
chk("AUCUN des deux echecs ne montre l'ajustement allonge de l'echec publie",
    all(det_runs[g]["fit_time_s"] < t_sain * 1.05 for g in ap),
    f"{det_runs['2']['fit_time_s']:.0f} s et {det_runs['4']['fit_time_s']:.0f} s "
    f"contre {t_sain:.0f} s pour les sains")

# =========================================================================
# E. Ce que le papier peut dire
# =========================================================================
print("\n\nE. Ce qui reste vrai des conclusions\n")
chk("a 10 s, un ajustement isole reste indigne de confiance sous les deux bras",
    len(av) > 0 and len(ap) > 0)
chk("la perte est discrete, pas graduelle : rien entre 0.84 et 0.99",
    not any(SEUIL > v > 0.84 for v in list(REF.values()) + list(DET.values())))
moy_det = sum(DET.values()) / 5
moy_ref = sum(REF.values()) / 5
chk("une moyenne sur graines dissimulerait les deux",
    moy_ref > 0.96 and moy_det > 0.84,
    f"moyennes {moy_ref:.4f} et {moy_det:.4f}")

print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("\nLECTURE. Le candidat principal est elimine. Rendre la grille\n"
          "d'histogramme deterministe ne stabilise pas la campagne : la graine 3\n"
          "guerit, les graines 2 et 4 s'effondrent, et la pire des deux tombe a\n"
          "0.4193 contre 0.8374 pour l'echec d'origine. L'instabilite a 10 s ne\n"
          "vient donc pas de la construction des bins, et le correctif qu'on\n"
          "aurait recommande en restant au premier volet aurait empire les\n"
          "choses. Ce que le papier rapporte est l'instabilite elle-meme.")
sys.exit(0 if all(ok) else 1)
