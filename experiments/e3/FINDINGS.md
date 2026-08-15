# E3 : calibration sous les deux protocoles, et audit residuel

Source : `e3_results.json`, calcule depuis `probs/`, `frozen_splits_60s.npz` et
`cache/slice60.npz`, sans reentrainement.

## A. La calibration se degrade sous le protocole temporel

L'article ne mesurait la calibration que sous le protocole stratifie, alors que
« Calibration » figure dans son titre. Elle est maintenant mesuree sous les deux.

| Detecteur | ECE stratifie | ECE temporel | facteur |
|---|---|---|---|
| LightGBM | 0.000018 | 0.008319 | **457x** |
| FT-Transformer | 0.000042 | 0.017389 | **410x** |
| XGBoost | 0.000025 | 0.006069 | **241x** |
| Foret aleatoire | 0.000150 | 0.017870 | 119x |
| k-NN | 0.000490 | 0.012487 | 25x |
| Regression log. | 0.000367 | 0.004474 | 12x |
| RNN | 0.000636 | 0.006422 | 10x |
| DNN | 0.000864 | 0.007268 | 8x |
| 1D CNN | 0.000438 | 0.003113 | 7x |
| Bayesien naif | 0.187945 | 0.228080 | 1x |

**Dix detecteurs sur onze se degradent.** Le onzieme est la baseline de classe
majoritaire, dont l'ECE ne depend pas du protocole.

Deux lectures. D'abord, la calibration quasi parfaite que l'article rapporte est
une propriete du protocole stratifie et non du detecteur : sous un protocole qui
demande de generaliser dans le temps, l'ECE de LightGBM passe de 1.8e-5 a 8.3e-3.
Ensuite, l'ordre des detecteurs change : les trois modeles les mieux calibres
sous le stratifie, les arbres boostes et le FT-Transformer, sont ceux qui se
degradent le plus.

La temperature calee raconte la meme chose. Sous le stratifie elle vaut 0.05 pour
les arbres boostes, plancher de la grille, ce qui signale des posterieurs quasi
deterministes. Sous le temporel elle remonte a 0.562 pour LightGBM.

Un controle a ete fait avant de lire ces chiffres : les ECE stratifies
reproduisent l'ordre de grandeur du Tableau 6 du manuscrit, ce qui ecarte la
crainte que l'aller-retour par le logarithme des probabilites en float16 degrade
la mesure. Les temperatures different legerement du Tableau 6, la grille de
recherche etant bornee a 0.05 en bas.

## B. Aucun doublon exact ne subsiste, mais huit paires quasi identiques

Sur les 55 colonnes retenues apres la liste noire :

**Doublons exacts : 0.** La boucle est fermee. L'article accuse l'importance par
permutation de manquer les raccourcis dupliques ; il peut maintenant affirmer
qu'aucune duplication exacte ne subsiste dans le jeu qu'il publie.

**Paires avec |r| > 0.99 : 8.**

| Paire | r |
|---|---|
| TotAppByte / DAppBytes | 0.99999 |
| DstBytes / DAppBytes | 0.99997 |
| DstBytes / TotAppByte | 0.99997 |
| TcpRtt / SynAck | 0.99995 |
| TotBytes / DstBytes | 0.99987 |
| TotBytes / TotAppByte | 0.99980 |
| TotBytes / DAppBytes | 0.99979 |
| DIntPktMin / DIntPktAct | 0.99216 |

Quatre colonnes de volume, `TotBytes`, `DstBytes`, `TotAppByte` et `DAppBytes`,
forment un groupe mutuellement correle au-dela de 0.9997, avec des informations
mutuelles elevees, de 1.14 a 1.78. Ce n'est pas une duplication exacte et la
regle de transferabilite ne les ecarte pas, mais c'est le meme mecanisme a un
degre moindre : quatre colonnes portent une information en grande partie
commune, et l'importance par permutation la repartira arbitrairement entre elles.

Le manuscrit doit le dire. C'est la difference entre affirmer qu'aucun raccourci
redondant ne subsiste, ce qui serait faux, et affirmer qu'aucune duplication
exacte ne subsiste et que la redondance residuelle est mesuree et publiee.
