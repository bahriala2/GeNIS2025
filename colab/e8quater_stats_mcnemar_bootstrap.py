# =========================================================================
# E8-quater — McNemar et bootstrap, sur la condition corrigee
# =========================================================================
# A coller dans une NOUVELLE cellule du notebook e8_republication, apres
# avoir execute les cellules 1 a 6 (Execution > Tout executer suffit).
#
# POURQUOI. Les figures 9 (McNemar apparie, correction de Holm) et 11
# (intervalles de confiance bootstrap) sont les deux dernieres du manuscrit
# qui portent encore la condition a douze colonnes. Elles se recalculent
# depuis les matrices de probabilites, qui font 380 Mo -- intransportables.
#
# Cette cellule fait le calcul LA OU SONT LES DONNEES et n'en garde que le
# resultat : 45 valeurs de p, 45 valeurs corrigees, 10 moyennes et 10
# intervalles. Quelques kilo-octets dans e8_results.json, que vous renvoyez
# comme d'habitude. Rien d'autre ne bouge.
#
# AUCUN REENTRAINEMENT. Compter une a deux minutes.
import itertools

import numpy as np
from scipy.stats import chi2 as chi2dist
from sklearn.metrics import f1_score

for _n in ("STATE", "save_state", "kfile", "SPLITS", "y"):
    if _n not in dir():
        raise NameError(
            f"{_n} n'est pas defini : execute d'abord les cellules 1 a 6 "
            "du notebook (Execution > Tout executer).")

# Protocole gele du pipeline, recopie de article1_pipeline.ipynb cellule 33.
BOOTSTRAP_B = 1000
MODELES = ["cnn", "dnn", "ftt", "knn", "lightgbm", "logreg", "nb", "rf",
           "rnn", "xgboost"]                        # majority est hors figure


def mcnemar_p(pa, pb, yt):
    """McNemar apparie avec correction de continuite, 1 degre de liberte."""
    ca, cb = pa == yt, pb == yt
    b_, c_ = int((ca & ~cb).sum()), int((~ca & cb).sum())
    if b_ + c_ == 0:
        return 1.0
    return float(chi2dist.sf((abs(b_ - c_) - 1) ** 2 / (b_ + c_), 1))


def statistiques(cond):
    """Les deux tests sur une condition, graine 1, protocole stratifie."""
    _, _, i_test = SPLITS["strat_seed1"]
    yte = y[i_test]
    preds = {}
    for m in MODELES:
        f = kfile(f"{m}|{cond}|strat_seed1")
        if not f.exists():
            print(f"  {m}|{cond} : pas de matrice, ignore")
            continue
        preds[m] = np.load(f)["probs_test"].argmax(1)

    brut = {f"{a}|{b}": mcnemar_p(preds[a], preds[b], yte)
            for a, b in itertools.combinations(sorted(preds), 2)}
    # Holm : on ordonne par p croissant et on multiplie par le nombre de
    # tests restants. Identique au pipeline.
    ordre = sorted(brut, key=brut.get)
    mt = len(ordre)
    holm = {k: min(1., brut[k] * (mt - i)) for i, k in enumerate(ordre)}

    rng = np.random.RandomState(0)
    boot = {}
    for m, pr in preds.items():
        vals = [f1_score(yte[ix], pr[ix], average="macro", zero_division=0)
                for ix in (rng.randint(0, len(yte), len(yte))
                           for _ in range(BOOTSTRAP_B))]
        boot[m] = {"macro_f1_mean": float(np.mean(vals)),
                   "macro_f1_ci95": [float(np.percentile(vals, 2.5)),
                                     float(np.percentile(vals, 97.5))]}
    return {"mcnemar_raw": brut, "mcnemar_holm": holm, "bootstrap": boot}


# Les deux bras : le corrige pour les figures, le publie pour le temoin.
for cond in ("corrigee", "publiee"):
    print(f"{cond} …", flush=True)
    STATE.setdefault("stats", {})[cond] = statistiques(cond)
save_state(STATE)

S_C = STATE["stats"]["corrigee"]
sig = sum(1 for v in S_C["mcnemar_holm"].values() if v < .05)
print(f"\ncondition corrigee : {sig}/{len(S_C['mcnemar_holm'])} paires "
      f"significatives sous Holm")

# --------------------------------------------------------------------------
# LE TEMOIN. Le bras publie doit retrouver la campagne du papier. Sans lui,
# on ne saurait pas si un ecart entre les deux figures vient de la correction
# ou de la demi-precision dans laquelle les matrices d'E8 sont stockees.
#
# On controle le BOOTSTRAP et non les valeurs de p : une valeur de p traverse
# des ordres de grandeur pour une poignee de flux qui changent de cote, alors
# que la moyenne bootstrap du macro-F1 est la grandeur que la figure 11
# dessine. On regarde tout de meme le nombre de paires significatives, qui
# est ce que la figure 9 montre.
# --------------------------------------------------------------------------
PUB = {"cnn": 0.997956, "dnn": 0.998100, "ftt": 0.999710, "knn": 0.995764,
       "lightgbm": 0.999905, "logreg": 0.999126, "nb": 0.534733,
       "rf": 0.999950, "rnn": 0.998819, "xgboost": 0.999990}
PUB_SIG = 34

S_P = STATE["stats"]["publiee"]
print(f"\n{'modele':<10}{'papier':>11}{'ici':>11}{'ecart':>10}")
ecarts = []
for m, v in PUB.items():
    b = S_P["bootstrap"].get(m)
    if not b:
        continue
    d = abs(v - b["macro_f1_mean"])
    ecarts.append((d, m))
    print(f"{m:<10}{v:>11.6f}{b['macro_f1_mean']:>11.6f}{d:>10.6f}")

sig_p = sum(1 for v in S_P["mcnemar_holm"].values() if v < .05)
print(f"\npaires significatives, bras publie : {sig_p} ici contre "
      f"{PUB_SIG} au papier")

if ecarts:
    emax, pire = max(ecarts)
    STATE["temoin_stats"] = {"ecart_max_bootstrap": emax, "pire": pire,
                             "paires_sig_publiee": sig_p,
                             "paires_sig_corrigee": sig,
                             "valide": bool(emax < 0.002)}
    save_state(STATE)
    print(f"\necart maximal sur la moyenne bootstrap : {emax:.6f} ({pire})")
    if emax < 0.002:
        print("TEMOIN VALIDE — le bras publie rejoue la campagne du papier.")
        print("Les figures 9 et 11 peuvent etre redessinees sur le corrige.")
    else:
        print("TEMOIN INVALIDE — m'envoyer ce tableau tel quel avant que je")
        print("touche aux figures.")

print("\nRenvoie e8_results.json.")
