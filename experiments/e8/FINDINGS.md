# E8 — la condition auditée republiée sur la liste corrigée

**`verify_e8.py` : 15 contrôles sur 15.** 177 runs sur 180 ; les trois
manquants sont la graine 5 de trois configurations, côté liste corrigée.

---

## 1. `Offset` n'est pas positionnel — la règle tranche contre le soupçon

La règle avait été écrite **avant** de voir le résultat : si la corrélation de
rang entre `Offset` et l'ordre de capture dépasse 0,95 dans chaque fichier, il
rejoint la liste positionnelle.

**Corrélation de rang minimale : 0,126.** Très loin de 0,95.

`Offset` n'est donc pas le décalage d'enregistrement que son nom suggère. Il
reste dans la condition auditée, et la §9 rapporte son AUC binaire de 0,9379
comme une **anomalie non résolue**.

**La liste noire passe à treize entrées, `IdleTime` seul ajouté.**

C'est le résultat que je voulais de ce dispositif : le soupçon était sérieux
(AUC binaire 0,94, τ = 3,0), et c'est la mesure qui a décidé, pas la prudence.

## 2. Ce qui rend la comparaison lisible

| contrôle | résultat |
|---|---|
| modèles quasi déterministes contre le papier | **0,0019** (tolérance 0,003) ✓ |
| bande de reproductibilité **intra-session**, 3 ajustements identiques | **0,0019** |

La bande intra-session est portée entièrement par le CNN (0,9982 / 0,9963 /
0,9963). `dnn`, `rnn` et `ftt` rendent **exactement** la même valeur trois fois.

**Les deux bras ont tourné dans la même session**, donc c'est bien la bande
intra-session qui borne ce qui est attribuable à la correction — pas la
dispersion entre sessions, qui est plus large.

## 3. Ce que la correction coûte

| | écart maximal hors bayésien naïf |
|---|---:|
| stratifié | **0,0040** (k-NN) |
| temporel | **0,0263** (k-NN) |

Rapport **×7**, la même signature que les douze autres raccourcis.

Les **cinq plus gros écarts** portent sur `knn`, `lightgbm`, `knn#tuned`, `rf`
et `xgboost` — tous des modèles qui se rejouent au quatrième chiffre. Le
résultat repose sur le sol le plus ferme.

Le bayésien naïf s'effondre (`nb#tuned` : −0,2235 en stratifié), ce que la §6.2
prédit déjà : un classifieur qui suppose l'indépendance conditionnelle est le
plus sensible aux colonnes corrélées restantes.

Seul `cnn` a un écart temporel (+0,0018) **sous la bande** : non attribuable.

## 4. Le classement temporel — la conclusion du papier se renforce

| rang | liste publiée (12) | liste corrigée (13) |
|---:|---|---|
| 1 | logreg#tuned 0,9950 | logreg#tuned 0,9928 |
| 2 | logreg 0,9949 | **ftt 0,9901** |
| 3 | **lightgbm 0,9906** | logreg 0,9881 |
| 4 | rnn 0,9892 | cnn 0,9848 |
| 5 | **xgboost 0,9888** | rnn 0,9837 |
| 6 | dnn 0,9887 | dnn 0,9773 |
| 7 | knn#tuned 0,9851 | **xgboost 0,9666** |
| 8 | knn 0,9837 | **lightgbm 0,9649** |
| … | | |
| 12 | rf 0,9758 | rf 0,9530 |

**LightGBM passe de la 3ᵉ à la 8ᵉ place, XGBoost de la 5ᵉ à la 7ᵉ.** La thèse
« les ensembles boostés quittent le sommet sous protocole temporel » n'est pas
seulement préservée : elle est bien plus nette qu'avec la liste publiée.

Un modèle linéaire mène toujours, et le corpus reste saturé sous le protocole
stratifié (les trois ensembles ≥ 0,999).

## 5. La limite à écrire : le FT-Transformer

| | macro-F1 temporel |
|---|---:|
| publié | 0,9966 |
| E8, liste publiée | 0,9779 — **écart au papier 0,0187** |
| E8, liste corrigée | 0,9901 — gain intra-session **+0,0122** |

`ftt` est le **seul détecteur qui gagne** à la correction, et il remonte de la
10ᵉ à la 2ᵉ place. Mais l'écart de cette session au papier (0,0187) **dépasse
l'effet mesuré** (0,0122).

**Ce que le papier peut dire :** dans une session où les deux bras sont
comparables, retirer `IdleTime` améliore le FT-Transformer et le ramène au
sommet. **Ce qu'il ne peut pas dire :** que 0,9901 est une amélioration sur le
0,9966 publié. Les deux doivent figurer.

Cette non-reproductibilité inter-session du `ftt` est elle-même à rapporter :
le papier ne quantifie nulle part la reproductibilité de ses détecteurs
neuronaux d'un environnement à l'autre.

## 6. Runs manquants

`dnn#tuned`, `ftt` et `knn#tuned`, graine 5, liste corrigée — le GPU a été
retiré au runtime. Toutes les moyennes ci-dessus sont calculées sur les
**graines communes aux deux listes**, donc sur une base identique de part et
d'autre. Reste à décider avant soumission : finir ces trois ajustements pour
un tableau uniforme à cinq graines, ou ramener tout le tableau à quatre.

## Entrées

- `experiments/e8/e8_results.json`
- `paper/article1_results.json`
