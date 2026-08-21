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

## 6. État des runs

**179 sur 180.** Il ne manque que `ftt|corrigee|strat_seed5`, qui demande un
GPU — le FT-Transformer coûte 228 à 610 s par ajustement sur GPU et des heures
sur CPU.

Les quatre autres manquants ont été faits sur CPU et relevés depuis la console
(`logreg#tuned` 0,9956, `nb#tuned` 0,5019, `knn#tuned` 0,9945, `dnn#tuned`
0,9836). Ils sont marqués `"source": "console, session CPU"` dans le JSON :
seul le macro-F1 en a été conservé, et la provenance doit rester traçable.

*Note de comptabilité :* j'avais signalé `nb#tuned` comme hors plage avec une
tolérance de 0,004. C'était un faux positif — l'étendue de `nb#tuned` sur cinq
graines dans la campagne publiée est de **0,0362**, dix fois celle des autres
modèles, et `GaussianNB` n'a de toute façon aucun générateur aléatoire.

**14 configurations sur 15 ont désormais leurs cinq graines**, `ftt` étant la
seule à quatre. Sa dispersion stratifiée est de 0,00008 sur ces quatre
(0,9998 / 0,9998 / 0,9998 / 1,0000), donc la cinquième ne déplacera pas sa
moyenne au quatrième chiffre — mais le tableau doit dire *n* = 4 tant qu'elle
manque.

## 6bis. Ce que la republication demande encore

| élément | disponible ? |
|---|---|
| Tableau 2, colonnes `full` et `clean` | **inchangées** — elles n'utilisent pas la liste noire |
| Tableau 2, colonnes auditées | oui, sauf le *n* de `ftt` |
| Tableau 7 (calibration + recherche) | ECE et température : oui. Essais, temps et Δval : **inchangés**, voir ci-dessous |
| Tableau 8 (ECE sous les deux protocoles) | oui, entièrement |
| Tableau 10 (coût d'inférence) | **non — la cellule de coût n'a jamais tourné** |

**Une réserve à écrire pour le bras réglé.** E8 applique à la condition
corrigée les `best_params` de la campagne publiée, qui avaient été cherchés sur
la condition à douze colonnes. Le bras `#tuned` mesure donc *les
hyperparamètres publiés appliqués à la condition corrigée*, et non un
réajustement sur celle-ci. C'est défendable — ça isole l'effet du retrait de la
colonne de celui d'un nouveau réglage — mais le papier doit le dire.

## Entrées

- `experiments/e8/e8_results.json`
- `paper/article1_results.json`


---

## 7. Un bug dans le notebook E8 : l'objectif du calage de température

Trouvé en republiant les Tableaux 7 et 8. Le pipeline ajuste la température en
minimisant la **NLL** sur une grille de 80 points
(`colab/e3_calibration_residual.py`, fonction `temperature`) ; la fonction
que j'ai écrite dans E8 minimise l'**ECE** sur une grille de 100 points au pas
de 0,05. **Objectif différent.**

La preuve : sur le bras `publiee`, qui devrait reproduire le Tableau 7, E8
donne pour naive Bayes T = 0,150 là où le papier a 5,821 et où E3-A avait
retrouvé 5,000. Les deux extrémités opposées de la grille — ce n'est pas un
artefact de grille.

| colonne | républiable depuis E8 ? |
|---|---|
| Tableau 7, `ECEraw` | **oui** — l'ECE brut ne dépend pas de la température |
| Tableau 7, `T` et `ECEcal` | **non** |
| Tableau 8, `ECE stratified`, `ECE temporal`, `ratio` | **oui** |
| Tableau 8, `T temporal`, `ECE temporal, calibrated` | **non** |

**Décision : les Tableaux 7 et 8 sont laissés en l'état.** Un tableau dont
certaines colonnes viennent de la liste à treize et d'autres de la liste à
douze induirait plus en erreur qu'un tableau non touché. Seul le Tableau 2 est
republié.

**Le correctif ne demande aucun réentraînement** : les matrices de
probabilités d'E8 sont conservées dans `e8_probs/`, et la température se
recalcule dessus avec l'objectif du pipeline.

### Ce que la recomputation changera, et qu'il faut anticiper

Les ECE bruts, eux, sont déjà mesurés et ils déplacent deux affirmations du
manuscrit :

- **§6.5 : « expected calibration error is at most 0.0009 for every model
  except naive Bayes ».** Sous la liste corrigée le maximum est **0,0084**, et
  il est porté par la régression logistique — dont l'ECE stratifié est passé de
  0,000313 à 0,008429, soit ×27.
- **§6.5 et conclusion : « ten of the eleven detectors » se dégradent sous le
  protocole temporel.** Ce sont maintenant **neuf sur onze** : la régression
  logistique **s'améliore** (rapport 0,4×), parce que c'est son bras stratifié
  qui s'est dégradé, pas son bras temporel qui a progressé.
- Les rapports des trois mieux calibrés passent de « 241 à 457 » à
  **« 146 à 1403 »**.


---

## 8. Ce qui est entré dans le manuscrit, et ce qui attend

### Entré

| élément | source |
|---|---|
| **Tableau 2** | E8, condition corrigée, entièrement |
| **Tableau 13**, colonne macro-F1 et ordre des lignes | E8 |
| **Figures 5, 10, 18** | redessinées, `paper/regen_e8_figures.py` |
| légendes des Figures 5, 10, 18 | recalculées |
| prose des §6.1, §6.3, §8 citant le Tableau 2 | recalculée |

Les Figures 5, 10 et 18 sont les seules que l'on puisse refaire sans les
matrices de probabilités. Elles remplacent les images d'origine **en place** :
le document les portait sous des noms de hachage, qu'on écrase sans toucher
aux relations ni aux `extent` déclarés.

### En attente, et pourquoi les cases sont vides plutôt que périmées

Le Tableau 13 a **deux colonnes vides** : le débit demande une mesure de coût
sur 54 colonnes, la température demande le recalage avec l'objectif du
pipeline. Une case vide n'induit personne en erreur ; une valeur de la
condition à douze posée à côté d'une valeur de la condition à treize, si.

| bloqué par | débloque |
|---|---|
| recalage des températures (NLL) | Tableaux 7, 8, 13 (température), §6.5 |
| mesure de coût (54 colonnes) | Tableau 10, 13 (débit), Figure 14, §8 |
| `e8_probs/` | Figures 9 (McNemar) et 11 (bootstrap) |
| `ftt` graine 5 | le *n* = 4 du Tableau 2 |

### Ce que la Figure 18 montre maintenant

C'est le changement le plus visible du manuscrit. Sous la liste publiée, la
perte se dispersait : « chaque détecteur perd ailleurs ». Sous la liste
corrigée elle **se concentre sur `dos-hulk` et `dos-slowloris`**, où le DNN,
XGBoost, LightGBM, k-NN et la forêt aléatoire tombent tous sous 0,93. La
cellule la plus basse est la forêt aléatoire sur `dos-hulk` à **0,814**, contre
0,957 pour la pire classe du détecteur de tête — et **onze de ces douze
cellules étaient au-dessus de 0,93** sous la liste publiée.

L'échelle de couleur a dû descendre de 0,90 à 0,80 : la légende publiée
affirmait que toute valeur montrée était au-dessus de 0,90, ce qui n'est plus
vrai.
