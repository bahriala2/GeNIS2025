# =========================================================================
# E8-bis — recalage des temperatures avec l'objectif du pipeline
# =========================================================================
# A coller dans une NOUVELLE cellule du notebook e8_republication, apres
# avoir execute les cellules 1 a 6 (Execution > Tout executer suffit).
#
# POURQUOI. La fonction temperature() que j'avais ecrite dans E8 minimise
# l'ECE sur une grille au pas de 0.05. Le pipeline minimise la NLL sur une
# grille de 80 points (colab/e3_calibration_residual.py). Objectif different,
# donc les colonnes T et "ECE calibree" d'E8 ne sont comparables ni au
# tableau 7 ni au tableau 8 du manuscrit.
#
# La preuve : sur le bras "publiee", qui devrait reproduire le tableau 7, E8
# donne T = 0.150 pour naive Bayes la ou le papier a 5.821 et ou E3-A avait
# retrouve 5.000. Les deux extremites opposees de la grille.
#
# AUCUN REENTRAINEMENT : les matrices de probabilites sont dans e8_probs/.
# Compter deux a trois minutes.
import numpy as np

for _n in ("STATE", "save_state", "kfile", "SPLITS", "y", "ece", "applique_t"):
    if _n not in dir():
        raise NameError(
            f"{_n} n'est pas defini : execute d'abord les cellules 1 a 6 "
            "du notebook (Execution > Tout executer).")

# Recopie mot pour mot de e3_calibration_residual.temperature.
GRILLE = np.concatenate([np.linspace(.05, 1, 40), np.linspace(1.05, 5, 40)])


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def temperature_nll(probs_val, y_val):
    """NLL sur la validation, grille de 80 points : l'objectif du pipeline."""
    lg = np.log(np.clip(probs_val, 1e-12, None))
    best, bt = np.inf, 1.0
    for T in GRILLE:
        p = _softmax(lg / T)
        nll = -np.log(np.clip(p[np.arange(len(y_val)), y_val],
                              1e-12, None)).mean()
        if nll < best:
            best, bt = nll, float(T)
    return bt


n_ok = n_saute = 0
print("recalage en cours…", flush=True)
for cle, r in sorted(STATE["runs"].items()):
    f = kfile(cle)
    if not f.exists():
        n_saute += 1
        continue
    proto = cle.split("|")[2]
    _, i_val, i_test = SPLITS[proto]
    z = np.load(f)
    T = temperature_nll(z["probs_val"], y[i_val])
    r["temperature_ece"] = r.get("temperature")   # on garde la trace
    r["temperature"] = T
    r["ece_calibree"] = ece(applique_t(z["probs_test"], T), y[i_test])
    n_ok += 1
save_state(STATE)
print(f"{n_ok} runs recalcules, {n_saute} sans matrice sauvegardee\n")

# ---------------------------------------------------------------------
# LE TEMOIN. Le bras publie doit maintenant retrouver le tableau 7 publie.
# Sans ce controle, on ne saurait pas si le recalage a repare quelque chose
# ou simplement deplace le probleme.
# ---------------------------------------------------------------------
P7 = {"xgboost": 0.091, "lightgbm": 0.050, "rf": 0.094, "ftt": 0.995,
      "logreg": 0.697, "rnn": 0.940, "cnn": 1.132, "dnn": 0.694,
      "knn": 2.835, "nb": 5.821}
print(f"{'modele':<10}{'tableau 7':>11}{'avant (ECE)':>13}{'apres (NLL)':>13}"
      f"{'ecart':>8}")
ecarts = []
for m, T in P7.items():
    r = STATE["runs"].get(f"{m}|publiee|strat_seed1")
    if not r or "temperature" not in r:
        continue
    d = abs(T - r["temperature"])
    ecarts.append(d)
    print(f"{m:<10}{T:>11.3f}{(r.get('temperature_ece') or 0):>13.3f}"
          f"{r['temperature']:>13.3f}{d:>8.3f}")

if ecarts:
    emax = max(ecarts)
    STATE["temoin_temperature"] = {"ecart_max": emax, "valide": bool(emax < 0.15)}
    save_state(STATE)
    print(f"\necart maximal {emax:.3f}")
    if emax < 0.15:
        print("TEMOIN VALIDE — c'est bien la finesse de grille qui reste, et")
        print("les tableaux 7, 8 et 13 peuvent etre republies.")
    else:
        print("TEMOIN INVALIDE — il reste autre chose que la grille. Ne pas")
        print("republier : m'envoyer ce tableau tel quel.")

print("\nRenvoie e8_results.json.")
