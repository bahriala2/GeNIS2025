# E4c — ce que coûte le choix du seuil

`e4c_results.json`. Critique 3 du rapport : la règle τ < 0.50 est un choix déclaré, le
manuscrit montre que la liste passe de 8 à 13 colonnes selon la normalisation, mais il
n'avait **jamais réentraîné** sous ces alternatives. La sensibilité restait descriptive.
Elle est maintenant mesurée.

## Les quatre listes alternatives, plus la publiée

| variante | règle | comportementales exclues |
|---|---|---|
| `clean` | aucune | 0 |
| `tau040` | τ < 0.40 | 6 |
| `tau050` | τ < 0.50 — **la règle publiée** | 8 |
| `tau070` | τ < 0.70 | 16 |
| `taustar` | τ\* < 0.50, corrigé du hasard | 13 |

Chaque détecteur réentraîné sous les deux protocoles. `tau050` n'est pas recalculée :
c'est la condition auditée de la campagne publiée.

## Le résultat : le seuil ne coûte presque rien

Étendue du macro-F1 sur les cinq variantes, par détecteur.

| détecteur | stratifié | temporel |
|---|---|---|
| logreg | 0.0006 | 0.0057 |
| k-NN | 0.0040 | 0.0103 |
| random forest | 0.0001 | 0.0070 |
| XGBoost | 0.0000 | 0.0078 |
| LightGBM | 0.0001 | 0.0046 |
| DNN | 0.0026 | 0.0233 |
| CNN | 0.0032 | 0.0078 |
| RNN | 0.0023 | 0.0151 |
| **naive Bayes** | **0.1075** | **0.1286** |

Médiane sur l'ensemble des écarts temporels : **0.0017**. Maximum : 0.1219, et il est sur
naive Bayes.

**Pour les huit détecteurs qui comptent, déplacer le seuil de 0.40 à 0.70 — de 6 à 16
colonnes exclues — change le macro-F1 temporel d'au plus 0.023, et de 0.004 sous le
protocole stratifié.** Le seul détecteur qui bouge vraiment est la ligne de base faible,
dont le manuscrit ne tire aucune conclusion.

## Deux observations qu'il faut écrire

**La liste publiée est conservatrice, pas flatteuse.** Sous le protocole temporel,
`tau070` — seize exclusions au lieu de huit — donne *mieux* que la règle publiée pour la
plupart des détecteurs : XGBoost passe de 0.9888 à 0.9967, logreg de 0.9944 à 0.9978,
LightGBM de 0.9897 à 0.9944. Le choix de 0.50 n'a donc pas été fait pour maximiser un
score ; l'exclusion plus large aurait donné de meilleurs chiffres.

**Naive Bayes est l'exception et il faut dire pourquoi.** Il passe de 0.4996 (`clean`) à
0.3775 (`tau070`) et 0.5061 (`taustar`) sous le protocole temporel. Un classifieur qui
suppose l'indépendance conditionnelle est le plus sensible à *quelles* colonnes
corrélées restent, ce qui est cohérent avec la redondance résiduelle documentée en 6.2
(huit paires au-dessus de 0.99). Ce n'est pas une instabilité de la règle, c'est une
propriété du détecteur.

## Ce que ça change pour le manuscrit

La section 9 dit aujourd'hui : « nous n'avons pas réentraîné les détecteurs sous ces
alternatives, donc le coût de ce choix est rapporté comme une liste de features et non
comme une mesure ». Cette phrase doit tomber. Le coût **est** mesuré, il est borné, et il
est petit — sauf pour la ligne de base faible.

C'est aussi ce qui fait passer la règle de « diagnostic proposé » à quelque chose dont on
connaît la sensibilité, ce que le relecteur demandait explicitement.
