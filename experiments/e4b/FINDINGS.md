# E4b — protocole temporel répété

> **La v2 a tourné et le passage est complet** : `e4b_results.json`. Les trois
> défauts décrits plus bas sont corrigés, le CNN et le RNN sont recalculés avec
> les architectures du pipeline, et le bootstrap apparié a produit ses résultats.
> `e4b_results_v1.json` est conservé comme trace du premier passage.

## Ce que la v2 donne

### Le CNN, une fois la bonne architecture en place

| | o0.40 | o0.45 | o0.50 | o0.55 | o0.60 | publié |
|---|---|---|---|---|---|---|
| macro-F1 | 0.9965 | 0.9927 | 0.9942 | 0.9958 | 0.9938 | 0.9949 |

L'écart à l'origine 0.60 tombe de **0.3147 à 0.0010** : c'est du bruit d'initialisation,
et c'est la confirmation que le défaut était bien l'architecture.

### Stabilité sur cinq origines glissantes, dix détecteurs

| détecteur | moyenne | σ | min | max |
|---|---|---|---|---|
| logreg | 0.9969 | **0.0013** | 0.9949 | 0.9985 |
| CNN | 0.9946 | 0.0014 | 0.9927 | 0.9965 |
| k-NN | 0.9776 | 0.0040 | 0.9731 | 0.9837 |
| random forest | 0.9919 | 0.0080 | 0.9775 | 0.9998 |
| DNN | 0.9782 | 0.0149 | 0.9504 | 0.9926 |
| RNN | 0.9797 | 0.0306 | 0.9186 | 0.9987 |
| naive Bayes | 0.5405 | 0.0310 | 0.4994 | 0.5869 |
| **XGBoost** | 0.9467 | **0.0562** | **0.8748** | 0.9944 |
| **LightGBM** | 0.9469 | **0.0562** | **0.8750** | 0.9944 |

Les deux ensembles boostés ne sont pas seulement délogés du sommet par le protocole
temporel : ce sont **les détecteurs les moins stables du lot**, avec un σ quarante fois
celui de la régression logistique et un plancher à 0.875 aux origines 0.40 et 0.45. Aux
origines basses leur accuracy reste à 0.9886 pendant que le macro-F1 tombe à 0.8812 :
c'est une classe entière qui disparaît, pas une dégradation diffuse.

### Bootstrap apparié, 1 000 rééchantillonnages

C'est le test que la section 4.5 recommande sans l'avoir fait. Il est fait.

| protocole | paires dont l'IC95 de l'écart contient zéro |
|---|---|
| stratifié, graine 1 | **7 / 45** — `cnn\|dnn`, `cnn\|rnn`, `dnn\|rnn`, `lightgbm\|rf`, `lightgbm\|xgboost`, `logreg\|rnn`, `rf\|xgboost` |
| temporel | **4 / 45** — `cnn\|logreg`, `lightgbm\|rnn`, `lightgbm\|xgboost`, `rnn\|xgboost` |

À comparer aux **11 / 45** paires non significatives sous McNemar (section 6.1). Le
bootstrap apparié sur le macro-F1 est donc *plus* discriminant que McNemar sur les
indicateurs de correction, ce qui est cohérent : les deux tests ne posent pas la même
question, et la section 4.5 le disait déjà. Le groupe de tête reste indistinguable dans
les deux cas — `lightgbm\|xgboost` et `rf\|xgboost` en font partie sous les deux tests.

### Leave-one-family-out

Les cinq détecteurs testés sont logreg, rf, xgboost, lightgbm et dnn — ni CNN ni RNN,
donc ces runs n'ont jamais été touchés par les défauts de la v1 et sont inchangés.

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

### La réserve sur les 1.000, levée — et la limite qu'elle révèle

`1.000` exactement, deux modèles, huit familles, méritait relecture du calcul. Elle est
faite.

**Ce n'est pas un artefact de mesure.** Un modèle qui prédirait « attaque » partout
obtiendrait un rappel de 1.000 sans rien avoir appris — mais son FPR bénin vaudrait 1.000
aussi. Or XGBoost et LightGBM ont un **FPR bénin de 0.000 sur les huit familles** : ils
classent correctement les 5 030 flux bénins tout en signalant 100 % de la famille jamais
vue. La séparation est réelle. Random forest à 0.000 sur `bruteforce-ftp` et 1.000 sur
`dos-icmp` confirme par ailleurs que la mesure discrimine.

**Mais l'expérience est plus faible que son nom.** Retirer `bruteforce-ftp` laisse
`bruteforce-smb` et `bruteforce-ssh` à l'entraînement ; retirer `dos-hulk` laisse quatre
autres familles DoS. Le modèle n'affronte donc jamais une catégorie d'attaque inconnue,
seulement une variante d'une catégorie qu'il connaît déjà. C'est ce qui explique les
1.000 sans les invalider.

Conséquence pour la rédaction : ce résultat s'énonce **« généralise à une variante non
vue d'une catégorie connue »**, et surtout pas « généralise à une attaque nouvelle ». Le
test qui répondrait à la seconde question est un leave-one-*category*-out — retirer les
trois brute-force d'un bloc, ou les cinq DoS. Il n'a pas été fait, et c'est la façon
honnête de présenter la chose : E4b répond à une question plus étroite que celle que la
section 4.2 déclare ouverte.

## Historique : le premier passage et ses trois défauts

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

Le notebook **v2** a réparé tout seul : détection d'un état v1 à l'absence du jeton
`meta.archi`, purge des dix runs `cnn|*` et `rnn|*`, remise à zéro du bootstrap, tout le
reste conservé. 50 → 40 origines puis retour à 50, et les 40 runs LOFO jamais recalculés.
Une heure au lieu de trois à cinq.
