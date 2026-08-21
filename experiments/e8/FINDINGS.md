# E8 — la condition auditée republiée sur la liste corrigée

**`verify_e8.py` : 19 contrôles sur 19.** 180 runs sur 180.

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
que j'ai écrite dans E8 minimisait l'**ECE** sur une grille de 100 points au
pas de 0,05. **Objectif différent.**

Le correctif n'a demandé aucun réentraînement : les matrices de probabilités
d'E8 étaient conservées, et la température s'y recalcule avec l'objectif du
pipeline (`colab/e8bis_recalage_temperature.py`). Les 180 runs portent
désormais `temperature` (NLL, la bonne) et `temperature_ece` (l'ancienne,
gardée pour que l'écart reste lisible).

### Le témoin s'est trompé de quantité avant de se tromper de verdict

La première version comparait **T** au Tableau 7 publié et annonçait un écart
maximal de **0,821**, donc l'échec. Les deux moitiés du contrôle étaient
fausses :

- **la cible.** Le T publié pour le bayésien naïf est 5,821. La grille du
  pipeline s'arrête à **5**. Le recalage rend exactement 5,000 — c'est-à-dire
  **la valeur d'E3-A**, la recomputation que la §6.5 déclare déjà comme la
  bonne. Tout l'écart de 0,821 est un plafond de grille ;
- **la quantité.** T est un paramètre *intermédiaire*, posé sur une surface
  très plate. Deux jeux de probabilités quasi identiques y donnent des T
  éloignés sans que rien de rapporté ne bouge. Ce qu'il faut contrôler est ce
  que le tableau **rapporte** : l'ECE après calage.

Le témoin corrigé teste l'ECE calibrée contre E3-A et écarte les T posés sur
une borne de grille, dont l'écart ne renseigne pas sur la procédure.

### Ce qu'il donne — et le contraste n'était pas attendu

`verify_e8.py`, contrôle F, calculé depuis les fichiers versionnés :

| | paires | écart max | |
|---|---:|---:|---|
| ECE **brute**, les deux protocoles | 22 | **0,0031** | `rnn\|temporal` |
| ECE **calibrée**, stratifié | 7 | **0,0002** | `rnn\|strat_seed1` |
| ECE **calibrée**, temporel | 7 | **0,0075** | `rf\|temporal` |

L'ajustement sous-jacent se rejoue partout. Ce qui ne se rejoue serré que
d'un côté, c'est l'ECE **après** calage : sur le bras temporel, l'optimum de
NLL se déplace assez pour déplacer l'ECE de 0,0075, alors que l'ajustement
qui le porte se rejoue à 0,0031.

**C'est le calage qui amplifie, pas l'ajustement.** La dernière colonne du
Tableau 8 est donc la moins stable du manuscrit, et sa légende le dit
maintenant — avec les deux chiffres, pas avec une formule prudente.

## 8. Ce qui est entré dans le manuscrit

| élément | source |
|---|---|
| **Tableau 2** | E8, condition corrigée, entièrement |
| **Tableau 7** (T, ECEraw, ECEcal) | E8 recalé, condition corrigée |
| **Tableau 8**, entièrement | E8 recalé, condition corrigée |
| **Tableau 10**, colonne macro-F1 | E8, condition corrigée |
| **Tableau 13**, macro-F1, ordre des lignes, température | E8 recalé |
| **Figures 5, 10, 18** | redessinées, `paper/regen_e8_figures.py` |
| légendes des Figures 5, 10, 18 | recalculées |
| prose des §6.1, §6.3, §6.5, §8 | recalculée |

Deux réserves écrites dans les légendes, parce qu'elles ne se devinent pas :

- **Tableau 7.** T est ajusté sur une grille bornée à 0,05 et 5, donc la
  valeur du bayésien naïf est *au plafond*. Et les colonnes essais, temps et
  Δval viennent de la recherche publiée, conduite sur la condition à douze
  colonnes : le bras `#tuned` mesure *les hyperparamètres publiés appliqués à
  la condition corrigée*, pas un réajustement sur celle-ci.
- **Tableau 8.** Le chiffre de stabilité ci-dessus.
- **Tableau 10.** La colonne macro-F1 vient de la condition corrigée, sur 54
  colonnes ; latence, débit et taille ont été mesurés **avant** la correction,
  sur 55 colonnes, et ne sont pas remesurés. La légende annonçait déjà
  « audited condition » alors que sa colonne macro-F1 portait encore les
  valeurs à douze — le bayésien naïf s'y trompait de **0,1028**. Nommer la
  provenance de chaque colonne vaut mieux qu'une colonne périmée sous une
  légende qui affirme le contraire.

La §8 lisait ce tableau à voix haute et affirmait donc le contraire de ce
qu'il montre désormais. Trois phrases corrigées : XGBoost n'est plus « à
égalité en tête » (LightGBM est seul au-dessus, de 0,0001), la régression
logistique passe de 0,9990 à 0,9963, et la marge temporelle du
FT-Transformer passe de « 0,9966 contre 0,9888 » à **0,9901 contre 0,9666**
— elle *grandit*, de 0,0078 à 0,0235.

### Les trois affirmations de la §6.5 qui ont bougé

| avant | après |
|---|---|
| ECE ≤ 0,0009 « pour tout modèle sauf le bayésien naïf » | ≤ **0,0015**, sauf la régression logistique **et** le bayésien naïf — l'erreur stratifiée de la logistique passe de 0,0003 à 0,0084 quand la colonne identifiante est retirée |
| « dix des onze détecteurs » se dégradent en temporel | **neuf sur onze**. Le onzième est la régression logistique, et elle va dans l'autre sens (rapport 0,4×) — non parce que son bras temporel progresse, mais parce que son bras stratifié est monté le rejoindre |
| rapports des trois mieux calibrés : 241 à 457 | **146 à 1403** |

Les températures des ensembles d'arbres ne sont **plus au plancher** de la
grille : XGBoost 0,85, LightGBM 1,46, forêt aléatoire 0,39. Retirer la colonne
identifiante a retiré ce qui rendait leurs postérieures quasi déterministes.

Ce qui **tient** : les trois détecteurs les mieux calibrés en stratifié
(`xgboost`, `lightgbm`, `ftt`) restent exactement les trois qui se dégradent
le plus. Même ensemble des deux côtés.

## 9. Ce qui attend encore, et pourquoi les cases sont vides

Une case vide n'induit personne en erreur ; une valeur de la condition à douze
posée à côté d'une valeur de la condition à treize, si.

| bloqué par | débloque |
|---|---|
| mesure de coût sur 54 colonnes (CPU, ~10 min) | colonnes de coût du Tableau 10, colonne débit du 13, axe horizontal de la Figure 14 |
| `e8_probs/` | Figures 9 (McNemar) et 11 (bootstrap) |

**La graine 5 du `ftt` est arrivée**, donc le Tableau 2 porte ses cinq graines
partout et le marqueur *n* = 4 a disparu de lui-même : il était calculé, pas
écrit à la main.

**La Figure 14 reste à redessiner.** Son axe vertical est le macro-F1
temporel, qui a changé pour tous les détecteurs ; son axe horizontal est le
débit, qui n'est pas remesuré. Sa légende est déjà juste au chiffre près
(0,0020 pour l'écart logistique–FT-Transformer), mais les points, eux, sont
encore placés à l'ancienne hauteur.

## 10. Ce que la Figure 18 montre maintenant

C'est le changement le plus visible du manuscrit. Sous la liste publiée, la
perte se dispersait : « chaque détecteur perd ailleurs ». Sous la liste
corrigée elle se rassemble sur `dos-hulk` et `dos-slowloris`, où le DNN,
XGBoost, LightGBM, k-NN et la forêt aléatoire tombent tous sous 0,93. La
cellule la plus basse est la forêt aléatoire sur `dos-hulk` à **0,814**, contre
0,957 pour la pire classe du détecteur de tête — et **onze de ces douze
cellules étaient au-dessus de 0,93** sous la liste publiée.

L'échelle de couleur a dû descendre de 0,90 à 0,80 : la légende publiée
affirmait que toute valeur montrée était au-dessus de 0,90, ce qui n'est plus
vrai.
