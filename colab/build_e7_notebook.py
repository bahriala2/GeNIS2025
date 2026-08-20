#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e7_idletime.ipynb.

E7 traite le defaut le plus grave trouve sur ce papier : IdleTime est retenu
dans la condition auditee alors que tout indique un IDENTIFIANT DE FICHIER DE
CAPTURE -- une ou deux valeurs distinctes par fichier, et ce sont des
horodatages Unix absolus.

experiments/e7/verify_idletime.py etablit deja, depuis le seul depot, tout ce
qui peut l'etre sans les fichiers bruts : 17 controles, dont le plafond a
9 classes calcule depuis les effectifs de classes, qui tombe a 0.009 de la
valeur mesuree. Ce notebook apporte ce qui manque, et repare.

Trois choses, dans cet ordre :

  1. la PREUVE DIRECTE : compter les valeurs distinctes par fichier, montrer
     que ce sont des horodatages, mesurer l'AUC binaire ;
  2. le DIAGNOSTIC MANQUANT, generalise : balayer TOUTES les colonnes a la
     recherche de la meme pathologie, parce qu'une regle qui a laisse passer
     IdleTime a pu en laisser passer d'autres. C'est la protection que le
     critere de transferabilite n'a pas, et c'est publiable ;
  3. la REPARATION : reentrainer sous la liste noire a treize entrees et
     mesurer ce que la correction coute.

Le point 2 est le plus important pour le papier. Un critere fonde sur un
RAPPORT entre deux protocoles est structurellement aveugle a une fuite figee
par groupe : elle garde le meme pouvoir des deux cotes. Ce que la colonne
trahit, ce n'est pas son association a l'etiquette, ce sont ses valeurs.

PREREQUIS : le corpus brut 2-flows.zip, comme E5.

Relancer ce script apres toute modification, puis deposer le .ipynb sur Colab.
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
# E7 — `IdleTime` est-il un identifiant de fichier de capture ?

> **Notebook {VERSION}, compilé le {BUILD}.** La cellule 1 réaffiche ce numéro.

**Le problème.** `IdleTime` est **retenu dans la condition auditée** du papier, et c'est
la colonne à laquelle l'importance par permutation donne le score **le plus élevé**
(0,2279, soit 6,4× la suivante). Un audit externe affirme qu'elle ne prend qu'une ou deux
valeurs distinctes par fichier de capture, et que ces valeurs sont des **horodatages Unix
absolus**. Si c'est vrai, la colonne n'encode pas un comportement : elle encode de quel
fichier vient la ligne, et elle résout parfaitement la tâche binaire.

**Ce qui est déjà établi sans les fichiers bruts.** `experiments/e7/verify_idletime.py`,
17 contrôles sur 17 :

| Contrôle | Résultat |
|---|---|
| plafond à 9 classes qu'impose la structure de fichiers | **0,6302** |
| exactitude mesurée d'un arbre sur `IdleTime` seul | **0,6210** |
| écart | **0,0092** |
| pas du `float32` à 1,74×10⁹ | **128 s** — d'où « une ou deux valeurs » |
| τ publié / τ imbriqué | 0,94 / **1,02** — l'exactitude *monte* sous le temporel |

Le plafond est calculé depuis les **seuls effectifs de classes**, une route que l'auditeur
externe n'a pas empruntée. Deux chemins indépendants, la même structure.

**Ce que ce notebook fait.**

1. **La preuve directe** — compter les valeurs distinctes par fichier, mesurer l'AUC binaire.
2. **Le diagnostic manquant, généralisé** — balayer *toutes* les colonnes pour la même
   pathologie. Une règle qui a laissé passer `IdleTime` a pu en laisser passer d'autres.
3. **La réparation** — réentraîner sous la liste noire à **treize** entrées.

**Durée.** Étapes 1–2 : ~10 min. Étape 3 : 10 détecteurs × 2 protocoles ≈ 2 à 3 h avec GPU.
Reprenable : relançable autant de fois qu'il faut, il saute ce qui est fait.

**À me renvoyer :** `e7_results.json`.
""")

code(r'''
# --- 1. Drive et dossier de travail --------------------------------------
E7_VERSION = "VERSION_PLACEHOLDER"; E7_BUILD = "BUILD_PLACEHOLDER"
print(f"E7 notebook {E7_VERSION}, compile le {E7_BUILD}\n")
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

R = json.loads((SAVE / MARQUEUR).read_text(encoding="utf-8"))
BLACKLIST = R["audit"]["blacklist"]
AUDITED = R["slice60"]["features_audited"]
print(f"liste noire publiee : {len(BLACKLIST)} colonnes")
print(f"IdleTime retenu dans la condition auditee : {'IdleTime' in AUDITED}")
if "IdleTime" not in AUDITED:
    sys.exit("IdleTime n'est pas retenu : ce notebook n'a pas lieu d'etre, "
             "verifie que le bon article1_results.json est en place.")
''')

code(r'''
# --- 2. Le corpus brut ---------------------------------------------------
# Meme chargement que E5, mot pour mot : les CSV, pas le cache 60 s, parce
# que le cache a deja subi le cast float32 qui detruit la preuve.
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
CSV60 = [c for c in csvs if "flows-60-sec" in c]
print(f"{len(csvs)} CSV au total, {len(CSV60)} pour la vue 60 s")
''')

code(r'''
# --- 3. PREUVE DIRECTE : une ou deux valeurs par fichier ? ---------------
# On lit chaque fichier separement, en int64, AVANT tout cast float32. Le
# cast est justement ce qui ecrase les valeurs voisines : le mesurer apres
# reviendrait a mesurer notre propre pipeline plutot que le corpus.
import datetime as dt

def utc(v):
    try:
        return dt.datetime.fromtimestamp(float(v), dt.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, OverflowError):
        return "hors plage"

PREUVE = {}
print(f"{'fichier':<34}{'flux':>9}{'valeurs':>9}   {'min (UTC)':<21}{'max (UTC)'}")
for c in sorted(CSV60):
    nom = pathlib.Path(c).stem
    d = pd.read_csv(c, usecols=["IdleTime"], low_memory=False)
    v = d["IdleTime"].dropna()
    u = sorted(v.unique().tolist())
    PREUVE[nom] = {"n": int(len(d)), "n_unique": len(u),
                   "min": float(min(u)) if u else None,
                   "max": float(max(u)) if u else None,
                   "valeurs": [float(x) for x in u[:6]]}
    print(f"{nom:<34}{len(d):>9}{len(u):>9}   {utc(min(u)):<21}{utc(max(u))}")

n_max = max(p["n_unique"] for p in PREUVE.values())
print(f"\nau plus {n_max} valeur(s) distincte(s) dans un fichier")
print("VERDICT :", "IDENTIFIANT DE FICHIER" if n_max <= 3
      else "cardinalite trop elevee, la these ne tient pas")

# Les valeurs sont-elles des horodatages de la campagne (fevrier 2025) ?
DEB = dt.datetime(2025, 2, 1, tzinfo=dt.timezone.utc).timestamp()
FIN = dt.datetime(2025, 2, 20, tzinfo=dt.timezone.utc).timestamp()
dans = [n for n, p in PREUVE.items() if p["min"] and DEB <= p["min"] <= FIN]
print(f"fichiers dont les valeurs tombent dans la campagne : {len(dans)}/{len(PREUVE)}")

# Les plages benignes et malveillantes sont-elles disjointes ?
ben = [p for n, p in PREUVE.items() if "benign" in n]
att = [p for n, p in PREUVE.items() if "benign" not in n]
if ben and att:
    hb, ba = max(p["max"] for p in ben), min(p["min"] for p in att)
    print(f"\ndernier benin  {utc(hb)}\npremiere attaque {utc(ba)}")
    print(f"fosse : {(ba - hb) / 3600:.1f} h   disjointes : {ba > hb}")
    print("=> une seule coupure separe parfaitement benin et attaque"
          if ba > hb else "=> les plages se chevauchent")
''')

code(r'''
# --- 4. LE DIAGNOSTIC MANQUANT, applique a TOUTES les colonnes -----------
# C'est le coeur du notebook. Le critere de transferabilite compare le
# pouvoir predictif d'un protocole a l'autre ; une valeur figee par fichier
# garde le meme des deux cotes et passe pour du signal. Le diagnostic qui la
# voit ne regarde pas l'etiquette du tout : il regarde si la colonne est
# CONSTANTE PAR FICHIER DE CAPTURE.
#
#   variance intra-fichier ~ 0  et  variance inter-fichier > 0
#     => la colonne encode le fichier, pas le flux.
#
# On l'applique a toutes les colonnes numeriques, sans exception, pour ne pas
# se contenter de confirmer celle qu'on soupconnait deja.
IDENT_LIST = ["FlowID", "AutoId", "SrcAddr", "DstAddr", "Ssaddr", "Sdaddr",
              "SrcMac", "DstMac", "SrcOui", "DstOui", "Sport", "Dport",
              "sIpId", "dIpId", "sMpls", "dMpls", "sAS", "dAS", "iAS",
              "sCo", "dCo", "sVid", "dVid"]
LAB_LIST = ["BinaryLabel", "CategoryLabel", "SubCategoryLabel"]

cardinalites, plages = {}, {}
for c in sorted(CSV60):
    d = pd.read_csv(c, low_memory=False)
    num = d.drop(columns=IDENT_LIST + LAB_LIST, errors="ignore")
    num = num.select_dtypes(include=[np.number])
    for col in num.columns:
        s = num[col].dropna()
        if not len(s):
            continue
        cardinalites.setdefault(col, []).append(int(s.nunique()))
        plages.setdefault(col, []).append((float(s.min()), float(s.max())))
    del d, num; gc.collect()

SUSPECTES = []
print(f"{'colonne':<18}{'cardinalite max':>16}{'chevauchement':>15}   verdict")
for col, cards in sorted(cardinalites.items()):
    cmax = max(cards)
    if cmax > 3:
        continue                    # varie a l'interieur d'un fichier : innocente
    # les intervalles par fichier se chevauchent-ils ? s'ils sont disjoints,
    # la colonne ordonne les fichiers, ce qui est la signature d'une horloge.
    iv = sorted(plages[col]); chevauche = any(iv[i][1] >= iv[i + 1][0]
                                              for i in range(len(iv) - 1))
    SUSPECTES.append({"colonne": col, "cardinalite_max": cmax,
                      "chevauchement": bool(chevauche),
                      "min": iv[0][0], "max": iv[-1][1]})
    print(f"{col:<18}{cmax:>16}{str(chevauche):>15}   "
          f"{'IDENTIFIANT DE FICHIER' if not chevauche else 'constante par fichier'}")

print(f"\n{len(SUSPECTES)} colonne(s) constante(s) par fichier de capture")
dures = [s['colonne'] for s in SUSPECTES if not s['chevauchement']]
print(f"dont {len(dures)} qui ordonnent les fichiers sans se chevaucher : {dures}")
print("\nRappel : aucune de ces colonnes n'est detectable par un critere fonde")
print("sur un rapport entre protocoles, puisqu'elle fuit autant des deux cotes.")
''')

code(r'''
# --- 5. L'AUC binaire, la mesure que l'audit n'a jamais faite -----------
# L'audit du papier mesure le pouvoir predictif en NEUF classes. La note
# externe fait remarquer qu'une colonne peut y plafonner a 0.62 tout en
# resolvant parfaitement la tache BINAIRE, qui est celle qui decide
# operationnellement. C'est un raffinement du protocole, pas une objection.
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

d = pd.concat([pd.read_csv(c, low_memory=False) for c in CSV60], ignore_index=True)
ysub = d["SubCategoryLabel"].astype(str).str.strip()
y9 = ysub.where(~ysub.str.startswith("benign"), "benign")
ybin = (y9 != "benign").astype(int)
print(f"{len(d)} flux, {ybin.mean():.4f} d'attaques")

A_TESTER = ["IdleTime", "Offset", "SIntPktMin", "DstBytes", "dTtl", "TotBytes"]
A_TESTER = [c for c in A_TESTER if c in d.columns]
tr, te = train_test_split(np.arange(len(d)), test_size=.2, random_state=1,
                          stratify=y9)
BIN = {}
print(f"\n{'colonne':<14}{'AUC binaire':>13}{'arbre binaire':>15}{'arbre 9 classes':>17}")
for col in A_TESTER:
    x = d[col].fillna(0).to_numpy(dtype="float64").reshape(-1, 1)
    try:
        auc = float(roc_auc_score(ybin, x.ravel()))
        auc = max(auc, 1 - auc)          # le sens du signe n'a pas d'interet
    except ValueError:
        auc = float("nan")
    a1 = DecisionTreeClassifier(random_state=1).fit(x[tr], ybin.iloc[tr])
    ab = float((a1.predict(x[te]) == ybin.iloc[te]).mean())
    a9 = DecisionTreeClassifier(random_state=1).fit(x[tr], y9.iloc[tr])
    a9s = float((a9.predict(x[te]) == y9.iloc[te]).mean())
    BIN[col] = {"auc_binaire": auc, "arbre_binaire": ab, "arbre_9_classes": a9s}
    print(f"{col:<14}{auc:>13.4f}{ab:>15.4f}{a9s:>17.4f}")

print("\nLECTURE. Une colonne a AUC 1.0000 en binaire et ~0.62 en neuf classes")
print("n'est pas un signal faible : c'est un raccourci parfait que la mesure")
print("multiclasse masque. C'est le point de methode a publier.")
del d; gc.collect()
''')

code(r'''
# --- 6. LA REPARATION : reentrainer sous la liste noire a treize --------
# On ne peut pas se contenter de constater. Tant que la campagne n'est pas
# refaite sans IdleTime, on ne sait pas ce que la correction coute, et le
# papier ne peut rien affirmer de sa condition auditee.
import numpy as np
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
SPLITS = {k: (zs[f"{k}_train"], zs[f"{k}_val"], zs[f"{k}_test"])
          for k in ("strat_seed1", "temporal")}

# La liste a treize : les douze publiees, plus IdleTime. On ajoute aussi les
# colonnes que la cellule 4 a trouvees, s'il y en a d'autres -- l'objet n'est
# pas de reparer IdleTime seul mais toutes celles qui ont la meme pathologie.
SUP = sorted({"IdleTime"} | {s["colonne"] for s in SUSPECTES
                             if not s["chevauchement"] and s["colonne"] in F_CLEAN})
BL13 = sorted(set(BLACKLIST) | set(SUP))
print(f"liste noire publiee : {len(BLACKLIST)}")
print(f"colonnes ajoutees   : {SUP}")
print(f"liste corrigee      : {len(BL13)}")

VARIANTES = {"publiee": BLACKLIST, "corrigee": BL13}
STATE_PATH = SAVE / "e7_results.json"
def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {"version": E7_VERSION, "build": E7_BUILD}, "runs": {}}
def save_state(s):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    tmp.replace(STATE_PATH)
STATE = load_state()
STATE["preuve_cardinalite"] = PREUVE
STATE["colonnes_constantes_par_fichier"] = SUSPECTES
STATE["auc_binaire"] = BIN
STATE["blacklist_publiee"] = BLACKLIST
STATE["blacklist_corrigee"] = BL13
save_state(STATE)
print(f"\netat : {len(STATE['runs'])} runs deja faits")
''')

code(r'''
# --- 7. Detecteurs, identiques au pipeline -------------------------------
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks

KNN_MAX_TRAIN = 50_000
SK = ["majority", "logreg", "nb", "knn", "rf", "xgboost", "lightgbm"]
DEEP = ["dnn", "cnn", "rnn"]
MODELES = SK + DEEP

def make_sk(name):
    if name == "majority": return DummyClassifier(strategy="most_frequent")
    if name == "logreg":   return LogisticRegression(max_iter=1000, n_jobs=-1)
    if name == "nb":       return GaussianNB()
    if name == "knn":      return KNeighborsClassifier(n_neighbors=5, n_jobs=2)
    if name == "rf":       return RandomForestClassifier(n_estimators=200, n_jobs=2,
                                                         random_state=0)
    if name == "xgboost":  return XGBClassifier(n_estimators=300, max_depth=8,
                                                learning_rate=.1, tree_method="hist",
                                                n_jobs=2, random_state=0,
                                                eval_metric="mlogloss")
    if name == "lightgbm": return LGBMClassifier(n_estimators=300, num_leaves=63,
                                                 learning_rate=.1, n_jobs=2,
                                                 random_state=0, verbose=-1)
    raise KeyError(name)

def build_deep(name, F):
    if name == "dnn":
        return models.Sequential([layers.Input((F,)),
            layers.Dense(128, activation="relu"), layers.Dropout(.3),
            layers.Dense(64, activation="relu"), layers.Dropout(.2),
            layers.Dense(C, activation="softmax")], name="dnn")
    if name == "cnn":
        return models.Sequential([layers.Input((F, 1)),
            layers.Conv1D(64, 3, activation="relu", padding="same"),
            layers.MaxPooling1D(2),
            layers.Conv1D(32, 3, activation="relu", padding="same"),
            layers.Flatten(),
            layers.Dense(64, activation="relu"), layers.Dropout(.3),
            layers.Dense(C, activation="softmax")], name="cnn")
    if name == "rnn":
        return models.Sequential([layers.Input((F, 1)),
            layers.SimpleRNN(64, activation="relu"), layers.Dropout(.3),
            layers.Dense(64, activation="relu"),
            layers.Dense(C, activation="softmax")], name="rnn")
    raise KeyError(name)

def ece(probs, yt, bins=15):
    conf = probs.max(1); pred = probs.argmax(1); ok = (pred == yt).astype(float)
    edges = np.linspace(0, 1, bins + 1); e = 0.0
    for i in range(bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.any():
            e += m.mean() * abs(ok[m].mean() - conf[m].mean())
    return float(e)

def evalue(yt, pr):
    p = pr.argmax(1); att, patt = yt != BENIGN, p != BENIGN
    return {"macro_f1": float(f1_score(yt, p, average="macro", zero_division=0)),
            "accuracy": float((p == yt).mean()),
            "mcc": float(matthews_corrcoef(yt, p)),
            "fpr": float(patt[~att].mean()) if (~att).any() else None,
            "ece": ece(pr, yt)}

def fit_predict(name, Xtr, ytr, Xva, yva, Xte):
    if name in SK:
        if name == "knn" and len(ytr) > KNN_MAX_TRAIN:
            rng = np.random.RandomState(0)
            keep = rng.choice(len(ytr), KNN_MAX_TRAIN, replace=False)
            Xtr, ytr = Xtr[keep], ytr[keep]
        clf = make_sk(name).fit(Xtr, ytr)
        pr = clf.predict_proba(Xte)
        if pr.shape[1] != C:
            full = np.zeros((len(Xte), C))
            for j, c_ in enumerate(clf.classes_):
                full[:, int(c_)] = pr[:, j]
            pr = full
        del clf; gc.collect(); return pr
    tf.keras.utils.set_random_seed(1)
    net = build_deep(name, Xtr.shape[1])
    net.compile(optimizer=keras.optimizers.Adam(1e-3),
                loss="sparse_categorical_crossentropy")
    cls = np.unique(ytr); w = compute_class_weight("balanced", classes=cls, y=ytr)
    net.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=30, batch_size=256, verbose=0,
            class_weight={int(c_): float(v) for c_, v in zip(cls, w)},
            callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=5,
                                               restore_best_weights=True)])
    pr = net.predict(Xte, batch_size=2048, verbose=0)
    del net; keras.backend.clear_session(); gc.collect(); return pr
print("detecteurs definis")
''')

code(r'''
# --- 8. La campagne : publiee contre corrigee ---------------------------
# Le bras "publiee" est un TEMOIN : il doit reproduire les chiffres du
# tableau 2. S'il ne les reproduit pas, la comparaison ne mesure pas la
# correction mais l'environnement, et il faut s'arreter la.
t_global = time.time()
for var, bl in VARIANTES.items():
    cols = [c for c in F_CLEAN if c not in bl]
    ci = [FEATS.index(c) for c in cols]
    print(f"\n{'='*70}\nvariante {var} : {len(cols)} features\n{'='*70}", flush=True)
    for proto in ("strat_seed1", "temporal"):
        tr_, va_, te_ = SPLITS[proto]
        Xtr = Xva = Xte = None
        for mod in MODELES:
            cle = f"{mod}|{var}|{proto}"
            if cle in STATE["runs"]:
                continue
            if Xtr is None:
                sc = RobustScaler().fit(X[tr_][:, ci])
                g = lambda ix: np.nan_to_num(sc.transform(X[ix][:, ci]),
                                             nan=0., posinf=0.,
                                             neginf=0.).astype("float32")
                Xtr, Xva, Xte = g(tr_), g(va_), g(te_)
            t1 = time.time()
            pr = fit_predict(mod, Xtr, y[tr_], Xva, y[va_], Xte)
            r = evalue(y[te_], pr); r["seconds"] = round(time.time() - t1, 1)
            r["n_features"] = len(cols)
            STATE["runs"][cle] = r; save_state(STATE)
            print(f"   [{proto:11s}] {mod:10s} mF1 {r['macro_f1']:.4f}  "
                  f"FPR {r['fpr'] if r['fpr'] is None else round(r['fpr'],4)}  "
                  f"{r['seconds']:.0f}s", flush=True)
print(f"\ntermine en {(time.time()-t_global)/60:.0f} min")
''')

code(r'''
# --- 9. Le temoin, puis le verdict --------------------------------------
MOD = json.loads((SAVE / "article1_results.json").read_text(encoding="utf-8"))["models"]
print("TEMOIN : le bras 'publiee' doit reproduire le tableau 2\n")
ecarts = []
for mod in MODELES:
    cle_pub = f"{mod}|audited|strat_seed1"
    if cle_pub not in MOD or f"{mod}|publiee|strat_seed1" not in STATE["runs"]:
        continue
    a = MOD[cle_pub]["macro_f1"]
    b = STATE["runs"][f"{mod}|publiee|strat_seed1"]["macro_f1"]
    ecarts.append(abs(a - b))
    print(f"   {mod:10s} publie {a:.4f}   rejoue {b:.4f}   ecart {abs(a-b):.4f}")
if ecarts:
    m = max(ecarts)
    print(f"\n   ecart maximal {m:.4f} -> "
          f"{'TEMOIN VALIDE' if m < 0.01 else 'TEMOIN INVALIDE, ne pas conclure'}")
    STATE["temoin"] = {"ecart_max": m, "valide": bool(m < 0.01)}

print("\n\nCE QUE COUTE LA CORRECTION\n")
print(f"{'detecteur':<12}{'stratifie':>22}{'temporel':>22}")
print(f"{'':12}{'publiee':>10}{'corrigee':>12}{'publiee':>10}{'corrigee':>12}")
resume = {}
for mod in MODELES:
    ligne = []
    for proto in ("strat_seed1", "temporal"):
        for var in ("publiee", "corrigee"):
            k = f"{mod}|{var}|{proto}"
            ligne.append(STATE["runs"][k]["macro_f1"] if k in STATE["runs"] else None)
    if any(v is None for v in ligne):
        continue
    resume[mod] = ligne
    print(f"{mod:<12}{ligne[0]:>10.4f}{ligne[1]:>12.4f}{ligne[2]:>10.4f}{ligne[3]:>12.4f}")

FORTS = [m for m in resume if m not in ("majority", "nb")]
if FORTS:
    ds = max(abs(resume[m][1] - resume[m][0]) for m in FORTS)
    dt_ = max(abs(resume[m][3] - resume[m][2]) for m in FORTS)
    print(f"\n   ecart maximal hors bayesien naif : "
          f"stratifie {ds:.4f}, temporel {dt_:.4f}")
    STATE["ecart_max"] = {"stratifie": ds, "temporel": dt_}
    print("\n   Si ces ecarts sont faibles, la conclusion du papier tient et")
    print("   IdleTime etait redondant avec le reste -- ce qui RENFORCE la these,")
    print("   puisque le raccourci le plus fort ne changeait rien.")
    print("   S'ils sont grands, la condition auditee doit etre republiee.")
save_state(STATE)
print(f"\n\necrit : {STATE_PATH}")
print("A renvoyer : e7_results.json")
''')

md("""
---

## Ce que le papier fera de ces résultats, dans les deux cas

**Quoi qu'il arrive, `IdleTime` sort de la condition auditée et la liste noire passe à
treize entrées au minimum.** La question que ce notebook tranche n'est pas *s'il faut le
faire* mais *ce que ça coûte*.

**Si les écarts sont faibles.** La thèse centrale du papier est renforcée et devient
symétrique : l'attribution donne ~0 aux huit raccourcis redondants **et** donne son score
maximal à un raccourci parfait. Elle échoue donc dans les deux sens, ce qui est plus fort
que ce que le papier affirme aujourd'hui.

**Si les écarts sont grands.** La condition auditée doit être republiée avec les nouveaux
chiffres. C'est du travail, mais c'est du travail fait avant la soumission plutôt qu'après
le rapport de relecture.

**Dans les deux cas, la section 9 gagne le paragraphe le plus important du papier :** le
critère de transférabilité a une cécité structurelle, elle est mesurée, et le diagnostic
qui la comble — chercher les colonnes constantes par fichier de capture — est publiable
indépendamment du corpus.

> ### ⚠️ Rappel pour le papier 1 (BAg-IDS)
>
> `docs/preliminary_findings.md` §3 portait l'action « réintégrer `IdleTime` dans BAg-IDS
> avant soumission ». **Cette action ne doit pas être exécutée.** Elle injecterait une
> fuite à AUC binaire 1,000. L'exclusion accidentelle par le motif `"id"` a protégé le
> papier 1 ; il faut la rendre volontaire et documentée, pas la défaire.
""")

nb = {"cells": CELLS,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

txt = json.dumps(nb, indent=1, ensure_ascii=False)
txt = txt.replace("VERSION_PLACEHOLDER", VERSION).replace("BUILD_PLACEHOLDER", BUILD)
out = HERE / "e7_idletime.ipynb"
out.write_text(txt, encoding="utf-8")
print(f"ecrit : {out}  ({len(CELLS)} cellules)")
