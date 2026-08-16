# E4b, premier passage : ce qui tient et ce qui ne tient pas

`e4b_results_v1.json` est la sortie du notebook **v1**. Elle est archivée telle quelle,
défauts compris, parce que deux de ses trois parties sont valides et que la troisième
documente une erreur de ma part qu'il vaut mieux garder que réécrire.

**Rien de ceci n'est encore entré dans le manuscrit.** Un run partiellement invalide ne
se verse pas dans un papier ; il se corrige, se relance, puis se verse.

## Le contrôle qui a révélé le défaut

L'origine glissante 0.60 reconstruit exactement la partition du protocole temporel
publié — même partition de test, 67 769 flux. Elle doit donc reproduire les chiffres
publiés. Pour les quatre détecteurs déterministes, elle les reproduit **au bit près** :

| détecteur | o0.60 | publié | écart |
|---|---|---|---|
| random forest | 0.9775 | 0.9775 | 0.0000 |
| XGBoost | 0.9888 | 0.9888 | 0.0000 |
| LightGBM | 0.9897 | 0.9897 | 0.0000 |
| naive Bayes | 0.4994 | 0.4994 | 0.0000 |
| k-NN | 0.9837 | 0.9839 | 0.0002 |
| logreg | 0.9949 | 0.9944 | 0.0005 |
| DNN | 0.9897 | 0.9730 | 0.0167 |
| RNN | 0.9939 | 0.9901 | 0.0038 |
| **CNN** | **0.6801** | **0.9949** | **0.3147** |

Un écart de 0.31 n'est pas du bruit d'initialisation. C'était un autre modèle.

## Les trois défauts de la v1

**1. Le CNN n'était pas celui du papier.** Le pipeline construit
`Conv1D(64,3) → MaxPooling1D(2) → Conv1D(32,3) → Flatten → Dense(64) → Dropout → Dense(C)`.
La v1 construisait `Conv1D(64,3) → Conv1D(32,3) → GlobalMaxPooling1D → Dropout → Dense(64) → Dense(C)`.
`GlobalMaxPooling1D` écrase l'axe des features : il ne conserve qu'une valeur par filtre
au lieu de 32 × F. Sur des données tabulaires remises en pseudo-séquence, c'est fatal, et
ça explique entièrement la chute à 0.68.

**2. Le RNN non plus.** Le pipeline demande `SimpleRNN(64, activation="relu")` ; la v1
laissait l'activation `tanh` par défaut. L'écart mesuré est faible (0.0038), mais ce
n'était pas le détecteur du papier.

**3. Le bootstrap apparié n'a jamais tourné.** `bootstrap_apparie` est vide. La fonction
de chargement cherchait `probs/<modele>__audited__<protocole>.npz` alors que le pipeline
écrit `<modele>_audited_<protocole>.npz` — un underscore, pas deux. Aucune matrice n'a
été trouvée, et la partie B s'est sautée en n'affichant qu'un message. Second défaut au
même endroit : elle prenait le premier tableau 2-D de l'archive, c'est-à-dire
`probs_val`, alors qu'il faut `probs_test`.

## Ce qui reste valide, et c'est l'essentiel

### Origines glissantes, huit détecteurs sur dix

| détecteur | moyenne | σ | min | max | publié (o0.60) |
|---|---|---|---|---|---|
| logreg | 0.9969 | 0.0013 | 0.9949 | 0.9985 | 0.9944 |
| random forest | 0.9919 | 0.0080 | 0.9775 | 0.9998 | 0.9775 |
| DNN | 0.9782 | 0.0149 | 0.9504 | 0.9926 | 0.9730 |
| k-NN | 0.9776 | 0.0040 | 0.9731 | 0.9837 | 0.9839 |
| **LightGBM** | **0.9469** | **0.0562** | **0.8750** | 0.9944 | 0.9897 |
| **XGBoost** | **0.9467** | **0.0562** | **0.8748** | 0.9944 | 0.9888 |
| naive Bayes | 0.5405 | 0.0310 | 0.4994 | 0.5869 | 0.4994 |
| majority | 0.0361 | 0.0000 | 0.0361 | 0.0361 | 0.0361 |

C'est un résultat, et il va plus loin que ce que dit la section 6.3. Les deux ensembles
boostés ne sont pas seulement délogés du sommet par le protocole temporel : ce sont **les
détecteurs les moins stables du lot**, avec un écart-type quarante fois celui de la
régression logistique et un plancher à 0.875 aux origines 0.40 et 0.45. La régression
logistique, elle, tient 0.9969 ± 0.0013 sur les cinq origines. Le classement observé sur
une partition unique devient une observation sur cinq, et elle pointe dans la même
direction, plus fort.

À noter : aux origines 0.40 et 0.45, l'accuracy des ensembles boostés reste à 0.9886
pendant que le macro-F1 tombe à 0.8812. C'est une classe entière qui disparaît, pas une
dégradation diffuse.

### Leave-one-family-out, entièrement valide

Les cinq détecteurs testés sont logreg, rf, xgboost, lightgbm et dnn — ni CNN ni RNN.
Aucun run n'est touché par les défauts ci-dessus.

Le résultat est net et il répond à la question que la section 4.2 déclare ouverte, celle
de la généralisation à une famille jamais vue :

| famille retirée | logreg | rf | xgboost | lightgbm | dnn |
|---|---|---|---|---|---|
| bruteforce-ftp | 0.032 | 0.000 | 1.000 | 1.000 | 0.240 |
| bruteforce-smb | 0.811 | 0.000 | 1.000 | 1.000 | 0.942 |
| bruteforce-ssh | 0.010 | 0.090 | 1.000 | 1.000 | 0.993 |
| dos-hulk | 1.000 | 0.847 | 1.000 | 1.000 | 0.999 |
| dos-icmp | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| dos-pushack | 1.000 | 0.995 | 1.000 | 1.000 | 1.000 |
| dos-slowloris | 0.985 | 0.429 | 1.000 | 1.000 | 0.968 |
| dos-udp | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

*(rappel de la famille inconnue, c'est-à-dire la part de ses flux reconnus comme attaque
alors que la famille est absente de l'entraînement)*

Deux lectures s'imposent, et une réserve.

La lecture : **le renversement est complet**. Les ensembles boostés, que le protocole
temporel déclasse et que les origines glissantes montrent instables, sont les seuls à
détecter 100 % des flux de chaque famille retirée. La régression logistique, la plus
stable des huit sur les origines, s'effondre sur trois familles et tombe à l'AUROC 0.4926
sur `dos-icmp`, c'est-à-dire au hasard. Le DNN fait de même sur `dos-udp` (AUROC 0.4879).
Aucun détecteur ne domine sur les deux axes.

La réserve : `1.000` exactement, pour deux modèles, sur les huit familles, avec des AUROC
à `1.0` exactement, est le genre de chiffre qui mérite qu'on le regarde deux fois avant
de l'écrire dans un papier. Le fait que random forest donne `0.000` sur deux familles et
`1.000` sur deux autres prouve que la mesure discrimine, donc ce n'est probablement pas
un artefact — mais je ne l'écrirai pas dans le manuscrit sans avoir relu le calcul.

## Ce qu'il faut relancer

Le notebook **v2** répare tout seul : il détecte un état v1 à l'absence du jeton
`meta.archi`, purge les dix runs `cnn|*` et `rnn|*`, vide le bootstrap, et garde le reste.
Simulation sur l'état réel : **50 → 40 origines, 40 runs LOFO conservés**.

Reste à calculer : dix runs d'origine (cinq CNN, cinq RNN) et la partie B. Compter une
heure environ, contre trois à cinq pour le passage complet.
