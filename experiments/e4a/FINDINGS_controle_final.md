# Le contrôle final : la liste noire issue du seul audit imbriqué

`python experiments/e4a/verify_nested_blacklist.py` → **19 contrôles sur 19**.

La demande était : produire au moins un contrôle avec la liste noire générée exclusivement
par l'audit imbriqué, puis montrer que les conclusions principales restent inchangées.

## Le résultat n'est pas une concordance, c'est une identité

En classant les 37 colonnes éligibles par leur τ imbriqué et en coupant **au plus grand
écart du classement** — la règle que la section 4.3 énonce, et qui ne sait pas combien de
colonnes attendre — on obtient :

```
['Dur', 'Max', 'Mean', 'Min', 'RunTime', 'SIntPkt', 'SIntPktMax', 'Sum']
```

soit **exactement la liste publiée, colonne pour colonne**. La condition auditée entraînée
sur la liste imbriquée *est* la condition auditée du papier. Chaque chiffre déjà publié est
donc ce contrôle : il n'y a pas de réentraînement à faire, il y a une identité à établir.

La coupure n'est pas fragile : l'écart retenu vaut 0.0621, le suivant 0.0517, soit un
rapport de 1.20. Et le seuil littéral τ < 0.50 n'exclut rien sur l'imbriqué (minimum
0.6229), ce que la section 4.3 disait déjà.

## Une identité peut sembler commode : on l'encadre

Les deux lectures dégradées du même audit sont **déjà entraînées** dans E4c.

| lecture de l'audit imbriqué | liste obtenue | variante E4c |
|---|---|---|
| 1 — rang + plus grand écart | 8 colonnes | = la campagne publiée |
| 2 — rang + écart suivant | 6 colonnes de durée | `tau040` |
| 3 — seuil littéral τ < 0.50 | aucune | `clean` |

Écart maximal au macro-F1 publié, hors bayésien naïf :

| protocole | lecture 2 | lecture 3 |
|---|---|---|
| stratifié | 0.0009 (CNN) | 0.0012 (CNN) |
| temporel | 0.0046 (CNN) | 0.0217 (DNN) |

## Les conclusions principales, sous les trois lectures

| conclusion | lecture 1 | lecture 2 | lecture 3 |
|---|---|---|---|
| corpus saturé en stratifié (XGB, LGBM, RF ≥ 0.9999) | ✔ | ✔ | ✔ |
| les deux ensembles boostés hors du podium temporel | 4ᵉ et 5ᵉ | 4ᵉ et 5ᵉ | 5ᵉ et 6ᵉ |
| ECE temporel ≫ ECE stratifié | ✔ | ×42 médian | ×36 médian |

Le raccourci d'horodatage et la cécité de l'attribution ne dépendent d'aucune liste : ce
sont des sondes et une propriété de l'audit, pas des modèles entraînés.

## Ce qui bouge, et qu'il faut écrire

**L'ordre à l'intérieur du groupe de tête permute** selon la lecture :

```
lecture 1 : cnn > logreg > rnn > lightgbm > xgboost
lecture 2 : rnn > logreg > cnn > lightgbm > xgboost
lecture 3 : dnn > cnn > rnn > logreg > lightgbm
```

Ce n'est pas une contradiction, c'est une confirmation. Les sections 6.1 et 6.8 déclarent
déjà ce groupe **statistiquement indistinguable** — 11 paires non significatives sous
McNemar, 4 sous bootstrap apparié temporel — et la section 6.3 dit explicitement qu'« aucun
des six premiers ne doit être lu comme établi au-dessus d'un autre ». Un ordre qui permute
sous une perturbation de 0.005 est exactement ce que cette déclaration prédit. Si l'ordre
avait été stable, il aurait fallu se demander pourquoi les tests ne le voyaient pas.

L'ensemble des détecteurs apparaissant dans les trois premiers, toutes lectures confondues,
se limite à quatre : CNN, DNN, logreg, RNN. Les deux ensembles boostés n'y entrent jamais.

## Où c'est écrit dans le manuscrit

Section 4.3, paragraphe « The control on the blacklist the nested audit produces alone »,
inséré après le paragraphe qui décrit l'audit imbriqué.
