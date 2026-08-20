# E7 — `IdleTime` est un identifiant de fichier de capture

**Origine.** Audit externe conduit sur le papier 1 (BAg-IDS), qui a recoupé
celui-ci. La note demandait explicitement à être **vérifiée, pas crue**.
Vérifiée : `verify_idletime.py`, **17 contrôles sur 17**.

**Gravité.** C'est le défaut le plus sérieux trouvé sur ce manuscrit. Il ne
touche pas la discussion mais les **résultats** : la condition auditée retient
une colonne qui, si la thèse est exacte, résout seule la tâche binaire.

---

## 1. Ce que le dépôt confirme seul

Tous les chiffres cités par la note correspondent **exactement** au dépôt :

| | valeur |
|---|---|
| `IdleTime` dans `features_audited` | **oui**, 1 des 55 colonnes retenues |
| `IdleTime` sur la liste noire | **non** |
| importance par permutation | **0,2279 — le maximum du papier**, 6,4× la suivante |
| τ publié | 0,94 (seuil d'exclusion 0,50) |
| τ imbriqué | **1,0191** — l'exactitude *monte* sous le protocole temporel |

## 2. Deux corroborations que l'auditeur n'a pas utilisées

Il est parti des fichiers bruts. Ces deux routes partent du dépôt.

### a. Le plafond à 9 classes, calculé depuis les seuls effectifs de classes

Si `IdleTime` est constant par fichier de capture, un arbre ne peut, dans
chaque groupe de classes partageant une valeur, que prédire la classe
majoritaire du groupe. Le découpage des fichiers étant connu — les trois
bruteforce dans un fichier, les quatre DoS sur une à deux valeurs, `dos-hulk`
et le bénin à part —, le plafond se calcule :

| hypothèse | plafond | écart au 0,6210 mesuré |
|---|---:|---:|
| les 4 classes DoS partagent **1** valeur | 0,4368 | 0,1842 |
| elles se séparent en **2** valeurs | **0,6302** | **0,0092** |

La mesure tombe à 0,009 sous le plafond que l'hypothèse prédit, du bon côté —
un ajustement ne peut pas dépasser son plafond. Une variable comportementale
continue n'a aucune raison d'atterrir là.

### b. L'arithmétique du `float32`

Un horodatage de février 2025 vaut ≈ 1,739×10⁹, donc 2³⁰ ≤ v < 2³¹. La
mantisse du `float32` fait 24 bits : le **pas y est de 128 s**. Une capture qui
dure deux minutes s'écrase donc sur une à deux valeurs — exactement ce que la
note rapporte.

Et le cast est dans le dépôt : `feature_sets()` du pipeline fait
`.astype(np.float32)`. Les six valeurs citées sont toutes des multiples exacts
de 128.

Contrôle annexe : 1739380352 = 2025-02-12 17:12:32 UTC, ce qui tombe bien dans
la fenêtre des captures `dos-*` que la note situe à 17:10–17:12. Le fossé entre
le dernier bénin et la première attaque est de **40,9 h**.

## 3. Pourquoi trois diagnostics l'ont laissée passer

| diagnostic | ce qu'il dit d'`IdleTime` |
|---|---|
| transférabilité τ | 0,94 — rang 55/63 des plus transférables |
| audit imbriqué | 1,0191 — l'exactitude monte |
| audit résiduel (E3) | rang 24/55 en information mutuelle, 33/55 en corrélation |

**Les trois mesurent un degré d'association avec l'étiquette**, et l'association
d'un identifiant de fichier est bornée par le plafond du §2a. C'est structurel :
un critère bâti sur un **rapport entre deux protocoles** est aveugle à une fuite
figée par groupe, puisqu'elle fuit autant des deux côtés.

Ce n'est pas une surprise — `genis_bench/README.md` l'écrivait déjà : « une
fuite invariante par groupe lui échappe ». La protection manquante était la
liste noire *a priori*, et l'analyse qui produit `transfer_table` ne passe pas
par elle.

**Ce qui trahit la colonne n'est pas son association, ce sont ses valeurs.**

## 4. Ce que ça touche

1. **Les résultats**, pas seulement la discussion : tous les chiffres de la
   condition auditée incluent cette colonne.
2. **La légende de la Figure 6 s'inverse.** Elle présente `IdleTime` comme
   « importance élevée mais peu prédictive isolément », donc comme la preuve
   que l'attribution *surestime*. C'est la seule mention d'`IdleTime` dans tout
   le manuscrit, et c'est celle qui bascule.
3. **Contradiction avec le résultat n° 2 du résumé** : le papier démontre qu'une
   sonde à horodatage seul atteint 0,9862 sous protocole temporel, puis conserve
   une colonne d'horodatage comme variable comportementale.
4. **La liste noire passe de douze à treize entrées au minimum.**

## 5. Ce que ce n'est pas : un affaiblissement

La thèse centrale — « l'attribution ne sépare pas les raccourcis du signal » —
devient **symétrique et plus forte** :

- l'attribution donne ≈ 0 aux huit raccourcis redondants ;
- l'attribution donne son **score maximal** à un raccourci parfait.

Elle échoue donc dans les deux sens. Et la cécité du critère de transférabilité,
**rapportée par les auteurs**, est une limite mesurée de la méthode — le registre
que le papier adopte déjà ailleurs.

## 6. MESURÉ — le notebook a tourné, `verify_e7_correction.py` : 20/20

### La preuve directe

| fichier | flux | valeurs distinctes |
|---|---:|---:|
| `attack-bruteforce-{ftp,smb,ssh}` | 18 033 | **1**, la même pour les trois |
| `attack-dos-{pushack,slowloris,udp}` | 183 071 | **1**, la même pour les trois |
| `attack-dos-icmp` | 65 536 | 2 |
| `attack-dos-hulk` | 47 033 | 1 |
| `benign-{admin,user}` | 16 864 | 1 chacun |
| `benign-background` | 8 283 | 2 |

**Maximum deux valeurs par fichier.** Toutes sont des multiples exacts de 128 —
le pas du `float32`. Toutes tombent en février 2025. Le fossé entre le dernier
bénin et la première attaque est de **40,9 h**.

### Le plafond n'est pas approché, il est atteint

Le socle imposé par la structure (bénin + `bruteforce-smb` + `dos-pushack` +
`dos-hulk`) vaut 0,4368. Il manque 62 403 flux pour atteindre le 0,6209 mesuré,
soit **95,2 % de `dos-icmp`** — la part de ce fichier posée sur sa valeur propre
1739380224. L'arbre fait donc exactement ce que la structure permet, ni plus ni
moins.

*Comptabilité : ma prédiction initiale de 0,6302 avait le bon ordre de grandeur
avec un groupement qui n'était pas le vrai. Le plafond exact vaut 0,6209.*

### L'AUC binaire

| colonne | AUC binaire | arbre binaire | arbre 9 classes |
|---|---:|---:|---:|
| **`IdleTime`** | **1,0000** | **1,0000** | 0,6209 |
| `Offset` | 0,9379 | 0,8960 | 0,0601 |
| `SIntPktMin` | 0,9165 | 0,9865 | 0,9392 |
| `DstBytes` | 0,6272 | 0,9946 | 0,9604 |

`IdleTime` sépare **parfaitement** bénin et attaque tout en plafonnant à 0,62 en
neuf classes. C'est le point de méthode : une mesure de pouvoir prédictif isolé
conduite en multiclasse peut masquer une colonne qui résout parfaitement la
tâche binaire.

## 7. Ce que la correction coûte

Témoin validé : le bras publié rejoue le Tableau 2 à **0,0021** près.

| détecteur | strat. publiée | strat. corrigée | Δ | temp. publiée | temp. corrigée | Δ |
|---|---:|---:|---:|---:|---:|---:|
| logreg | 0,9997 | 0,9967 | −0,0030 | 0,9949 | 0,9881 | −0,0068 |
| knn | 0,9965 | 0,9927 | −0,0038 | 0,9837 | 0,9574 | −0,0263 |
| rf | 0,9999 | 0,9999 | −0,0001 | 0,9775 | 0,9532 | −0,0243 |
| xgboost | 1,0000 | 0,9998 | −0,0002 | 0,9888 | 0,9666 | −0,0222 |
| **lightgbm** | 0,9999 | 0,9999 | −0,0000 | 0,9897 | **0,9577** | **−0,0320** |
| dnn | 0,9979 | 0,9954 | −0,0026 | 0,9887 | 0,9733 | −0,0154 |
| cnn | 0,9958 | 0,9949 | −0,0009 | 0,9939 | 0,9778 | −0,0161 |
| rnn | 0,9979 | 0,9970 | −0,0009 | 0,9942 | 0,9892 | −0,0050 |
| nb | 0,5347 | 0,4387 | −0,0961 | 0,4994 | 0,4843 | −0,0151 |

**Toutes les pertes sont négatives : les modèles s'en servaient.** Le coût
stratifié reste faible (≤ 0,0038) et le coût temporel est **8× plus grand**
(jusqu'à 0,0320). C'est exactement la signature des douze autres raccourcis :
peu cher sous découpage aléatoire, cher sous protocole temporel. `IdleTime` se
comporte comme ses pairs.

Prix à écrire : le taux de faux positifs stratifié de la régression logistique
passe de 0,0006 à 0,0167 (×28), et celui de k-NN de 0,0006 à 0,0171 (×29).

## 7bis. Ce que le témoin d'E7 ne contrôlait pas — correction

**Le témoin d'E7 ne comparait que le bras stratifié.** Le bras **temporel**, qui
porte tout le résultat, n'a jamais été contrôlé. C'est une faiblesse de ma
conception, trouvée en préparant E8.

Contrôlé après coup, l'écart au publié sur le bras temporel :

| détecteur | coût mesuré | écart au publié | attribuable ? |
|---|---:|---:|---|
| lightgbm | −0,0320 | **0,0000** | oui, se rejoue exactement |
| knn | −0,0263 | 0,0002 | oui |
| rf | −0,0243 | 0,0000 | oui |
| xgboost | −0,0222 | 0,0000 | oui |
| cnn | −0,0161 | 0,0010 | oui |
| **dnn** | −0,0154 | **0,0156** | **non, dans le bruit** |
| logreg | −0,0068 | 0,0005 | oui |
| **rnn** | −0,0050 | 0,0041 | **non, dans le bruit** |

**Les coûts mesurés sur le DNN et le RNN ne se distinguent pas du bruit
d'environnement** et ne doivent pas être rapportés comme des effets.

Ce n'est pas un problème pour la conclusion, et c'est même rassurant : **les
quatre écarts les plus grands portent sur `lightgbm`, `knn`, `rf` et `xgboost`,
qui se rejouent au quatrième chiffre.** Le résultat repose sur le sol le plus
ferme du jeu de détecteurs.

**La leçon de méthode**, que le papier doit publier : la dispersion sur les
graines ne borne pas la dispersion sur l'environnement. Le CNN a un écart-type
de 0,00069 sur cinq graines publiées et se déplace de 0,0114 d'une session
Colab à l'autre **à graine identique**. E8 mesure cette bande explicitement, en
rejouant trois fois la même configuration.

## 8. Les conclusions du papier tiennent, et l'une se renforce

| conclusion | sous la liste corrigée |
|---|---|
| corpus saturé en stratifié | **tient** — les trois ensembles ≥ 0,9998 |
| les boostés quittent le sommet en temporel | **renforcée** — LightGBM passe de 4ᵉ à **6ᵉ** |
| la calibration s'effondre en temporel | **tient** — médiane ×35, max ×994 |

Ordre temporel publié : `logreg > rnn > cnn > lightgbm > xgboost > dnn > knn > rf`
Ordre corrigé : `rnn > logreg > cnn > dnn > xgboost > lightgbm > knn > rf`

## 9. La décision : republier, pas commenter

**0,0320 dépasse ce que le papier traite comme du bruit.** Il écrit que le
groupe de tête est statistiquement indiscernable sur des écarts de 0,0022 à
0,0069 ; un déplacement de 0,032 ne peut pas être rangé là.

La condition auditée doit donc être **republiée sur la liste à treize entrées**,
pas seulement commentée en section 9. Les chiffres d'E7 sont sur la graine 1 :
une republication du Tableau 2 demande les cinq graines.

## 10. Ce qui restait à faire — fait

La preuve directe — compter les valeurs distinctes, mesurer l'AUC binaire — et
la réparation demandent le corpus brut. `colab/e7_idletime.ipynb` :

1. compte les valeurs distinctes par fichier, **avant** le cast `float32` ;
2. balaye **toutes** les colonnes pour la même pathologie — une règle qui a
   laissé passer `IdleTime` a pu en laisser passer d'autres ;
3. mesure l'AUC binaire, la mesure que l'audit n'a jamais faite ;
4. réentraîne sous la liste corrigée, avec le bras publié en **témoin**.

**Le manuscrit ne doit pas être soumis avant la republication de la
condition auditée.**

## 11. ⚠️ Le papier 1

`docs/preliminary_findings.md` §3 portait l'action « réintégrer `IdleTime` dans
BAg-IDS avant soumission ». Corrigé (voir le fichier, section barrée).

**Cette action injecterait une fuite à AUC binaire 1,000 dans le papier 1**, à
la veille d'une soumission Q1. L'exclusion accidentelle par le motif `"id"` a
protégé BAg-IDS. Il faut la rendre **volontaire et documentée**, pas la défaire.

## Entrées

- `paper/article1_results.json` — la campagne publiée
- `experiments/e4a/e4abis_results.json` — l'audit imbriqué
- `experiments/e3/e3_results.json` — l'audit résiduel
