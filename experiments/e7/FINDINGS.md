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

## 6. Ce qui reste à faire, et qui ne peut pas se faire ici

La preuve directe — compter les valeurs distinctes, mesurer l'AUC binaire — et
la réparation demandent le corpus brut. `colab/e7_idletime.ipynb` :

1. compte les valeurs distinctes par fichier, **avant** le cast `float32` ;
2. balaye **toutes** les colonnes pour la même pathologie — une règle qui a
   laissé passer `IdleTime` a pu en laisser passer d'autres ;
3. mesure l'AUC binaire, la mesure que l'audit n'a jamais faite ;
4. réentraîne sous la liste corrigée, avec le bras publié en **témoin**.

**Le manuscrit ne doit pas être soumis avant ce résultat.**

## 7. ⚠️ Le papier 1

`docs/preliminary_findings.md` §3 portait l'action « réintégrer `IdleTime` dans
BAg-IDS avant soumission ». Corrigé (voir le fichier, section barrée).

**Cette action injecterait une fuite à AUC binaire 1,000 dans le papier 1**, à
la veille d'une soumission Q1. L'exclusion accidentelle par le motif `"id"` a
protégé BAg-IDS. Il faut la rendre **volontaire et documentée**, pas la défaire.

## Entrées

- `paper/article1_results.json` — la campagne publiée
- `experiments/e4a/e4abis_results.json` — l'audit imbriqué
- `experiments/e3/e3_results.json` — l'audit résiduel
