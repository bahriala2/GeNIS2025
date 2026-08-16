#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e5_intervalles_cinq_graines.ipynb.

E5 repond au majeur 11 du rapport de relecture, qui demande trois choses :

  1. des effectifs de graines identiques entre intervalles. La campagne
     publiee tourne cinq graines a 60 s et trois seulement a 5, 10 et 30 s ;
  2. de rapporter tous les runs individuels, pas seulement la moyenne ;
  3. de ne plus resumer le resultat LightGBM a 10 s par sa moyenne, qui vaut
     0.9458 +/- 0.0766 parce qu'une graine sur trois s'y effondre a 0.8374.

Les points 2 et 3 sont deja regles dans le manuscrit : les runs individuels
sont dans article1_results.json depuis le debut et le tableau 6 les affiche
graine par graine. Ce notebook regle le point 1, le seul qui demande du calcul.

Il N'EST PAS un rejeu integral. Les graines 1 a 3 sont deja mesurees et
enregistrees ; le notebook verifie d'abord qu'il les reproduit sur un run
temoin, puis ne calcule que les graines 4 et 5. Cela divise le cout par
trois : environ 1 h 30 de calcul pur au lieu de 4 h 30, plus le temps de
relecture des CSV bruts.

Le notebook a besoin du CORPUS BRUT (2-flows.zip), pas du cache 60 s.

PREREQUIS : E4a-bis doit avoir confirme la liste noire par l'audit imbrique,
puisque la condition auditee de chaque intervalle est construite dessus.

Relancer ce script apres toute modification, puis deposer le .ipynb sur Colab.
"""
import json
from pathlib import Path

VERSION = "v1"
BUILD = "2026-08-16"
HERE = Path(__file__).resolve().parent

CELLS = []
md = lambda s: CELLS.append({"cell_type": "markdown", "metadata": {},
                             "source": s.strip("\n").split("\n")})
code = lambda s: CELLS.append({"cell_type": "code", "execution_count": None,
                               "metadata": {}, "outputs": [],
                               "source": s.strip("\n").split("\n")})

md(f"""
# E5 — cinq graines à tous les intervalles

> **Notebook {VERSION}, compilé le {BUILD}.** La cellule 1 réaffiche ce numéro.

**Prérequis : E4a-bis doit avoir tourné et confirmé la liste noire**, puisque la condition
auditée de chaque intervalle est construite dessus.

**La critique à laquelle ce notebook répond.** Le majeur 11 demande trois choses :

1. des effectifs de graines identiques entre intervalles — la campagne publiée tourne
   **cinq** graines à 60 s et **trois** à 5, 10 et 30 s ;
2. de rapporter tous les runs individuels ;
3. de ne plus résumer LightGBM à 10 s par sa moyenne.

Les points 2 et 3 sont déjà réglés dans le manuscrit : les runs individuels étaient dans
`article1_results.json` depuis le début, et le tableau 6 les affiche désormais graine par
graine, cellule vide comprise là où la graine manque. **Ce notebook règle le point 1**,
le seul qui demande du calcul.

**Ce n'est pas un rejeu intégral.** Les graines 1 à 3 sont déjà mesurées. Le notebook
vérifie d'abord qu'il les reproduit sur un run témoin (LightGBM, graine 1, intervalle
30 s, le moins cher), puis ne calcule que **les graines 4 et 5**. Si le témoin ne
reproduit pas, il le dit et recalcule les cinq, parce que mélanger deux environnements
dans une même moyenne serait pire que le déséquilibre qu'on corrige.

**Durée.** Mesurée sur les temps d'ajustement enregistrés : 21 min par graine à 5 s,
18 min à 10 s, 7 min à 30 s, soit **≈ 1 h 30 de calcul pur** pour deux graines sur les
trois intervalles, plus 5 à 10 min de relecture des CSV par intervalle. Compter 2 à 3 h.
Le notebook est reprenable : il saute tout run déjà présent dans son état.

**Ce que ça règle.** Soit l'effondrement de la graine 3 à 10 s se reproduit sur les
graines 4 ou 5, et c'est alors un résultat sur la stabilité de LightGBM à cet intervalle ;
soit il reste isolé, et la section 6.4 peut le qualifier sur cinq observations au lieu de
trois. Dans les deux cas la comparaison entre intervalles devient équilibrée.

**À me renvoyer :** `e5_results.json`.
""")

code(r'''
# --- 1. Drive, dossier, verrou de la liste noire --------------------------
E5_VERSION = "VERSION_PLACEHOLDER"; E5_BUILD = "BUILD_PLACEHOLDER"
print(f"E5 notebook {E5_VERSION}, compile le {E5_BUILD}\n")
import pathlib, json, sys, os, glob, shutil, time, gc
from google.colab import drive
drive.mount("/content/drive")

MYDRIVE = pathlib.Path("/content/drive/MyDrive")
MARQUEUR = "article1_results.json"
candidats = [MYDRIVE / "GeNIS" / "article1_final", MYDRIVE / "article1_final",
             MYDRIVE / "GeNIS"]
trouves = [c for c in candidats if (c / MARQUEUR).exists()]
if not trouves:
    for prof in ("*/", "*/*/", "*/*/*/"):
        trouves = [p.parent for p in MYDRIVE.glob(prof + MARQUEUR)]
        if trouves:
            break
if not trouves:
    sys.exit(f"{MARQUEUR} introuvable sous {MYDRIVE}.")
SAVE = trouves[0]
print(f"dossier de travail : {SAVE}")

# Meme verrou que E4b et E4c : c'est l'audit imbrique de E4a-bis qui fait foi,
# et la condition auditee de chaque intervalle est construite sur sa liste.
E4AB = SAVE / "e4abis_results.json"
if not E4AB.exists():
    sys.exit("e4abis_results.json introuvable : lance E4a-bis d'abord. Le "
             "verdict de E4a seul ne suffit pas ; voir experiments/e4a/FINDINGS.md")
_B = json.loads(E4AB.read_text(encoding="utf-8"))
_R = json.loads((SAVE / MARQUEUR).read_text(encoding="utf-8"))
_N = _B["nested"]
_PUB = sorted(f for f in _R["audit"]["blacklist"] if f in _N)
_P, _K = _R["audit"]["chance"], _R["audit"]["rule"]["min_acc_x_chance"]
_elig = [f for f in _N if _N[f]["strat"] > _K * _P]
_srt = sorted(_elig, key=lambda f: _N[f]["tau"])
_ok_liste = set(_srt[:len(_PUB)]) == set(_PUB)
print(f"audit imbrique : {len(_elig)} eligibles, {len(_PUB)} colonnes publiees")
print(f"   les {len(_PUB)} publiees sont-elles les {len(_PUB)} plus basses ? "
      f"{'OUI' if _ok_liste else 'NON'}")
if not _ok_liste:
    sys.exit("\nARRET. L'audit imbrique ne retrouve pas la liste publiee.")
print("verrou leve.\n")
''')

code(r'''
# --- 2. Corpus brut, et le pretraitement de la cellule 1.3 ---------------
# Les intervalles courts ne sont PAS dans le cache 60 s : il faut les CSV.
import numpy as np, pandas as pd
WORK = pathlib.Path("/content/genis"); WORK.mkdir(parents=True, exist_ok=True)
os.chdir(WORK)
drive_zip = MYDRIVE / "GeNIS" / "2-flows.zip"
if not pathlib.Path("flows").exists():
    if drive_zip.exists():
        print("copie de 2-flows.zip depuis Drive…", flush=True)
        shutil.copy(drive_zip, "2-flows.zip")
    else:
        print("telechargement depuis Zenodo (~380 Mo)…", flush=True)
        os.system('wget -q "https://zenodo.org/records/14919237/files/'
                  '2-flows.zip?download=1" -O 2-flows.zip')
    os.system("unzip -o -q 2-flows.zip -d flows")
csvs = sorted(glob.glob("flows/**/*.csv", recursive=True))
assert csvs, "aucun CSV trouve"
print(f"{len(csvs)} fichiers CSV")

# Recopie mot pour mot de la cellule 1.3 du pipeline. Toute divergence ici
# casserait la reproduction des graines 1 a 3, donc rien n'est "ameliore".
IDENT_LIST = ["FlowID", "AutoId", "SrcAddr", "DstAddr", "Ssaddr", "Sdaddr",
              "SrcMac", "DstMac", "SrcOui", "DstOui", "Sport", "Dport",
              "sIpId", "dIpId", "sMpls", "dMpls", "sAS", "dAS", "iAS",
              "sCo", "dCo", "sVid", "dVid"]
POS_LIST = ["StartTime", "LastTime", "Rank", "Seq"]
LAB_LIST = ["BinaryLabel", "CategoryLabel", "SubCategoryLabel"]

def feature_sets(d):
    ident = [c for c in IDENT_LIST if c in d.columns]
    pos = [c for c in POS_LIST if c in d.columns]
    num = (d.drop(columns=ident + LAB_LIST, errors="ignore")
             .select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan))
    nu = num.nunique(dropna=True); const = nu[nu <= 1].index.tolist()
    num = num.drop(columns=const).fillna(0.0).astype(np.float32)
    return num, list(num.columns), [c for c in num.columns if c not in pos], pos, ident, const

def load_slice_df(iv):
    files = [c for c in csvs if f"flows-{iv}-sec" in c]
    d = pd.concat([pd.read_csv(c, low_memory=False) for c in files], ignore_index=True)
    ysub = d["SubCategoryLabel"].astype(str).str.strip()
    y9 = ysub.where(~ysub.str.startswith("benign"), "benign")
    return d, y9

R = _R
BLACKLIST = R["audit"]["blacklist"]
CLASS_NAMES = R["slice60"]["classes"]; C = len(CLASS_NAMES)
BENIGN = CLASS_NAMES.index("benign")
INTERVALLES = ["5", "10", "30"]
GRAINES = [1, 2, 3, 4, 5]
MODELES = ["lightgbm", "xgboost", "dnn"]
print(f"\nliste noire : {len(BLACKLIST)} colonnes | classes : {C}")
''')

code(r'''
# --- 3. Detecteurs et evaluation, identiques a la cellule 6.4 ------------
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import f1_score, matthews_corrcoef, average_precision_score, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

def make_sk(name):
    if name == "xgboost":
        return XGBClassifier(n_estimators=300, max_depth=8, learning_rate=.1,
                             tree_method="hist", n_jobs=2, random_state=0,
                             eval_metric="mlogloss")
    if name == "lightgbm":
        return LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=.1,
                              n_jobs=2, random_state=0, verbose=-1)
    raise KeyError(name)

def build_dnn(F):
    return models.Sequential([layers.Input((F,)),
        layers.Dense(128, activation="relu"), layers.Dropout(.3),
        layers.Dense(64, activation="relu"), layers.Dropout(.2),
        layers.Dense(C, activation="softmax")], name="dnn")

def class_weights_safe(ytr):
    present = np.unique(ytr)
    w = compute_class_weight("balanced", classes=present, y=ytr)
    cw = {int(c): 1.0 for c in range(C)}
    cw.update({int(c): float(v) for c, v in zip(present, w)})
    return cw

def fit_sk(mname, Xtr, ytr):
    present = np.unique(ytr); model = make_sk(mname)
    model.fit(Xtr, np.searchsorted(present, ytr) if len(present) < C else ytr)
    def predict_full(Xa):
        p = model.predict_proba(Xa)
        if len(present) == C and list(getattr(model, "classes_", range(C))) == list(range(C)):
            return p
        out = np.zeros((len(Xa), C), dtype=np.float32)
        out[:, (present if len(present) < C else np.asarray(model.classes_, int))] = p
        return out
    return model, predict_full

def evaluate(y_true, probs, fit_t, pred_t):
    pred = probs.argmax(1); present = np.unique(y_true)
    is_att, pred_att = y_true != BENIGN, pred != BENIGN
    p_att = 1.0 - probs[:, BENIGN]
    return {"accuracy": float((pred == y_true).mean()),
            "macro_f1": float(f1_score(y_true, pred, labels=present, average="macro",
                                       zero_division=0)),
            "weighted_f1": float(f1_score(y_true, pred, average="weighted", zero_division=0)),
            "mcc": float(matthews_corrcoef(y_true, pred)),
            "per_class_f1": {CLASS_NAMES[i]: float(v) for i, v in zip(range(C),
                f1_score(y_true, pred, labels=range(C), average=None, zero_division=0))},
            "binary": {"detection_f1": float(f1_score(is_att, pred_att, zero_division=0)),
                       "fpr": float(pred_att[~is_att].mean()) if (~is_att).any() else None,
                       "fnr": float((~pred_att[is_att]).mean()) if is_att.any() else None,
                       "pr_auc": float(average_precision_score(is_att, p_att)) if 0 < is_att.mean() < 1 else None,
                       "roc_auc": float(roc_auc_score(is_att, p_att)) if 0 < is_att.mean() < 1 else None},
            "fit_time_s": round(fit_t, 2), "predict_time_s": round(pred_t, 3),
            "n_test": int(len(y_true))}

def un_run(mname, s, Xiv, y_iv, itr, iva_, ite_):
    sc = RobustScaler().fit(Xiv[itr])
    Xtr, Xva, Xte = [np.nan_to_num(sc.transform(Xiv[i_]), nan=0., posinf=0., neginf=0.)
                     .astype(np.float32) for i_ in (itr, iva_, ite_)]
    ytr_, yte_ = y_iv[itr], y_iv[ite_]
    if mname in ("lightgbm", "xgboost"):
        t0 = time.time(); mdl, pf = fit_sk(mname, Xtr, ytr_); ft = time.time() - t0
        t0 = time.time(); pte = pf(Xte); pt = time.time() - t0
        out = evaluate(yte_, pte, ft, pt)
        del mdl, pf, pte
    else:
        tf.keras.utils.set_random_seed(s)
        mdl = build_dnn(Xtr.shape[1])
        mdl.compile(optimizer="adam", loss="sparse_categorical_crossentropy",
                    metrics=["accuracy"])
        t0 = time.time()
        mdl.fit(Xtr, ytr_, validation_data=(Xva, y_iv[iva_]), epochs=30, batch_size=256,
                class_weight=class_weights_safe(ytr_), verbose=0,
                callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=5,
                                                   restore_best_weights=True)])
        ft = time.time() - t0
        t0 = time.time(); pte = mdl.predict(Xte, batch_size=1024, verbose=0)
        pt = time.time() - t0
        out = evaluate(yte_, pte, ft, pt)
        del mdl, pte; tf.keras.backend.clear_session()
    del Xtr, Xva, Xte; gc.collect()
    return out

def split_de(y_iv, s):
    idx = np.arange(len(y_iv))
    itr, itmp = train_test_split(idx, test_size=.4, random_state=s, stratify=y_iv)
    iva_, ite_ = train_test_split(itmp, test_size=.5, random_state=s, stratify=y_iv[itmp])
    return itr, iva_, ite_

STATE_PATH = SAVE / "e5_results.json"
def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {"version": E5_VERSION, "build": E5_BUILD},
            "temoin": None, "runs": {}}
def save_state(st):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    tmp.replace(STATE_PATH)
STATE = load_state()
print(f"etat : {len(STATE['runs'])} runs deja faits")
''')

code(r'''
# --- 4. Temoin : reproduit-on les graines deja publiees ? ----------------
# On rejoue le run le moins cher de la campagne (LightGBM, graine 1, 30 s) et
# on le compare a la valeur enregistree. Tant qu'on ne sait pas si les graines
# 1 a 3 sont reproductibles ici, on ne sait pas si on a le droit de les
# melanger aux graines 4 et 5 dans une meme moyenne.
TOL = 1e-4
if STATE.get("temoin") is None:
    print("chargement de l'intervalle 30 s pour le temoin…", flush=True)
    d30, y9_30 = load_slice_df("30")
    num30, _, clean30, _, _, _ = feature_sets(d30)
    aud30 = [c for c in clean30 if c not in BLACKLIST]
    X30 = np.ascontiguousarray(num30[aud30].values, dtype=np.float32)
    y30 = np.array([CLASS_NAMES.index(v) for v in y9_30])
    del d30, num30; gc.collect()
    itr, iva_, ite_ = split_de(y30, 1)
    r = un_run("lightgbm", 1, X30, y30, itr, iva_, ite_)
    ref = R["intervals"]["30"]["runs"]["lightgbm|seed1"]["macro_f1"]
    ecart = abs(r["macro_f1"] - ref)
    STATE["temoin"] = {"rejoue": r["macro_f1"], "publie": ref, "ecart": ecart,
                       "reproduit": bool(ecart <= TOL)}
    save_state(STATE)
    del X30, y30; gc.collect()
T = STATE["temoin"]
print(f"temoin LightGBM 30 s graine 1 : rejoue {T['rejoue']:.6f}, "
      f"publie {T['publie']:.6f}, ecart {T['ecart']:.2e}")
if T["reproduit"]:
    A_CALCULER = [4, 5]
    print("environnement reproductible : on ne calcule que les graines 4 et 5.\n")
else:
    A_CALCULER = [1, 2, 3, 4, 5]
    print("ATTENTION : le temoin ne reproduit pas la valeur publiee.\n"
          "Les cinq graines seront recalculees ici, et c'est CE jeu-la qui doit\n"
          "etre rapporte, pas un melange des deux environnements.\n")
''')

code(r'''
# --- 5. Les graines manquantes, intervalle par intervalle ---------------
for iv in INTERVALLES:
    manque = [(m, s) for s in A_CALCULER for m in MODELES
              if f"{iv}|{m}|seed{s}" not in STATE["runs"]]
    if not manque:
        print(f"=== intervalle {iv} s : deja complet ===", flush=True)
        continue
    print(f"\n=== intervalle {iv} s : {len(manque)} run(s) a faire ===", flush=True)
    d_iv, y9_iv = load_slice_df(iv)
    num_iv, _, cleanc, _, _, _ = feature_sets(d_iv)
    audc = [c for c in cleanc if c not in BLACKLIST]
    Xiv = np.ascontiguousarray(num_iv[audc].values, dtype=np.float32)
    y_iv = np.array([CLASS_NAMES.index(v) for v in y9_iv])
    del d_iv, num_iv; gc.collect()
    STATE.setdefault("intervalles", {})[iv] = {
        "n": int(len(y_iv)), "benign_share": float((y_iv == BENIGN).mean()),
        "n_features": len(audc)}
    print(f"  {len(y_iv):,} flux, {len(audc)} colonnes auditees", flush=True)
    for s in A_CALCULER:
        if all(f"{iv}|{m}|seed{s}" in STATE["runs"] for m in MODELES):
            continue
        itr, iva_, ite_ = split_de(y_iv, s)
        for m in MODELES:
            cle = f"{iv}|{m}|seed{s}"
            if cle in STATE["runs"]:
                continue
            t0 = time.time()
            print(f"  [graine {s}] {m} …", end="", flush=True)
            STATE["runs"][cle] = un_run(m, s, Xiv, y_iv, itr, iva_, ite_)
            save_state(STATE)
            print(f" macro-F1 {STATE['runs'][cle]['macro_f1']:.4f} "
                  f"({time.time()-t0:.0f} s)", flush=True)
    del Xiv, y_iv; gc.collect()
print("\ntous les runs demandes sont faits.")
''')

code(r'''
# --- 6. Tous les runs individuels, et le verdict sur 10 s ---------------
# Le relecteur demande explicitement les runs individuels : on les imprime
# tous, sans moyenne, avant toute synthese.
def valeurs(iv, m):
    """macro-F1 par graine, en prenant le publie pour 1-3 et le neuf pour 4-5."""
    out = {}
    for s in GRAINES:
        cle = f"{iv}|{m}|seed{s}"
        if cle in STATE["runs"]:
            out[s] = STATE["runs"][cle]["macro_f1"]
        elif s in (1, 2, 3):
            r_ = R["intervals"].get(iv, {}).get("runs", {}).get(f"{m}|seed{s}")
            if r_:
                out[s] = r_["macro_f1"]
    return out

print(f"{'iv':>4} {'modele':<10}" + "".join(f"{'graine '+str(s):>10}" for s in GRAINES)
      + f"{'min':>9}{'mediane':>10}{'max':>9}")
TABLE = {}
for iv in INTERVALLES + ["60"]:
    for m in MODELES:
        if iv == "60":
            v = {s: R["models"][f"{m}|audited|strat_seed{s}"]["macro_f1"]
                 for s in GRAINES if f"{m}|audited|strat_seed{s}" in R["models"]}
        else:
            v = valeurs(iv, m)
        if not v:
            continue
        TABLE[f"{iv}|{m}"] = v
        xs = sorted(v.values())
        med = xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs)//2-1] + xs[len(xs)//2]) / 2
        print(f"{iv:>4} {m:<10}" + "".join(
              (f"{v[s]:>10.4f}" if s in v else f"{'-':>10}") for s in GRAINES)
              + f"{xs[0]:>9.4f}{med:>10.4f}{xs[-1]:>9.4f}")

SEUIL = 0.99
print("\n--- effondrements (macro-F1 < %.2f) ---" % SEUIL)
eff = {k: {s: x for s, x in v.items() if x < SEUIL}
       for k, v in TABLE.items() if any(x < SEUIL for x in v.values())}
for k, v in eff.items():
    print(f"  {k:<16} graines {sorted(v)} -> {[round(x,4) for x in v.values()]}")

k10 = "10|lightgbm"
if k10 in TABLE:
    v = TABLE[k10]
    bas = sorted(s for s, x in v.items() if x < SEUIL)
    print(f"\nVERDICT 10 s, LightGBM : {len(bas)} graine(s) sur {len(v)} "
          f"sous {SEUIL} -> {bas}")
    print("  " + ("effondrement ISOLE : la graine 3 reste seule, la section 6.4 "
                  "peut le qualifier sur cinq observations."
                  if len(bas) == 1 else
                  "effondrement REPRODUIT : ce n'est plus un accident de graine "
                  "mais une instabilite de LightGBM a cet intervalle, et la "
                  "section 6.4 doit le dire ainsi."))

STATE["table_macro_f1"] = TABLE
STATE["effondrements"] = eff
STATE["meta"]["graines_calculees"] = A_CALCULER
save_state(STATE)
print(f"\necrit : {STATE_PATH}")
''')

md("""
## Ce qu'il faut me renvoyer

`e5_results.json`, depuis le dossier de travail. Il contient :

- `temoin` — le run témoin et son écart à la valeur publiée, donc la preuve que les
  graines 1 à 3 et les graines 4 et 5 viennent du même environnement, ou l'aveu qu'elles
  n'en viennent pas ;
- `runs` — chaque run individuel calculé ici, au format complet du pipeline (macro-F1,
  F1 par classe, vue binaire, temps) ;
- `table_macro_f1` — le tableau complet graine par graine, intervalle 60 s inclus, qui
  remplace le tableau 6 du manuscrit ;
- `effondrements` — la liste explicite des runs sous 0.99, qui est ce que le relecteur
  demande de ne pas noyer dans une moyenne.

## Ce que ce notebook ne fait pas

Il ne retouche pas `article1_results.json`. Les graines 4 et 5 vivent dans un fichier à
part tant que le témoin n'a pas été lu, parce qu'écrire dans le fichier de la campagne
publiée avant d'avoir vérifié la reproductibilité mélangerait deux environnements de
façon irréversible.

Il ne rejoue pas non plus le protocole temporel aux intervalles courts. La campagne
publiée ne l'a jamais fait à 5, 10 et 30 s, le manuscrit ne le prétend pas, et le
majeur 11 ne le demande pas.
""")

nb = {"cells": CELLS,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

txt = json.dumps(nb, indent=1, ensure_ascii=False)
txt = txt.replace("VERSION_PLACEHOLDER", VERSION).replace("BUILD_PLACEHOLDER", BUILD)
out = HERE / "e5_intervalles_cinq_graines.ipynb"
out.write_text(txt, encoding="utf-8")
print(f"ecrit : {out}  ({len(CELLS)} cellules)")
