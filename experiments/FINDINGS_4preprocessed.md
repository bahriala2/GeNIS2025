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

## Les sondes à une feature

`probe_4preprocessed.json` est archivé, et `verify_4preprocessed.py` contrôle désormais
ses chiffres aussi : **32 contrôles sur 32**. Les quatre valeurs citées en section 2.4
tombent à la décimale.

`timestamp_probes` est vide dans le rapport structurel, et c'est le résultat attendu :
ce script-là ne sonde que les colonnes positionnelles, et elles ne sont plus dans le
module.

### Sur les treize sous-catégories (classe majoritaire 0.1785)

| colonne | accuracy | macro-F1 | valeurs |
|---|---|---|---|
| `Seq` | 0.1713 | 0.1840 | 67 303 |
| `Offset` | 0.0672 | 0.1038 | 282 379 |
| `Dur` | 0.8957 | 0.7144 | 120 941 |
| `Ssaddr` | 0.6192 | 0.3576 | 85 |
| `Sdaddr` | **0.9947** | **0.9102** | 76 |
| `TotBytes` (témoin) | 0.9190 | 0.8699 | 5 805 |

`Seq` et `Offset` classent **sous** le taux de la classe majoritaire : les deux compteurs
Argus restants ne transmettent pas le raccourci de calendrier.

### Sur la tâche à quatre classes, celle que la baseline évalue réellement

C'est l'apport de ce rapport, et le manuscrit ne l'avait pas. Citer la tâche à treize
classes revenait à citer une tâche que Silva et al. ne font pas.

| colonne | accuracy | macro-F1 |
|---|---|---|
| `Sdaddr` | **0.9985** | **0.9950** |
| `Dport` | 0.9838 | 0.9652 |
| `TotBytes` (témoin) | 0.9892 | 0.9758 |

Un compteur de topologie à 76 valeurs distinctes résout donc presque la tâche à quatre
classes, et le port de destination n'en est pas loin.

**La nuance qui doit accompagner ces chiffres**, et qui est maintenant dans le manuscrit :
le témoin comportemental `TotBytes` obtient 0.9892 / 0.9758 sur la même tâche. Le pouvoir
prédictif isolé ne sépare donc pas à lui seul un compteur de topologie d'un comportement
de trafic — c'est exactement ce que la section 6.2 démontre par ailleurs. Ce qui les
sépare, c'est qu'un compteur de topologie est stable dans le temps et survivrait donc à
notre propre audit : d'où l'exclusion par nom maintenue comme remède distinct en
section 9.

## Provenance du rapport de sondage

Le `.json` d'origine a été écrit dans `C:\Users\ASUS` et n'a pas été transmis ; le
fichier archivé ici est reconstitué **fidèlement** depuis la sortie console du script,
qui contient chacun de ses champs (accuracy, macro-F1, valeurs distinctes, taux de classe
majoritaire, nombre de classes). Le fichier porte cette provenance dans une clé
`_provenance`. Relancer le script écrase la reconstitution par l'original ; les contrôles
de `verify_4preprocessed.py` doivent alors passer à l'identique.
