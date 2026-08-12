#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic : pourquoi XGBoost et LightGBM s'effondrent sur la tache a 13 classes
de 4-preprocessed, alors que la foret aleatoire tient a 0.9657.

A coller dans une cellule du notebook E1, APRES la cellule 7.1 (le moteur est
deja charge : TRAIN, TEST, CONDITIONS, get_xy). Environ 10 minutes.

Quatre hypotheses testees, dans l'ordre de vraisemblance :

  H1  la mise a l'echelle produit des valeurs extremes ou non finies
      -> on inspecte la matrice, puis on refait XGBoost SANS mise a l'echelle
         (les arbres sont invariants par transformation monotone : si le score
          remonte, le probleme vient du scaler et de rien d'autre)
  H2  300 tours a un taux d'apprentissage de 0.3 ne suffisent pas
      -> 300 tours a 0.1, puis 1000 tours a 0.1
  H3  la profondeur 8 est trop faible pour treize classes
      -> profondeur 12
  H4  le desequilibre extreme etouffe les classes rares
      -> poids par classe inversement proportionnels a l'effectif

Le verdict s'imprime a la fin.
"""

import numpy as np
import time
from sklearn.metrics import f1_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pandas as pd

LABEL = "SubCategoryLabel"
COND = "no-topology"


def score(model, Xtr, ytr, Xte, yte, nom):
    t0 = time.time()
    model.fit(Xtr, ytr)
    p = model.predict(Xte)
    mf1 = f1_score(yte, p, average="macro", zero_division=0)
    acc = accuracy_score(yte, p)
    zero = int((f1_score(yte, p, average=None, zero_division=0) < 0.01).sum())
    print(f"   {nom:<44} macro-F1 {mf1:.4f}  acc {acc:.4f}  "
          f"classes a zero {zero:>2}/13  ({time.time()-t0:.0f} s)", flush=True)
    return mf1


def main():
    g = globals()
    TRAIN, TEST, CONDITIONS = g["TRAIN"], g["TEST"], g["CONDITIONS"]
    cols = CONDITIONS[COND]

    le = LabelEncoder().fit(TRAIN[LABEL].astype(str))
    ytr = le.transform(TRAIN[LABEL].astype(str))
    yte = le.transform(TEST[LABEL].astype(str))

    # --- matrices brutes, sans aucune mise a l'echelle -----------------------
    Rtr = TRAIN[cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy("float32")
    Rte = TEST[cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy("float32")

    # --- matrices telles que le notebook les fabrique ------------------------
    Str, Ste, _, _, _ = g["get_xy"](COND, LABEL)

    print("=" * 78)
    print("H1  Etat des matrices")
    print("=" * 78)
    for nom, M in (("brutes", Rtr), ("mises a l'echelle", Str)):
        fini = np.isfinite(M)
        print(f"   {nom:<20} min {np.nanmin(M[fini]):>12.4g}  max {np.nanmax(M[fini]):>12.4g}  "
              f"non finies {int((~fini).sum()):>6}  |x|>1e6 : {int((np.abs(M[fini]) > 1e6).sum()):>7}")
    if not np.isfinite(Str).all() or np.abs(Str[np.isfinite(Str)]).max() > 1e6:
        print("\n   >>> la matrice mise a l'echelle contient des valeurs non finies ou enormes")

    print()
    print("=" * 78)
    print(f"H1 a H4  XGBoost sur {LABEL} / {COND}  ({len(cols)} features)")
    print("=" * 78)
    ref = dict(n_estimators=300, max_depth=8, tree_method="hist",
               random_state=1, n_jobs=2, verbosity=0)

    res = {}
    res["reference"] = score(xgb.XGBClassifier(**ref), Str, ytr, Ste, yte,
                             "reference du notebook (echelle, 300 x lr 0.3, prof. 8)")
    res["H1 sans echelle"] = score(xgb.XGBClassifier(**ref), Rtr, ytr, Rte, yte,
                                   "H1  memes reglages, matrices BRUTES")
    res["H2 lr 0.1"] = score(xgb.XGBClassifier(**{**ref, "learning_rate": 0.1}), Str, ytr, Ste, yte,
                             "H2  300 tours, lr 0.1")
    res["H2 1000 x lr 0.1"] = score(xgb.XGBClassifier(**{**ref, "learning_rate": 0.1,
                                                         "n_estimators": 1000}), Str, ytr, Ste, yte,
                                    "H2  1000 tours, lr 0.1")
    res["H3 profondeur 12"] = score(xgb.XGBClassifier(**{**ref, "max_depth": 12}), Str, ytr, Ste, yte,
                                    "H3  profondeur 12")
    cnt = np.bincount(ytr)
    w = (len(ytr) / (len(cnt) * cnt))[ytr]
    m = xgb.XGBClassifier(**ref)
    t0 = time.time(); m.fit(Str, ytr, sample_weight=w); p = m.predict(Ste)
    res["H4 poids de classe"] = f1_score(yte, p, average="macro", zero_division=0)
    print(f"   {'H4  poids inversement proportionnels':<44} macro-F1 "
          f"{res['H4 poids de classe']:.4f}  acc {accuracy_score(yte, p):.4f}  "
          f"classes a zero "
          f"{int((f1_score(yte, p, average=None, zero_division=0) < 0.01).sum()):>2}/13  "
          f"({time.time()-t0:.0f} s)")

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    base = res["reference"]
    best = max(res, key=res.get)
    print(f"   reference {base:.4f}   meilleur : {best} a {res[best]:.4f}  "
          f"(gain {res[best]-base:+.4f})")
    if res["H1 sans echelle"] - base > 0.05:
        print("   >>> la mise a l'echelle est en cause : ne pas normaliser pour les arbres.")
    elif max(res["H2 lr 0.1"], res["H2 1000 x lr 0.1"]) - base > 0.05:
        print("   >>> convergence insuffisante : baisser le taux et augmenter les tours.")
    elif res["H3 profondeur 12"] - base > 0.05:
        print("   >>> profondeur insuffisante pour treize classes.")
    elif res["H4 poids de classe"] - base > 0.05:
        print("   >>> desequilibre : ponderer les classes.")
    else:
        print("   >>> aucune hypothese ne redresse le score. La tache a 13 classes prive de\n"
              "       Sdaddr est alors reellement hors de portee de ce modele, et le contraste\n"
              "       avec la foret aleatoire a 0.9657 devient le resultat a expliquer.")
    return res


if __name__ == "__main__":
    main()
