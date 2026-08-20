#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e8_republication.ipynb.

E7 a demontre qu'IdleTime est un identifiant de fichier de capture et mesure
ce que son retrait coute : 0.0038 en stratifie, 0.0320 en temporel. Le second
chiffre depasse ce que le papier traite comme du bruit -- il declare le groupe
de tete indiscernable sur des ecarts de 0.0022 a 0.0069. La condition auditee
doit donc etre REPUBLIEE, pas commentee.

DEUX MANQUES D'E7 QUE CE NOTEBOOK COMBLE, ET QU'IL FAUT DIRE :

  1. E7 n'a pas fait tourner le FT-Transformer. C'est le detecteur qui MENE
     sous protocole temporel dans le papier publie (0.9966, 1er et 2e places).
     Sa conclusion << aucune conclusion principale ne tombe >> a donc ete
     etablie sans le detecteur de tete. Ici, ftt est present.
  2. E7 n'a pas fait tourner le bras regle (#tuned), soit dix configurations
     de plus, ni les graines 2 a 5 en stratifie.

Ce notebook produit tout ce qu'il faut pour republier la condition auditee :
21 configurations x (5 graines stratifiees + 1 temporel), les matrices de
probabilites pour McNemar et le bootstrap, le F1 par classe, la calibration
avant et apres temperature, et le cout d'inference.

IL TRANCHE AUSSI LE CAS D'OFFSET, PAR MESURE ET NON PAR PRUDENCE. Sa regle est
enoncee AVANT de voir le resultat, ce qui est la seule facon de ne pas choisir
la lecture qui arrange.

PREREQUIS : E7 doit avoir tourne (e7_results.json) et le corpus brut pour
l'etape A. Compter 8 a 12 h avec GPU. Le notebook est reprenable.
"""
import json
from pathlib import Path

VERSION = "v1"
BUILD = "2026-08-20"
HERE = Path(__file__).resolve().parent

CELLS = []
md = lambda s: CELLS.append({"cell_type": "markdown", "metadata": {},
                             "source": s.strip("\n").split("\n")})
code = lambda s: CELLS.append({"cell_type": "code", "execution_count": None,
                               "metadata": {}, "outputs": [],
                               "source": s.strip("\n").split("\n")})

md(f"""
# E8 — republier la condition auditée sur la liste corrigée

> **Notebook {VERSION}, compilé le {BUILD}.** La cellule 1 réaffiche ce numéro.

**Pourquoi republier et non commenter.** E7 a mesuré que retirer `IdleTime` coûte
**0,0320** de macro-F1 temporel à LightGBM. Le papier déclare son groupe de tête
statistiquement indiscernable sur des écarts de 0,0022 à 0,0069 : un déplacement de 0,032
ne peut pas être rangé dans le bruit. La condition auditée doit porter les nouveaux
chiffres.

**Deux manques d'E7 que ce notebook comble, et qu'il faut dire.**

1. **E7 n'a pas fait tourner le FT-Transformer**, qui est le détecteur **de tête** sous
   protocole temporel dans le papier publié (0,9966, 1ᵉ et 2ᵉ places). Sa conclusion
   « aucune conclusion principale ne tombe » a donc été établie sans le détecteur qui
   mène. Ici, `ftt` est présent.
2. E7 n'a pas fait tourner le **bras réglé** (`#tuned`, dix configurations de plus), ni
   les **graines 2 à 5** en stratifié.

**Ce que le notebook produit.**

| étape | contenu | durée |
|---|---|---|
| **A** | le cas d'`Offset`, tranché par une règle énoncée d'avance | ~10 min |
| **B** | témoin : la liste publiée rejoue le Tableau 2 | ~20 min |
| **C** | 21 configurations × temporel — le classement, d'abord | ~1 h |
| **D** | 21 configurations × 5 graines stratifiées | ~5 à 8 h |
| **E** | calibration, température, coût d'inférence, F1 par classe | ~1 h |

Les matrices de probabilités sont sauvegardées : McNemar et le bootstrap apparié se
recalculent ensuite sans réentraîner.

**À me renvoyer :** `e8_results.json` et le dossier `e8_probs/`.
""")

code(r'''
# --- 1. Drive, dossier, verrou E7 ----------------------------------------
E8_VERSION = "VERSION_PLACEHOLDER"; E8_BUILD = "BUILD_PLACEHOLDER"
print(f"E8 notebook {E8_VERSION}, compile le {E8_BUILD}\n")
import pathlib, json, sys, os, glob, shutil, time, gc
from google.colab import drive
drive.mount("/content/drive")

MYDRIVE = pathlib.Path("/content/drive/MyDrive")
MARQUEUR = "article1_results.json"
trouves = [c for c in (MYDRIVE / "GeNIS" / "article1_final", MYDRIVE / "article1_final",
                       MYDRIVE / "GeNIS") if (c / MARQUEUR).exists()]
if not trouves:
    for prof in ("*/", "*/*/", "*/*/*/"):
        trouves = [p.parent for p in MYDRIVE.glob(prof + MARQUEUR)]
        if trouves:
            break
if not trouves:
    sys.exit(f"{MARQUEUR} introuvable sous {MYDRIVE}.")
SAVE = trouves[0]
print(f"dossier de travail : {SAVE}")

# Verrou : E7 doit avoir etabli la preuve, sinon ce notebook n'a pas de base.
E7P = SAVE / "e7_results.json"
if not E7P.exists():
    sys.exit("e7_results.json introuvable : lance e7_idletime.ipynb d'abord.")
E7 = json.loads(E7P.read_text(encoding="utf-8"))
P7 = E7["preuve_cardinalite"]
cmax = max(d["n_unique"] for d in P7.values())
if cmax > 2:
    sys.exit(f"E7 rapporte {cmax} valeurs distinctes par fichier : la these "
             "de l'identifiant de fichier ne tient pas, ne republie rien.")
if E7["auc_binaire"]["IdleTime"]["auc_binaire"] < 0.999:
    sys.exit("E7 ne rapporte pas une AUC binaire de 1.0 pour IdleTime.")
if not E7.get("temoin", {}).get("valide"):
    sys.exit("le temoin d'E7 n'est pas valide : ses chiffres ne sont pas comparables.")
print(f"verrou leve : {cmax} valeurs max par fichier, AUC binaire "
      f"{E7['auc_binaire']['IdleTime']['auc_binaire']:.4f}, temoin valide\n")

R = json.loads((SAVE / MARQUEUR).read_text(encoding="utf-8"))
BL_PUB = R["audit"]["blacklist"]
print(f"liste noire publiee : {len(BL_PUB)} colonnes")
''')

md("""
## Étape A — le cas d'`Offset`, tranché par une règle énoncée d'avance

`Offset` pose une question que je ne veux pas trancher par prudence. Les faits mesurés
par E7 :

- **AUC binaire 0,9379** — il sépare presque parfaitement bénin et attaque ;
- **exactitude 9 classes 0,0601** — c'est *sous* le taux de la classe majoritaire (0,1942),
  donc il ne distingue rien du tout entre classes ;
- **transférabilité 3,0** — l'exactitude *monte* sous le protocole temporel, ce qui est
  anormal ;
- il **varie à l'intérieur** de chaque fichier : ce n'est donc **pas** un identifiant de
  fichier, contrairement à `IdleTime`.

L'exclure « parce qu'il est suspect » serait exactement le défaut que ce papier reproche
aux autres : écarter par intuition plutôt que par mesure. Et sous la règle publiée il
n'est même pas *éligible* — son pouvoir prédictif isolé est très en dessous du filtre de
prédictivité (3 × 0,1942 = 0,5827).

> ### La règle, énoncée avant de voir le résultat
>
> Dans Argus, `Offset` est le décalage de l'enregistrement dans le fichier de capture.
> Si c'est bien ce qu'il est, il est **monotone avec l'ordre de capture** à l'intérieur
> de chaque fichier, exactement comme `Rank` et `Seq` — qui sont, eux, déjà sur la liste
> positionnelle du §4.3.
>
> **Si la corrélation de rang entre `Offset` et l'ordre de capture dépasse 0,95 dans
> chaque fichier, `Offset` rejoint la liste positionnelle** — non pas comme une nouvelle
> exclusion discrétionnaire, mais parce que la liste de noms du §4.3 l'avait **omis**.
> La liste passe alors à quatorze.
>
> **Sinon il reste**, et le §9 rapporte son AUC binaire comme une anomalie non résolue.

C'est une omission de liste de noms, pas une défaillance de la règle — et c'est une
distinction que le papier doit faire, parce que les deux appellent des remèdes différents.
""")

code(r'''
# --- 2. Etape A : Offset est-il positionnel ? ----------------------------
import numpy as np, pandas as pd
from scipy.stats import spearmanr

WORK = pathlib.Path("/content/genis"); WORK.mkdir(parents=True, exist_ok=True)
os.chdir(WORK)
drive_zip = MYDRIVE / "GeNIS" / "2-flows.zip"
if not pathlib.Path("flows").exists():
    if drive_zip.exists():
        shutil.copy(drive_zip, "2-flows.zip")
    else:
        os.system('wget -q "https://zenodo.org/records/14919237/files/'
                  '2-flows.zip?download=1" -O 2-flows.zip')
    os.system("unzip -o -q 2-flows.zip -d flows")
CSV60 = sorted(c for c in glob.glob("flows/**/*.csv", recursive=True)
               if "flows-60-sec" in c)
print(f"{len(CSV60)} fichiers 60 s\n")

SEUIL_POS = 0.95
rhos, cards = {}, {}
print(f"{'fichier':<32}{'rho(Offset, StartTime)':>24}{'valeurs':>10}")
for c in sorted(CSV60):
    d = pd.read_csv(c, usecols=["Offset", "StartTime"], low_memory=False).dropna()
    if len(d) < 10:
        continue
    rho = float(spearmanr(d["Offset"], d["StartTime"]).statistic)
    nom = pathlib.Path(c).stem
    rhos[nom] = rho; cards[nom] = int(d["Offset"].nunique())
    print(f"{nom:<32}{rho:>24.4f}{cards[nom]:>10}")

rmin = min(abs(r) for r in rhos.values())
OFFSET_POSITIONNEL = rmin > SEUIL_POS
print(f"\ncorrelation de rang minimale sur les {len(rhos)} fichiers : {rmin:.4f}")
print(f"seuil enonce d'avance : {SEUIL_POS}")
_v = "EST" if OFFSET_POSITIONNEL else "N'EST PAS"
print(f"\nVERDICT : Offset {_v} positionnel")
if OFFSET_POSITIONNEL:
    print("  -> il rejoint la liste positionnelle du 4.3, omise par la liste de noms.")
    print("  -> la liste noire passe a QUATORZE.")
else:
    print("  -> il reste dans la condition auditee ; la 9 rapporte son AUC binaire")
    print("     de 0.9379 comme une anomalie non resolue.")

SUP = ["IdleTime"] + (["Offset"] if OFFSET_POSITIONNEL else [])
BLACKLIST = sorted(set(BL_PUB) | set(SUP))
print(f"\nliste noire corrigee : {len(BLACKLIST)} colonnes")
print(f"  ajoutees : {SUP}")
del d; gc.collect()
''')

code(r'''
# --- 3. Donnees, decoupages, etat ---------------------------------------
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import f1_score, matthews_corrcoef

M = json.loads((SAVE / "cache" / "slice60_meta.json").read_text(encoding="utf-8"))
z = np.load(SAVE / "cache" / "slice60.npz")
X, y = z["X"], z["y"].astype(int)
FEATS = M["feat_all"]
F_CLEAN = R["slice60"]["features_clean"]
CLASS_NAMES = R["slice60"]["classes"]; C = len(CLASS_NAMES)
BENIGN = CLASS_NAMES.index("benign")

zs = np.load(SAVE / "frozen_splits_60s.npz")
PROTOS = ["temporal"] + [f"strat_seed{s}" for s in range(1, 6)]
SPLITS = {}
for k in PROTOS:
    try:
        SPLITS[k] = (zs[f"{k}_train"], zs[f"{k}_val"], zs[f"{k}_test"])
    except KeyError:
        print(f"  attention : decoupage {k} absent de frozen_splits_60s.npz")
PROTOS = [k for k in PROTOS if k in SPLITS]
print(f"protocoles disponibles : {PROTOS}")

COLS = {"publiee": [c for c in F_CLEAN if c not in BL_PUB],
        "corrigee": [c for c in F_CLEAN if c not in BLACKLIST]}
for k, v in COLS.items():
    print(f"  {k:9s} {len(v)} features")

PROBS = SAVE / "e8_probs"; PROBS.mkdir(exist_ok=True)
STATE_PATH = SAVE / "e8_results.json"
def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {"version": E8_VERSION, "build": E8_BUILD}, "runs": {}}
def save_state(s):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    tmp.replace(STATE_PATH)
STATE = load_state()
STATE["offset"] = {"rho_par_fichier": rhos, "rho_min": rmin,
                   "seuil": SEUIL_POS, "positionnel": bool(OFFSET_POSITIONNEL)}
STATE["blacklist_publiee"] = BL_PUB
STATE["blacklist_corrigee"] = BLACKLIST
STATE["colonnes_ajoutees"] = SUP
save_state(STATE)
print(f"\netat : {len(STATE['runs'])} runs deja faits")

def kfile(cle):
    return PROBS / (cle.replace("|", "_").replace("#", "-") + ".npz")
''')

code(r'''
# --- 4. Detecteurs : recopie mot pour mot du pipeline principal ---------
# Toute divergence ici casserait la comparaison avec les chiffres publies.
# Les architectures, les defauts et le FT-Transformer viennent des cellules
# 6.1 et 6.2 de article1_pipeline ; les hyperparametres regles viennent de
# R["hpo"][modele]["best_params"], donc du meme fichier que le papier.
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from lightgbm import LGBMClassifier
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks

DEFAULTS_SK = {"majority": {}, "logreg": {"max_iter": 1000}, "nb": {},
               "knn": {"n_neighbors": 5},
               "rf": {"n_estimators": 200},
               "xgboost": {"n_estimators": 300, "max_depth": 8, "learning_rate": .1},
               "lightgbm": {"n_estimators": 300, "num_leaves": 63, "learning_rate": .1}}

def make_sk(name, seed=0, extra=None):
    p = dict(DEFAULTS_SK[name]); p.update(extra or {})
    if name == "majority": return DummyClassifier(strategy="most_frequent")
    if name == "logreg":   return LogisticRegression(n_jobs=-1, **p)
    if name == "nb":       return GaussianNB(**p)
    if name == "knn":      return KNeighborsClassifier(n_jobs=2, **p)
    if name == "rf":       return RandomForestClassifier(n_jobs=2, random_state=seed, **p)
    if name == "xgboost":  return xgb.XGBClassifier(tree_method="hist", n_jobs=2,
                                                    random_state=seed,
                                                    eval_metric="mlogloss", **p)
    if name == "lightgbm": return LGBMClassifier(n_jobs=2, random_state=seed,
                                                 verbose=-1, **p)
    raise KeyError(name)

DEFAULTS_DEEP = {
    "dnn": {"h1": 128, "h2": 64, "d1": .3, "d2": .2, "lr": 1e-3, "bs": 256},
    "cnn": {"f1": 64, "f2": 32, "dense": 64, "drop": .3, "lr": 1e-3, "bs": 256},
    "rnn": {"units": 64, "dense": 64, "drop": .3, "lr": 1e-3, "bs": 256},
    "ftt": {"d": 64, "heads": 8, "blocks": 3, "ff": 128, "drop": .1, "lr": 5e-4, "bs": 256}}

def build_dnn(F, C, q):
    return keras.Sequential([layers.Input((F,)),
        layers.Dense(q["h1"], activation="relu"), layers.Dropout(q["d1"]),
        layers.Dense(q["h2"], activation="relu"), layers.Dropout(q["d2"]),
        layers.Dense(C, activation="softmax")], name="dnn")

def build_cnn(F, C, q):
    return keras.Sequential([layers.Input((F, 1)),
        layers.Conv1D(q["f1"], 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Conv1D(q["f2"], 3, activation="relu", padding="same"), layers.Flatten(),
        layers.Dense(q["dense"], activation="relu"), layers.Dropout(q["drop"]),
        layers.Dense(C, activation="softmax")], name="cnn")

def build_rnn(F, C, q):
    return keras.Sequential([layers.Input((F, 1)),
        layers.SimpleRNN(q["units"], activation="relu"), layers.Dropout(q["drop"]),
        layers.Dense(q["dense"], activation="relu"),
        layers.Dense(C, activation="softmax")], name="rnn")

class FeatureTokenizer(layers.Layer):
    def __init__(self, d, **kw): super().__init__(**kw); self.d = d
    def build(self, shape):
        F = int(shape[-1])
        self.w = self.add_weight(shape=(F, self.d), initializer="glorot_uniform", name="w")
        self.b = self.add_weight(shape=(F, self.d), initializer="zeros", name="b")
    def call(self, x): return x[:, :, None] * self.w + self.b
    def get_config(self): return {**super().get_config(), "d": self.d}

class ClsToken(layers.Layer):
    def __init__(self, d, **kw): super().__init__(**kw); self.d = d
    def build(self, shape):
        self.cls = self.add_weight(shape=(1, 1, self.d), initializer="glorot_uniform",
                                   name="cls")
    def call(self, x): return tf.concat([tf.tile(self.cls, [tf.shape(x)[0], 1, 1]), x],
                                        axis=1)
    def get_config(self): return {**super().get_config(), "d": self.d}

def build_ftt(F, C, q):
    d, heads, blocks, ff, drop = q["d"], q["heads"], q["blocks"], q["ff"], q["drop"]
    inp = layers.Input((F,)); x = ClsToken(d)(FeatureTokenizer(d)(inp))
    for _ in range(blocks):
        h = layers.LayerNormalization()(x)
        h = layers.MultiHeadAttention(num_heads=heads, key_dim=max(1, d // heads),
                                      dropout=drop)(h, h)
        x = layers.Add()([x, h])
        h = layers.LayerNormalization()(x)
        h = layers.Dense(ff, activation="gelu")(h); h = layers.Dropout(drop)(h)
        x = layers.Add()([x, layers.Dense(d)(h)])
    return keras.Model(inp, layers.Dense(C, activation="softmax")(
        layers.LayerNormalization()(x[:, 0])), name="ftt")

NEURAL = {"rnn": build_rnn, "cnn": build_cnn, "dnn": build_dnn, "ftt": build_ftt}
def shape_for(name, A): return A if name in ("dnn", "ftt") else A.reshape(-1, A.shape[1], 1)

SK = ["majority", "logreg", "nb", "knn", "rf", "xgboost", "lightgbm"]
DEEP = ["dnn", "cnn", "rnn", "ftt"]
BASE = SK + DEEP
HPO = R.get("hpo", {})
TUNED = [f"{m}#tuned" for m in BASE
         if m != "majority" and HPO.get(m, {}).get("best_params")]
CONFIGS = BASE + TUNED
print(f"{len(CONFIGS)} configurations : {len(BASE)} de base + {len(TUNED)} reglees")
print(f"  ftt present : {'ftt' in BASE}  <- absent d'E7, c'est le detecteur de tete")
print(f"  reglees : {TUNED}")
''')

code(r'''
# --- 5. Ajustement, evaluation, calibration -----------------------------
KNN_MAX_TRAIN = 50_000

def ece(probs, yt, bins=15):
    conf = probs.max(1); pred = probs.argmax(1); ok = (pred == yt).astype(float)
    edges = np.linspace(0, 1, bins + 1); e = 0.0
    for i in range(bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.any():
            e += m.mean() * abs(ok[m].mean() - conf[m].mean())
    return float(e)

def brier(probs, yt):
    oh = np.zeros_like(probs); oh[np.arange(len(yt)), yt] = 1.0
    return float(((probs - oh) ** 2).sum(1).mean())

def temperature(pv, yv, grille=np.concatenate([np.arange(.05, 5.01, .05)])):
    """Meme grille bornee que le pipeline : 0.05 en bas, 5 en haut."""
    lp = np.log(np.clip(pv, 1e-12, 1))
    best, bt = None, 1.0
    for t in grille:
        q = np.exp(lp / t); q /= q.sum(1, keepdims=True)
        e = ece(q, yv)
        if best is None or e < best:
            best, bt = e, float(t)
    return bt, best

def applique_t(pr, t):
    lp = np.log(np.clip(pr, 1e-12, 1)); q = np.exp(lp / t)
    return q / q.sum(1, keepdims=True)

def evalue(yt, pr):
    p = pr.argmax(1); att, patt = yt != BENIGN, p != BENIGN
    f1c = f1_score(yt, p, average=None, labels=list(range(C)), zero_division=0)
    return {"macro_f1": float(f1_score(yt, p, average="macro", zero_division=0)),
            "accuracy": float((p == yt).mean()),
            "mcc": float(matthews_corrcoef(yt, p)),
            "fpr": float(patt[~att].mean()) if (~att).any() else None,
            "ece": ece(pr, yt), "brier": brier(pr, yt),
            "per_class_f1": {CLASS_NAMES[i]: float(v) for i, v in enumerate(f1c)}}

def fit_predict(config, Xtr, ytr, Xva, yva, Xte, seed):
    """Rend (probs_val, probs_test). La validation sert a la temperature."""
    nom = config.split("#")[0]
    extra = HPO.get(nom, {}).get("best_params", {}) if "#tuned" in config else {}
    if nom in SK:
        if nom == "knn" and len(ytr) > KNN_MAX_TRAIN:
            rng = np.random.RandomState(0)
            keep = rng.choice(len(ytr), KNN_MAX_TRAIN, replace=False)
            Xtr, ytr = Xtr[keep], ytr[keep]
        clf = make_sk(nom, seed=seed, extra=extra).fit(Xtr, ytr)
        def full(A):
            pr = clf.predict_proba(A)
            if pr.shape[1] == C:
                return pr
            out = np.zeros((len(A), C))
            for j, c_ in enumerate(clf.classes_):
                out[:, int(c_)] = pr[:, j]
            return out
        pv, pt = full(Xva), full(Xte)
        del clf; gc.collect(); return pv, pt
    q = dict(DEFAULTS_DEEP[nom]); q.update(extra)
    tf.keras.utils.set_random_seed(seed)
    net = NEURAL[nom](Xtr.shape[1], C, q)
    net.compile(optimizer=keras.optimizers.Adam(q.get("lr", 1e-3)),
                loss="sparse_categorical_crossentropy")
    cls = np.unique(ytr); w = compute_class_weight("balanced", classes=cls, y=ytr)
    net.fit(shape_for(nom, Xtr), ytr,
            validation_data=(shape_for(nom, Xva), yva),
            epochs=30, batch_size=q.get("bs", 256), verbose=0,
            class_weight={int(c_): float(v) for c_, v in zip(cls, w)},
            callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=5,
                                               restore_best_weights=True)])
    pv = net.predict(shape_for(nom, Xva), batch_size=2048, verbose=0)
    pt = net.predict(shape_for(nom, Xte), batch_size=2048, verbose=0)
    del net; keras.backend.clear_session(); gc.collect(); return pv, pt
print("detecteurs et metriques definis")
''')

code(r'''
# --- 6. La campagne ------------------------------------------------------
# L'ordre compte : le temporel d'abord, parce que c'est lui qui porte le
# classement et donc la conclusion. Si la session tombe apres l'etape C, on
# a deja de quoi savoir ce que le papier doit dire.
def campagne(variantes, protocoles, configs):
    for proto in protocoles:
        tr_, va_, te_ = SPLITS[proto]
        seed = 1 if proto == "temporal" else int(proto.replace("strat_seed", ""))
        for var in variantes:
            ci = [FEATS.index(c) for c in COLS[var]]
            Xtr = Xva = Xte = None
            for cfg in configs:
                cle = f"{cfg}|{var}|{proto}"
                if cle in STATE["runs"]:
                    continue
                if Xtr is None:
                    sc = RobustScaler().fit(X[tr_][:, ci])
                    g = lambda ix: np.nan_to_num(sc.transform(X[ix][:, ci]), nan=0.,
                                                 posinf=0., neginf=0.).astype("float32")
                    Xtr, Xva, Xte = g(tr_), g(va_), g(te_)
                t1 = time.time()
                pv, pt = fit_predict(cfg, Xtr, y[tr_], Xva, y[va_], Xte, seed)
                r = evalue(y[te_], pt)
                t_opt, e_cal = temperature(pv, y[va_])
                r["temperature"] = t_opt
                r["ece_calibree"] = ece(applique_t(pt, t_opt), y[te_])
                r["seconds"] = round(time.time() - t1, 1)
                r["n_features"] = len(COLS[var])
                np.savez_compressed(kfile(cle), probs_val=pv.astype("float32"),
                                    probs_test=pt.astype("float32"))
                STATE["runs"][cle] = r; save_state(STATE)
                print(f"   [{proto:12s}|{var:8s}] {cfg:16s} mF1 {r['macro_f1']:.4f}  "
                      f"ECE {r['ece']:.5f}->{r['ece_calibree']:.5f}  "
                      f"{r['seconds']:.0f}s", flush=True)

print("=" * 72)
print("ETAPE B — temoin : la liste publiee doit rejouer le tableau 2")
print("=" * 72, flush=True)
campagne(["publiee"], ["temporal", "strat_seed1"], CONFIGS)
''')

code(r'''
# --- 7. Le temoin, avant d'aller plus loin ------------------------------
MOD = R["models"]
ec = {}
for cfg in CONFIGS:
    for proto, suf in (("strat_seed1", "strat_seed1"), ("temporal", "temporal")):
        kp, kn = f"{cfg}|audited|{suf}", f"{cfg}|publiee|{proto}"
        if kp in MOD and kn in STATE["runs"]:
            ec[f"{cfg}|{proto}"] = abs(MOD[kp]["macro_f1"]
                                       - STATE["runs"][kn]["macro_f1"])
if ec:
    pire = max(ec, key=ec.get); emax = ec[pire]
    print(f"{len(ec)} comparaisons, ecart maximal {emax:.4f} sur {pire}")
    for k in sorted(ec, key=ec.get, reverse=True)[:6]:
        print(f"   {k:34s} {ec[k]:.4f}")
    STATE["temoin"] = {"ecart_max": emax, "pire": pire, "valide": bool(emax < 0.01)}
    save_state(STATE)
    if emax >= 0.01:
        print("\nARRET. Le temoin ne rejoue pas le tableau 2 : ce qui suit ne")
        print("mesurerait pas la correction mais l'environnement.")
        sys.exit("temoin invalide")
    print("\nTEMOIN VALIDE — la comparaison porte bien sur la correction.")
else:
    print("aucune comparaison possible : verifie les cles de R['models'].")
''')

code(r'''
# --- 8. ETAPE C et D : la condition corrigee ----------------------------
print("=" * 72)
print("ETAPE C — le classement temporel, d'abord")
print("=" * 72, flush=True)
campagne(["corrigee"], ["temporal"], CONFIGS)

FORTS = [c for c in CONFIGS if c.split("#")[0] not in ("majority", "nb")]
def classement(var):
    return sorted(((c, STATE["runs"][f"{c}|{var}|temporal"]["macro_f1"])
                   for c in FORTS if f"{c}|{var}|temporal" in STATE["runs"]),
                  key=lambda kv: -kv[1])
print("\n\nCLASSEMENT TEMPOREL\n")
print(f"{'rang':>5}  {'liste publiee':<24}{'liste corrigee':<24}")
cp, cc = classement("publiee"), classement("corrigee")
for i in range(max(len(cp), len(cc))):
    a = f"{cp[i][0]} {cp[i][1]:.4f}" if i < len(cp) else ""
    b = f"{cc[i][0]} {cc[i][1]:.4f}" if i < len(cc) else ""
    print(f"{i+1:>5}  {a:<24}{b:<24}")
''')

code(r'''
# --- 9. ETAPE D : les cinq graines stratifiees --------------------------
print("=" * 72)
print("ETAPE D — cinq graines stratifiees, les deux listes")
print("=" * 72, flush=True)
campagne(["publiee", "corrigee"],
         [p for p in PROTOS if p.startswith("strat_seed")], CONFIGS)

print("\n\nTABLEAU 2, VERSION CORRIGEE\n")
print(f"{'configuration':<17}{'strat. moy.':>13}{'ecart-type':>12}{'temporel':>11}")
TABLE = {}
for cfg in CONFIGS:
    v = [STATE["runs"][f"{cfg}|corrigee|strat_seed{s}"]["macro_f1"]
         for s in range(1, 6) if f"{cfg}|corrigee|strat_seed{s}" in STATE["runs"]]
    kt = f"{cfg}|corrigee|temporal"
    if not v or kt not in STATE["runs"]:
        continue
    t = STATE["runs"][kt]["macro_f1"]
    TABLE[cfg] = {"strat_mean": float(np.mean(v)), "strat_std": float(np.std(v)),
                  "strat_runs": v, "temporal": t}
    print(f"{cfg:<17}{np.mean(v):>13.4f}{np.std(v):>12.4f}{t:>11.4f}")
STATE["table2_corrigee"] = TABLE
save_state(STATE)
''')

code(r'''
# --- 10. Le cout d'inference, sur la condition corrigee -----------------
# Le nombre de features change, donc le cout aussi : le tableau 10 doit etre
# recalcule et non recopie.
import platform
tr_, va_, te_ = SPLITS["strat_seed1"]
ci = [FEATS.index(c) for c in COLS["corrigee"]]
sc = RobustScaler().fit(X[tr_][:, ci])
g = lambda ix: np.nan_to_num(sc.transform(X[ix][:, ci]), nan=0., posinf=0.,
                             neginf=0.).astype("float32")
Xtr, Xva, Xte = g(tr_), g(va_), g(te_)
COUT = {}
print(f"{'configuration':<17}{'p50 (ms)':>10}{'p99 (ms)':>10}{'flux/s':>12}")
for cfg in BASE:
    if cfg == "majority":
        continue
    nom = cfg.split("#")[0]
    try:
        if nom in SK:
            clf = make_sk(nom, seed=1).fit(Xtr, y[tr_])
            f1_ = lambda A: clf.predict_proba(A)
        else:
            q = DEFAULTS_DEEP[nom]
            tf.keras.utils.set_random_seed(1)
            net = NEURAL[nom](Xtr.shape[1], C, q)
            net.compile(optimizer=keras.optimizers.Adam(q["lr"]),
                        loss="sparse_categorical_crossentropy")
            net.fit(shape_for(nom, Xtr), y[tr_], epochs=2, batch_size=q["bs"], verbose=0)
            f1_ = lambda A: net.predict(shape_for(nom, A), batch_size=512, verbose=0)
        lat = []
        for i in range(200):
            a = Xte[i:i + 1]
            t0 = time.perf_counter(); f1_(a); lat.append((time.perf_counter() - t0) * 1e3)
        lot = Xte[:512 * 20]
        t0 = time.perf_counter(); f1_(lot); dt_ = time.perf_counter() - t0
        COUT[cfg] = {"p50_ms": float(np.percentile(lat, 50)),
                     "p99_ms": float(np.percentile(lat, 99)),
                     "flows_per_s": float(len(lot) / dt_),
                     "n_features": len(COLS["corrigee"])}
        print(f"{cfg:<17}{COUT[cfg]['p50_ms']:>10.2f}{COUT[cfg]['p99_ms']:>10.2f}"
              f"{COUT[cfg]['flows_per_s']:>12.0f}")
    except Exception as e:
        print(f"{cfg:<17} echec : {e}")
    finally:
        keras.backend.clear_session(); gc.collect()
STATE["cout_corrige"] = COUT
STATE["plateforme"] = platform.platform()
save_state(STATE)
print(f"\nmesure sur {platform.platform()}")
print("A rapporter tel quel : le papier declare deja que le cout depend du materiel.")
''')

code(r'''
# --- 11. Le verdict ------------------------------------------------------
print("=" * 72); print("CE QUE LA CORRECTION CHANGE"); print("=" * 72)
print(f"\nliste noire : {len(BL_PUB)} -> {len(BLACKLIST)}  (ajoutees : {SUP})\n")

d_s, d_t = {}, {}
print(f"{'configuration':<17}{'strat. pub.':>12}{'strat. corr.':>13}{'delta':>8}"
      f"{'temp. pub.':>12}{'temp. corr.':>13}{'delta':>8}")
for cfg in CONFIGS:
    ks = [f"{cfg}|{v}|strat_seed1" for v in ("publiee", "corrigee")]
    kt = [f"{cfg}|{v}|temporal" for v in ("publiee", "corrigee")]
    if not all(k in STATE["runs"] for k in ks + kt):
        continue
    a, b = (STATE["runs"][k]["macro_f1"] for k in ks)
    c_, d_ = (STATE["runs"][k]["macro_f1"] for k in kt)
    d_s[cfg], d_t[cfg] = b - a, d_ - c_
    print(f"{cfg:<17}{a:>12.4f}{b:>13.4f}{b-a:>+8.4f}"
          f"{c_:>12.4f}{d_:>13.4f}{d_-c_:>+8.4f}")

F2 = [c for c in d_t if c.split("#")[0] not in ("majority", "nb")]
if F2:
    ms, mt = (max(abs(d_s[c]) for c in F2), max(abs(d_t[c]) for c in F2))
    print(f"\necart maximal hors bayesien naif : stratifie {ms:.4f}, temporel {mt:.4f}")
    STATE["ecart_max"] = {"stratifie": ms, "temporel": mt}

# La question qu'E7 ne pouvait pas poser, faute de FT-Transformer.
ftts = [c for c in cc if c.split("#")[0] == "ftt"]
if ftts:
    print(f"\nLE DETECTEUR DE TETE, QUE E7 N'AVAIT PAS FAIT TOURNER :")
    for c, v in cc[:3]:
        print(f"   {c:16s} {v:.4f}")
    rang_ftt = min(i for i, (c, _) in enumerate(cc, 1) if c.split("#")[0] == "ftt")
    print(f"   le FT-Transformer est {rang_ftt}e sous la liste corrigee")
    STATE["rang_ftt_corrigee"] = rang_ftt
save_state(STATE)
print(f"\n\necrit : {STATE_PATH}")
print(f"matrices de probabilites : {PROBS}")
print("\nA renvoyer : e8_results.json et le dossier e8_probs/")
''')

md("""
---

## Ce que le manuscrit fera de ces résultats

**Ce qui change à coup sûr**, quel que soit le verdict sur `Offset` :

| élément | action |
|---|---|
| liste noire, §4.3 et Tableau 3 | 12 → 13 ou 14 entrées, avec la statistique d'audit d'`IdleTime` |
| Tableau 2 | republié sur la condition corrigée |
| légende de la Figure 6 | **elle s'inverse** — `IdleTime` cesse d'être la preuve que l'attribution surestime |
| Tableaux 7 et 8, calibration | recalculés |
| Tableau 10, coût | recalculé, le nombre de features change |
| Figures 5, 9, 10, 11, 14, 18 | redessinées depuis les nouvelles matrices |
| §9 | **le paragraphe le plus important du papier** : la cécité structurelle du critère |

**Le paragraphe de la §9**, dans les termes que les mesures autorisent :

> Un critère fondé sur le rapport entre deux protocoles ne peut pas voir une fuite figée
> par groupe, puisqu'elle fuit autant des deux côtés. `IdleTime` en est l'instance sur ce
> corpus : τ = 0,94 sous le critère publié, **1,02** sous l'audit imbriqué, rang 24/55
> dans l'audit résiduel — et pourtant une AUC binaire de **1,0000**. Le diagnostic qui la
> voit ne regarde pas l'étiquette : il regarde si la colonne est constante par fichier de
> capture. Nous l'ajoutons à la méthode et nous rapportons que le critère seul ne
> suffisait pas.

**Et la thèse centrale devient symétrique**, ce qui est plus fort que ce que le papier
affirme aujourd'hui : l'attribution donne ≈ 0 aux huit raccourcis redondants **et** donne
son score maximal (0,2279) à un raccourci parfait. Elle échoue dans les deux sens.
""")

nb = {"cells": CELLS,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

txt = json.dumps(nb, indent=1, ensure_ascii=False)
txt = txt.replace("VERSION_PLACEHOLDER", VERSION).replace("BUILD_PLACEHOLDER", BUILD)
out = HERE / "e8_republication.ipynb"
out.write_text(txt, encoding="utf-8")
print(f"ecrit : {out}  ({len(CELLS)} cellules)")
