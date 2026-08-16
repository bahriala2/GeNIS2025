# Le module 4-preprocessed, et ce qu'il confirme

Rapport structurel produit par `inspect_4preprocessed.py` sur la machine qui détient
le corpus, archivé ici sous `inspection_4preprocessed.json`. Le contrôle qui l'exploite
est `verify_4preprocessed.py` : **17 contrôles sur 17 passent.**

```
python verify_4preprocessed.py
```

## Pourquoi ça compte

La section 3.2 du manuscrit avance l'affirmation la plus contestable du papier : un écart
de **29 736 flux** entre les 368 556 flux de 60 s sur lesquels la baseline du corpus
évalue et les 338 820 que le module `2-flows` publie, avec une décomposition dont elle
dit qu'**aucune des deux causes n'est documentée**. C'est une accusation d'incohérence
portée contre un corpus publié. Elle doit être vérifiable, et pas seulement par nous.

Le module `4-preprocessed` fournit exactement ça : une **troisième source**, indépendante
du descripteur et des fichiers `2-flows`, qui distribue les mêmes données 60 s sous forme
d'un couple entraînement/holdout déjà encodé et qui porte ses propres comptes.

## Ce que la reconstitution donne

Le module ship 294 844 + 73 712 = **368 556** flux, soit exactement le total attribué à
la baseline, en 80/20 (part d'entraînement mesurée : 0.799998). En remettant la
composition de la partition d'entraînement à l'échelle, chaque compte revient **au flux
près** :

| | manuscrit | reconstitué |
|---|---|---|
| total du module | 368 556 | 368 556 |
| `recon-nmap` | 27 713 | 27 713 |
| `recon-dns` | 20 | 20 |
| `benign-background` (descripteur) | 10 286 | 10 286 |
| manque sur `benign-background` | 2 003 | 2 003 |
| écart total | 29 736 | 29 736 |
| 368 556 − écart | 338 820 | 338 820 |
| flux bénins de `2-flows` (tableau 5) | 25 147 | 25 147 |

Le total reconstitué retombe sur 368 556 exactement, ce qui vaut contrôle interne du
procédé de remise à l'échelle : aucune classe n'a été arrondie dans le mauvais sens.

## Ce que ça confirme aussi pour la section 2.4

- `StartTime`, `LastTime` et `Rank` sont **absents** du module. Le raccourci de calendrier
  de la section 6.2 n'est donc pas transmis par lui.
- `Seq` y est **resté**, avec `Offset`. C'est pour ça que `probe_4preprocessed.py` existe.
- Les **six colonnes de durée numériquement identiques** sont présentes et inchangées :
  un seul groupe, 15 paires, `{Dur, RunTime, Mean, Sum, Min, Max}`. La duplication
  survit au prétraitement.
- `Ssaddr`, `Sdaddr`, `Sport` et `Dport` sont présents. Silva et al. les excluent de
  leurs expériences, donc leurs résultats ne sont pas en cause ; l'observation porte sur
  le module tel que distribué, qu'une étude ultérieure peut charger directement.
- 13 sous-catégories, dont `recon-nmap` et `recon-dns` que `2-flows` ne contient pas.
- Aucune colonne constante, alors que notre tranche 60 s de `2-flows` en écarte 23.

## Ce qui reste non vérifié

`timestamp_probes` est **vide**, et c'est le résultat attendu : le script ne sonde que les
colonnes positionnelles, et elles ne sont pas là. Les accuracies à une feature citées en
section 2.4 —

| feature | accuracy | macro-F1 |
|---|---|---|
| `Seq` | 0.1713 | — |
| `Offset` | 0.0672 | — |
| `Dur` | 0.8957 | — |
| `Sdaddr` | 0.9947 | 0.9102 |

— viennent de **`probe_4preprocessed.py`**, dont la sortie n'est pas encore archivée ici.
Pour fermer ce dernier trou :

```
python probe_4preprocessed.py "D:\Genis\4-preprocessed\4-preprocessed"
```

et déposer le `probe_4preprocessed.json` produit dans ce dossier. Les chiffres du
manuscrit ont été mesurés, mais tant que ce fichier manque, ils sont les seuls du papier
qu'aucun script du dépôt ne peut reproduire.
