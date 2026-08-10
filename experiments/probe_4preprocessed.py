#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sonde a une feature sur le module 4-preprocessed de GeNIS.

Complement de inspect_4preprocessed.py, qui ne sondait que StartTime et LastTime.
Or ces deux colonnes ont ete retirees du module, tandis que Seq, le compteur
d'enregistrements d'Argus, y est reste : melanger les lignes ne change pas la
valeur de ce compteur, qui continue donc d'encoder l'ordre de capture.

Pour chaque feature listee, un arbre de decision est entraine sur cette seule
colonne, sur leur partition d'entrainement, et evalue sur leur holdout. La
comparaison se fait au taux de la classe majoritaire.

Usage :
    python probe_4preprocessed.py "D:\\Genis\\4-preprocessed\\4-preprocessed"

Options :
    --interval 60     defaut 60
    --label SubCategoryLabel   defaut : les trois etiquettes

Dependances : pandas, numpy, scikit-learn.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score

DEFAULT_DIR = r"D:\Genis\4-preprocessed\4-preprocessed"

# Ce que l'on sonde, et pourquoi
PROBES = [
    ("Seq",        "compteur d'enregistrements Argus : ordre de capture"),
    ("Offset",     "decalage Argus : autre trace de position"),
    ("Dur",        "famille de duree, une des six colonnes identiques"),
    ("Ssaddr",     "compteur HERA lie a la topologie"),
    ("Sdaddr",     "compteur HERA lie a la topologie"),
    ("Sport",      "port source : identifiant reseau"),
    ("Dport",      "port destination : identifiant reseau"),
    ("TotBytes",   "volume : feature comportementale legitime, pour contraste"),
    ("SrcLoad",    "debit : zone grise tau*"),
]


def read_csv(path):
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError("encodage illisible : %s" % path)


def probe(train, test, feat, label):
    xtr = pd.to_numeric(train[feat], errors="coerce").to_numpy(dtype="float64").reshape(-1, 1)
    xte = pd.to_numeric(test[feat], errors="coerce").to_numpy(dtype="float64").reshape(-1, 1)
    ytr, yte = train[label].astype(str), test[label].astype(str)
    ktr, kte = ~np.isnan(xtr).ravel(), ~np.isnan(xte).ravel()
    if ktr.sum() < 100 or kte.sum() < 100:
        return None
    clf = DecisionTreeClassifier(random_state=1).fit(xtr[ktr], ytr[ktr])
    pred = clf.predict(xte[kte])
    return {
        "accuracy": round(float(accuracy_score(yte[kte], pred)), 4),
        "macro_f1": round(float(f1_score(yte[kte], pred, average="macro", zero_division=0)), 4),
        "majority_class_rate": round(float(yte[kte].value_counts(normalize=True).iloc[0]), 4),
        "n_classes": int(yte[kte].nunique()),
        "n_unique_values": int(np.unique(xtr[ktr]).size),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", nargs="?", default=DEFAULT_DIR)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--label", default=None)
    a = ap.parse_args()

    root = Path(a.directory)
    pat = "%d-sec" % a.interval
    csvs = sorted(root.rglob("*.csv"))
    ftr = next(p for p in csvs if pat in p.name.lower() and "train" in p.name.lower())
    fte = next(p for p in csvs if pat in p.name.lower() and "test" in p.name.lower())
    print("train : %s" % ftr.name)
    print("test  : %s" % fte.name, flush=True)

    train, test = read_csv(ftr), read_csv(fte)
    print("lignes : %s / %s   colonnes : %d\n"
          % (f"{len(train):,}".replace(",", " "), f"{len(test):,}".replace(",", " "),
             train.shape[1]), flush=True)

    labels = [a.label] if a.label else [c for c in ("SubCategoryLabel", "CategoryLabel", "BinaryLabel")
                                        if c in train.columns]
    out = {"directory": str(root), "interval": a.interval,
           "n_train": len(train), "n_test": len(test), "probes": {}}

    for label in labels:
        maj = test[label].astype(str).value_counts(normalize=True).iloc[0]
        n_cls = test[label].nunique()
        print("=" * 76)
        print("%s : %d classes, classe majoritaire %.4f" % (label, n_cls, maj))
        print("=" * 76)
        print("%-11s %9s %9s %8s   %s" % ("feature", "accuracy", "macro-F1", "valeurs", "nature"))
        out["probes"][label] = {}
        for feat, why in PROBES:
            if feat not in train.columns:
                print("%-11s %9s %9s %8s   %s" % (feat, "absent", "-", "-", why))
                continue
            r = probe(train, test, feat, label)
            if r is None:
                print("%-11s %9s" % (feat, "echec"))
                continue
            out["probes"][label][feat] = r
            flag = "  <<<" if r["accuracy"] > 3 * maj else ""
            print("%-11s %9.4f %9.4f %8d   %s%s"
                  % (feat, r["accuracy"], r["macro_f1"], r["n_unique_values"], why, flag))
        print()

    p = Path(__file__).resolve().parent / "probe_4preprocessed.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("rapport : %s" % p)


if __name__ == "__main__":
    main()
