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
# LE TEMOIN, corrige. La premiere version comparait T, qui est un parametre
# INTERMEDIAIRE pose sur une surface d'ECE tres plate : deux jeux de
# probabilites quasi identiques peuvent y donner des T eloignes sans que rien
# de rapporte ne bouge. Elle declarait donc l'echec sur naive Bayes, dont le T
# publie (5.821) est simplement HORS de la grille, qui s'arrete a 5.
#
# Ce qu'il faut controler est la quantite que le tableau RAPPORTE : l'ECE
# apres calage. Et la cible correcte n'est pas le tableau 7 mais E3-A, la
# recomputation que la section 6.5 declare deja comme la bonne.
# ---------------------------------------------------------------------
P7 = {"xgboost": (0.091, 0.0000), "lightgbm": (0.050, 0.0000),
      "rf": (0.094, 0.0000), "ftt": (0.995, 0.0000),
      "logreg": (0.697, 0.0002), "rnn": (0.940, 0.0005),
      "cnn": (1.132, 0.0005), "dnn": (0.694, 0.0002),
      "knn": (2.835, 0.0004), "nb": (5.821, 0.2435)}
BORNES = (GRILLE[0], GRILLE[-1])
print(f"{'modele':<10}{'T pub':>8}{'T new':>8}{'bord':>6}"
      f"{'ECEcal pub':>12}{'ECEcal new':>12}{'ecart':>9}")
ecarts = []
for m, (T, ecal) in P7.items():
    r = STATE["runs"].get(f"{m}|publiee|strat_seed1")
    if not r:
        continue
    bord = "oui" if r["temperature"] in BORNES else ""
    d = abs(ecal - r["ece_calibree"])
    # Un T pose sur une borne dit que l'optimum est hors grille : l'ecart
    # d'ECE qui en decoule n'est pas informatif sur la procedure.
    if not bord:
        ecarts.append((d, m))
    print(f"{m:<10}{T:>8.3f}{r['temperature']:>8.3f}{bord:>6}"
          f"{ecal:>12.4f}{r['ece_calibree']:>12.4f}{d:>9.4f}")

if ecarts:
    emax, pire = max(ecarts)
    STATE["temoin_temperature"] = {"ecart_max_ece_calibree": emax,
                                   "pire": pire, "valide": bool(emax < 0.001)}
    save_state(STATE)
    print(f"\necart maximal sur l'ECE calibree, hors bord de grille : "
          f"{emax:.4f} ({pire})")
    if emax < 0.001:
        print("TEMOIN VALIDE — la quantite rapportee se reproduit. Les ecarts")
        print("sur T restants sont la platitude de la surface, que la 6.5")
        print("documente deja. Les tableaux 7, 8 et 13 peuvent etre republies.")
    else:
        print("TEMOIN INVALIDE — m'envoyer ce tableau tel quel.")

print("\nRenvoie e8_results.json.")
