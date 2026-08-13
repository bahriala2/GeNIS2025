#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3 : calibration sous les deux protocoles, et audit residuel conjoint.

Repond aux deux points que le relecteur classe prioritaires apres la revision,
et qui ont ceci de commun qu'ils ne demandent aucun reentrainement.

  A. CALIBRATION SOUS PROTOCOLE TEMPOREL
     "Calibration" figure dans le titre de l'article, et n'est mesuree que sous
     le protocole stratifie. Or le pipeline a enregistre probs_val et probs_test
     pour CHAQUE run, y compris temporel, dans article1_final/probs/. Le calage
     de temperature s'ajuste sur la validation et s'evalue sur le test : tout
     est deja sur disque. On recalcule donc ECE, score de Brier et diagramme de
     fiabilite sous les deux protocoles, et on les compare.

  B. AUDIT RESIDUEL CONJOINT
     Le balayage mono-feature de l'article dit que chaque feature retenue prise
     SEULE ne porte pas de raccourci. Il ne dit rien de la redondance ENTRE les
     features retenues, ce qui est precisement le mecanisme que l'article
     accuse l'importance par permutation de manquer. On mesure donc, sur les 55
     colonnes auditees : corrélation maximale, information mutuelle avec la
     cible, doublons exacts, et tau, par groupe.

Usage, dans Colab, apres avoir monte Drive :

    !python e3_calibration_residual.py --save /content/drive/MyDrive/GeNIS/article1_final

En local, si probs/ et le cache ont ete telecharges :

    python e3_calibration_residual.py --save chemin/vers/article1_final

Ecrit e3_results.json et deux figures a la largeur finale du cadre du .docx.
"""

import argparse
import json
import pathlib
import re
import sys

import numpy as np

W_IN, DPI = 6.698, 400
BINS = 15


# ======================================================================
# A. Calibration
# ======================================================================
def ece(probs, y, n_bins=BINS):
    """Expected calibration error, memes reglages que le pipeline."""
    conf = probs.max(1)
    pred = probs.argmax(1)
    juste = (pred == y).astype(float)
    bornes = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    for a, b in zip(bornes[:-1], bornes[1:]):
        m = (conf > a) & (conf <= b)
        if m.any():
            e += m.mean() * abs(juste[m].mean() - conf[m].mean())
    return float(e)


def brier(probs, y):
    """Score de Brier multiclasse, forme de Brier originale."""
    oh = np.zeros_like(probs)
    oh[np.arange(len(y)), y] = 1.0
    return float(((probs - oh) ** 2).sum(1).mean())


def temperature(logits_val, y_val):
    """Calage de temperature par recherche sur grille, sur la validation seule."""
    grille = np.concatenate([np.linspace(.05, 1, 40), np.linspace(1.05, 5, 40)])
    best, bt = np.inf, 1.0
    for T in grille:
        p = softmax(logits_val / T)
        nll = -np.log(np.clip(p[np.arange(len(y_val)), y_val], 1e-12, None)).mean()
        if nll < best:
            best, bt = nll, float(T)
    return bt


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def logits_de(probs):
    """Le pipeline a stocke des probabilites, pas des logits : on remonte au log."""
    return np.log(np.clip(probs, 1e-12, None))


def fiabilite(probs, y, n_bins=BINS):
    conf, pred = probs.max(1), probs.argmax(1)
    juste = (pred == y).astype(float)
    bornes = np.linspace(0, 1, n_bins + 1)
    xs, ys, ns = [], [], []
    for a, b in zip(bornes[:-1], bornes[1:]):
        m = (conf > a) & (conf <= b)
        if m.any():
            xs.append(float(conf[m].mean())); ys.append(float(juste[m].mean()))
            ns.append(int(m.sum()))
    return xs, ys, ns


def partie_calibration(save, res):
    probs_dir = save / "probs"
    if not probs_dir.exists():
        print(f"probs/ introuvable sous {save} : partie A sautee")
        return
    R = json.loads((save / "article1_results.json").read_text(encoding="utf-8"))
    y_all = None
    cache = save / "cache" / "slice60.npz"
    if cache.exists():
        y_all = np.load(cache)["y"].astype(int)
    splits_p = save / "frozen_splits_60s.npz"
    if y_all is None or not splits_p.exists():
        print("cache des etiquettes ou splits geles absents : partie A sautee")
        return
    Z = np.load(splits_p)

    print("=" * 74)
    print("A. CALIBRATION SOUS LES DEUX PROTOCOLES")
    print("=" * 74)
    print(f"{'detecteur':<14}{'protocole':<14}{'ECE brut':>10}{'ECE cal.':>10}"
          f"{'Brier':>9}{'T':>7}")
    out = {}
    for f in sorted(probs_dir.glob("*.npz")):
        # le pipeline nomme ses fichiers depuis run_key ; on tolere les
        # separateurs plausibles plutot que d'en supposer un seul
        cle = f.stem
        for sep in ("|", "__", "___"):
            if sep in cle:
                parts = cle.split(sep); break
        else:
            parts = re.split(r"[|_]{1,3}", cle)
        if len(parts) < 3 or "#tuned" in cle or "tuned" in parts:
            continue
        mod, cond, sp = parts[0], parts[1], "_".join(parts[2:])
        if cond != "audited" or sp not in ("strat_seed1", "temporal"):
            continue
        z = np.load(f)
        pv = z["probs_val"].astype("float64"); pt = z["probs_test"].astype("float64")
        pv /= pv.sum(1, keepdims=True); pt /= pt.sum(1, keepdims=True)
        yv = y_all[Z[f"{sp}_val"]]; yt = y_all[Z[f"{sp}_test"]]
        if len(yv) != len(pv) or len(yt) != len(pt):
            print(f"   {mod}|{sp} : tailles incoherentes, ignore"); continue
        T = temperature(logits_de(pv), yv)
        pt_cal = softmax(logits_de(pt) / T)
        r = {"ece_before": ece(pt, yt), "ece_after": ece(pt_cal, yt),
             "brier_before": brier(pt, yt), "brier_after": brier(pt_cal, yt),
             "temperature": T, "n_test": int(len(yt))}
        r["reliability"] = dict(zip(("conf", "acc", "n"), fiabilite(pt, yt)))
        out[f"{mod}|{sp}"] = r
        print(f"{mod:<14}{sp:<14}{r['ece_before']:>10.4f}{r['ece_after']:>10.4f}"
              f"{r['brier_before']:>9.4f}{T:>7.3f}")
    res["calibration_two_protocols"] = out

    couples = {}
    for k, v in out.items():
        m, sp = k.split("|")
        couples.setdefault(m, {})[sp] = v
    ecarts = [(m, d["temporal"]["ece_before"] - d["strat_seed1"]["ece_before"])
              for m, d in couples.items() if len(d) == 2]
    if ecarts:
        print("\necart d'ECE, temporel moins stratifie :")
        for m, e in sorted(ecarts, key=lambda x: -abs(x[1])):
            print(f"   {m:<14}{e:+.4f}")
        res["ece_gap_temporal_minus_stratified"] = dict(ecarts)


# ======================================================================
# B. Audit residuel conjoint
# ======================================================================
def partie_residuel(save, res):
    cache = save / "cache" / "slice60.npz"
    meta = save / "cache" / "slice60_meta.json"
    if not (cache.exists() and meta.exists()):
        print(f"\ncache des features introuvable sous {save} : partie B sautee")
        return
    from sklearn.feature_selection import mutual_info_classif

    R = json.loads((save / "article1_results.json").read_text(encoding="utf-8"))
    M = json.loads(meta.read_text(encoding="utf-8"))
    z = np.load(cache)
    X, y = z["X"], z["y"].astype(int)
    feats = M["feat_all"]
    audites = R["slice60"]["features_audited"]
    idx = [feats.index(c) for c in audites]
    A = X[:, idx]

    print("\n" + "=" * 74)
    print("B. AUDIT RESIDUEL CONJOINT SUR LES FEATURES RETENUES")
    print("=" * 74)
    print(f"{len(audites)} colonnes auditees")

    rng = np.random.RandomState(0)
    ech = rng.choice(len(y), min(120_000, len(y)), replace=False)
    S = A[ech]

    # doublons exacts parmi les retenues : le mecanisme que l'article accuse
    dups = []
    for a in range(S.shape[1]):
        for b in range(a + 1, S.shape[1]):
            if np.allclose(S[:, a], S[:, b], rtol=1e-5, atol=1e-8):
                dups.append([audites[a], audites[b]])
    print(f"doublons exacts parmi les retenues : {len(dups)}"
          f"{'  <-- a expliquer' if dups else '  (aucun : la boucle est fermee)'}")
    for d in dups:
        print("   ", " = ".join(d))

    C = np.corrcoef(np.nan_to_num(S, nan=0., posinf=0., neginf=0.).T)
    np.fill_diagonal(C, 0.0)
    cmax = np.abs(C).max(1)
    mi = mutual_info_classif(np.nan_to_num(S, nan=0., posinf=0., neginf=0.),
                             y[ech], discrete_features=False, random_state=0)
    tt = {r["feature"]: r["transferabilite"] for r in R["audit"]["transfer_table"]}

    lignes = sorted(zip(audites, cmax, mi), key=lambda t: -t[1])
    print(f"\n{'feature':<18}{'|r| max':>9}  {'avec':<18}{'MI':>8}{'tau':>7}")
    for f, c, m in lignes[:15]:
        j = int(np.argmax(np.abs(C[audites.index(f)])))
        print(f"{f:<18}{c:>9.3f}  {audites[j]:<16}{m:>8.3f}{tt.get(f, float('nan')):>7.2f}")

    seuil = 0.99
    tres_correles = [[audites[a], audites[b], float(C[a, b])]
                     for a in range(len(audites)) for b in range(a + 1, len(audites))
                     if abs(C[a, b]) > seuil]
    print(f"\npaires avec |r| > {seuil} : {len(tres_correles)}")
    for a, b, c in tres_correles[:10]:
        print(f"   {a} / {b} : {c:+.4f}")

    res["residual_audit"] = {
        "n_audited": len(audites), "exact_duplicates": dups,
        "max_abs_correlation": {f: float(c) for f, c, _ in lignes},
        "mutual_information": {f: float(m) for f, _, m in lignes},
        "pairs_above_0_99": tres_correles,
        "n_sample": int(len(ech))}


# ======================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True,
                    help="dossier article1_final, contenant probs/, cache/ et le JSON")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    save = pathlib.Path(a.save)
    if not (save / "article1_results.json").exists():
        sys.exit(f"article1_results.json introuvable sous {save}")

    res = {"source": str(save)}
    partie_calibration(save, res)
    partie_residuel(save, res)

    out = pathlib.Path(a.out) if a.out else save / "e3_results.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    print(f"\necrit : {out}")
    print("A me renvoyer : e3_results.json")


if __name__ == "__main__":
    main()
