#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pourquoi une graine de LightGBM s'effondre a 10 s, et pas les quatre autres.

Le manuscrit qualifiait l'evenement statistiquement -- un echec isole d'un
seul ajustement -- sans dire pourquoi un ajustement echoue. Un relecteur a eu
raison de le demander : sur un benchmark, un effondrement inexplique d'un
ensemble booste peut signaler une instabilite numerique, et il faut savoir
laquelle.

CE QUE LA GRAINE PILOTE REELLEMENT, ET QU'IL FAUT DIRE D'ABORD

  Dans tout ce papier, "graine" designe la graine du DECOUPAGE stratifie
  (train_test_split(..., random_state=s)). Le detecteur, lui, est construit
  avec random_state=0 fixe. Changer de graine change donc quels flux sont a
  l'entrainement et au test -- et, par ricochet, la grille d'histogramme de
  LightGBM, puisque ses bornes sont posees a partir d'un tirage de 200 000
  lignes DU JEU D'ENTRAINEMENT.

  Les deux bougent ensemble sur GeNIS, et ce script ne les separe pas. Il
  etablit trois choses plus modestes, et dit ce qu'il faudrait pour trancher.

CE QUE CE SCRIPT ETABLIT

  1. Le bagging et le tirage de colonnes sont desactives dans la
     configuration publiee : les deux mecanismes que l'on soupconne en
     premier devant un ensemble booste instable sont hors de cause.
  2. Le profil de l'echec est celui d'une defaillance cote entrainement, pas
     d'un tirage de test malheureux : degradation ordonnee par la rarete des
     classes, ROC-AUC effondre, exactitude globale intacte, ajustement plus
     long de 15 % a budget d'arbres fixe.
  3. Le tirage des bornes d'histogramme, A LUI SEUL et decoupage fixe, suffit
     a produire des chutes DISCRETES de grande amplitude sur une classe rare
     -- la forme exacte observee sur GeNIS. Quand on le desactive, la graine
     ne pilote plus rien : toutes les graines rendent la meme valeur.

CE QUE CE SCRIPT N'ETABLIT PAS

  Que c'est bien ce qui est arrive a la graine 3. Sur GeNIS, composition du
  jeu d'entrainement et grille d'histogramme changent ensemble. L'experience
  qui les separe est dans colab/ et coute cinq ajustements : refaire les cinq
  decoupages a 10 s avec subsample_for_bin porte au-dela de la taille du jeu
  d'entrainement. Si l'effondrement disparait, c'est la grille ; s'il
  persiste, c'est la composition du decoupage.

    python reproduce_binning.py
"""
import json
import pathlib
import sys

import numpy as np

try:
    import lightgbm as lgb
    from sklearn.metrics import f1_score
except ImportError as e:                     # pragma: no cover
    sys.exit(f"il manque une dependance : {e}")

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
R = json.loads((REPO / "paper" / "article1_results.json").read_text(encoding="utf-8"))

GRAINES = 16
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK ' if cond else 'ECHEC'}  {nom}{('  ' + detail) if detail else ''}")


# =========================================================================
# A. Ce que la configuration publiee met hors de cause
# =========================================================================
print("A. Quels mecanismes la configuration publiee elimine-t-elle ?\n")
# La campagne fixe trois parametres et laisse tout le reste aux defauts de la
# librairie. Ce sont ces defauts-la qui nous interessent.
DECLARES = {"n_estimators": 300, "num_leaves": 63, "learning_rate": 0.1}
print(f"   declares par le pipeline : {DECLARES}")
chk("aucun parametre supplementaire n'a ete adopte par la recherche",
    R["hpo"]["lightgbm"]["best_params"] == {},
    f"la configuration declaree atteignait deja "
    f"{R['hpo']['lightgbm']['default_val_macro_f1']:.4f} en validation")

p = lgb.LGBMClassifier(**DECLARES).get_params()
print(f"\n   ce que LightGBM {lgb.__version__} met alors en place tout seul :")
for k in ("subsample", "subsample_freq", "colsample_bytree", "subsample_for_bin",
          "min_child_samples"):
    print(f"     {k:20s} {p[k]}")

# Les deux mecanismes qu'on soupconne en premier devant un ensemble booste
# instable sont donc hors de cause, et il faut le dire avant d'en proposer
# un troisieme.
chk("\n   pas de bagging : le sous-echantillonnage de lignes est hors de cause",
    p["subsample"] == 1.0 and p["subsample_freq"] == 0,
    f"subsample={p['subsample']}, subsample_freq={p['subsample_freq']}")
chk("   pas de tirage de colonnes : hors de cause aussi",
    p["colsample_bytree"] == 1.0)
chk("   mais les bornes d'histogramme sont posees sur un tirage",
    p["subsample_for_bin"] == 200_000,
    f"subsample_for_bin={p['subsample_for_bin']:,} lignes du jeu d'entrainement")

# =========================================================================
# B. Ce que ce tirage couvre, intervalle par intervalle
# =========================================================================
print("\n\nB. Couverture du tirage de binning, selon l'intervalle d'agregation\n")
I = R["interval_stats"]
COUV = {}
print(f"   {'iv':>5s} {'entrainement':>13s} {'couverture':>11s} {'bruteforce-ftp':>15s}")
for iv in ("5", "10", "30", "60"):
    n_tr = int(0.6 * I[iv]["total"])
    COUV[iv] = min(1.0, p["subsample_for_bin"] / n_tr)
    ftp = I[iv]["files"]["attack-bruteforce-ftp"]
    print(f"   {iv+' s':>5s} {n_tr:>13,} {100*COUV[iv]:10.1f} % "
          f"{100*ftp/I[iv]['total']:14.3f} %")
# A 60 s le tirage prend presque toutes les lignes : la grille y est fixee
# par les donnees et ne peut guere varier d'un decoupage a l'autre. C'est le
# seul intervalle ou aucune graine ne s'ecarte.
chk("\n   a 60 s la grille est presque determinee par les donnees",
    COUV["60"] > 0.95, f"{100*COUV['60']:.1f} % des lignes")
chk("   a 10 s elle ne l'est pas", COUV["10"] < 0.30,
    f"{100*COUV['10']:.1f} % des lignes")

# =========================================================================
# C. Le profil de l'echec : entrainement, pas tirage de test
# =========================================================================
print("\n\nC. La graine 3 a 10 s, contre les quatre autres\n")
G3 = R["intervals"]["10"]["runs"]["lightgbm|seed3"]
G1 = R["intervals"]["10"]["runs"]["lightgbm|seed1"]
f, T = I["10"]["files"], I["10"]["total"]
PART = {"benign": f["benign-admin-activity"] + f["benign-background-activity"]
        + f["benign-user-activity"]}
for c in ("bruteforce-ftp", "bruteforce-smb", "bruteforce-ssh", "dos-hulk",
          "dos-icmp", "dos-pushack", "dos-slowloris", "dos-udp"):
    PART[c] = f["attack-" + c]

rangs = sorted(PART, key=lambda c: PART[c])
print(f"   {'classe':16s} {'part':>9s} {'F1 graine 3':>12s} {'F1 graine 1':>12s}")
for c in rangs:
    print(f"   {c:16s} {100*PART[c]/T:8.3f} % {G3['per_class_f1'][c]:12.4f} "
          f"{G1['per_class_f1'][c]:12.4f}")


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for j, i in enumerate(o):
            r[i] = j + 1
        return r
    a, b, n = rk(x), rk(y), len(x)
    return 1 - 6 * sum((a[i] - b[i]) ** 2 for i in range(n)) / (n * (n * n - 1))


rho = spearman([PART[c] for c in rangs], [G3["per_class_f1"][c] for c in rangs])
chk("\n   la degradation suit la rarete des classes", rho > 0.85,
    f"Spearman rho = {rho:.3f}")
chk("   l'exactitude globale bouge a peine",
    G3["accuracy"] > 0.98, f"{G3['accuracy']:.4f} contre {G1['accuracy']:.5f}")
# Un tirage de test malheureux deplacerait le seuil, pas l'ordonnancement.
chk("   mais le ROC-AUC chute : le modele n'ordonne plus",
    G3["binary"]["roc_auc"] < 0.98,
    f"{G3['binary']['roc_auc']:.4f} contre {G1['binary']['roc_auc']:.4f}")
chk("   et l'ajustement a suivi un autre chemin, a budget d'arbres fixe",
    G3["fit_time_s"] > 1.1 * G1["fit_time_s"],
    f"{G3['fit_time_s']:.1f} s contre {G1['fit_time_s']:.1f} s, "
    f"+{100*(G3['fit_time_s']/G1['fit_time_s']-1):.0f} %")

# =========================================================================
# D. Le binning seul, decoupage fixe, suffit-il a produire cette forme ?
# =========================================================================
print("\n\nD. Reproduction minimale : le binning seul, a decoupage fixe\n")
# Une classe rare a la meme part que bruteforce-ftp a 10 s, separee des
# autres par un intervalle etroit sur une seule colonne. Le decoupage est
# calcule UNE fois et ne bouge pas ; seul subsample_for_bin change entre les
# deux bras. C'est ce qui permet d'attribuer l'ecart au binning et a rien
# d'autre -- ce que les donnees de GeNIS, elles, ne permettent pas.
N, P_RARE = 400_000, PART["bruteforce-ftp"] / T
rng = np.random.default_rng(0)
n_rare = int(N * P_RARE)
X = np.empty((N, 4), dtype=np.float32)
y = np.zeros(N, dtype=int)
X[:, 0] = rng.normal(0, 10, N)
for j in (1, 2, 3):
    X[:, j] = rng.normal(0, 1, N)
y[:N // 3] = 1
y[N // 3:2 * N // 3] = 2
X[y == 1, 0] += 25
X[y == 2, 0] -= 25
idx = rng.choice(np.where(y == 0)[0], n_rare, replace=False)
y[idx] = 3
X[idx, 0] = rng.normal(4.0, 0.02, n_rare)
tr = np.zeros(N, bool)
tr[rng.choice(N, int(.6 * N), replace=False)] = True
n_tr = int(tr.sum())

print(f"   {N:,} lignes, classe rare {n_rare} = {100*n_rare/N:.3f} % "
      f"(celle de bruteforce-ftp a 10 s),")
print(f"   separee par un intervalle de 1/{np.ptp(X[:,0])/np.ptp(X[idx,0]):.0f} "
      f"de l'axe. Entrainement {n_tr:,} lignes, DECOUPAGE FIXE,")
print(f"   {GRAINES} graines par bras.\n")


def bras(sub, nom):
    v = np.array([f1_score(
        y[~tr],
        lgb.LGBMClassifier(random_state=s, subsample_for_bin=sub, n_jobs=8,
                           verbose=-1, deterministic=True, force_row_wise=True,
                           **DECLARES).fit(X[tr], y[tr]).predict(X[~tr]),
        average=None, labels=[0, 1, 2, 3])[3] for s in range(1, GRAINES + 1)])
    print(f"   {nom}")
    print(f"     subsample_for_bin = {sub:,}"
          + ("  (< n : tirage)" if sub < n_tr else "  (>= n : toutes les lignes)"))
    print(f"     moyenne {v.mean():.4f}  ecart-type {v.std(ddof=1):.4f}  "
          f"etendue {np.ptp(v):.4f}")
    print("     " + " ".join(f"{x:.3f}" for x in np.sort(v)) + "\n")
    return v


a = bras(int(COUV["10"] * n_tr), "bras A, binning echantillonne a la couverture de 10 s")
b = bras(n_tr + 1, "bras B, binning deterministe")

chk("le binning seul fait varier la classe rare d'une graine a l'autre",
    a.std(ddof=1) > 0.05, f"ecart-type {a.std(ddof=1):.4f}, etendue {np.ptp(a):.4f}")
# La forme compte autant que l'amplitude : sur GeNIS, aucun run n'a score
# entre 0.84 et 0.99. Une dispersion continue ne ressemblerait pas a cela.
_s = np.sort(a)
_trous = np.diff(_s)
chk("les valeurs sont discretes, pas une dispersion autour d'une moyenne",
    _trous.max() > 4 * np.median(_trous),
    f"plus grand trou {_trous.max():.4f} contre un ecart median de "
    f"{np.median(_trous):.4f}")
chk("binning deterministe : la graine ne pilote plus rien du tout",
    b.std(ddof=1) == 0.0, f"les {GRAINES} graines rendent {b[0]:.4f}")

# =========================================================================
print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("""
LECTURE. Le bagging et le tirage de colonnes sont hors de cause. Le profil de
l'echec est celui d'une defaillance cote entrainement. Et le tirage des bornes
d'histogramme, a lui seul et decoupage fixe, produit exactement la forme
observee : des chutes discretes sur la classe la plus rare, qui disparaissent
completement quand on rend le binning deterministe.

CE QUI RESTE OUVERT. Sur GeNIS la graine change le decoupage, donc la
composition du jeu d'entrainement ET la grille d'histogramme qui en derive.
Les deux bougent ensemble et ce script ne les separe pas. L'experience qui
tranche est dans colab/ : cinq ajustements a 10 s, binning rendu
deterministe.""")

(HERE / "e6_results.json").write_text(json.dumps({
    "ce_que_la_graine_pilote": "le decoupage stratifie ; le detecteur est a random_state=0 fixe",
    "params_declares": DECLARES,
    "defauts_librairie": {k: p[k] for k in ("subsample", "subsample_freq",
                                            "colsample_bytree", "subsample_for_bin")},
    "couverture_binning": COUV,
    "spearman_rarete_f1": rho,
    "graine3_10s": {k: G3[k] for k in ("macro_f1", "accuracy", "fit_time_s")},
    "graine3_roc_auc": G3["binary"]["roc_auc"],
    "graine1_10s_fit_time_s": G1["fit_time_s"],
    "reproduction": {
        "n": N, "part_classe_rare": P_RARE, "graines": GRAINES,
        "decoupage": "fixe entre les deux bras",
        "bras_a_echantillonne": {"ecart_type": a.std(ddof=1), "etendue": float(np.ptp(a)),
                                 "valeurs": sorted(a.tolist())},
        "bras_b_deterministe": {"ecart_type": b.std(ddof=1), "etendue": float(np.ptp(b)),
                                "valeurs": sorted(b.tolist())},
    },
}, indent=1), encoding="utf-8")
sys.exit(0 if all(ok) else 1)
