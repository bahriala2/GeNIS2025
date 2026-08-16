#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e4b_temporel_repete.ipynb.

E4b repond aux critiques 4 et 5 et au majeur 8 du rapport de relecture :

  A. origines temporelles glissantes  -> la colonne temporelle gagne enfin une
     variance, un intervalle de confiance et des tests apparies. C'est ce qui
     fragilisait le plus la conclusion centrale, parce que le manuscrit
     presente le classement temporel comme le seul interpretable tout en
     reconnaissant qu'il ne repose que sur une partition deterministe.
  B. bootstrap APPARIE de l'ecart de macro-F1, calcule depuis probs/ sans
     reentrainer : McNemar teste la discordance des erreurs, pas l'ecart de
     macro-F1, et le manuscrit confondait les deux questions.
  C. leave-one-family-out : apres avoir retire l'horodatage et les raccourcis,
     les modeles apprennent-ils un comportement transferable ou la signature
     des huit scenarios scriptes ? C'est la vraie question ouverte du papier.

PREREQUIS : E4a-bis. Le verrou recalcule le classement de l'audit imbrique et
verifie qu'il retrouve la liste noire publiee. E4a seul ne suffit pas : il a
montre que tau ne peut pas s'estimer sur la validation, adjacente au train.

Relancer ce script apres toute modification, puis deposer le .ipynb sur Colab.
"""
import json
from pathlib import Path

VERSION = "v2"
BUILD = "2026-08-16"
HERE = Path(__file__).resolve().parent

CELLS = []
md = lambda s: CELLS.append({"cell_type": "markdown", "metadata": {},
                             "source": s.strip("\n").split("\n")})
code = lambda s: CELLS.append({"cell_type": "code", "execution_count": None,
                               "metadata": {}, "outputs": [],
                               "source": s.strip("\n").split("\n")})

md(f"""
# E4b — la colonne temporelle gagne sa statistique

> **Notebook {VERSION}, compilé le {BUILD}.** La cellule 1 réaffiche ce numéro.

**Prérequis : E4a-bis doit avoir tourné.** La cellule 2 recalcule le classement de
l'audit imbriqué et s'arrête s'il ne retrouve pas la liste noire publiée. C'est E4a-bis
qui fait foi, pas E4a : ce dernier a montré que τ ne peut pas s'estimer sur la validation,
adjacente à la fenêtre d'entraînement.

**Ce que ce notebook règle.**

| Partie | Critique du rapport | Ce qu'elle produit |
|---|---|---|
| A | **Critique 4** — le classement temporel n'a ni variance ni test | 11 détecteurs × k origines temporelles glissantes → moyenne, écart-type, IC |
| B | **Critique 5** — McNemar teste la discordance, pas l'écart de macro-F1 | bootstrap **apparié** de l'écart, 45 paires, sans réentraîner |
| C | **Majeur 8** — comportement transférable ou signature de scénario ? | leave-one-family-out : 8 familles × 4 détecteurs |

**Pourquoi les origines glissantes.** Le protocole temporel par classe coupe à 60/20/20 et
ne donne qu'une partition. En déplaçant l'origine — entraîner sur les premiers *o* %, valider
sur les 20 % suivants, tester sur les 20 % d'après — on obtient plusieurs partitions qui
respectent toutes l'invariant d'ordre à l'intérieur de chaque classe. La dispersion entre
origines est une vraie mesure d'incertitude temporelle, pas une resample du même découpage.

**Pourquoi le leave-one-family-out.** C'est la question que l'audit ne tranche pas : une fois
l'horodatage et les huit raccourcis retirés, un détecteur qui n'a jamais vu `dos-hulk`
le signale-t-il comme attaque ? Si oui, il a appris du comportement. Sinon, il a appris
huit signatures.

**Durée.** Partie A : 11 détecteurs × 5 origines, dont quatre réseaux — compter 3 à 5 h avec
GPU. Partie B : quelques minutes. Partie C : 8 × 4 runs rapides, ~1 h.
Les trois parties sont indépendantes et reprenables : on peut n'en lancer qu'une.

**À me renvoyer :** `e4b_results.json`.
""")

code(r'''
# --- 1. Drive, dossier, verification -------------------------------------
E4B_VERSION = "VERSION_PLACEHOLDER"; E4B_BUILD = "BUILD_PLACEHOLDER"
print(f"E4b notebook {E4B_VERSION}, compile le {E4B_BUILD}\n")
import pathlib, json, sys
from google.colab import drive
drive.mount("/content/drive")

MYDRIVE = pathlib.Path("/content/drive/MyDrive")
MARQUEUR = "article1_results.json"
candidats = [MYDRIVE / "GeNIS" / "article1_final", MYDRIVE / "article1_final",
             MYDRIVE / "GeNIS"]
trouves = [c for c in candidats if (c / MARQUEUR).exists()]
if not trouves:
    print(f"recherche de {MARQUEUR} dans MyDrive...", flush=True)
    for prof in ("*/", "*/*/", "*/*/*/"):
        trouves = [p.parent for p in MYDRIVE.glob(prof + MARQUEUR)]
        if trouves:
            break
if not trouves:
    sys.exit(f"{MARQUEUR} introuvable sous {MYDRIVE}.")
SAVE = trouves[0]
print(f"dossier de travail : {SAVE}")
''')

code(r'''
# --- 2. Verrou : l'audit imbrique doit confirmer la liste noire ----------
# E4a a montre que tau ne peut pas se calculer sur la validation, qui est
# adjacente au train et sous-estime la decroissance. C'est donc E4a-bis,
# l'audit imbrique dans la partition d'entrainement, qui fait foi. Le verrou
# recalcule le classement depuis les donnees plutot que de lire un booleen.
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
_taus = [_N[f]["tau"] for f in _srt]
_gmax, _imax = max((_taus[i + 1] - _taus[i], i) for i in range(len(_taus) - 1))
_ok_liste = set(_srt[:len(_PUB)]) == set(_PUB)
_ok_ecart = _imax + 1 == len(_PUB)
print(f"audit imbrique : {len(_elig)} eligibles, {len(_PUB)} colonnes publiees")
print(f"   les {len(_PUB)} publiees sont-elles les {len(_PUB)} plus basses ? "
      f"{'OUI' if _ok_liste else 'NON'}")
print(f"   le plus large ecart ({_gmax:.4f}) tombe-t-il apres le rang {len(_PUB)} ? "
      f"{'OUI' if _ok_ecart else 'NON, apres le rang %d' % (_imax + 1)}")
if not _ok_liste:
    print(f"   classement imbrique : {_srt[:len(_PUB) + 2]}")
    sys.exit("\nARRET. L'audit imbrique ne retrouve pas la liste publiee : le "
             "benchmark doit d'abord etre relance sur la liste qu'il retourne.")
if not _ok_ecart:
    print("   avertissement : la liste est retrouvee mais la coupure naturelle "
          "ne tombe pas exactement apres elle. On continue.")
print("verrou leve : la liste noire est confirmee sans information de test.\n")
''')

code(r'''
# --- 3. Chargement, splits, etat reprenable ------------------------------
import numpy as np, pandas as pd, time, gc, itertools
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import f1_score, matthews_corrcoef

R = json.loads((SAVE / "article1_results.json").read_text(encoding="utf-8"))
M = json.loads((SAVE / "cache" / "slice60_meta.json").read_text(encoding="utf-8"))
z = np.load(SAVE / "cache" / "slice60.npz")
X, y = z["X"], z["y"].astype(int)
FEATS = M["feat_all"]
F_AUDIT = R["slice60"]["features_audited"]
CI = [FEATS.index(c) for c in F_AUDIT]
CLASS_NAMES = R["slice60"]["classes"]
C = len(CLASS_NAMES)
BENIGN = CLASS_NAMES.index("benign")

# l'ordre temporel : on le reconstruit depuis le split temporel gele, dont le
# train de chaque classe precede le test de la meme classe.
zs = np.load(SAVE / "frozen_splits_60s.npz")
TEMPORAL = (zs["temporal_train"], zs["temporal_val"], zs["temporal_test"])
RANG = np.empty(len(y), dtype=np.int64)
RANG[np.concatenate(TEMPORAL)] = np.arange(len(y))   # position dans l'ordre temporel

print(f"{len(y):,} flux, {len(F_AUDIT)} features auditees, {C} classes"
      .replace(",", " "))

STATE_PATH = SAVE / "e4b_results.json"
def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {"version": E4B_VERSION, "n": int(len(y))},
            "origines": {}, "bootstrap_apparie": {}, "lofo": {}}
def save_state(s):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=float),
                   encoding="utf-8")
    tmp.replace(STATE_PATH)
STATE = load_state()

# --- reparation d'un etat produit par la v1 -------------------------------
# La v1 construisait un CNN et un RNN qui n'etaient pas ceux du pipeline :
# GlobalMaxPooling1D au lieu de MaxPooling1D(2) + Flatten, et SimpleRNN laisse
# sur tanh au lieu de relu. Les lignes cnn et rnn mesuraient donc un autre
# detecteur, et le CNN tombait a 0.68 la ou le papier publie 0.99. La partie B
# ne trouvait par ailleurs aucune matrice de probabilites, faute de respecter
# la convention de nommage du pipeline. On purge ce qui est perime, on garde
# le reste : rien de ce qui a ete calcule correctement n'est recalcule.
if STATE["meta"].get("archi") != "pipeline":
    perimes = [k for k in STATE["origines"] if k.split("|")[0] in ("cnn", "rnn")]
    for k in perimes:
        del STATE["origines"][k]
    if perimes:
        print(f"etat v1 detecte : {len(perimes)} runs cnn/rnn purges "
              f"(architecture non conforme au pipeline)")
    if STATE.get("bootstrap_apparie"):
        STATE["bootstrap_apparie"] = {}
        print("   bootstrap apparie purge : il sera recalcule")
    STATE["meta"]["archi"] = "pipeline"
    STATE["meta"]["version"] = E4B_VERSION
    save_state(STATE)

print(f"etat : {len(STATE['origines'])} runs d'origine, "
      f"{len(STATE['lofo'])} runs leave-one-family-out")
''')

code(r'''
# --- 4. Detecteurs : memes definitions que le pipeline -------------------
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

def build_deep(name, F, n_out):
    if name == "dnn":
        return models.Sequential([layers.Input((F,)),
            layers.Dense(128, activation="relu"), layers.Dropout(.3),
            layers.Dense(64, activation="relu"), layers.Dropout(.2),
            layers.Dense(n_out, activation="softmax")], name="dnn")
    # Recopie mot pour mot de build_cnn et build_rnn du pipeline principal.
    # Une version anterieure de ce notebook mettait GlobalMaxPooling1D la ou le
    # pipeline met MaxPooling1D(2) puis Flatten, et laissait SimpleRNN sur son
    # activation tanh par defaut la ou le pipeline demande relu. Ce n'etaient
    # pas les memes detecteurs, et le CNN tombait de 0.99 a 0.68.
    if name == "cnn":
        return models.Sequential([layers.Input((F, 1)),
            layers.Conv1D(64, 3, activation="relu", padding="same"),
            layers.MaxPooling1D(2),
            layers.Conv1D(32, 3, activation="relu", padding="same"),
            layers.Flatten(),
            layers.Dense(64, activation="relu"), layers.Dropout(.3),
            layers.Dense(n_out, activation="softmax")], name="cnn")
    if name == "rnn":
        return models.Sequential([layers.Input((F, 1)),
            layers.SimpleRNN(64, activation="relu"), layers.Dropout(.3),
            layers.Dense(64, activation="relu"),
            layers.Dense(n_out, activation="softmax")], name="rnn")
    raise KeyError(name)

SK = ["majority", "logreg", "nb", "knn", "rf", "xgboost", "lightgbm"]
DEEP = ["dnn", "cnn", "rnn"]

def fit_predict(name, Xtr, ytr, Xva, yva, Xte, n_out):
    """Renvoie les probabilites sur Xte."""
    if name in SK:
        if name == "knn" and len(ytr) > KNN_MAX_TRAIN:
            rng = np.random.RandomState(0)
            keep = rng.choice(len(ytr), KNN_MAX_TRAIN, replace=False)
            Xtr, ytr = Xtr[keep], ytr[keep]
        clf = make_sk(name).fit(Xtr, ytr)
        pr = clf.predict_proba(Xte)
        # completer si une classe manque du train
        if pr.shape[1] != n_out:
            full = np.zeros((len(Xte), n_out), dtype="float64")
            for j, c_ in enumerate(clf.classes_):
                full[:, int(c_)] = pr[:, j]
            pr = full
        del clf; gc.collect()
        return pr
    tf.keras.utils.set_random_seed(1)
    net = build_deep(name, Xtr.shape[1], n_out)
    net.compile(optimizer=keras.optimizers.Adam(1e-3),
                loss="sparse_categorical_crossentropy")
    cls = np.unique(ytr)
    w = compute_class_weight("balanced", classes=cls, y=ytr)
    net.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=30, batch_size=256, verbose=0,
            class_weight={int(c_): float(v) for c_, v in zip(cls, w)},
            callbacks=[callbacks.EarlyStopping(monitor="val_loss", patience=5,
                                               restore_best_weights=True)])
    pr = net.predict(Xte, batch_size=2048, verbose=0)
    del net; keras.backend.clear_session(); gc.collect()
    return pr

def metriques(yt, pr, n_out):
    p = pr.argmax(1)
    att, patt = yt != BENIGN, p != BENIGN
    return {"macro_f1": float(f1_score(yt, p, average="macro", zero_division=0)),
            "accuracy": float((p == yt).mean()),
            "mcc": float(matthews_corrcoef(yt, p)),
            "fpr": float(patt[~att].mean()) if (~att).any() else None}
print("detecteurs definis")
''')

md("""
## A. Origines temporelles glissantes

Pour une origine *o*, chaque classe est ordonnée dans le temps puis coupée en
entraînement `[0, o)`, validation `[o, o+0.2)`, test `[o+0.2, o+0.4)`. L'invariant est
le même que celui du manuscrit — tout flux de test postdate tout flux d'entraînement de
sa classe — mais la partition change avec *o*.

`o = 0.60` reproduit exactement le protocole publié, à ceci près que le test s'arrête à
100 % : c'est le point de contrôle.
""")

code(r'''
# --- 5. A. origines glissantes -------------------------------------------
ORIGINES = [0.40, 0.45, 0.50, 0.55, 0.60]     # test = [o+0.2, o+0.4]
MODELES = SK + DEEP                            # 10 detecteurs, majority compris

def split_origine(o):
    tr, va, te = [], [], []
    for c_ in range(C):
        ix = np.where(y == c_)[0]
        ix = ix[np.argsort(RANG[ix], kind="stable")]
        n = len(ix)
        a, b, d = int(o * n), int((o + .2) * n), int(min(o + .4, 1.0) * n)
        tr.append(ix[:a]); va.append(ix[a:b]); te.append(ix[b:d])
    return np.concatenate(tr), np.concatenate(va), np.concatenate(te)

def matrices(tr_, va_, te_):
    sc = RobustScaler().fit(X[tr_][:, CI])
    f = lambda ix: np.nan_to_num(sc.transform(X[ix][:, CI]),
                                 nan=0., posinf=0., neginf=0.).astype("float32")
    return f(tr_), f(va_), f(te_)

t0 = time.time()
for o in ORIGINES:
    tr_, va_, te_ = split_origine(o)
    # invariant : dans chaque classe, le test postdate le train
    ok = all(RANG[tr_][y[tr_] == c_].max() <= RANG[te_][y[te_] == c_].min()
             for c_ in range(C) if (y[tr_] == c_).any() and (y[te_] == c_).any())
    print(f"\n=== origine {o:.2f} : train {len(tr_):,} / val {len(va_):,} / "
          f"test {len(te_):,} | invariant {'OK' if ok else 'VIOLE'} ==="
          .replace(",", " "), flush=True)
    if not ok:
        print("   invariant viole, origine ignoree"); continue
    Xtr = Xva = Xte = None
    for mod in MODELES:
        cle = f"{mod}|o{o:.2f}"
        if cle in STATE["origines"]:
            continue
        if Xtr is None:
            Xtr, Xva, Xte = matrices(tr_, va_, te_)
        t1 = time.time()
        pr = fit_predict(mod, Xtr, y[tr_], Xva, y[va_], Xte, C)
        r = metriques(y[te_], pr, C); r["seconds"] = round(time.time() - t1, 1)
        r["n_test"] = int(len(te_))
        STATE["origines"][cle] = r; save_state(STATE)
        print(f"   {mod:10s} macro-F1 {r['macro_f1']:.4f}  acc {r['accuracy']:.4f}  "
              f"({r['seconds']:.0f} s)", flush=True)
        del pr; gc.collect()
    del Xtr, Xva, Xte; gc.collect()
print(f"\npartie A terminee en {(time.time()-t0)/60:.0f} min")
''')

code(r'''
# --- 6. A. synthese : le classement temporel avec sa dispersion ----------
lignes = []
for mod in MODELES:
    v = [STATE["origines"][f"{mod}|o{o:.2f}"]["macro_f1"]
         for o in ORIGINES if f"{mod}|o{o:.2f}" in STATE["origines"]]
    if not v:
        continue
    pub = R["models"].get(f"{mod}|audited|temporal", {}).get("macro_f1")
    lignes.append((mod, np.mean(v), np.std(v), min(v), max(v), len(v), pub))
lignes.sort(key=lambda t: -t[1])

print(f"{'detecteur':<12}{'moyenne':>9}{'ecart-type':>12}{'min':>8}{'max':>8}"
      f"{'k':>4}{'publie (1 partition)':>22}")
print("-" * 76)
for m_, mu, sd, lo, hi, k, pub in lignes:
    print(f"{m_:<12}{mu:>9.4f}{sd:>12.4f}{lo:>8.4f}{hi:>8.4f}{k:>4}"
          f"{(f'{pub:.4f}' if pub is not None else '--'):>22}")

print("\nCe qu'il faut en tirer pour le manuscrit :")
sd_max = max(l[2] for l in lignes if l[0] != "majority")
ecart_tete = lignes[0][1] - lignes[min(5, len(lignes)-1)][1]
print(f"   ecart-type maximal entre origines : {sd_max:.4f}")
print(f"   ecart entre la tete et le 6e       : {ecart_tete:.4f}")
print("   -> si l'ecart-type depasse l'ecart entre les premiers, aucun classement")
print("      n'est etabli et le manuscrit doit le dire.")
STATE["origines_synthese"] = [
    {"modele": m_, "mean": mu, "std": sd, "min": lo, "max": hi, "k": k, "publie": pub}
    for m_, mu, sd, lo, hi, k, pub in lignes]
save_state(STATE)
''')

md("""
## B. Bootstrap apparié de l'écart de macro-F1

McNemar teste si deux détecteurs se trompent sur des flux différents. Ce n'est pas la
question « leur macro-F1 diffère-t-il ». Cette partie répond directement à la seconde, en
rééchantillonnant **les mêmes indices** pour les deux détecteurs, ce qui préserve
l'appariement. Elle ne réentraîne rien : elle lit `probs/`.
""")

code(r'''
# --- 7. B. bootstrap apparie sur les probabilites deja stockees ----------
PROBS = SAVE / "probs"
B = 1000

def charge(cle):
    # Convention du pipeline, cellule kfile() : "|" -> "_" et "#" -> "-".
    # Une version anterieure cherchait un double underscore et ne trouvait
    # jamais rien, ce qui faisait sauter toute la partie B en silence.
    p = PROBS / f"{cle.replace('|', '_').replace('#', '-')}.npz"
    if not p.exists():
        print(f"   introuvable : {p.name}")
        return None
    with np.load(p) as zz:
        # le fichier contient probs_val ET probs_test : on veut le test, et le
        # prendre par son nom plutot que par sa position dans l'archive.
        if "probs_test" not in zz.files:
            print(f"   {p.name} ne contient pas probs_test : {zz.files}")
            return None
        return zz["probs_test"]

for proto, split_idx in (("strat_seed1", None), ("temporal", TEMPORAL[2])):
    if proto in STATE["bootstrap_apparie"]:
        continue
    yt = y[np.load(SAVE / "frozen_splits_60s.npz")[f"{proto}_test"]]
    preds = {}
    for mod in MODELES:
        pr = charge(f"{mod}|audited|{proto}")
        if pr is not None and len(pr) == len(yt):
            preds[mod] = pr.argmax(1)
    print(f"\n{proto} : {len(preds)} detecteurs charges depuis probs/")
    if len(preds) < 2:
        print("   pas assez de matrices : partie B sautee pour ce protocole")
        continue
    rng = np.random.RandomState(0)
    idx = [rng.randint(0, len(yt), len(yt)) for _ in range(B)]
    f1s = {m_: np.array([f1_score(yt[i_], p_[i_], average="macro", zero_division=0)
                         for i_ in idx]) for m_, p_ in preds.items()}
    out = {}
    for a, b in itertools.combinations(sorted(preds), 2):
        d = f1s[a] - f1s[b]
        lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
        out[f"{a}|{b}"] = {"delta_mean": float(d.mean()), "ci95": [lo, hi],
                           "significatif": bool(lo > 0 or hi < 0)}
    STATE["bootstrap_apparie"][proto] = out; save_state(STATE)
    ns = sum(1 for v in out.values() if not v["significatif"])
    print(f"   paires dont l'IC95 de l'ecart contient zero : {ns}/{len(out)}")
    for k_, v in sorted(out.items(), key=lambda kv: abs(kv[1]["delta_mean"]))[:8]:
        print(f"      {k_:<22} delta {v['delta_mean']:+.5f}  "
              f"IC [{v['ci95'][0]:+.5f}, {v['ci95'][1]:+.5f}]"
              f"{'' if v['significatif'] else '   non significatif'}")
''')

md("""
## C. Leave-one-family-out

Pour chaque famille d'attaque, le détecteur est entraîné sur le bénin et les **sept
autres** familles, puis on lui présente la famille retenue. La question est binaire :
la signale-t-il comme attaque ?

C'est la mesure que le manuscrit n'a pas et que le rapport réclame. Un détecteur qui
n'a appris que des signatures de scénario échouera ; un détecteur qui a appris du
comportement d'attaque généralisera au moins en partie.
""")

code(r'''
# --- 8. C. leave-one-family-out ------------------------------------------
LOFO_MODELES = ["logreg", "rf", "xgboost", "lightgbm", "dnn"]
FAMILLES = [c for c in CLASS_NAMES if c != "benign"]
tr_ref, va_ref, te_ref = TEMPORAL

t0 = time.time()
for fam in FAMILLES:
    fi = CLASS_NAMES.index(fam)
    garde = y != fi
    tr_ = tr_ref[garde[tr_ref]]; va_ = va_ref[garde[va_ref]]
    # test : le benin du test habituel + TOUTE la famille retenue
    te_benin = te_ref[y[te_ref] == BENIGN]
    te_fam = np.where(y == fi)[0]
    te_ = np.concatenate([te_benin, te_fam])
    yb = (y[te_] != BENIGN).astype(int)          # 1 = attaque
    print(f"\n=== sans {fam} : train {len(tr_):,} | test {len(te_benin):,} benins "
          f"+ {len(te_fam):,} flux de la famille ===".replace(",", " "), flush=True)
    Xtr = Xva = Xte = None
    for mod in LOFO_MODELES:
        cle = f"{mod}|{fam}"
        if cle in STATE["lofo"]:
            continue
        if Xtr is None:
            sc = RobustScaler().fit(X[tr_][:, CI])
            g = lambda ix: np.nan_to_num(sc.transform(X[ix][:, CI]),
                                         nan=0., posinf=0., neginf=0.).astype("float32")
            Xtr, Xva, Xte = g(tr_), g(va_), g(te_)
        # reetiquetage dense : les classes restantes sont renumerotees
        classes = sorted(set(y[tr_].tolist()))
        remap = {c_: i for i, c_ in enumerate(classes)}
        ytr = np.array([remap[v] for v in y[tr_]])
        yva = np.array([remap[v] for v in y[va_]])
        t1 = time.time()
        pr = fit_predict(mod, Xtr, ytr, Xva, yva, Xte, len(classes))
        p_att = 1.0 - pr[:, remap[BENIGN]]        # probabilite d'etre une attaque
        pred_att = (pr.argmax(1) != remap[BENIGN]).astype(int)
        from sklearn.metrics import roc_auc_score
        rec = float(pred_att[yb == 1].mean())     # rappel sur la famille inconnue
        fpr = float(pred_att[yb == 0].mean())
        try:
            auc = float(roc_auc_score(yb, p_att))
        except Exception:
            auc = None
        STATE["lofo"][cle] = {"recall_famille_inconnue": rec, "fpr_benin": fpr,
                              "auroc": auc, "n_famille": int(len(te_fam)),
                              "seconds": round(time.time() - t1, 1)}
        save_state(STATE)
        print(f"   {mod:10s} rappel {rec:.4f}  FPR benin {fpr:.4f}  "
              f"AUROC {auc if auc is None else round(auc, 4)}", flush=True)
        del pr; gc.collect()
    del Xtr, Xva, Xte; gc.collect()
print(f"\npartie C terminee en {(time.time()-t0)/60:.0f} min")
''')

code(r'''
# --- 9. C. synthese ------------------------------------------------------
print(f"{'famille':<18}" + "".join(f"{m_:>12}" for m_ in LOFO_MODELES))
print("-" * (18 + 12 * len(LOFO_MODELES)))
for fam in FAMILLES:
    row = "".join(
        f"{STATE['lofo'][f'{m_}|{fam}']['recall_famille_inconnue']:>12.4f}"
        if f"{m_}|{fam}" in STATE["lofo"] else f"{'--':>12}" for m_ in LOFO_MODELES)
    print(f"{fam:<18}{row}")
print("\nrappel = part des flux de la famille jamais vue signales comme attaque")
vals = [v["recall_famille_inconnue"] for v in STATE["lofo"].values()]
if vals:
    print(f"\nrappel moyen sur familles inconnues : {np.mean(vals):.4f}  "
          f"(min {min(vals):.4f}, max {max(vals):.4f})")
    print("   proche de 1 : les modeles ont appris du comportement d'attaque")
    print("   proche de 0 : ils ont appris huit signatures de scenario")
''')

code(r'''
# --- 10. Export ----------------------------------------------------------
save_state(STATE)
print(f"resultats : {STATE_PATH}")
print(f"taille    : {STATE_PATH.stat().st_size/1024:.0f} Ko")
print("\nA me renvoyer : e4b_results.json")
''')

nb = {"cells": CELLS,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True},
                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

txt = json.dumps(nb, indent=1, ensure_ascii=False)
txt = txt.replace("VERSION_PLACEHOLDER", VERSION).replace("BUILD_PLACEHOLDER", BUILD)
out = HERE / "e4b_temporel_repete.ipynb"
out.write_text(txt, encoding="utf-8")
print(f"ecrit : {out}  ({len(CELLS)} cellules)")
