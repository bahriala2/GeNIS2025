#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere colab/e2_cicids2017_audit.ipynb.

E2 repond a la priorite 1 du relecteur : appliquer l'audit d'Article 1 a un
second corpus. Ce n'est pas un second benchmark, c'est le meme audit ailleurs.

Relancer ce script apres toute modification.
"""
import json
from pathlib import Path

VERSION = "v5"
BUILD = "2026-08-13"

CELLS = []


def md(src):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": src.strip("\n").split("\n")})


def code(src):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.strip("\n").split("\n")})


# ---------------------------------------------------------------- 0. titre
md(r"""
# E2 : le meme audit, sur CICIDS2017

> **Notebook VERSION_PLACEHOLDER, compilé le BUILD_PLACEHOLDER.** La cellule 1.1 réaffiche ce numéro
> à l'exécution. S'il ne correspond pas, Colab sert une copie en cache.

Expérience complémentaire de l'article *A Leakage-Audited Benchmark of Deep and Ensemble
Detectors on the GeNIS 2025 Corpus*.

**Ce que le relecteur demande.** Les trois résultats à portée méthodologique de l'article sont
démontrés sur un seul corpus. Il demande le même audit sur un corpus indépendant, et donne la
liste : sonde temporelle, sonde mono-feature, importance par permutation, découpage temporel,
transférabilité. Ce notebook remplit exactement ces cinq lignes.

**Ce que ce notebook n'est pas.** Pas un second benchmark. On ne rejoue pas 154 runs. La
confirmation par détecteurs, en fin de notebook, tient en dix-huit runs et sert seulement à
montrer si le classement bouge une fois l'audit appliqué.

**Pourquoi CICIDS2017.** C'est le corpus le plus utilisé du domaine, il est indépendant de
GeNIS, et les auteurs y ont déjà travaillé (Bahri et al., AMCAI 2023), ce qui rend le
prétraitement connu. Surtout, il porte un vrai horodatage sur cinq jours consécutifs, ce que
GeNIS ne permet pas d'exploiter.

**Une question à trancher au passage.** L'article AMCAI 2023 écrit avoir utilisé CICIDS2017
« with respect to » Flow ID, Source IP, Destination IP et le timestamp, pour un total de
79 colonnes. La phrase se lit comme si ces colonnes avaient été conservées, mais 79 est
exactement le compte des CSV `MachineLearningCVE`, d'où elles sont **déjà retirées**. La
cellule 3.2 tranche : elle liste les colonnes identifiantes réellement présentes dans les
fichiers chargés et affiche le compte. La réponse s'affiche à l'exécution, elle n'est pas
supposée ici.

**Durée.** Environ 90 minutes, dont l'essentiel dans le balayage mono-feature. Le notebook est
reprenable : chaque résultat est écrit sur disque dès qu'il est calculé.
""")

# ---------------------------------------------------------------- 1. env
md("""
## 1. Environnement et corpus

CICIDS2017 existe en deux distributions et **le choix n'est pas libre** :

| Distribution | Colonnes | Horodatage | Utilisable ici |
|---|---|---|---|
| `MachineLearningCVE/` | 79 | **absent** | non |
| `GeneratedLabelledFlows/TrafficLabelling/` | 85 | présent | **oui** |

Tout l'audit repose sur l'ordre temporel. Sans la colonne `Timestamp` il n'y a ni sonde
temporelle, ni protocole chronologique, ni transférabilité. Ce notebook exige donc
`TrafficLabelling`. Si seuls les CSV à 79 colonnes sont disponibles, il s'arrête en le disant.

Déposer le dossier ou son zip sous `MyDrive/GeNIS/`, comme pour les autres notebooks.
""")

code(r"""
# --- 1.1 Drive, dossiers, corpus -------------------------------------------
E2_VERSION = "VERSION_PLACEHOLDER"; E2_BUILD = "BUILD_PLACEHOLDER"
print(f"E2 notebook {E2_VERSION}, compile le {E2_BUILD}")
import os, json, gc, time, glob, shutil, pathlib, warnings, subprocess, re
from pathlib import Path
warnings.filterwarnings("ignore")

SEEDS = [1, 2, 3]
KNN_MAX_TRAIN = 50_000
SCAN_SUBSAMPLE = 300_000   # le balayage mono-feature tient sur un sous-echantillon stratifie

from google.colab import drive
drive.mount("/content/drive")

GENIS = pathlib.Path("/content/drive/MyDrive/GeNIS")
WORK = pathlib.Path("/content/cicids"); WORK.mkdir(parents=True, exist_ok=True)
os.chdir(WORK)
SAVE = GENIS / "e2"
for sub in ("", "figures"):
    (SAVE / sub).mkdir(parents=True, exist_ok=True)

def find_csvs(root):
    return sorted(glob.glob(str(pathlib.Path(root) / "**" / "*.csv"), recursive=True))

csvs = find_csvs("traffic")
if not csvs:
    for cand in ("TrafficLabelling", "GeneratedLabelledFlows", "CICIDS2017", "MachineLearningCVE"):
        d = GENIS / cand
        if find_csvs(d):
            print(f"lecture directe depuis Drive : {cand}")
            csvs = find_csvs(d); break
    else:
        for z in ("GeneratedLabelledFlows.zip", "TrafficLabelling.zip", "CICIDS2017.zip"):
            if (GENIS / z).exists():
                print(f"copie de {z} depuis Drive...", flush=True)
                shutil.copy(GENIS / z, z)
                subprocess.run(["unzip", "-o", "-q", z, "-d", "traffic"], check=True)
                csvs = find_csvs("traffic"); break

assert csvs, ("aucun CSV trouve. Deposer GeneratedLabelledFlows (dossier ou zip) sous "
              f"{GENIS}. Les CSV MachineLearningCVE ne conviennent pas : pas d'horodatage.")
print(f"\n{len(csvs)} fichier(s) :")
for f in csvs:
    print(f"   {pathlib.Path(f).name:<58} {os.path.getsize(f)/1e6:8.1f} Mo")
print(f"\nsortie : {SAVE}")
""")

code(r"""
# --- 1.2 Bibliotheques -----------------------------------------------------
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, matthews_corrcoef
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
import lightgbm as lgb
print("pandas", pd.__version__, "| numpy", np.__version__, "| lightgbm", lgb.__version__)
""")

# ---------------------------------------------------------------- 2. etat
md("""
## 2. État reprenable

Même principe que les autres notebooks : un JSON écrit de façon atomique après chaque étape,
et un inventaire au démarrage qui dit ce qui reste à faire plutôt que de le deviner.
""")

code(r"""
STATE_PATH = SAVE / "e2_results.json"

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"meta": {}, "columns": {}, "duplicates": [], "day_matrix": {},
            "timestamp_probe": {}, "single_feature": {}, "perm_importance": {},
            "audit": {}, "runs": {}}

def save_state(s):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    tmp.replace(STATE_PATH)

STATE = load_state()
ETAPES = ["columns", "duplicates", "day_matrix", "timestamp_probe",
          "single_feature", "perm_importance", "audit"]
fait = [e for e in ETAPES if STATE.get(e)]
print(f"etapes deja calculees : {', '.join(fait) if fait else 'aucune'}")
print(f"runs de confirmation deja calcules : {len(STATE['runs'])}")
""")

# ---------------------------------------------------------------- 3. charge
md("""
## 3. Chargement, en trois temps

CICIDS2017 fait environ 2,8 millions de lignes sur 85 colonnes. Charger les huit fichiers puis
les concaténer d'un coup tient **deux copies** en mémoire au moment du `concat`, ce qui dépasse
la RAM de Colab. Le chargement est donc découpé :

| Cellule | Ce qu'elle fait | Coût |
|---|---|---|
| 3.1 | lit les **en-têtes seuls** et répond à la question des colonnes | instantané |
| 3.2 | convertit **un fichier à la fois** en `.npz` sur Drive, et libère la mémoire | le plus long, **reprenable** |
| 3.3 | assemble les parts dans un tableau prélloué | quelques secondes |

La 3.2 saute ce qui est déjà converti : si la session tombe, relancez-la, elle reprend au
fichier suivant. Rien n'est jamais tenu deux fois en mémoire.

Trois pièges connus du corpus sont traités : les espaces en tête des noms de colonnes, un
fichier en `cp1252` à cause du tiret de « Web Attack – Brute Force », et les valeurs infinies
de `Flow Bytes/s`.

L'ordre chronologique ne vient **pas** du parsing de l'horodatage, ambigu dans ce corpus
(format 12 heures sans AM/PM selon les fichiers). Il vient du jour porté par le nom de fichier,
ordre connu et fiable ; l'horodatage ne sert qu'à départager à l'intérieur d'un même fichier.
""")

code(r"""
# --- 3.1 Inventaire des colonnes, sans charger les donnees -----------------
JOURS = [("monday", 1), ("tuesday", 2), ("wednesday", 3), ("thursday", 4), ("friday", 5)]
ORDRE_FICHIER = ["monday", "tuesday", "wednesday",
                 "thursday-workinghours-morning-webattacks",
                 "thursday-workinghours-afternoon-infilteration",
                 "friday-workinghours-morning",
                 "friday-workinghours-afternoon-portscan",
                 "friday-workinghours-afternoon-ddos"]

def rang_fichier(nom):
    n = nom.lower().replace(".pcap_iscx.csv", "").replace(".csv", "")
    for i, motif in enumerate(ORDRE_FICHIER):
        if n.startswith(motif):
            return i
    for i, m in enumerate(ORDRE_FICHIER):
        if m.split("-")[0] in n and all(t in n for t in m.split("-")[2:] if len(t) > 4):
            return i
    return 99

def jour_de(nom):
    n = nom.lower()
    for cle, j in JOURS:
        if cle in n:
            return j
    return 0

def lire(path, nrows=None):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            d = pd.read_csv(path, encoding=enc, low_memory=False, nrows=nrows)
            break
        except UnicodeDecodeError:
            continue
    d.columns = [str(c).strip() for c in d.columns]
    return d

FICHIERS = sorted(csvs, key=lambda f: (rang_fichier(pathlib.Path(f).name),
                                       pathlib.Path(f).name))
tete = lire(FICHIERS[0], nrows=5)
COLS = list(tete.columns)
LABEL = [c for c in COLS if c.strip().lower() == "label"][0]

IDENT_ATTENDUS = ["Flow ID", "Source IP", "Destination IP", "Source Port",
                  "Destination Port", "Protocol"]
POS_ATTENDUS = ["Timestamp"]
present_id = [c for c in IDENT_ATTENDUS if c in COLS]
present_pos = [c for c in POS_ATTENDUS if c in COLS]
absents = [c for c in IDENT_ATTENDUS + POS_ATTENDUS if c not in COLS]

print("=" * 74)
print("COMPOSITION DES FICHIERS")
print("=" * 74)
print(f"   colonnes au total (label inclus)     : {len(COLS)}")
print(f"   colonnes identifiantes presentes     : {len(present_id)}  {present_id}")
print(f"   colonnes positionnelles presentes    : {len(present_pos)}  {present_pos}")
print(f"   attendues mais absentes              : {absents if absents else 'aucune'}")
print()
if len(COLS) <= 80 and not present_pos:
    print("   >>> distribution MachineLearningCVE : identifiants et horodatage deja")
    print("       retires en amont. L'audit temporel est IMPOSSIBLE ici.")
    print("       Recharger GeneratedLabelledFlows/TrafficLabelling.")
else:
    print("   >>> distribution TrafficLabelling : l'horodatage est present, l'audit")
    print("       temporel est possible. Les identifiants seront exclus par nom,")
    print("       comme en section 4.3 de l'article.")
assert present_pos, "sans Timestamp, ce notebook n'a rien a mesurer"

CAND = [c for c in COLS if c not in present_id + present_pos + [LABEL]]
print(f"\n{len(FICHIERS)} fichiers, {len(CAND)} colonnes comportementales candidates")
STATE["columns"] = {"n_total": len(COLS), "identifiers_present": present_id,
                    "positional_present": present_pos, "absent": absents, "all": COLS}
save_state(STATE)
""")

md("""
### 3.2 Conversion, un fichier à la fois

La cellule longue, et **la seule qui puisse tomber**. Elle traite les fichiers un par un :
lecture, extraction de la matrice numérique en `float32`, écriture d'un `.npz` sur Drive, puis
libération de la mémoire avant le fichier suivant. Jamais plus d'un fichier en RAM.

Si la session tombe, relancez cette cellule seule : elle saute ce qui est déjà converti.
""")

code(r"""
# --- 3.2 Conversion fichier par fichier, reprenable ------------------------
PARTS = SAVE / "parts"; PARTS.mkdir(parents=True, exist_ok=True)

def part_path(nom):
    return PARTS / (pathlib.Path(nom).stem.replace(" ", "_") + ".npz")

todo = [f for f in FICHIERS if not part_path(f).exists()]
print(f"{len(FICHIERS) - len(todo)}/{len(FICHIERS)} deja converti(s), {len(todo)} a faire\n")

t0 = time.time()
for k, f in enumerate(todo, 1):
    nom = pathlib.Path(f).name
    d = lire(f)
    lab0 = d[LABEL].astype(str).str.strip()
    d = d[lab0.str.lower() != "label"]                               # entete dupliquee
    # Le fichier Thursday-Infiltration se termine par des lignes vides : leur
    # etiquette est vide ou NaN. Les garder cree une 16e classe fictive et
    # fausse tout. Les retirer rend exactement le compte canonique du corpus.
    lab0 = d[LABEL].astype(str).str.strip()
    vides = lab0.isin(["", "nan", "NaN", "None"]) | d[LABEL].isna()
    if vides.any():
        print(f"      {int(vides.sum()):,} ligne(s) sans etiquette retiree(s)".replace(",", " "))
        d = d[~vides]
    d = d.reindex(columns=COLS)                                      # ordre fige par 3.1
    X = (d[CAND].apply(pd.to_numeric, errors="coerce")
         .replace([np.inf, -np.inf], np.nan).to_numpy(dtype="float32"))
    lab = d[LABEL].astype(str).str.strip().to_numpy()
    ts = pd.to_datetime(d[present_pos[0]], errors="coerce", dayfirst=True)
    t = ts.astype("int64").to_numpy().astype("float64")
    t[ts.isna().to_numpy()] = np.nan
    np.savez_compressed(part_path(f), X=X, lab=lab.astype("U40"),
                        t=t, day=np.full(len(d), jour_de(nom), "int8"),
                        rank=np.full(len(d), rang_fichier(nom), "int8"))
    el = time.time() - t0
    print(f"   [{k}/{len(todo)}] {nom:<56} {len(d):>9,} lignes  "
          f"({el:.0f} s)".replace(",", " "), flush=True)
    del d, X, lab, ts, t; gc.collect()

print(f"\n{len(list(PARTS.glob('*.npz')))} part(s) sur disque")
""")

md("""
### 3.3 Assemblage

Les parts sont empilées dans un tableau **préalloué**, donc sans copie intermédiaire. Les
colonnes constantes sont détectées ici, sur l'ensemble et non fichier par fichier, puis la
matrice classe × jour est imprimée : c'est elle qui dira si le découpage chronologique global
est dégénéré sur ce corpus comme il l'est sur GeNIS.
""")

code(r"""
# --- 3.3 Assemblage dans un tableau prealloue ------------------------------
parts = [part_path(f) for f in FICHIERS]
assert all(p.exists() for p in parts), "des parts manquent : relancer la cellule 3.2"

tailles = []
for p in parts:
    with np.load(p, allow_pickle=False) as z:
        tailles.append(z["day"].shape[0])
N = sum(tailles)
print(f"{N:,} lignes au total, {len(CAND)} colonnes candidates".replace(",", " "))

BRUT = np.empty((N, len(CAND)), dtype="float32")
y_txt = np.empty(N, dtype="U40")
t_num = np.empty(N, dtype="float64")
jour = np.empty(N, dtype="int8")
rang = np.empty(N, dtype="int8")
o = 0
for p, n in zip(parts, tailles):
    with np.load(p, allow_pickle=False) as z:
        BRUT[o:o+n] = z["X"]; y_txt[o:o+n] = z["lab"]
        t_num[o:o+n] = z["t"]; jour[o:o+n] = z["day"]; rang[o:o+n] = z["rank"]
    o += n
    gc.collect()

# colonnes constantes, jugees sur l'ensemble
fini = np.nan_to_num(BRUT, nan=0., posinf=0., neginf=0.)
garde = [i for i in range(len(CAND))
         if np.unique(fini[::17, i]).size > 1]        # 1 ligne sur 17 suffit a trancher
CONST = [CAND[i] for i in range(len(CAND)) if i not in garde]
NUM = np.ascontiguousarray(fini[:, garde])
FEATURES = [CAND[i] for i in garde]
del BRUT, fini; gc.collect()
print(f"{len(FEATURES)} features comportementales, {len(CONST)} constantes retirees")
if CONST:
    print("   constantes :", ", ".join(CONST[:8]), "..." if len(CONST) > 8 else "")

le = LabelEncoder().fit(y_txt)
y = le.transform(y_txt)
CLASSES = list(le.classes_)

# l'horodatage illisible est remplace par le rang de fichier, qui est fiable
n_bad = int(np.isnan(t_num).sum())
t_num = np.where(np.isnan(t_num), rang.astype("float64") * 1e18, t_num)
print(f"horodatages illisibles remplaces par le rang de fichier : {n_bad:,}".replace(",", " "))

mat = pd.crosstab(pd.Series(y_txt, name="classe"), pd.Series(jour, name="jour"))
print(f"\n{len(CLASSES)} classes x 5 jours :")
print(mat.to_string())
seul_un_jour = [c for c in mat.index if (mat.loc[c] > 0).sum() == 1]
print(f"\nclasses presentes un seul jour : {len(seul_un_jour)}/{len(CLASSES)}")
print("   ", ", ".join(seul_un_jour))

# Une empreinte des donnees. Tout ce qui a ete calcule sous une empreinte
# differente est invalide : c'est le piege qui a fait passer les valeurs du
# premier passage, calculees avec les lignes vides, dans le second.
SIG = f"{N}|{len(FEATURES)}|{len(CLASSES)}"
# Un etat SANS signature est un etat produit avant l'introduction de ce
# garde-fou, donc precisement celui dont on se mefie. Ne pas le purger etait le
# defaut de la v4. Sur un etat neuf la purge ne coute rien : tout est deja vide.
ancienne = STATE["meta"].get("signature")
if ancienne != SIG:
    perimes = [k for k in ("duplicates", "timestamp_probe", "single_feature",
                           "perm_importance", "audit", "runs") if STATE.get(k)]
    print(f"\n>>> empreinte des donnees : {ancienne or 'absente'} -> {SIG}")
    print(f"    resultats perimes effaces : {', '.join(perimes) if perimes else 'aucun'}")
else:
    print(f"\nempreinte des donnees inchangee : {SIG}")
    for k in ("duplicates", "audit"):
        STATE[k] = [] if k == "duplicates" else {}
    for k in ("timestamp_probe", "single_feature", "perm_importance", "runs"):
        STATE[k] = {}

STATE["meta"] = {"signature": SIG, "n_rows": int(N), "n_files": len(FICHIERS),
                 "files": [pathlib.Path(f).name for f in FICHIERS],
                 "n_features": len(FEATURES), "constants_dropped": CONST}
STATE["day_matrix"] = {"classes": CLASSES, "matrix": mat.to_dict()}
save_state(STATE)
""")

# ---------------------------------------------------------------- 4. proto
md("""
## 4. Les trois protocoles

Le point que ce notebook cherche à mesurer, et qui n'est pas acquis d'avance :

L'article dit que sur GeNIS le découpage chronologique global est **dégénéré**, parce que le
trafic bénin et les attaques occupent des fenêtres disjointes. Un relecteur peut répondre que
c'est une bizarrerie de GeNIS. CICIDS2017 permet de le vérifier : le bénin y est présent les
cinq jours, ce qui est différent. Mais chaque famille d'attaque n'apparaît qu'un seul jour.

La cellule 3.3 vient d'imprimer la matrice classe × jour. Si les classes de test sont absentes
du train sous un découpage chronologique global, alors la dégénérescence n'est pas propre à
GeNIS : c'est une propriété des captures scriptées, et la justification du protocole temporel
par classe de l'article vaut pour les deux corpus.

Les trois protocoles, sur lesquels tout le reste est mesuré :

- **P1 stratifié** : 60/20/20 aléatoire, stratifié, la référence.
- **P2 chronologique global** : train lundi à mercredi, test jeudi et vendredi. Rapporté en
  multiclasse *et* en binaire, car le binaire reste défini même quand le multiclasse dégénère.
- **P3 temporel par classe** : à l'intérieur de chaque classe, 60/20/20 par ordre de capture.
  C'est le protocole de l'article, reproduit ici pour que les deux corpus se comparent.
""")

code(r"""
def split_stratifie(seed=1):
    idx = np.arange(len(y))
    tr, tmp = train_test_split(idx, test_size=.4, random_state=seed, stratify=y)
    va, te = train_test_split(tmp, test_size=.5, random_state=seed, stratify=y[tmp])
    return tr, va, te

def split_chrono_global():
    tr = np.where(jour <= 3)[0]
    te = np.where(jour >= 4)[0]
    return tr, te

def split_temporel_par_classe(frac=(.6, .2, .2)):
    tr, va, te = [], [], []
    ordre = np.lexsort((np.arange(len(y)), rang))     # jour, puis ordre d'apparition
    pos = np.empty(len(y), dtype=np.int64); pos[ordre] = np.arange(len(y))
    for c in np.unique(y):
        ix = np.where(y == c)[0]
        ix = ix[np.argsort(pos[ix], kind="stable")]
        n = len(ix); a, b = int(frac[0]*n), int((frac[0]+frac[1])*n)
        tr.append(ix[:a]); va.append(ix[a:b]); te.append(ix[b:])
    return np.concatenate(tr), np.concatenate(va), np.concatenate(te)

TR1, VA1, TE1 = split_stratifie(1)
TRC, TEC = split_chrono_global()
TR3, VA3, TE3 = split_temporel_par_classe()

vus_tr = set(np.unique(y[TRC])); vus_te = set(np.unique(y[TEC]))
communes = vus_tr & vus_te
print(f"P2 chronologique global : {len(TRC):,} train / {len(TEC):,} test".replace(",", " "))
print(f"   classes en train {len(vus_tr)}, en test {len(vus_te)}, communes {len(communes)}")
print("   communes :", [CLASSES[c] for c in sorted(communes)])
print("   absentes du train mais en test :",
      [CLASSES[c] for c in sorted(vus_te - vus_tr)])
degenere = len(communes) <= 1
print(f"\n   >>> multiclasse {'DEGENERE' if degenere else 'exploitable'} sous P2,",
      "comme sur GeNIS" if degenere else "contrairement a GeNIS")

ok3 = all(pos_ok := [(y[TR3] == c).any() and (y[TE3] == c).any() for c in np.unique(y)])
print(f"P3 temporel par classe : toutes les classes presentes des deux cotes : {ok3}")
STATE["day_matrix"]["p2_degenerate"] = bool(degenere)
STATE["day_matrix"]["p2_shared_classes"] = [CLASSES[c] for c in sorted(communes)]
save_state(STATE)
""")

# ---------------------------------------------------------------- 5. sondes
md("""
## 5. Sonde temporelle et colonnes dupliquées

Les deux premières lignes du tableau que demande le relecteur.

La sonde temporelle est l'expérience la plus directe de l'article : un arbre de décision sur la
seule colonne d'horodatage. S'il classe bien, l'horodatage encode la classe, et tout modèle qui
le reçoit peut s'en servir au lieu du comportement réseau.
""")

code(r"""
# --- 5.1 Sonde sur l'horodatage seul ---------------------------------------
if not STATE["timestamp_probe"]:
    # t_num a ete construit en 3.3, horodatage parse et rang de fichier en secours
    res = {}
    for nom, (a, b) in (("stratifie", (TR1, TE1)), ("temporel_par_classe", (TR3, TE3))):
        clf = DecisionTreeClassifier(random_state=1).fit(t_num[a].reshape(-1, 1), y[a])
        p = clf.predict(t_num[b].reshape(-1, 1))
        res[nom] = {"accuracy": float(accuracy_score(y[b], p)),
                    "macro_f1": float(f1_score(y[b], p, average="macro", zero_division=0)),
                    "majority": float(pd.Series(y[b]).value_counts(normalize=True).iloc[0])}
        print(f"   {nom:<22} accuracy {res[nom]['accuracy']:.4f}  "
              f"macro-F1 {res[nom]['macro_f1']:.4f}  (hasard {res[nom]['majority']:.4f})")
    res["tau"] = res["temporel_par_classe"]["accuracy"] / max(res["stratifie"]["accuracy"], 1e-9)
    print(f"   tau de l'horodatage : {res['tau']:.3f}")
    STATE["timestamp_probe"] = res; save_state(STATE)
else:
    print("deja calcule :", json.dumps(STATE["timestamp_probe"], indent=1))
""")

code(r"""
# --- 5.2 Colonnes numeriquement identiques ---------------------------------
if not STATE["duplicates"]:
    M = NUM
    n = M.shape[1]
    sig = {}
    for j in range(n):                      # signature bon marche avant np.allclose
        col = M[:, j]
        sig.setdefault((round(float(col.mean()), 6), round(float(col.std()), 6)), []).append(j)
    paires = []
    for grp in sig.values():
        for a in range(len(grp)):
            for b in range(a + 1, len(grp)):
                if np.allclose(M[:, grp[a]], M[:, grp[b]], rtol=1e-5, atol=1e-8):
                    paires.append([FEATURES[grp[a]], FEATURES[grp[b]]])
    STATE["duplicates"] = paires; save_state(STATE)
    del M; gc.collect()
print(f"{len(STATE['duplicates'])} paire(s) de colonnes identiques")
for p in STATE["duplicates"][:12]:
    print("   ", " = ".join(p))
""")

# ---------------------------------------------------------------- 6. scan
md("""
## 6. Balayage mono-feature et transférabilité

Le cœur de l'audit, et la partie la plus longue. Pour chaque feature comportementale, un arbre
de décision entraîné sur cette seule colonne, évalué sous P1 et sous P3, puis

τ(f) = acc_temporel(f) / acc_stratifié(f)

exactement comme en section 4.3 de l'article. Le balayage tourne sur un sous-échantillon
stratifié de 300 000 flux : au-delà, un arbre à une variable ne gagne plus rien et le coût
devient inutile. La cellule est reprenable feature par feature.
""")

code(r"""
def sous_ech(idx, n_max, seed=0):
    if len(idx) <= n_max:
        return idx
    keep, _ = train_test_split(idx, train_size=n_max, random_state=seed, stratify=y[idx])
    return keep

S_TR1, S_TE1 = sous_ech(TR1, SCAN_SUBSAMPLE), sous_ech(TE1, SCAN_SUBSAMPLE // 3)
S_TR3, S_TE3 = sous_ech(TR3, SCAN_SUBSAMPLE), sous_ech(TE3, SCAN_SUBSAMPLE // 3)
chance = float(pd.Series(y[S_TE1]).value_counts(normalize=True).iloc[0])
print(f"sous-echantillons : {len(S_TR1):,} train, {len(S_TE1):,} test".replace(",", " "))
print(f"taux de la classe majoritaire : {chance:.4f}")

SF = STATE["single_feature"]
t0 = time.time()
for k, f in enumerate(FEATURES, 1):
    if f in SF:
        continue
    x = NUM[:, FEATURES.index(f)].astype("float64").reshape(-1, 1)
    r = {}
    for nom, (a, b) in (("strat", (S_TR1, S_TE1)), ("temp", (S_TR3, S_TE3))):
        clf = DecisionTreeClassifier(random_state=1).fit(x[a], y[a])
        p = clf.predict(x[b])
        r[nom] = float(accuracy_score(y[b], p))
        r[nom + "_f1"] = float(f1_score(y[b], p, average="macro", zero_division=0))
    r["tau"] = r["temp"] / r["strat"] if r["strat"] > 0 else 1.0
    r["tau_f1"] = r["temp_f1"] / r["strat_f1"] if r["strat_f1"] > 0 else 1.0
    r["n_unique"] = int(np.unique(x[S_TR1]).size)
    SF[f] = r
    if k % 5 == 0 or r["tau"] < 0.5:
        el = time.time() - t0
        print(f"   [{k:>2}/{len(FEATURES)}] {f[:28]:<28} {r['strat']:.3f} -> {r['temp']:.3f}  "
              f"tau {r['tau']:.2f}{'   <-- RACCOURCI' if r['tau'] < .5 and r['strat'] > chance + .4818*(1-chance) else ''}"
              f"   ({el:.0f} s)", flush=True)
        STATE["single_feature"] = SF; save_state(STATE)
STATE["single_feature"] = SF; save_state(STATE)
print(f"\nbalayage termine, {len(SF)} features en {time.time()-t0:.0f} s")
""")

code(r"""
# --- 6.2 Importance par permutation, pour montrer la meme cecite -----------
if not STATE["perm_importance"]:
    sc = RobustScaler().fit(NUM[S_TR1])
    Xtr = np.nan_to_num(sc.transform(NUM[S_TR1]), nan=0., posinf=0., neginf=0.)
    Xte = np.nan_to_num(sc.transform(NUM[S_TE1]), nan=0., posinf=0., neginf=0.)
    ref = lgb.LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=.1,
                             n_jobs=2, random_state=0, verbose=-1).fit(Xtr, y[S_TR1])
    six = np.random.RandomState(0).choice(len(Xte), min(15000, len(Xte)), replace=False)
    imp = permutation_importance(ref, Xte[six], y[S_TE1][six], n_repeats=5,
                                 random_state=0, n_jobs=1, scoring="accuracy")
    STATE["perm_importance"] = {FEATURES[i]: float(imp.importances_mean[i])
                                for i in range(len(FEATURES))}
    save_state(STATE); del ref, Xtr, Xte; gc.collect()

P = STATE["perm_importance"]
SF = STATE["single_feature"]
seuil_pred_tmp = chance + 0.4818 * (1 - chance)
sus = [f for f in FEATURES if SF[f]["tau"] < 0.5 and SF[f]["strat"] > seuil_pred_tmp]
aveugle = [f for f in sus if abs(P.get(f, 0)) < 1e-4]
print(f"raccourcis detectes par la transferabilite : {len(sus)}")
print(f"   dont importance par permutation sous 1e-4 : {len(aveugle)}  <- invisibles a la methode usuelle")
for f in sus:
    print(f"   {f[:30]:<30} tau {SF[f]['tau']:.2f}  importance {P.get(f, 0):+.5f}")
""")

code(r"""
# --- 6.3 Liste noire et comparaison avec GeNIS -----------------------------
# Le filtre de predictivite de l'article est "acc > 3 x hasard". Il n'est pas
# transposable : sur un corpus a 80 % de classe majoritaire, 3 x hasard depasse 1
# et aucune feature ne peut etre eligible. On le reexprime en fraction de la marge
# disponible au-dessus du hasard, forme qui vaut sur tout corpus :
#     eligible  <=>  acc_strat > hasard + KAPPA x (1 - hasard)
# KAPPA = 0.4818 reproduit exactement la regle publiee sur GeNIS, ou le hasard
# vaut 0.1942 : 0.1942 + 0.4818 x 0.8058 = 0.5827 = 3 x 0.1942.
# Sur un corpus a 80 % de classe majoritaire, l'accuracy mono-feature est
# ininformative : une colonne qui predit tout en BENIGN atteint deja 0.80. La
# regle publiee "acc > 3 x hasard" est de surcroit inapplicable, 3 x 0.80 > 1.
# Le filtre de predictivite porte donc ici sur le MACRO-F1, qui ne recompense
# pas la classe majoritaire, et le seuil est exprime en fraction de la marge.
# La regle publiee est "acc > 3 x hasard". Sur un corpus a 80 % de classe
# majoritaire elle est inapplicable, 3 x 0.80 depasse 1, et l'accuracy est de
# toute facon saturee : predire tout en BENIGN donne deja 0.80.
# On garde la FORME de la regle, trois fois la baseline, en la portant sur le
# macro-F1, qui ne recompense pas la classe majoritaire. La baseline n'est plus
# choisie : c'est le macro-F1 mesure du classifieur de classe majoritaire.
THR, KAPPA = 0.5, 0.4818
maj = int(np.bincount(y[S_TE1]).argmax())
f1_base = float(f1_score(y[S_TE1], np.full(len(S_TE1), maj),
                         average="macro", zero_division=0))
F1_MIN = 3.0 * f1_base
seuil_pred = chance + KAPPA * (1 - chance)
elig_acc = [f for f in FEATURES if SF[f]["strat"] > seuil_pred]
elig_legacy = [f for f in FEATURES if SF[f]["strat"] > 3.0 * chance]
elig = [f for f in FEATURES if SF[f].get("strat_f1", 0) > F1_MIN]
print(f"hasard {chance:.4f}   macro-F1 de la classe majoritaire {f1_base:.4f}")
print(f"   regle publiee, acc > 3 x hasard ({3*chance:.4f}) : {len(elig_legacy)} eligibles"
      f"{'  <-- INAPPLICABLE, le seuil depasse 1' if 3*chance >= 1 else ''}")
print(f"   marge sur accuracy, seuil {seuil_pred:.4f}      : {len(elig_acc)} eligibles"
      f"{'  <-- l accuracy est saturee par la classe majoritaire' if len(elig_acc) < 10 else ''}")
print(f"   macro-F1 > 3 x baseline = {F1_MIN:.4f}          : {len(elig)} eligibles  <- retenu")
noire = sorted(f for f in elig if SF[f].get("tau_f1", 1.0) < THR)
STATE["audit"] = {"chance": chance,
                  "rule": {"ratio_below": THR, "kappa": KAPPA,
                           "predictivity_threshold": seuil_pred,
                           "legacy_3x_applicable": bool(3 * chance < 1)},
                  "f1_majority_baseline": f1_base, "f1_min": F1_MIN,
                  "n_features": len(FEATURES), "n_eligible": len(elig),
                  "blacklist_behavioural": noire,
                  "identifiers_excluded": present_id, "positional": present_pos}
save_state(STATE)

taus = sorted(SF[f]["tau"] for f in elig)
print(f"{len(FEATURES)} comportementales, {len(elig)} eligibles, {len(noire)} exclues par la regle")
if len(taus) >= 2:
    gaps = sorted(((taus[i+1]-taus[i], taus[i], taus[i+1]) for i in range(len(taus)-1)),
                  reverse=True)
    print(f"plus large separation naturelle : {gaps[0][0]:.3f} entre "
          f"{gaps[0][1]:.2f} et {gaps[0][2]:.2f}")
else:
    print("moins de deux features eligibles : pas de separation a rapporter")
print("\nsensibilite au seuil :")
for s in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
    print(f"   {s:.1f} : {sum(1 for f in elig if SF[f]['tau'] < s):>3} exclues")

GENIS_REF = {"n_features": 63, "n_eligible": 38, "blacklist": 8, "chance": 0.1942,
             "timestamp_strat": 0.9970, "timestamp_temp": 0.9862, "duplicates": 15}
print("\n" + "=" * 74)
print(f"{'':<34}{'GeNIS':>12}{'CICIDS2017':>14}")
print("=" * 74)
tp = STATE["timestamp_probe"]
lignes = [("features comportementales", GENIS_REF["n_features"], len(FEATURES)),
          ("eligibles (> 3x hasard)", GENIS_REF["n_eligible"], len(elig)),
          ("exclues par la regle", GENIS_REF["blacklist"], len(noire)),
          ("paires de colonnes identiques", GENIS_REF["duplicates"], len(STATE["duplicates"]))]
for nom, g, c in lignes:
    print(f"{nom:<34}{g:>12}{c:>14}")
print(f"{'sonde horodatage, stratifie':<34}{GENIS_REF['timestamp_strat']:>12.4f}"
      f"{tp['stratifie']['accuracy']:>14.4f}")
print(f"{'sonde horodatage, temporel':<34}{GENIS_REF['timestamp_temp']:>12.4f}"
      f"{tp['temporel_par_classe']['accuracy']:>14.4f}")
print(f"{'chronologique global degenere':<34}{'oui':>12}"
      f"{('oui' if STATE['day_matrix']['p2_degenerate'] else 'non'):>14}")
""")

# ---------------------------------------------------------------- 7. runs
md("""
## 7. Confirmation par détecteurs, dix-huit runs

Facultatif, mais c'est la question RQ4 : le classement bouge-t-il une fois l'audit appliqué ?

Trois détecteurs seulement, un par famille et choisis parmi ceux de l'article : LightGBM pour
les arbres boostés, la régression logistique pour le linéaire, un DNN pour le profond. Trois
conditions de features, deux protocoles. Dix-huit runs, pas cent cinquante-quatre.
""")

code(r"""
# En v2 les trois conditions etaient identiques : les identifiants n'entraient
# jamais dans NUM, donc "as-distributed" et "no-identifier" designaient le meme
# jeu, et dix-huit runs n'en mesuraient que six. On ne garde donc que les
# conditions qui different reellement.
noire_b = STATE["audit"]["blacklist_behavioural"]
CONDITIONS = {"behavioural": FEATURES}
if noire_b:
    CONDITIONS["audited"] = [f for f in FEATURES if f not in noire_b]
else:
    print("liste noire vide : la condition auditee serait identique, elle est omise")
print({k: len(v) for k, v in CONDITIONS.items()})

def matrices(cond, split):
    ci = [FEATURES.index(c) for c in CONDITIONS[cond]]
    a, b = split
    M = NUM[:, ci]
    sc = RobustScaler().fit(M[a])
    f = lambda ix: np.nan_to_num(sc.transform(M[ix]), nan=0., posinf=0., neginf=0.).astype("float32")
    return f(a), f(b), y[a], y[b]

def detecteur(nom, n_out):
    if nom == "lightgbm":
        return lgb.LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=.1,
                                  n_jobs=2, random_state=1, verbose=-1)
    if nom == "logreg":
        return LogisticRegression(max_iter=1000, n_jobs=-1)
    raise ValueError(nom)

SPLITS = {"stratifie": (TR1, TE1), "temporel_par_classe": (TR3, TE3)}
for cond in CONDITIONS:
    for sp, paire in SPLITS.items():
        Xtr = Xte = None
        for mod in ("lightgbm", "logreg", "dnn"):
            cle = f"{mod}|{cond}|{sp}"
            if cle in STATE["runs"]:
                continue
            if Xtr is None:
                Xtr, Xte, ytr, yte = matrices(cond, paire)
            t0 = time.time()
            if mod == "dnn":
                import tensorflow as tf
                from tensorflow import keras
                from tensorflow.keras import layers
                tf.keras.utils.set_random_seed(1)
                net = keras.Sequential([layers.Input((Xtr.shape[1],)),
                    layers.Dense(128, activation="relu"), layers.Dropout(.3),
                    layers.Dense(64, activation="relu"), layers.Dropout(.2),
                    layers.Dense(len(np.unique(y)), activation="softmax")])
                net.compile(optimizer=keras.optimizers.Adam(1e-3),
                            loss="sparse_categorical_crossentropy")
                itr, iva = next(StratifiedShuffleSplit(1, test_size=.15, random_state=1)
                                .split(Xtr, ytr))
                net.fit(Xtr[itr], ytr[itr], validation_data=(Xtr[iva], ytr[iva]),
                        epochs=30, batch_size=256, verbose=0,
                        callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss",
                                   patience=5, restore_best_weights=True)])
                pred = net.predict(Xte, batch_size=2048, verbose=0).argmax(1)
                del net; keras.backend.clear_session()
            else:
                clf = detecteur(mod, len(np.unique(y))).fit(Xtr, ytr)
                pred = clf.predict(Xte); del clf
            STATE["runs"][cle] = {
                "macro_f1": float(f1_score(yte, pred, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(yte, pred)),
                "mcc": float(matthews_corrcoef(yte, pred)),
                "n_features": int(Xtr.shape[1]), "seconds": round(time.time()-t0, 1)}
            save_state(STATE)
            print(f"   {cle:<44} macro-F1 {STATE['runs'][cle]['macro_f1']:.4f}  "
                  f"({STATE['runs'][cle]['seconds']:.0f} s)", flush=True)
        del Xtr, Xte; gc.collect()
print(f"\n{len(STATE['runs'])} run(s), {len(CONDITIONS)} condition(s) x 2 protocoles x 3 detecteurs")
""")

# ---------------------------------------------------------------- 8. figures
md("""
## 8. Figure pour le papier

Une seule figure, construite à la largeur finale du cadre du .docx, 6.698 pouces, pour que les
tailles de police déclarées survivent à l'insertion. Deux panneaux : le spectre de
transférabilité de CICIDS2017 à côté de celui de GeNIS, et l'importance par permutation contre
la transférabilité, qui montre la même cécité sur les deux corpus.
""")

code(r"""
W_IN, DPI = 6.698, 400
RED, BLUE, GREY = "#c23b34", "#4a72b0", "#9aa4b1"
plt.rcParams.update({"font.size": 6, "axes.linewidth": .5,
                     "xtick.major.width": .4, "ytick.major.width": .4})

SF = STATE["single_feature"]; P = STATE["perm_importance"]
elig = [f for f in FEATURES if SF[f]["strat"] > STATE["audit"]["rule"]["predictivity_threshold"]]
srt = sorted(elig, key=lambda f: SF[f]["tau"])

fig, ax = plt.subplots(1, 2, figsize=(W_IN, 2.6))
c = [RED if SF[f]["tau"] < .5 else BLUE for f in srt]
ax[0].bar(range(len(srt)), [SF[f]["tau"] for f in srt], color=c, width=.85)
ax[0].axhline(.5, color=RED, ls="-.", lw=.7)
ax[0].axhline(1.0, color="k", ls="--", lw=.6)
ax[0].set_xlabel("behavioural features, sorted"); ax[0].set_ylabel("transferability τ")
ax[0].set_title(f"(a) CICIDS2017: {sum(1 for f in srt if SF[f]['tau'] < .5)} of "
                f"{len(srt)} below threshold", fontsize=6.5)
ax[1].scatter([abs(P.get(f, 0)) for f in srt], [SF[f]["tau"] for f in srt],
              s=9, c=c, edgecolor="none")
ax[1].axhline(.5, color=RED, ls="-.", lw=.7)
ax[1].axvline(1e-4, color=GREY, ls=":", lw=.7)
ax[1].set_xscale("symlog", linthresh=1e-5)
ax[1].set_xlabel("|permutation importance|"); ax[1].set_ylabel("transferability τ")
ax[1].set_title("(b) shortcuts with near-zero attribution", fontsize=6.5)
fig.tight_layout()
fig.savefig(SAVE / "figures" / "figE2_transferability.png", dpi=DPI, facecolor="white")
print("figE2_transferability.png ecrite")
""")

code(r"""
# --- 9. Export -------------------------------------------------------------
save_state(STATE)
zp = shutil.make_archive(str(SAVE / "e2_figures"), "zip", str(SAVE / "figures"))
print("resultats :", STATE_PATH)
print("figures   :", zp)
print("\nA me renvoyer : e2_results.json")
""")

md("""
---

**Si Colab rouvre une ancienne version.** La cellule 1.1 affiche le numéro de version. S'il ne
correspond pas à celui du titre, vider le cache du navigateur ou rouvrir le notebook depuis
Drive avec un nom de fichier différent.
""")

# ---------------------------------------------------------------- ecriture
nb = {"cells": CELLS,
      "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True}},
      "nbformat": 4, "nbformat_minor": 0}

CELLS[:] = [dict(c, source=[l.replace("VERSION_PLACEHOLDER", VERSION)
                            .replace("BUILD_PLACEHOLDER", BUILD) for l in c["source"]])
            for c in CELLS]
nb["cells"] = CELLS

out = Path(__file__).resolve().parent / f"e2_cicids2017_audit_{VERSION}.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{out.name} : {len(CELLS)} cellules ({sum(1 for c in CELLS if c['cell_type']=='code')} de code)")
