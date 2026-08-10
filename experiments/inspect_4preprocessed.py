#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspection du module 4-preprocessed de GeNIS, avant toute experience E1.

Ne fait aucun entrainement lourd. Repond a six questions :
  1. Quels fichiers, combien de lignes, combien de colonnes ?
  2. Quelle est la liste exacte des colonnes ?
  3. Les colonnes positionnelles (StartTime, LastTime, Rank, Seq) survivent-elles ?
  4. Les six colonnes numeriquement identiques (Dur = RunTime = Mean = Sum = Min = Max)
     survivent-elles, et y en a-t-il d'autres ?
  5. Quelles colonnes liees a la topologie (IP, MAC, VLAN, Ssaddr, Sdaddr) restent ?
  6. Un arbre de decision entraine sur le seul horodatage separe-t-il les classes,
     sur leur propre partition train/holdout ?

Usage (Windows, depuis n'importe ou) :

    python inspect_4preprocessed.py "D:\\Genis\\4-preprocessed\\4-preprocessed"

Sans argument, le chemin ci-dessus est utilise par defaut.
Options :
    --interval 60      intervalle a inspecter (5, 10, 30 ou 60 ; defaut 60)
    --all-intervals    inspecte les quatre (plus long, plus de memoire)

Produit un rapport a l'ecran et un fichier inspection_4preprocessed.json
a cote du script, a me renvoyer.

Dependances : pandas, numpy, scikit-learn.
"""

import argparse
import json
import re
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_DIR = r"D:\Genis\4-preprocessed\4-preprocessed"

# Les douze colonnes que notre audit exclut, telles que nommees par HERA
POSITIONAL = ["StartTime", "LastTime", "Rank", "Seq"]
DUPLICATE_FAMILY = ["Dur", "RunTime", "Mean", "Sum", "Min", "Max"]
INTERPACKET = ["SIntPkt", "SIntPktMax"]
BLACKLIST = POSITIONAL + DUPLICATE_FAMILY + INTERPACKET
# Les cinq que la normalisation corrigee du hasard fait basculer
GREY_ZONE = ["SrcLoad", "SrcRate", "DstLoad", "Rate", "Load"]
# Colonnes liees a la topologie, a exclure de tout modele generalisable
TOPOLOGY_RE = r"(addr|ipv?[46]?$|^s?ip|mac|vlan|ssaddr|sdaddr|sport|dport|^proto|flowid|autoid|_id$)"
LABEL_HINTS = ["label", "class", "target", "attack", "category"]


def log(msg=""):
    print(msg, flush=True)


def section(title):
    log()
    log("=" * 78)
    log(title)
    log("=" * 78)


def read_csv(path, nrows=None):
    """Lecture tolerante : encodage et separateur peuvent varier."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, nrows=nrows, encoding=enc, low_memory=False)
            if df.shape[1] == 1:            # mauvais separateur
                df = pd.read_csv(path, nrows=nrows, encoding=enc, sep=";", low_memory=False)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError("encodage illisible : %s" % path)


def find_files(root, interval):
    """Retrouve la paire train/test de l'intervalle demande, quel que soit le nommage."""
    root = Path(root)
    if not root.is_dir():
        sys.exit("Dossier introuvable : %s" % root)
    csvs = sorted(root.rglob("*.csv"))
    if not csvs:
        sys.exit("Aucun CSV sous %s" % root)
    pat = "%d-sec" % interval
    train = [p for p in csvs if pat in p.name.lower() and "train" in p.name.lower()]
    test = [p for p in csvs if pat in p.name.lower() and "test" in p.name.lower()]
    return csvs, (train[0] if train else None), (test[0] if test else None)


def duplicate_groups(df, sample=20000, tol=0.0):
    """Colonnes numeriquement identiques, en deux passes : criblage puis confirmation.

    tol = 0.0 -> egalite exacte (np.array_equal sur les valeurs non nulles).
    """
    num = df.select_dtypes(include=[np.number])
    cols = list(num.columns)
    if len(cols) < 2:
        return [], []
    probe = num.sample(min(sample, len(num)), random_state=0) if len(num) > sample else num

    # criblage : signature rapide sur l'echantillon
    sig = {}
    for c in cols:
        v = probe[c].to_numpy(dtype="float64", na_value=np.nan)
        sig.setdefault(round(float(np.nansum(v)), 6), []).append(c)
    candidates = [g for g in sig.values() if len(g) > 1]

    # confirmation sur la totalite des lignes
    groups, pairs = [], []
    for grp in candidates:
        remaining = list(grp)
        while remaining:
            ref = remaining.pop(0)
            a = num[ref].to_numpy(dtype="float64", na_value=np.nan)
            same = [ref]
            for other in list(remaining):
                b = num[other].to_numpy(dtype="float64", na_value=np.nan)
                equal = np.allclose(a, b, rtol=0, atol=tol, equal_nan=True)
                if equal:
                    same.append(other)
                    remaining.remove(other)
            if len(same) > 1:
                groups.append(same)
                for i in range(len(same)):
                    for j in range(i + 1, len(same)):
                        pairs.append((same[i], same[j]))
    return groups, pairs


def timestamp_probe(train, test, ts_col, label_col):
    """Arbre de decision sur le seul horodatage, entraine et evalue sur leur split."""
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import accuracy_score

    def as_numeric(s):
        if pd.api.types.is_numeric_dtype(s):
            return s.astype("float64")
        try:
            conv = pd.to_datetime(s, errors="coerce", utc=True)
            if conv.notna().mean() > 0.9:
                return (conv.view("int64") if hasattr(conv, "view")
                        else conv.astype("int64")).astype("float64") / 1e9
        except Exception:                                          # noqa: BLE001
            pass
        return pd.to_numeric(s, errors="coerce").astype("float64")

    xtr = as_numeric(train[ts_col]).to_numpy().reshape(-1, 1)
    xte = as_numeric(test[ts_col]).to_numpy().reshape(-1, 1)
    ytr, yte = train[label_col].astype(str), test[label_col].astype(str)
    ok_tr = ~np.isnan(xtr).ravel()
    ok_te = ~np.isnan(xte).ravel()
    if ok_tr.sum() < 100 or ok_te.sum() < 100:
        return None
    clf = DecisionTreeClassifier(random_state=1).fit(xtr[ok_tr], ytr[ok_tr])
    acc = accuracy_score(yte[ok_te], clf.predict(xte[ok_te]))
    vc = yte[ok_te].value_counts(normalize=True)
    if vc.empty:
        return None
    majority = vc.iloc[0]
    return {"feature": ts_col, "label": label_col, "accuracy": round(float(acc), 4),
            "majority_class_rate": round(float(majority), 4),
            "n_classes": int(yte[ok_te].nunique())}


def inspect(root, interval, report):
    csvs, ftrain, ftest = find_files(root, interval)

    section("1. FICHIERS")
    log("Dossier : %s" % root)
    log("%d fichiers CSV trouves :" % len(csvs))
    for p in csvs:
        log("   %-34s %8.1f Mo" % (p.name, p.stat().st_size / 1e6))
    if ftrain is None or ftest is None:
        log()
        log("!! paire train/test introuvable pour l'intervalle %d s." % interval)
        log("   Renseigne --interval avec une valeur presente ci-dessus.")
        return
    log()
    log("Intervalle inspecte : %d s" % interval)
    log("   train : %s" % ftrain.name)
    log("   test  : %s" % ftest.name)

    train = read_csv(ftrain)
    test = read_csv(ftest)
    n_tr, n_te = len(train), len(test)
    log()
    log("   lignes : train %s, holdout %s, total %s" % (f"{n_tr:,}".replace(",", " "),
                                                        f"{n_te:,}".replace(",", " "),
                                                        f"{n_tr+n_te:,}".replace(",", " ")))
    log("   part holdout : %.1f %%" % (100 * n_te / (n_tr + n_te)))
    log("   colonnes : %d" % train.shape[1])

    cols = list(train.columns)
    section("2. LISTE DES COLONNES")
    for i in range(0, len(cols), 4):
        log("   " + "".join("%-24s" % c for c in cols[i:i + 4]))

    lower = {c.lower(): c for c in cols}

    section("3. COLONNES DE NOTRE LISTE NOIRE")
    present, absent = [], []
    for c in BLACKLIST:
        (present if c.lower() in lower else absent).append(c)
    log("   PRESENTES (%d/12) : %s" % (len(present), ", ".join(present) or "aucune"))
    log("   absentes  (%d/12) : %s" % (len(absent), ", ".join(absent) or "aucune"))
    log()
    grey_present = [c for c in GREY_ZONE if c.lower() in lower]
    log("   Zone grise tau* (%d/5) : %s" % (len(grey_present), ", ".join(grey_present) or "aucune"))

    section("4. COLONNES NUMERIQUEMENT IDENTIQUES")
    log("   Detection sur %s lignes du train..." % f"{n_tr:,}".replace(",", " "))
    groups, pairs = duplicate_groups(train)
    if groups:
        for g in groups:
            log("   [%d colonnes, %d paires] %s" % (len(g), len(g) * (len(g) - 1) // 2, " = ".join(g)))
        log()
        log("   total : %d groupes, %d paires identiques" % (len(groups), len(pairs)))
    else:
        log("   aucune colonne dupliquee detectee")
    fam = [c for c in DUPLICATE_FAMILY if c.lower() in lower]
    log()
    log("   Famille de duree attendue presente : %d/6  (%s)" % (len(fam), ", ".join(fam) or "aucune"))

    section("5. COLONNES LIEES A LA TOPOLOGIE")
    topo = [c for c in cols if re.search(TOPOLOGY_RE, c.lower())]
    log("   %d colonnes dont le nom evoque une adresse, un port ou un identifiant :" % len(topo))
    for i in range(0, len(topo), 4):
        log("   " + "".join("%-24s" % c for c in topo[i:i + 4]))
    log()
    const = [c for c in train.columns if train[c].nunique(dropna=False) <= 1]
    log("   colonnes constantes : %d %s" % (len(const), ("(%s)" % ", ".join(const[:8])) if const else ""))

    section("6. ETIQUETTES ET SONDE D'HORODATAGE")
    labels = [c for c in cols if any(h in c.lower() for h in LABEL_HINTS)]
    log("   colonnes d'etiquette : %s" % (", ".join(labels) or "aucune trouvee"))
    label_stats = {}
    for lab in labels:
        vc = train[lab].astype(str).value_counts()
        label_stats[lab] = {k: int(v) for k, v in vc.items()}
        log()
        log("   %s : %d classes" % (lab, len(vc)))
        for k, v in vc.items():
            log("      %-24s %10s  (%5.2f %%)" % (k, f"{v:,}".replace(",", " "), 100 * v / len(train)))

    probes = []
    ts_cols = [lower[c.lower()] for c in ("StartTime", "LastTime") if c.lower() in lower]
    if not ts_cols:
        log()
        log("   Pas de colonne d'horodatage : sonde impossible (bonne nouvelle).")
    for ts in ts_cols:
        for lab in labels:
            try:
                r = timestamp_probe(train, test, ts, lab)
            except Exception as e:                                # noqa: BLE001
                log("   sonde %s / %s : echec (%s)" % (ts, lab, e)); continue
            if r:
                probes.append(r)
                log()
                log("   Sonde %s -> %s : accuracy %.4f  contre %.4f pour la classe majoritaire"
                    " (%d classes)" % (ts, lab, r["accuracy"], r["majority_class_rate"], r["n_classes"]))

    report["intervals"][str(interval)] = {
        "train_file": ftrain.name, "test_file": ftest.name,
        "n_train": n_tr, "n_test": n_te, "n_columns": int(train.shape[1]),
        "columns": cols,
        "blacklist_present": present, "blacklist_absent": absent,
        "grey_zone_present": grey_present,
        "duplicate_groups": groups, "n_duplicate_pairs": len(pairs),
        "topology_like_columns": topo, "constant_columns": const,
        "label_columns": labels, "label_distribution": label_stats,
        "timestamp_probes": probes,
    }


def main():
    ap = argparse.ArgumentParser(description="Inspection du module 4-preprocessed de GeNIS")
    ap.add_argument("directory", nargs="?", default=DEFAULT_DIR)
    ap.add_argument("--interval", type=int, default=60, choices=[5, 10, 30, 60])
    ap.add_argument("--all-intervals", action="store_true")
    a = ap.parse_args()

    report = {"directory": str(a.directory), "intervals": {},
              "pandas": pd.__version__, "numpy": np.__version__}
    for iv in ([5, 10, 30, 60] if a.all_intervals else [a.interval]):
        try:
            inspect(a.directory, iv, report)
        except MemoryError:
            log("\n!! memoire insuffisante pour l'intervalle %d s, passe au suivant." % iv)

    out = Path(__file__).resolve().parent / "inspection_4preprocessed.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    section("RAPPORT ECRIT")
    log("   %s" % out)
    log("   Renvoie-moi ce fichier.")


if __name__ == "__main__":
    main()
