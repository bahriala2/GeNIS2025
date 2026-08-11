#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e1_anchored_comparison.ipynb.

Ecrire le JSON d'un notebook a la main est fragile ; ce generateur le produit et
le valide. Relancer ce script apres toute modification.
"""
import json
from pathlib import Path

CELLS = []


def md(src):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": src.strip("\n").split("\n")})


def code(src):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.strip("\n").split("\n")})


# ---------------------------------------------------------------- 0. titre
md(r"""
# E1 : comparaison ancrée sur le module `4-preprocessed` de GeNIS

Expérience complémentaire de l'article *A Leakage-Audited Benchmark of Deep and Ensemble
Detectors on the GeNIS 2025 Corpus*.

**Question.** L'article évalue le module `2-flows` sous un protocole audité. La baseline du
corpus (Silva et al., FPS 2025) évalue le module `4-preprocessed` sous un découpage aléatoire.
Les deux ne sont donc pas comparables terme à terme. E1 rejoue **nos modèles sur leurs
données, leur découpage et leur taxonomie**, puis mesure ce que l'audit y change.

**Ce que le notebook produit.**

1. Un audit du module tel qu'il est distribué : colonnes dupliquées, pouvoir prédictif de
   chaque colonne prise seule sur leur holdout.
2. Onze détecteurs sous **trois conditions de features** :
   `as-distributed` (les 87 colonnes), `no-topology` (sans les identifiants),
   `audited` (sans les identifiants ni les doublons de durée).
3. Deux granularités : leur tâche à 4 classes `CategoryLabel`, qui est l'ancrage, et la tâche
   à 13 classes `SubCategoryLabel`, qui est la granularité que l'article défend.
4. Trois figures prêtes pour le papier et un JSON de résultats.

**Durée.** Environ 60 à 90 minutes avec GPU, davantage sans. Le notebook est **reprenable** :
chaque résultat est écrit sur disque dès qu'il est calculé, une déconnexion ne fait perdre que
le modèle en cours.

**Prérequis.** Le dossier `4-preprocessed` accessible depuis Colab. Deux voies au choix dans la
cellule suivante : Google Drive, ou dépôt direct dans `/content`.
""")

# ---------------------------------------------------------------- 1. environnement
md("""
## 1. Environnement et chemins

Colab ne voit pas le disque de votre machine. Il faut donc lui donner les deux fichiers dont
E1 a besoin, et **deux fichiers suffisent** : `genis-60-sec-train.csv` et
`genis-60-sec-test.csv`. Inutile de transférer les trois autres intervalles, ni les captures
brutes.

Trois voies, à choisir dans la cellule suivante avec `SOURCE`.

| `SOURCE` | quand l'utiliser | transfert |
|---|---|---|
| `"drive"` | **recommandé** : déposer les deux CSV dans un dossier de Google Drive, une fois pour toutes | une fois |
| `"upload"` | essai rapide, sans Drive | à chaque session |
| `"url"` | télécharger directement depuis Zenodo dans Colab | rien depuis votre PC |

Avec `"drive"`, les résultats et les figures sont écrits sur Drive eux aussi : une déconnexion
ne fait rien perdre. Avec `"upload"`, tout disparaît à la fin de la session, pensez à
récupérer `e1_results.json` et `e1_figures.zip` avant de fermer.
""")

code(r"""
# --- 1.1 Ou sont les donnees ? ---------------------------------------------

SOURCE = "drive"          # "drive" | "upload" | "url"

# SOURCE = "drive" : dossier de Drive contenant les deux CSV
DRIVE_DIR = "/content/drive/MyDrive/Genis/4-preprocessed"

# SOURCE = "url" : liens directs vers les deux fichiers (Zenodo, ou tout autre hebergeur)
URL_TRAIN = ""
URL_TEST  = ""

INTERVAL = 60             # 5, 10, 30 ou 60. L'article se concentre sur 60 s.
SEEDS = [1, 2, 3]         # 3 graines suffisent pour l'ecart entre conditions
KNN_MAX_TRAIN = 50_000    # k-NN : sous-echantillon declare, comme dans l'article
HPO = False               # E1 compare des conditions, pas des hyperparametres

import os, json, gc, time, warnings, shutil, subprocess
from pathlib import Path
warnings.filterwarnings("ignore")

if SOURCE == "drive":
    from google.colab import drive
    drive.mount("/content/drive")
    DATA_DIR = DRIVE_DIR
    OUT_DIR = str(Path(DRIVE_DIR).parent / "E1")

elif SOURCE == "upload":
    from google.colab import files
    DATA_DIR = OUT_DIR = "/content/e1"
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    have = list(Path(DATA_DIR).glob("*.csv"))
    if len(have) < 2:
        print(f"Selectionnez genis-{INTERVAL}-sec-train.csv ET genis-{INTERVAL}-sec-test.csv")
        for name, blob in files.upload().items():
            Path(DATA_DIR, name).write_bytes(blob)
    else:
        print("fichiers deja presents, televersement saute")

elif SOURCE == "url":
    DATA_DIR = OUT_DIR = "/content/e1"
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    assert URL_TRAIN and URL_TEST, "renseigner URL_TRAIN et URL_TEST"
    for url, name in ((URL_TRAIN, f"genis-{INTERVAL}-sec-train.csv"),
                      (URL_TEST,  f"genis-{INTERVAL}-sec-test.csv")):
        dest = Path(DATA_DIR, name)
        if dest.exists():
            print("deja la :", name); continue
        print("telechargement :", name, flush=True)
        subprocess.run(["wget", "-q", "--show-progress", "-O", str(dest), url], check=True)
else:
    raise ValueError("SOURCE doit valoir drive, upload ou url")

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
for sub in ("figures", "models"):
    Path(OUT_DIR, sub).mkdir(exist_ok=True)

# --- verification : les deux fichiers sont-ils bien la ? --------------------
found = sorted(Path(DATA_DIR).rglob(f"*{INTERVAL}-sec*.csv"))
print(f"\ndonnees : {DATA_DIR}")
for f in found:
    print(f"   {f.name:<32} {f.stat().st_size/1e6:8.1f} Mo")
assert any("train" in f.name.lower() for f in found), \
    f"genis-{INTERVAL}-sec-train.csv introuvable sous {DATA_DIR}"
assert any("test" in f.name.lower() for f in found), \
    f"genis-{INTERVAL}-sec-test.csv introuvable sous {DATA_DIR}"
print("sorties :", OUT_DIR)
if SOURCE != "drive":
    print("\nATTENTION : /content est efface a la fin de la session."
          "\nRecuperez e1_results.json et e1_figures.zip avant de fermer.")
""")

code(r"""
# --- 1.2 Bibliotheques et GPU ----------------------------------------------
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, matthews_corrcoef, confusion_matrix
from sklearn.dummy import DummyClassifier

import xgboost as xgb, lightgbm as lgb
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

GPU = len(tf.config.list_physical_devices("GPU")) > 0
print("TensorFlow", tf.__version__, "| GPU :", "OUI" if GPU else "NON (les modeles profonds seront lents)")
print("pandas", pd.__version__, "| numpy", np.__version__)
""")

# ---------------------------------------------------------------- 2. etat reprenable
md("""
## 2. État reprenable

Tout résultat calculé est écrit immédiatement dans `e1_results.json`. Relancer le notebook
après une déconnexion reprend là où il s'était arrêté : les runs déjà présents sont sautés.
""")

code(r"""
STATE_PATH = Path(OUT_DIR, "e1_results.json")

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {}, "columns": {}, "single_feature": {}, "runs": {}, "duplicates": []}

def save_state(s):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    tmp.replace(STATE_PATH)

STATE = load_state()
print("runs deja presents :", len(STATE["runs"]))
""")

# ---------------------------------------------------------------- 3. donnees
md("## 3. Chargement de leur découpage")

code(r"""
def read_csv(path):
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError("encodage illisible : %s" % path)

root = Path(DATA_DIR)
pat = f"{INTERVAL}-sec"
csvs = sorted(root.rglob("*.csv"))
assert csvs, f"aucun CSV sous {root}"
ftr = next(p for p in csvs if pat in p.name.lower() and "train" in p.name.lower())
fte = next(p for p in csvs if pat in p.name.lower() and "test" in p.name.lower())

TRAIN, TEST = read_csv(ftr), read_csv(fte)
print(f"train  {ftr.name}  {TRAIN.shape}")
print(f"holdout {fte.name}  {TEST.shape}")
print(f"total {len(TRAIN)+len(TEST):,} flux, {TRAIN.shape[1]} colonnes".replace(",", " "))

LABELS = [c for c in ("BinaryLabel", "CategoryLabel", "SubCategoryLabel") if c in TRAIN.columns]
for lab in LABELS:
    vc = TRAIN[lab].astype(str).value_counts()
    print(f"\n{lab} : {len(vc)} classes, majoritaire {vc.iloc[0]/len(TRAIN):.4f}")
    print("   " + ", ".join(f"{k} {v}" for k, v in vc.items()))

STATE["meta"] = {"interval": INTERVAL, "n_train": len(TRAIN), "n_test": len(TEST),
                 "n_columns": int(TRAIN.shape[1]), "train_file": ftr.name, "test_file": fte.name}
save_state(STATE)
""")

# ---------------------------------------------------------------- 4. taxonomie des colonnes
md("""
## 4. Taxonomie des colonnes et détection des doublons

Les trois conditions de features sont définies ici. La liste des identifiants reprend celle de
la section 4.3 de l'article : exclusion **par noms explicites**, jamais par motif de
sous-chaîne, un `"id"` naïf capturant `IdleTime`.
""")

code(r"""
# --- 4.1 Identifiants et colonnes liees a la topologie ----------------------
IDENT_NAMES = {
    "SrcAddr", "DstAddr", "Sport", "Dport", "Proto", "sMac", "dMac", "SrcMac", "DstMac",
    "sVid", "dVid", "SrcVid", "DstVid", "sAS", "dAS", "SrcAS", "DstAS",
    "Ssaddr", "Sdaddr", "FlowID", "AutoId", "SrcId", "Trans", "Seq", "Rank",
    "StartTime", "LastTime",
}
DUP_FAMILY = ["Dur", "RunTime", "Mean", "Sum", "Min", "Max"]   # famille de duree de l'article
INTERPKT = ["SIntPkt", "SIntPktMax"]

cols = [c for c in TRAIN.columns if c not in LABELS]
ident = [c for c in cols if c in IDENT_NAMES]
print(f"identifiants presents ({len(ident)}) : {', '.join(ident) or 'aucun'}")

num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(TRAIN[c])]
print(f"colonnes numeriques : {len(num_cols)} / {len(cols)}")
""")

code(r"""
# --- 4.2 Colonnes numeriquement identiques (np.allclose, deux passes) -------
def duplicate_groups(df, cols, sample=20000):
    probe = df[cols].sample(min(sample, len(df)), random_state=0) if len(df) > sample else df[cols]
    sig = {}
    for c in cols:
        v = probe[c].to_numpy(dtype="float64", na_value=np.nan)
        sig.setdefault(round(float(np.nansum(v)), 6), []).append(c)
    groups = []
    for grp in [g for g in sig.values() if len(g) > 1]:
        rest = list(grp)
        while rest:
            ref = rest.pop(0)
            a = df[ref].to_numpy(dtype="float64", na_value=np.nan)
            same = [ref]
            for other in list(rest):
                b = df[other].to_numpy(dtype="float64", na_value=np.nan)
                if np.allclose(a, b, rtol=0, atol=0, equal_nan=True):
                    same.append(other); rest.remove(other)
            if len(same) > 1:
                groups.append(same)
    return groups

t0 = time.time()
GROUPS = duplicate_groups(TRAIN, num_cols)
print(f"detection en {time.time()-t0:.0f} s")
n_pairs = sum(len(g)*(len(g)-1)//2 for g in GROUPS)
for g in GROUPS:
    print(f"   [{len(g)} colonnes, {len(g)*(len(g)-1)//2} paires] " + " = ".join(g))
print(f"total {len(GROUPS)} groupes, {n_pairs} paires identiques")

# on ne garde qu'un representant par groupe
DUP_DROP = [c for g in GROUPS for c in g[1:]]
STATE["duplicates"] = GROUPS
save_state(STATE)
""")

code(r"""
# --- 4.3 Les trois conditions ----------------------------------------------
CONDITIONS = {
    "as-distributed": cols,                                            # les 87 colonnes
    "no-topology":    [c for c in cols if c not in ident],             # sans les identifiants
    "audited":        [c for c in cols if c not in ident and c not in DUP_DROP],
}
for k, v in CONDITIONS.items():
    print(f"{k:>15} : {len(v)} features")
print(f"\nretirees par no-topology : {', '.join(ident)}")
print(f"retirees en plus par audited : {', '.join(DUP_DROP)}")

STATE["columns"] = {k: v for k, v in CONDITIONS.items()}
STATE["columns"]["identifiers"] = ident
STATE["columns"]["duplicates_dropped"] = DUP_DROP
save_state(STATE)
""")

# ---------------------------------------------------------------- 5. audit une feature
md("""
## 5. Audit à une feature sur leur holdout

Un arbre de décision par colonne, entraîné sur leur partition d'entraînement et évalué sur leur
holdout. C'est la mesure qui alimente la note de la section 2.4 de l'article, et la figure E1.1.

Sans horodatage dans ce module, aucun protocole temporel n'est constructible : on rapporte donc
un **pouvoir prédictif isolé**, jamais une transférabilité.
""")

code(r"""
def single_feature_scan(label, features):
    y_tr = TRAIN[label].astype(str).to_numpy()
    y_te = TEST[label].astype(str).to_numpy()
    maj = pd.Series(y_te).value_counts(normalize=True).iloc[0]
    out = {}
    for i, c in enumerate(features, 1):
        xtr = pd.to_numeric(TRAIN[c], errors="coerce").to_numpy(dtype="float64").reshape(-1, 1)
        xte = pd.to_numeric(TEST[c], errors="coerce").to_numpy(dtype="float64").reshape(-1, 1)
        ktr, kte = ~np.isnan(xtr).ravel(), ~np.isnan(xte).ravel()
        if ktr.sum() < 100 or kte.sum() < 100:
            continue
        clf = DecisionTreeClassifier(random_state=1).fit(xtr[ktr], y_tr[ktr])
        pred = clf.predict(xte[kte])
        out[c] = {"accuracy": float(accuracy_score(y_te[kte], pred)),
                  "macro_f1": float(f1_score(y_te[kte], pred, average="macro", zero_division=0)),
                  "n_unique": int(np.unique(xtr[ktr]).size)}
        if i % 10 == 0:
            print(f"   {i}/{len(features)}", flush=True)
    return {"majority_class_rate": float(maj), "n_classes": int(pd.Series(y_te).nunique()),
            "features": out}

for lab in ("SubCategoryLabel", "CategoryLabel"):
    if lab in LABELS and lab not in STATE["single_feature"]:
        print(f"\nbalayage sur {lab} ({len(num_cols)} colonnes)")
        STATE["single_feature"][lab] = single_feature_scan(lab, num_cols)
        save_state(STATE)

for lab, r in STATE["single_feature"].items():
    top = sorted(r["features"].items(), key=lambda kv: -kv[1]["accuracy"])[:8]
    print(f"\n{lab} : {r['n_classes']} classes, hasard {r['majority_class_rate']:.4f}")
    for c, v in top:
        in_dup = any(c in g for g in GROUPS)
        tag = "identifiant" if c in ident else ("doublon" if in_dup else "")
        print(f"   {c:<14} {v['accuracy']:.4f}  ({v['n_unique']:>6} valeurs) {tag}")
""")

# ---------------------------------------------------------------- 6. modeles
md("""
## 6. Les onze détecteurs

Mêmes architectures que dans l'article, pour que la comparaison soit lisible : trio RNN, CNN,
DNN de l'étude comparative antérieure, FT-Transformer, trois ensembles d'arbres, régression
logistique, k-NN, bayésien naïf, et une baseline de classe majoritaire.
""")

code(r"""
def build_rnn(n_in, n_out):
    m = keras.Sequential([layers.Input((n_in, 1)), layers.SimpleRNN(64), layers.Dense(n_out, activation="softmax")])
    return m

def build_cnn(n_in, n_out):
    return keras.Sequential([layers.Input((n_in, 1)),
                             layers.Conv1D(64, 3, activation="relu"), layers.Conv1D(32, 3, activation="relu"),
                             layers.GlobalMaxPooling1D(), layers.Dense(64, activation="relu"),
                             layers.Dense(n_out, activation="softmax")])

def build_dnn(n_in, n_out):
    return keras.Sequential([layers.Input((n_in,)), layers.Dense(128, activation="relu"),
                             layers.Dense(64, activation="relu"), layers.Dense(n_out, activation="softmax")])

class FTTBlock(layers.Layer):
    def __init__(self, d, h, **kw):
        super().__init__(**kw)
        self.att = layers.MultiHeadAttention(h, d // h)
        self.n1, self.n2 = layers.LayerNormalization(), layers.LayerNormalization()
        self.ff = keras.Sequential([layers.Dense(2 * d, activation="gelu"), layers.Dense(d)])
    def call(self, x):
        x = self.n1(x + self.att(x, x))
        return self.n2(x + self.ff(x))

class CLSToken(layers.Layer):
    # jeton CLS appris ; une tf.Variable creee dans un modele fonctionnel ne se
    # serialise pas et casse au build, il faut donc passer par une couche
    def build(self, shape):
        self.tok = self.add_weight(shape=(1, 1, shape[-1]), name="cls",
                                   initializer="random_normal", trainable=True)
    def call(self, x):
        return tf.concat([tf.tile(self.tok, [tf.shape(x)[0], 1, 1]), x], axis=1)

def build_ftt(n_in, n_out, d=64, heads=8, blocks=3):
    inp = layers.Input((n_in,))
    t = layers.Dense(d)(layers.Reshape((n_in, 1))(inp))
    t = CLSToken()(t)
    for _ in range(blocks):
        t = FTTBlock(d, heads)(t)
    return keras.Model(inp, layers.Dense(n_out, activation="softmax")(t[:, 0]))

NEURAL = {"rnn": build_rnn, "cnn": build_cnn, "dnn": build_dnn, "ftt": build_ftt}

def make_sk(name, n_classes, seed):
    if name == "xgboost":
        return xgb.XGBClassifier(n_estimators=300, max_depth=8, tree_method="hist",
                                 random_state=seed, n_jobs=2, verbosity=0)
    if name == "lightgbm":
        return lgb.LGBMClassifier(n_estimators=300, num_leaves=63, random_state=seed,
                                  n_jobs=2, verbose=-1)
    if name == "rf":       return RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=2)
    if name == "logreg":   return LogisticRegression(max_iter=1000, n_jobs=2, random_state=seed)
    if name == "knn":      return KNeighborsClassifier(n_neighbors=5, n_jobs=2)
    if name == "nb":       return GaussianNB()
    if name == "majority": return DummyClassifier(strategy="most_frequent")
    raise ValueError(name)

MODELS = ["xgboost", "lightgbm", "rf", "ftt", "logreg", "rnn", "cnn", "dnn", "knn", "nb", "majority"]
print(len(MODELS), "detecteurs :", ", ".join(MODELS))
""")

# ---------------------------------------------------------------- 7. boucle
md("""
## 7. Campagne

`11 détecteurs × 3 conditions × 2 taxonomies`. Chaque run affiche ce qui est en cours et son
temps, et est écrit sur disque dès qu'il finit. Une déconnexion ne coûte que le run en cours.
""")

code(r"""
def prepare(cond_cols, label, seed):
    # Matrices mises a l'echelle ; le scaler est ajuste sur LEUR train uniquement
    Xtr = TRAIN[cond_cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy("float32")
    Xte = TEST[cond_cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy("float32")
    sc = RobustScaler().fit(Xtr)
    Xtr, Xte = sc.transform(Xtr).astype("float32"), sc.transform(Xte).astype("float32")
    le = LabelEncoder().fit(TRAIN[label].astype(str))
    ytr = le.transform(TRAIN[label].astype(str))
    yte = le.transform(TEST[label].astype(str))
    return Xtr, Xte, ytr, yte, le

def evaluate(yte, pred, le):
    return {"accuracy": float(accuracy_score(yte, pred)),
            "macro_f1": float(f1_score(yte, pred, average="macro", zero_division=0)),
            "mcc": float(matthews_corrcoef(yte, pred)),
            "per_class_f1": {c: float(v) for c, v in
                             zip(le.classes_, f1_score(yte, pred, average=None, zero_division=0))}}

def run_one(model, cond, label, seed):
    key = f"{model}|{cond}|{label}|seed{seed}"
    if key in STATE["runs"]:
        return
    cols_c = CONDITIONS[cond]
    t0 = time.time()
    print(f"  -> {key}  ({len(cols_c)} features)", flush=True)
    Xtr, Xte, ytr, yte, le = prepare(cols_c, label, seed)
    n_out = len(le.classes_)

    if model in NEURAL:
        tf.keras.utils.set_random_seed(seed)
        xtr, xte = (Xtr[..., None], Xte[..., None]) if model in ("rnn", "cnn") else (Xtr, Xte)
        net = NEURAL[model](Xtr.shape[1], n_out)
        net.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        net.fit(xtr, ytr, epochs=30, batch_size=512, verbose=0, validation_split=0.15,
                callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)])
        pred = net.predict(xte, batch_size=1024, verbose=0).argmax(1)
        del net; keras.backend.clear_session()
    else:
        if model == "knn" and len(Xtr) > KNN_MAX_TRAIN:
            idx = np.random.RandomState(seed).choice(len(Xtr), KNN_MAX_TRAIN, replace=False)
            fit_X, fit_y = Xtr[idx], ytr[idx]
        else:
            fit_X, fit_y = Xtr, ytr
        clf = make_sk(model, n_out, seed).fit(fit_X, fit_y)
        pred = clf.predict(Xte)
        del clf

    r = evaluate(yte, pred, le)
    r.update({"n_features": len(cols_c), "seconds": round(time.time() - t0, 1)})
    STATE["runs"][key] = r
    save_state(STATE)
    print(f"     macro-F1 {r['macro_f1']:.4f}  accuracy {r['accuracy']:.4f}  ({r['seconds']:.0f} s)",
          flush=True)
    del Xtr, Xte; gc.collect()

TASKS = [lab for lab in ("CategoryLabel", "SubCategoryLabel") if lab in LABELS]
total = len(MODELS) * len(CONDITIONS) * len(TASKS) * len(SEEDS)
done = 0
for label in TASKS:
    for cond in CONDITIONS:
        print(f"\n=== {label} | {cond} ===", flush=True)
        for model in MODELS:
            for seed in SEEDS:
                run_one(model, cond, label, seed)
                done += 1
        print(f"    avancement global : {len(STATE['runs'])}/{total}", flush=True)
print("\ncampagne terminee :", len(STATE["runs"]), "runs")
""")

# ---------------------------------------------------------------- 8. tableau
md("## 8. Tableau de synthèse")

code(r"""
import statistics as st

def agg(model, cond, label):
    v = [STATE["runs"][k]["macro_f1"] for k in STATE["runs"]
         if k.startswith(f"{model}|{cond}|{label}|")]
    return (st.mean(v), st.pstdev(v)) if v else (float("nan"), float("nan"))

for label in TASKS:
    n_cls = STATE["single_feature"].get(label, {}).get("n_classes", "?")
    print(f"\n{'='*74}\n{label} ({n_cls} classes) : macro-F1 moyen sur {len(SEEDS)} graines\n{'='*74}")
    print(f"{'modele':<12}{'as-distributed':>16}{'no-topology':>14}{'audited':>11}{'delta':>10}")
    for m in MODELS:
        a = agg(m, "as-distributed", label)[0]
        b = agg(m, "no-topology", label)[0]
        c = agg(m, "audited", label)[0]
        print(f"{m:<12}{a:>16.4f}{b:>14.4f}{c:>11.4f}{c-a:>+10.4f}")
""")

# ---------------------------------------------------------------- 9. figures
md("""
## 9. Figures pour le papier

Trois figures, construites **à leur taille finale dans la page** (6.698 pouces de large, la
largeur du bloc de texte du Word) avec des polices déclarées en points. C'est ce qui garantit
les 6 pt minimum exigés par l'éditeur : dessiner large puis réduire divise les tailles par le
facteur de réduction.

Textes en anglais, aucun tiret cadratin.
""")

code(r"""
W_IN, DPI = 6.698, 400
RED, ORANGE, BLUE, GREY = "#c23b34", "#e0913c", "#4a72b0", "#9aa4b1"
plt.rcParams.update({"font.size": 6, "axes.linewidth": .5,
                     "xtick.major.width": .4, "ytick.major.width": .4,
                     "xtick.major.size": 1.8, "ytick.major.size": 1.8})

def family(col):
    if col in ident:                       return "identifier / topology"
    if col in DUP_DROP or col in DUP_FAMILY: return "duplicated duration column"
    if col in ("SrcLoad", "SrcRate", "DstLoad", "Rate", "Load"): return "grey zone"
    return "retained behavioural"

COLOUR = {"identifier / topology": RED, "duplicated duration column": ORANGE,
          "grey zone": GREY, "retained behavioural": BLUE}
""")

code(r"""
# --- Figure E1.1 : pouvoir predictif de chaque colonne prise seule ----------
# 84 etiquettes sur une seule rangee tomberaient a 5 pt ; deux panneaux empiles
# doublent la largeur par etiquette et permettent 6 pt, le minimum editorial
LAB = "SubCategoryLabel" if "SubCategoryLabel" in STATE["single_feature"] else TASKS[0]
sf = STATE["single_feature"][LAB]
items = sorted(sf["features"].items(), key=lambda kv: -kv[1]["accuracy"])
half = (len(items) + 1) // 2
panels = [items[:half], items[half:]]

fig, axes = plt.subplots(2, 1, figsize=(W_IN, 4.6), dpi=DPI)
for ax, part in zip(axes, panels):
    names = [c for c, _ in part]
    vals = [v["accuracy"] for _, v in part]
    ax.bar(range(len(names)), vals, color=[COLOUR[family(c)] for c in names], edgecolor="none")
    ax.axhline(sf["majority_class_rate"], ls="--", lw=.8, color="black")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=90, fontsize=6)
    ax.set_xlim(-.8, len(names) - .2)
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.grid(axis="y", color="0.9", lw=.4)
    ax.set_axisbelow(True)
axes[0].text(len(panels[0]) - 1, sf["majority_class_rate"] + .02,
             f"majority-class rate ({sf['majority_class_rate']:.4f})",
             ha="right", va="bottom", fontsize=6)
axes[0].set_title(f"Single-feature predictive power in the 4-preprocessed module, "
                  f"{sf['n_classes']} classes, sorted", fontsize=7.5, pad=4)
fig.supylabel("single-feature accuracy on the module's own holdout", fontsize=7, x=.008)
from matplotlib.patches import Patch
axes[0].legend(handles=[Patch(facecolor=v, label=k) for k, v in COLOUR.items()],
               loc="upper right", fontsize=6, framealpha=.95, ncol=2)
fig.tight_layout(pad=.3, rect=[.035, 0, 1, 1])   # marge gauche pour le supylabel
fig.savefig(Path(OUT_DIR, "figures", "figE1_single_feature.png"), dpi=DPI, facecolor="white")
print("figE1_single_feature.png ecrite")
plt.close(fig)
""")

code(r"""
# --- Figure E1.2 : ce que chaque condition retire, par modele ---------------
fig, axes = plt.subplots(1, len(TASKS), figsize=(W_IN, 3.1), dpi=DPI, sharey=False)
axes = np.atleast_1d(axes)
order = [m for m in MODELS if m != "majority"]
x = np.arange(len(order)); w = .27
for ax, label in zip(axes, TASKS):
    for k, (cond, colr) in enumerate([("as-distributed", RED), ("no-topology", ORANGE), ("audited", BLUE)]):
        mu = [agg(m, cond, label)[0] for m in order]
        sd = [agg(m, cond, label)[1] for m in order]
        ax.bar(x + (k - 1) * w, mu, width=w, yerr=sd, color=colr, label=cond,
               error_kw={"lw": .5, "capsize": 1.2})
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=90, fontsize=6)
    n_cls = STATE["single_feature"].get(label, {}).get("n_classes", "")
    ax.set_title(f"{label} ({n_cls} classes)", fontsize=7)
    ax.grid(axis="y", color="0.9", lw=.4); ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=6.5)
axes[0].set_ylabel("macro-F1", fontsize=7)
axes[0].legend(fontsize=6, loc="lower left", framealpha=.95)
fig.suptitle("What the audited feature set costs on the corpus authors' own split",
             fontsize=7.5, y=.995)
fig.tight_layout(pad=.3)
fig.savefig(Path(OUT_DIR, "figures", "figE1_conditions.png"), dpi=DPI, facecolor="white")
print("figE1_conditions.png ecrite")
plt.close(fig)
""")

code(r"""
# --- Figure E1.3 : F1 par classe, condition auditee ------------------------
label = TASKS[-1]
rows = [m for m in MODELS if m not in ("majority", "nb")]
per = {}
for m in rows:
    ks = [k for k in STATE["runs"] if k.startswith(f"{m}|audited|{label}|")]
    if not ks: continue
    acc = {}
    for k in ks:
        for c, v in STATE["runs"][k]["per_class_f1"].items():
            acc.setdefault(c, []).append(v)
    per[m] = {c: st.mean(v) for c, v in acc.items()}
if not per:
    print("aucun run auditee disponible : figure par classe sautee")
    raise SystemExit
classes = sorted(next(iter(per.values())).keys())
M = np.array([[per[m][c] for c in classes] for m in per])

fig, ax = plt.subplots(figsize=(W_IN, 0.30 * len(per) + 2.0), dpi=DPI)
im = ax.imshow(M, cmap="RdYlGn", vmin=max(0, M.min() - .01), vmax=1.0, aspect="auto")
ax.set_xticks(range(len(classes))); ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=6)
ax.set_yticks(range(len(per))); ax.set_yticklabels(list(per), fontsize=6.5)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i, j]:.3f}".lstrip("0"), ha="center", va="center", fontsize=4.8,
                color="black" if M[i, j] > (M.min() + M.max()) / 2 else "white")
ax.set_title(f"Per-class F1 under the audited condition, {label}", fontsize=7.5, pad=4)
fig.colorbar(im, ax=ax, fraction=.02, pad=.01).ax.tick_params(labelsize=6)
fig.tight_layout(pad=.3)
fig.savefig(Path(OUT_DIR, "figures", "figE1_perclass.png"), dpi=DPI, facecolor="white")
print("figE1_perclass.png ecrite")
plt.close(fig)
""")

# ---------------------------------------------------------------- 10. export
md("## 10. Export")

code(r"""
import shutil
save_state(STATE)
zip_path = shutil.make_archive(str(Path(OUT_DIR, "e1_figures")), "zip",
                               str(Path(OUT_DIR, "figures")))
print("resultats :", STATE_PATH)
print("figures   :", zip_path)
print("\nA me renvoyer : e1_results.json et e1_figures.zip")
for f in sorted(Path(OUT_DIR, "figures").glob("*.png")):
    print("   ", f.name, f"{f.stat().st_size/1e3:.0f} ko")
""")

md("""
---

### Lecture attendue

- `as-distributed` devrait être très haut partout : c'est le module tel qu'il est livré, avec
  `Sdaddr` qui résout presque la tâche à lui seul.
- `no-topology` mesure ce que valait cette fuite.
- `audited` est le chiffre honnête, comparable à ceux de l'article.

L'écart entre la première et la troisième colonne est le résultat de E1. S'il est faible, c'est
que les features légitimes suffisent et la baseline tient ; s'il est large, c'est que les
nombres publiés sur ce module reposent en partie sur des colonnes que leurs propres auteurs
recommandent d'exclure.
""")

nb = {"cells": CELLS,
      "metadata": {"colab": {"provenance": [], "toc_visible": True},
                   "kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

out = Path(__file__).resolve().parent / "e1_anchored_comparison.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{out.name} : {len(CELLS)} cellules "
      f"({sum(c['cell_type']=='code' for c in CELLS)} de code)")
