# E6 — pourquoi une graine de LightGBM s'effondre à 10 s

**Demande.** Un rapport de limites objecte que le manuscrit qualifie l'effondrement
— une graine sur cinq à macro-F1 0,8374 à l'intervalle de 10 s, les quatre
autres au-dessus de 0,9999 — sans dire quel mécanisme algorithmique le
produit, et suggère trois pistes : artéfacts de binning d'histogrammes,
écrêtage de gradient, stochastique de sous-échantillonnage.

L'objection est fondée. « Un échec isolé d'un seul ajustement » **décrit**
l'événement ; ça ne l'explique pas.

## Ce qu'il faut établir en premier, et qui n'était écrit nulle part

**Dans tout ce papier, une graine est la graine du découpage stratifié.** Le
pipeline construit ses détecteurs avec `random_state=0` fixe et fait varier
`train_test_split(..., random_state=s)`. Vérifié dans
`colab/article1_pipeline.ipynb` et repris à l'identique par E5.

Conséquence, et c'est elle qui structure tout le reste : changer de graine
change **deux choses ensemble** —

1. la composition du jeu d'entraînement (et du test) ;
2. la grille d'histogramme de LightGBM, puisque ses bornes sont posées à
   partir d'un tirage de 200 000 lignes **de ce jeu d'entraînement**.

Sur GeNIS, les deux sont confondues. Aucune analyse des résultats archivés ne
peut les séparer.

## Ce que le script établit

`reproduce_binning.py`, 13 contrôles, tous passés.

### A. Deux des trois pistes du rapport sont hors de cause

La campagne fixe `n_estimators=300`, `num_leaves=63`, `learning_rate=0.1`
(`DEFAULTS_SK` du pipeline) et laisse le reste aux défauts de la librairie.
La recherche d'hyperparamètres n'a rien adopté de plus : `best_params` est
vide, la configuration déclarée atteignant déjà 1,0000 en validation.

Les défauts qui comptent :

```
subsample         = 1.0    subsample_freq = 0   ->  pas de bagging
colsample_bytree  = 1.0                         ->  pas de tirage de colonnes
subsample_for_bin = 200 000                     ->  bins poses sur un tirage
```

Le sous-échantillonnage de lignes et de colonnes est donc **éliminé**. Reste
le binning, qui était la première piste du rapport.

### B. La couverture du tirage suit l'intervalle, et le seul intervalle sans incident est le seul où elle est complète

| intervalle | entraînement | couverture des bins | part de bruteforce-ftp |
|---|---:|---:|---:|
| 5 s | 1 664 146 | 12,0 % | 0,121 % |
| **10 s** | **883 279** | **22,6 %** | **0,227 %** |
| 30 s | 346 471 | 57,7 % | 0,579 % |
| 60 s | 203 292 | **98,4 %** | 0,987 % |

À 60 s le tirage prend presque toutes les lignes : la grille y est quasi
déterminée par les données. C'est le seul intervalle où aucune graine ne
s'écarte. **La coïncidence rend l'hypothèse intéressante ; elle ne la
démontre pas** — à 5 s la couverture est encore plus faible et aucune graine
ne tombe.

### C. Le profil de l'échec est celui de l'entraînement, pas d'un test malheureux

| mesure | graine 3 | graine 1 |
|---|---:|---:|
| macro-F1 | 0,8374 | 0,9999 |
| exactitude globale | 0,9893 | 0,99999 |
| ROC-AUC binaire | **0,9604** | 1,0000 |
| taux de faux positifs | 7,71 % | 0,014 % |
| temps d'ajustement | **335,7 s** | 291,4 s |

La dégradation suit la rareté des classes (Spearman ρ = 0,93 sur les neuf) :
bruteforce-ftp (0,227 % du corpus) tombe à 0,0561, bruteforce-ssh (0,589 %) à
0,6439, tandis que les cinq classes les plus communes restent au-dessus de
0,99.

Deux lectures ferment des portes :

- **le ROC-AUC** tombe de 1,0000 à 0,9604. Un tirage de test malheureux
  déplacerait le seuil, pas l'ordonnancement. Le modèle a perdu la capacité
  d'ordonner ces flux ;
- **l'ajustement est 15 % plus long** à budget d'arbres fixe et sur des
  données de même taille. C'est une autre structure d'arbres, pas une
  exécution plus lente.

### D. Le binning seul, à découpage fixe, produit exactement cette forme

Une classe rare à 0,23 % du corpus, séparée par un intervalle d'un millième
de l'axe, découpage calculé une fois et **immobile** entre les deux bras.
Seul `subsample_for_bin` change.

| bras | moyenne | écart-type sur 16 graines | étendue |
|---|---:|---:|---:|
| binning échantillonné, couverture de 10 s | 0,3622 | **0,1317** | **0,4498** |
| binning déterministe | 0,5063 | **0,0000** | **0,0000** |

Valeurs mesurées :

```
bras A, echantillonne   moyenne 0.3622  ecart-type 0.1317  etendue 0.4498
  0.092 0.116 0.246 0.273 0.331 0.337 0.353 0.378
  0.378 0.389 0.404 0.462 0.467 0.489 0.538 0.542

bras B, deterministe    moyenne 0.5063  ecart-type 0.0000  etendue 0.0000
  0.506 x 16
```

Trois lectures, et la troisième n'était pas attendue :

- **l'amplitude** — le binning seul fait varier le F1 de la classe rare de
  **0,45** d'une graine à l'autre, découpage identique ;
- **la forme** — les valeurs se groupent en paquets séparés par un trou de
  **0,130**, contre un écart médian de 0,022 entre valeurs voisines. Ce n'est
  pas une dispersion autour d'une moyenne. C'est exactement ce qu'on observe
  sur GeNIS, où aucun run n'a scoré entre 0,84 et 0,99 ;
- **le binning déterministe est aussi le meilleur** : 0,5063 contre une
  moyenne de 0,3622 en échantillonné, et au-dessus des seize valeurs sauf
  deux. Poser les bornes sur toutes les lignes ne fait pas que stabiliser, ça
  améliore la classe rare.

Binning déterministe : les seize graines rendent **exactement** la même
valeur. La graine ne pilote alors plus rien du tout — **sur ces données
synthétiques**, où le binning est la seule source d'aléa qui reste. C'est une
preuve de suffisance : ce mécanisme *peut* produire la forme observée. La
section suivante montre que sur GeNIS, ce n'est pas lui qui la produit.

## Ce que le script n'établit pas

**Que c'est ce qui est arrivé à la graine 3.** Sur GeNIS, composition du
découpage et grille d'histogramme bougent ensemble ; ce script les sépare sur
des données synthétiques, pas sur le corpus.

## L'expérience qui tranche — faite, et elle tranche contre l'hypothèse

`colab/e6_binning_deterministe.ipynb`, cinq ajustements à 10 s, mêmes cinq
découpages, `subsample_for_bin` porté à 883 281 pour 883 279 lignes
d'entraînement. Rien d'autre ne change.
`verify_e6_deterministe.py` : **20 contrôles sur 20**.

### Le témoin, qui rend la comparaison lisible

Une graine saine rejouée avec le binning d'origine rend
`0.9998729764672524` — la valeur publiée **au dernier chiffre**. Sans ce
contrôle, tout écart entre les deux bras pourrait venir de l'environnement
Colab. Il vient du binning.

### Le résultat

| graine | publié | déterministe | |
|---|---:|---:|---|
| 1 | 0,9999 | 1,0000 | |
| 2 | 1,0000 | **0,4193** | ← s'effondre |
| 3 | **0,8374** | 1,0000 | ← guérit |
| 4 | 1,0000 | **0,8106** | ← s'effondre |
| 5 | 1,0000 | 1,0000 | |

C'est la **troisième** issue du tableau que ce document annonçait : la liste
change sans que les effondrements disparaissent. Et elle est plus tranchée
que prévu — il y en a **deux au lieu d'un**, et le pire tombe à 0,4193 contre
0,8374.

### Les nouveaux échecs n'ont pas la signature de l'ancien

| graine | macro-F1 | ROC-AUC | FPR | ajustement |
|---|---:|---:|---:|---:|
| 2 | 0,4193 | **0,5143** | **0,9571** | 229 s |
| 4 | 0,8106 | 0,9458 | 0,1074 | 231 s |
| sains | ≥ 0,9999 | 1,0000 | 0,0000 | 236 s en moyenne |

La graine 2 est à **0,5143 de ROC-AUC**, c'est-à-dire au hasard, avec 95,7 %
de faux positifs et trois classes à exactement zéro. Ce n'est plus « une
classe rare perdue », c'est un ajustement dégénéré.

Et surtout : **aucun des deux n'a l'ajustement allongé** qui marquait l'échec
publié (336 s contre 291 s). Les nouveaux échecs ne sont pas le même
phénomène déplacé.

## Conclusion : le candidat principal est éliminé

Le binning n'est pas la cause. Il produit la bonne *forme* sur données
synthétiques — ça reste vrai, et c'est une preuve de suffisance —, mais sur
GeNIS le rendre déterministe ne retire rien.

**Ce que ça aurait coûté de s'arrêter au premier volet :** nous aurions
recommandé de fixer `subsample_for_bin`. Sur ce corpus, ce correctif fait
passer de un effondrement à deux et abaisse le pire de 0,84 à 0,42. La
recommandation aurait empiré les choses.

C'est un argument pour la thèse du papier lui-même : un résultat qui tient
sur un seul essai ne tient pas.

## Ce que le manuscrit dit aujourd'hui

Deux paragraphes portent ce qui précède, y compris — et surtout — le
résultat négatif, et lisent leurs chiffres dans les deux fichiers de
résultats : « What makes one fit fail and not the others » en §6.4 et « One
run-to-run failure resists explanation » en §9.

Ils ont été **réécrits** quand le notebook est revenu : leur première version
annonçait l'expérience comme à faire et penchait vers le binning. Ce qu'ils
disent aujourd'hui est que le candidat est éliminé et qu'aucun mécanisme ne
le remplace.

**Défaut trouvé en chemin, que le rapport ne signalait pas :** la §8 décrivait
encore l'effondrement comme « one LightGBM seed out of three … while the other
two stayed near 1.0000 », alors que le Tableau 6 porte cinq graines depuis E5.
Corrigé (`d869fbc`).

## Entrées

- `experiments/e6/e6_deterministe_results.json` — les cinq ajustements déterministes
- `paper/article1_results.json` — les runs par intervalle, `interval_stats`,
  la trace d'HPO
- `colab/article1_pipeline.ipynb` — la construction des détecteurs et le
  découpage, pour établir ce que la graine pilote
