# =========================================================================
# E9 — la robustesse a l'intervalle, pour six detecteurs de plus
# =========================================================================
# A coller dans une NOUVELLE cellule du notebook
# e5_intervalles_cinq_graines, apres avoir execute ses cellules 1 a 4
# (Execution > Tout executer suffit). ATTENTION : ce notebook-ci et pas
# celui d'E8 -- E9 reutilise load_slice_df, feature_sets, split_de et
# evaluate, qui n'existent que dans le notebook des intervalles.
#
# POURQUOI. Le tableau 13 evalue chaque detecteur sur quatre axes, et la
# colonne « robustesse a l'intervalle » porte « not measured » sur sept
# lignes sur dix : l'etude par intervalle ne couvre que XGBoost, LightGBM et
# le DNN. C'est exact, et c'est declare, mais ca rend cet axe inutilisable
# comme comparaison -- recommander XGBoost pour sa robustesse ne dit rien
# tant que la regression logistique n'a pas ete mesuree.
#
# Six des sept manquants sont a portee. Le septieme, le FT-Transformer, ne
# l'est pas : un seul de ses ajustements a 60 s a demande 31 602 s, et les
# intervalles courts portent jusqu'a huit fois plus de flux. Il gardera son
# « not measured », et le papier dira pourquoi.
#
# COUT, et pourquoi l'ordre compte. Les detecteurs sont pris du moins cher au
# plus cher, et les intervalles de 30 s vers 5 s, pour la meme raison :
# chaque unite terminee est sauvegardee, donc vous pouvez arreter n'importe
# quand et ce qui est fait reste fait. Estimation par extrapolation des temps
# a 60 s, pour trois graines et trois intervalles :
#
#     nb        quelques minutes        knn       ~30 min
#     rf        ~30 min                 cnn       ~2 h
#     logreg    ~3 h                    rnn       ~4 h
#
# Faites-en autant que vous voulez. Une ligne du tableau 13 devient une
# mesure des qu'un detecteur a ses trois intervalles.
import gc
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.utils.class_weight import compute_class_weight

for _n in ("STATE", "save_state", "load_slice_df", "feature_sets", "split_de",
           "evaluate", "BLACKLIST", "CLASS_NAMES", "C", "tf", "layers",
           "callbacks"):
    if _n not in dir():
        raise NameError(
            f"{_n} n'est pas defini : execute d'abord les cellules 1 a 4 du "
            "notebook e5 (Execution > Tout executer).")

GRAINES_E9 = [1, 2, 3]          # trois, comme l'etude d'intervalle d'origine
INTERVALLES_E9 = ["30", "10", "5"]
MODELES_E9 = ["nb", "rf", "knn", "cnn", "logreg", "rnn"]
KNN_MAX_TRAIN = 50_000

# Recopie des reglages du pipeline. Un detecteur mesure ici doit etre le meme
# que celui du tableau 2, sinon la ligne du tableau 13 melange deux modeles.
DEFAULTS_SK_E9 = {"logreg": {"max_iter": 1000}, "nb": {}, "knn": {},
                  "rf": {"n_estimators": 200}}
DEFAULTS_DEEP_E9 = {
    "cnn": {"f1": 64, "f2": 32, "dense": 64, "drop": .3, "lr": 1e-3, "bs": 256},
    "rnn": {"units": 64, "dense": 64, "drop": .3, "lr": 1e-3, "bs": 256}}


def make_sk_e9(nom, seed):
    p = dict(DEFAULTS_SK_E9[nom])
    if nom == "logreg":
        return LogisticRegression(n_jobs=-1, **p)
    if nom == "nb":
        return GaussianNB(**p)
    if nom == "knn":
        return KNeighborsClassifier(n_jobs=2, **p)
    if nom == "rf":
        return RandomForestClassifier(n_jobs=2, random_state=seed, **p)
    raise KeyError(nom)


def build_cnn_e9(F, q):
    return tf.keras.Sequential([layers.Input((F, 1)),
        layers.Conv1D(q["f1"], 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Conv1D(q["f2"], 3, activation="relu", padding="same"),
        layers.Flatten(),
        layers.Dense(q["dense"], activation="relu"), layers.Dropout(q["drop"]),
        layers.Dense(C, activation="softmax")], name="cnn")


def build_rnn_e9(F, q):
    return tf.keras.Sequential([layers.Input((F, 1)),
        layers.SimpleRNN(q["units"], activation="relu"),
        layers.Dropout(q["drop"]),
        layers.Dense(q["dense"], activation="relu"),
        layers.Dense(C, activation="softmax")], name="rnn")


NEURAL_E9 = {"cnn": build_cnn_e9, "rnn": build_rnn_e9}


def un_run_e9(nom, s, Xiv, y_iv, itr, iva_, ite_):
    """Un ajustement, evalue comme les trois detecteurs deja couverts."""
    sc = RobustScaler().fit(Xiv[itr])
    Xtr, Xva, Xte = [np.nan_to_num(sc.transform(Xiv[i_]), nan=0., posinf=0.,
                                   neginf=0.).astype(np.float32)
                     for i_ in (itr, iva_, ite_)]
    ytr_, yva_, yte_ = y_iv[itr], y_iv[iva_], y_iv[ite_]

    if nom in DEFAULTS_SK_E9:
        if nom == "knn" and len(ytr_) > KNN_MAX_TRAIN:
            # Le plafond du pipeline, et il compte double ici : a 5 s le jeu
            # d'entrainement porte huit fois plus de flux qu'a 60 s.
            rng = np.random.RandomState(0)
            keep = rng.choice(len(ytr_), KNN_MAX_TRAIN, replace=False)
            Xtr, ytr_ = Xtr[keep], ytr_[keep]
        t0 = time.time()
        clf = make_sk_e9(nom, s).fit(Xtr, ytr_)
        ft = time.time() - t0
        t0 = time.time()
        pr = clf.predict_proba(Xte)
        pt = time.time() - t0
        if pr.shape[1] != C:                     # une classe absente du train
            plein = np.zeros((len(Xte), C))
            for j, c_ in enumerate(clf.classes_):
                plein[:, int(c_)] = pr[:, j]
            pr = plein
        out = evaluate(yte_, pr, ft, pt)
        del clf, pr
    else:
        q = DEFAULTS_DEEP_E9[nom]
        tf.keras.utils.set_random_seed(s)
        net = NEURAL_E9[nom](Xtr.shape[1], q)
        net.compile(optimizer=tf.keras.optimizers.Adam(q["lr"]),
                    loss="sparse_categorical_crossentropy",
                    metrics=["accuracy"])
        cls = np.unique(ytr_)
        w = compute_class_weight("balanced", classes=cls, y=ytr_)
        t0 = time.time()
        net.fit(Xtr.reshape(-1, Xtr.shape[1], 1), ytr_,
                validation_data=(Xva.reshape(-1, Xva.shape[1], 1), yva_),
                epochs=30, batch_size=q["bs"], verbose=0,
                class_weight={int(c_): float(v) for c_, v in zip(cls, w)},
                callbacks=[callbacks.EarlyStopping(monitor="val_loss",
                                                   patience=5,
                                                   restore_best_weights=True)])
        ft = time.time() - t0
        t0 = time.time()
        pr = net.predict(Xte.reshape(-1, Xte.shape[1], 1), batch_size=1024,
                         verbose=0)
        pt = time.time() - t0
        out = evaluate(yte_, pr, ft, pt)
        del net, pr
        tf.keras.backend.clear_session()
    del Xtr, Xva, Xte
    gc.collect()
    return out


# --------------------------------------------------------------------------
# La campagne, intervalle par intervalle : charger un intervalle coute cher,
# donc on fait tous ses runs avant de passer au suivant.
# --------------------------------------------------------------------------
RUNS = STATE["runs"]
faits = 0
for iv in INTERVALLES_E9:
    manquants = [(m, s) for m in MODELES_E9 for s in GRAINES_E9
                 if f"{iv}|{m}|seed{s}" not in RUNS]
    if not manquants:
        print(f"{iv} s : rien a faire")
        continue
    print(f"\n=== {iv} s : {len(manquants)} run(s) ===", flush=True)
    # Colonnes et type identiques a la cellule 5 du notebook : un detecteur
    # mesure sur d'autres colonnes ne serait pas comparable aux trois deja
    # couverts, et la colonne du tableau 13 melangerait deux conditions.
    d, y9 = load_slice_df(iv)
    num, _, cleanc, _, _, _ = feature_sets(d)
    audc = [c for c in cleanc if c not in BLACKLIST]
    Xiv = np.ascontiguousarray(num[audc].values, dtype=np.float32)
    y_iv = np.array([CLASS_NAMES.index(v) for v in y9])
    del d, num
    gc.collect()
    print(f"  {len(y_iv):,} flux, {len(audc)} colonnes auditees"
          .replace(",", "\u202f"), flush=True)

    for s in sorted({g for _, g in manquants}):
        # Le decoupage se calcule une fois par graine, comme en cellule 5 :
        # sur 2,7 millions de lignes il n'est pas gratuit.
        itr, iva_, ite_ = split_de(y_iv, s)
        for m in [m for m, g in manquants if g == s]:
            t0 = time.time()
            try:
                RUNS[f"{iv}|{m}|seed{s}"] = un_run_e9(m, s, Xiv, y_iv, itr,
                                                      iva_, ite_)
                r = RUNS[f"{iv}|{m}|seed{s}"]
                print(f"  {m:<8} graine {s}  macro-F1 {r['macro_f1']:.4f}  "
                      f"FPR {100 * r['binary']['fpr']:.2f} %  "
                      f"({time.time() - t0:.0f} s)", flush=True)
                faits += 1
            except Exception as e:
                print(f"  {m:<8} graine {s}  echec : {e}", flush=True)
            finally:
                save_state(STATE)      # une deconnexion ne coute qu'un run
    del Xiv, y_iv
    gc.collect()

print(f"\n{faits} run(s) ajoutes cette session")

# --------------------------------------------------------------------------
# Ce que le tableau 13 pourra dire, detecteur par detecteur.
#
# Deux choses differentes peuvent arriver a un detecteur quand la fenetre
# raccourcit, et la section 6.4 les distingue explicitement. Un ECHEC DE
# GRAINE est un trou a l'interieur d'un meme intervalle : quatre runs a 1.0000
# et un a 0.8374, ce qui est arrive a LightGBM a 10 s. Un DECLIN est une baisse
# reguliere d'un intervalle au suivant, portee par toutes les graines, ce qui
# est arrive au DNN. Confondre les deux ferait dire au tableau 13 le contraire
# de ce que la 6.4 etablit, donc on les mesure separement.
#
# Une ligne ne devient une mesure que si les TROIS intervalles sont la : un
# detecteur robuste a 30 s et inconnu a 5 s n'est pas un detecteur robuste.
# --------------------------------------------------------------------------
SEUIL_TROU = .05


def trou_max(xs):
    """Le plus grand ecart entre deux valeurs voisines, une fois triees."""
    t = sorted(xs)
    return max((t[k + 1] - t[k] for k in range(len(t) - 1)), default=0.)


print(f"\n{'detecteur':<10}" + "".join(f"{iv + ' s':>10}"
                                       for iv in ("5", "10", "30"))
      + "   verdict pour le tableau 13")
for m in MODELES_E9:
    par_iv = {iv: [RUNS[f"{iv}|{m}|seed{s}"]["macro_f1"] for s in GRAINES_E9
                   if f"{iv}|{m}|seed{s}" in RUNS] for iv in ("5", "10", "30")}
    cols = "".join(f"{min(par_iv[iv]):>10.4f}" if par_iv[iv] else f"{'-':>10}"
                   for iv in ("5", "10", "30"))
    if any(len(par_iv[iv]) < len(GRAINES_E9) for iv in par_iv):
        print(f"{m:<10}{cols}   incomplet")
        continue

    # (a) un echec de graine : le trou est DANS un intervalle.
    graine = [(iv, trou_max(par_iv[iv])) for iv in par_iv
              if trou_max(par_iv[iv]) > SEUIL_TROU]
    # (b) un declin : les minima par intervalle baissent avec la fenetre.
    mins = [min(par_iv[iv]) for iv in ("30", "10", "5")]
    bas = min(mins)

    # Les deux peuvent coexister, et c'est le cas du DNN : quatre graines
    # groupees a 0.849 et une a 0.9879 a 30 s, ET un declin porte par toutes
    # les graines quand la fenetre raccourcit. Choisir l'un des deux
    # effacerait la moitie de ce que la 6.4 rapporte.
    dits = []
    if graine:
        # On rapporte les DEUX groupes que le trou separe, sans decider lequel
        # est l'anomalie : chez LightGBM a 10 s c'est le groupe bas qui l'est,
        # chez le DNN a 30 s c'est le groupe haut, et compter « les graines a
        # l'ecart » donnerait 1 dans un cas et 4 dans l'autre.
        iv, _ = max(graine, key=lambda x: x[1])
        t = sorted(par_iv[iv])
        k = max(range(len(t) - 1), key=lambda j: t[j + 1] - t[j]) + 1
        dits.append(f"splits at {iv} s: {k} seed(s) at "
                    f"{t[0]:.4f}\u2013{t[k - 1]:.4f} and {len(t) - k} at "
                    f"{t[k]:.4f}\u2013{t[-1]:.4f}")
    if mins[0] - mins[-1] > SEUIL_TROU:
        dits.append(f"declines from {mins[0]:.4f} at 30 s to {mins[-1]:.4f} "
                    "at 5 s")
    verdict = "; ".join(dits) if dits else f">= {bas:.4f} at every interval"
    print(f"{m:<10}{cols}   {verdict}")

print("\nLe FT-Transformer reste hors de portee : un ajustement a 60 s a")
print("demande 31 602 s, et les intervalles courts portent jusqu'a huit fois")
print("plus de flux. Sa ligne gardera « not measured », et le papier dira")
print("pourquoi plutot que de laisser la case muette.")
print("\nRenvoie e5_results.json.")
