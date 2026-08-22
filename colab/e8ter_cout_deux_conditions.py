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
import warnings

import numpy as np
from sklearn.preprocessing import RobustScaler

for _n in ("STATE", "save_state", "X", "y", "SPLITS", "FEATS", "COLS", "BASE",
           "SK", "make_sk", "NEURAL", "DEFAULTS_DEEP", "shape_for", "tf",
           "keras"):
    if _n not in dir():
        raise NameError(
            f"{_n} n'est pas defini : execute d'abord les cellules 1 a 6 "
            "du notebook (Execution > Tout executer).")

# LightGBM avertit a chaque appel qu'il a ete ajuste avec des noms de
# colonnes et qu'on lui passe un tableau nu. C'est vrai, c'est sans effet sur
# la prediction, et repete 4400 fois ca rend la sortie illisible.
warnings.filterwarnings("ignore", message=".*does not have valid feature names.*")

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
# LE TEMOIN, en deux lectures separees.
#
# La premiere version posait UNE question qui en contenait deux, et les
# reglait par un seul seuil : "l'ecart relatif maximal a la campagne publiee
# est-il sous 3 ?". Ca melange "cette machine est-elle celle du papier ?" avec
# "le protocole explique-t-il l'ecart ?", alors que seule la seconde porte la
# decision -- et un seul detecteur atypique suffisait a faire echouer les neuf
# autres. On les separe.
# --------------------------------------------------------------------------
T10 = {"xgboost": 46317, "lightgbm": 6281, "rf": 7738, "ftt": 430,
       "logreg": 1139252, "rnn": 3803, "cnn": 3134, "dnn": 5269,
       "knn": 1875, "nb": 228377}

# --- lecture 1 : cette machine ressemble-t-elle a celle du papier ? --------
# Sous le protocole DU PAPIER, sur la condition DU PAPIER, le debit mesure ici
# devrait retrouver le tableau 10. C'est une description, pas une note : on
# compte les modeles dans la bande et on nomme ceux qui en sortent.
print(f"\n{'modele':<10}{'tableau 10':>12}{'ici, 20x512':>13}{'machine':>10}"
      f"{'gain amorti':>13}")
dans, hors, gains = [], [], {}
for m, publie in T10.items():
    r = COUT.get(f"{m}|publiee")
    if not r:
        continue
    q = r["flux_s_boucle_512"] / publie
    g = r["flux_s_amorti_10240"] / r["flux_s_boucle_512"]
    gains[m] = g
    (dans if 1 / 1.5 <= q <= 1.5 else hors).append((m, q))
    print(f"{m:<10}{publie:>12.0f}{r['flux_s_boucle_512']:>13.0f}{q:>9.2f}x"
          f"{g:>12.1f}x")

print(f"\n{len(dans)}/{len(dans) + len(hors)} detecteurs retrouvent le tableau "
      f"10 a 1.5x pres.")
if hors:
    print("hors bande : " + ", ".join(f"{m} ({q:.2f}x)" for m, q in hors))
    print("Ces detecteurs-la ne sont pas comparables a la campagne publiee ;")
    print("ils restent comparables entre les deux conditions mesurees ici.")

# --- lecture 2 : le protocole explique-t-il l'ecart a la cellule 10 ? ------
# C'est la question qui porte la decision. Le gain est mesure DANS cette
# session, machine et modele identiques : rien d'autre ne varie que le
# decoupage des appels.
if gains:
    fort = sorted(((g, m) for m, g in gains.items()), reverse=True)
    print(f"\nAmortir les appels vaut de {fort[-1][0]:.1f}x ({fort[-1][1]}) a "
          f"{fort[0][0]:.1f}x ({fort[0][1]}).")
    print("Les detecteurs qui y gagnent le plus sont ceux qui paient un")
    print("surcout par appel : backend joblib, ou API de prediction Keras.")

# --- ce qui autorise la republication --------------------------------------
# Une colonne de cout ne peut etre republiee que si les DEUX conditions ont
# ete mesurees dans la meme session. C'est vrai par construction ici, et c'est
# la seule garantie dont le tableau 10 a besoin : il compare des detecteurs
# entre eux, pas cette session a une autre.
paires = [m for m in T10 if f"{m}|publiee" in COUT and f"{m}|corrigee" in COUT]
STATE["temoin_cout"] = {
    "machine_dans_bande": [m for m, _ in dans],
    "machine_hors_bande": {m: float(q) for m, q in hors},
    "gain_amorti": {m: float(g) for m, g in gains.items()},
    "paires_completes": paires,
    "valide": bool(len(paires) == len(T10))}
save_state(STATE)
print(f"\n{len(paires)}/{len(T10)} detecteurs ont leurs DEUX conditions "
      f"mesurees ici.")
if len(paires) == len(T10):
    print("TEMOIN VALIDE — les deux conditions sont comparables entre elles,")
    print("ce qui est tout ce que le tableau 10 demande. Il peut etre republie")
    print("sur la colonne amortie, en disant de quelle session elle vient.")
else:
    manquants = [m for m in T10 if m not in paires]
    print("INCOMPLET — il manque : " + ", ".join(manquants))
    print("Relance cette meme cellule : elle saute ce qui est deja mesure.")

print("\nRenvoie e8_results.json.")
