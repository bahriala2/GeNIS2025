#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pourquoi les deux mesures de cout ne sont pas comparables.

Le tableau 10 du manuscrit porte des debits mesures sur la condition a 55
colonnes. E8 a remesure sur 54. Les deux jeux different d'un facteur 0.42 a
13.4 selon le detecteur, dans les deux sens -- ce qu'une colonne retiree sur
55 ne peut pas produire.

Ce script etablit UNE des causes, et il l'etablit par la mesure et non par
lecture de code : les deux campagnes n'utilisent pas le meme protocole de
debit.

    papier   for _ in range(20): predict_proba(lot_de_512)
    E8       predict_proba(lot_de_10240)          # une seule fois

Sur un estimateur parallele, chaque appel paie un demarrage du backend
joblib. Le protocole du papier le paie vingt fois, celui d'E8 une fois. La
meme remarque vaut pour les quatre modeles Keras, dont chaque appel a
predict() paie un surcout d'API fixe que le manuscrit chiffre lui-meme a
77 ms : le papier fait vingt appels de 512 lignes, E8 un appel de 10240
lignes decoupe en interne.

Ce qui est en jeu. La legende publiee du tableau 10 affirme que la colonne
de debit « amortises that overhead and is the one on which we base the
comparison ». Pour les estimateurs qui ont un surcout par appel, c'est
l'inverse : la boucle le paie a chaque tour.

Ce que ce script N'etablit PAS : que le protocole explique TOUT l'ecart. Le
k-NN va dans l'autre sens, et les deux sessions n'ont pas tourne sur la meme
machine. Il etablit qu'une part substantielle de l'ecart est un artefact de
mesure, ce qui suffit a interdire de recopier une colonne dans l'autre.

Sans TensorFlow ici, seule la moitie scikit-learn est mesuree. La moitie
Keras se lit dans le manuscrit lui-meme, qui chiffre le surcout par appel.
"""
import sys
import time

from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

N, F, C = 60000, 54, 9
X, y = make_classification(n_samples=N, n_features=F, n_informative=20,
                           n_classes=C, n_clusters_per_class=1, random_state=0)
X = X.astype("float32")
Xtr, ytr, Xte = X[:40000], y[:40000], X[40000:]
LOT = Xte[:512 * 20]

# Memes reglages que les deux campagnes : n_jobs=2 pour la foret et le k-NN.
MODELES = [("foret aleatoire",
            RandomForestClassifier(n_estimators=300, n_jobs=2, random_state=0)),
           ("k-NN",
            KNeighborsClassifier(n_neighbors=5, n_jobs=2))]

print(f"{'modele':<18}{'20 x 512 (papier)':>20}{'1 x 10240 (E8)':>18}{'rapport':>10}")
rapports = []
for nom, mdl in MODELES:
    mdl.fit(Xtr, ytr)

    def boucle():
        return [mdl.predict_proba(Xte[i * 512:(i + 1) * 512]) for i in range(20)]

    def unique():
        return mdl.predict_proba(LOT)

    debits = []
    for f in (boucle, unique):
        f()                                    # chauffe : on ne mesure pas le premier
        t0 = time.perf_counter()
        f()
        debits.append(len(LOT) / (time.perf_counter() - t0))
    r = debits[1] / debits[0]
    rapports.append((r, nom))
    print(f"{nom:<18}{debits[0]:>15.0f} f/s{debits[1]:>13.0f} f/s{r:>9.1f}x")

print()
pire = max(rapports)
print(f"Le seul changement de protocole vaut jusqu'a {pire[0]:.1f}x sur "
      f"{pire[1]},")
print("machine identique, modele identique, donnees identiques.")
print()
print("Consequence pour le manuscrit : les colonnes de cout du tableau 10 et")
print("celles d'E8 ne peuvent pas etre melangees ni substituees l'une a")
print("l'autre, et la phrase de la legende publiee sur l'amortissement du")
print("surcout doit etre revue.")

# Le controle n'a de valeur que si l'effet est net : sous 2x, on ne pourrait
# pas le distinguer du bruit de mesure d'une machine partagee.
sys.exit(0 if pire[0] >= 2 else 1)
