# =========================================================================
# E8-ter — le cout d'inference, les deux conditions, une seule session
# =========================================================================
# A coller dans une NOUVELLE cellule du notebook e8_republication, apres
# avoir execute les cellules 1 a 6 (Execution > Tout executer suffit).
#
# POURQUOI. Le tableau 10 du manuscrit porte des debits mesures sur 55
# colonnes ; la cellule 10 d'E8 en a mesure sur 54. Les deux jeux different
# d'un facteur 0.42 a 13.4 selon le detecteur, DANS LES DEUX SENS, ce qu'une
# colonne retiree sur 55 ne peut pas produire. Deux causes se superposent :
#
#   1. les deux sessions n'ont pas tourne sur la meme machine ;
#   2. elles n'emploient pas le meme protocole de debit --
#          papier   for _ in range(20): predict(lot_de_512)
#          E8       predict(lot_de_10240)          # un seul appel
#      et chaque appel paie un surcout fixe : demarrage du backend joblib
#      pour un estimateur parallele, surcout d'API pour un modele Keras, que
#      le manuscrit chiffre lui-meme a 77 ms. La boucle du papier le paie
#      vingt fois. Mesure a machine et modele identiques
#      (experiments/e8/verify_cout_protocole.py), ce seul changement vaut
#      5.6x sur la foret aleatoire.
#
# Ni l'un ni l'autre jeu ne peut donc etre recopie dans le tableau, et les
# melanger serait pire. Cette cellule refait les DEUX conditions dans UNE
# session, sous le protocole qui amortit reellement le surcout -- celui que
# la legende publiee annonce deja.
#
# COUT. Un ajustement par detecteur et par condition, sur la graine 1. Les
# quatre modeles Keras sont ajustes deux epoques : on mesure une
# architecture, pas une qualite, et aucun chiffre de detection ne sort d'ici.
# Compter dix a quinze minutes sur CPU. Reprend ou elle s'est arretee.
import gc
import platform
import time

import numpy as np
from sklearn.preprocessing import RobustScaler

for _n in ("STATE", "save_state", "X", "y", "SPLITS", "FEATS", "COLS", "BASE",
           "SK", "make_sk", "NEURAL", "DEFAULTS_DEEP", "shape_for", "tf",
           "keras"):
    if _n not in dir():
        raise NameError(
            f"{_n} n'est pas defini : execute d'abord les cellules 1 a 6 "
            "du notebook (Execution > Tout executer).")

N_LOTS, TAILLE, N_LAT = 20, 512, 200
COUT = STATE.setdefault("cout_deux_conditions", {})


def prepare(liste):
    """Les trois matrices mises a l'echelle sur les colonnes demandees."""
    tr_, va_, te_ = SPLITS["strat_seed1"]
    ci = [FEATS.index(c) for c in liste]
    sc = RobustScaler().fit(X[tr_][:, ci])

    def g(ix):
        return np.nan_to_num(sc.transform(X[ix][:, ci]), nan=0., posinf=0.,
                             neginf=0.).astype("float32")

    return g(tr_), g(te_), tr_


def mesure(predit, Xte):
    """Latence a une ligne, et debit sous LES DEUX protocoles.

    On garde le protocole du papier a cote du protocole amorti : sans les
    deux, on ne saurait pas si un ecart au tableau 10 publie vient de la
    machine ou de la mesure. C'est la seule facon de rendre l'ancienne
    colonne et la nouvelle comparables.
    """
    predit(Xte[:8])                                   # chauffe
    lat = []
    for i in range(N_LAT):
        t0 = time.perf_counter()
        predit(Xte[i:i + 1])
        lat.append((time.perf_counter() - t0) * 1e3)

    lot = Xte[:TAILLE * N_LOTS]
    t0 = time.perf_counter()
    for k in range(N_LOTS):
        predit(lot[k * TAILLE:(k + 1) * TAILLE])
    d_boucle = len(lot) / (time.perf_counter() - t0)

    t0 = time.perf_counter()
    predit(lot)
    d_amorti = len(lot) / (time.perf_counter() - t0)

    return {"p50_ms": float(np.percentile(lat, 50)),
            "p99_ms": float(np.percentile(lat, 99)),
            "flux_s_boucle_512": float(d_boucle),
            "flux_s_amorti_10240": float(d_amorti)}


print(f"{'configuration':<24}{'p50 ms':>9}{'20x512':>12}{'1x10240':>12}"
      f"{'gain':>8}")
for cond in ("publiee", "corrigee"):
    Xtr, Xte, tr_ = prepare(COLS[cond])
    for cfg in BASE:
        if cfg == "majority":
            continue                              # ne predit rien a mesurer
        cle = f"{cfg}|{cond}"
        if cle in COUT:
            continue
        nom = cfg.split("#")[0]
        try:
            if nom in SK:
                clf = make_sk(nom, seed=1).fit(Xtr, y[tr_])
                predit = clf.predict_proba
            else:
                q = DEFAULTS_DEEP[nom]
                tf.keras.utils.set_random_seed(1)
                net = NEURAL[nom](Xtr.shape[1], len(set(y)), q)
                net.compile(optimizer=keras.optimizers.Adam(q["lr"]),
                            loss="sparse_categorical_crossentropy")
                net.fit(shape_for(nom, Xtr), y[tr_], epochs=2,
                        batch_size=q["bs"], verbose=0)

                def predit(A, _n=nom, _net=net):
                    return _net.predict(shape_for(_n, A), batch_size=TAILLE,
                                        verbose=0)

            r = mesure(predit, Xte)
            r["n_features"] = len(COLS[cond])
            COUT[cle] = r
            print(f"{cle:<24}{r['p50_ms']:>9.2f}"
                  f"{r['flux_s_boucle_512']:>12.0f}"
                  f"{r['flux_s_amorti_10240']:>12.0f}"
                  f"{r['flux_s_amorti_10240'] / r['flux_s_boucle_512']:>7.1f}x")
        except Exception as e:
            print(f"{cle:<24} echec : {e}")
        finally:
            keras.backend.clear_session()
            gc.collect()
            save_state(STATE)                     # une deconnexion ne coute
                                                  # que la mesure en cours
    del Xtr, Xte
    gc.collect()

STATE["plateforme_cout"] = platform.platform()
save_state(STATE)

# --------------------------------------------------------------------------
# LE TEMOIN. La condition publiee, sous le protocole du papier, doit
# retrouver l'ordre de grandeur du tableau 10. Si elle ne le retrouve pas,
# c'est la machine qui differe et non la mesure, et il faudra le dire plutot
# que de substituer une colonne a l'autre.
# --------------------------------------------------------------------------
T10 = {"xgboost": 46317, "lightgbm": 6281, "rf": 7738, "ftt": 430,
       "logreg": 1139252, "rnn": 3803, "cnn": 3134, "dnn": 5269,
       "knn": 1875, "nb": 228377}
print(f"\n{'modele':<10}{'tableau 10':>12}{'ici, 20x512':>13}{'rapport':>10}")
rapports = []
for m, publie in T10.items():
    r = COUT.get(f"{m}|publiee")
    if not r:
        continue
    q = r["flux_s_boucle_512"] / publie
    rapports.append(q)
    print(f"{m:<10}{publie:>12.0f}{r['flux_s_boucle_512']:>13.0f}{q:>9.1f}x")

if rapports:
    pire = max(max(rapports), 1 / min(rapports))
    STATE["temoin_cout"] = {"ecart_relatif_max": float(pire),
                            "valide": bool(pire < 3)}
    save_state(STATE)
    print(f"\necart relatif maximal a la campagne publiee : {pire:.1f}x")
    if pire < 3:
        print("TEMOIN VALIDE — la machine est comparable a celle du papier,")
        print("donc l'ecart entre l'ancienne colonne et la nouvelle est bien")
        print("le protocole. La colonne amortie peut remplacer le tableau 10.")
    else:
        print("TEMOIN INVALIDE — cette machine n'est pas celle du papier. Les")
        print("deux conditions restent comparables ENTRE ELLES, mais pas avec")
        print("la campagne publiee : m'envoyer ce tableau tel quel.")

print("\nRenvoie e8_results.json.")
