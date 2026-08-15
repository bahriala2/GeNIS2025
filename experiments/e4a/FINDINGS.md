# E4a : l'audit ne peut pas se calculer sur la validation

Source : `e4a_results.json`, empreinte `338820|67|63|9`, notebook E4a v1.

## Le verdict, et pourquoi ce n'est pas un bug

Calcule sur la partition de VALIDATION, l'audit n'exclut plus rien : la liste
noire comportementale passe de huit colonnes a **zero**.

Le controle ecarte l'hypothese du bug. Le meme code, la meme matrice et les
memes arbres, evalues sur le TEST, reproduisent **exactement** les huit
colonnes publiees (`controle_test_ok: true`).

## Le mecanisme

| | validation | test |
|---|---|---|
| accuracy stratifiee de `Dur` | 0.9210 | 0.9221 |
| accuracy temporelle de `Dur` | 0.6271 | **0.3041** |
| tau | 0.681 | **0.330** |

L'accuracy **stratifiee** est la meme sur les deux partitions, ecart moyen
0.0008 sur les 63 colonnes : sous un tirage aleatoire, validation et test sont
echangeables, comme ils doivent l'etre.

L'accuracy **temporelle** ne l'est pas. La validation donne un chiffre plus
eleve que le test pour **53 colonnes sur 63**, de +0.075 en moyenne et jusqu'a
+0.323.

La cause est dans la construction du decoupage : train `[0, 60 %)`,
validation `[60, 80 %)`, test `[80, 100 %)` a l'interieur de chaque classe.
La validation est **adjacente** au train ; le test est un cran plus loin. Une
feature dont le pouvoir predictif decroit avec la distance temporelle ne montre
sur la validation qu'une fraction de cette decroissance.

La composition est ecartee comme explication : validation et test portent le
meme nombre de flux par classe, a une unite pres.

## Ce que cela change

Le remede que le relecteur proposait — calculer la liste noire sur la
validation et la geler avant d'ouvrir le test — **n'est pas disponible**. Ce
n'est pas que la liste change : c'est que l'instrument est mal place. tau mesure
une decroissance avec la distance, et la validation est trop proche du train
pour la voir.

Le remede qui reste est un audit **imbrique** dans la partition
d'entrainement, avec une fenetre d'evaluation posterieure a la fenetre
d'ajustement, de sorte que l'audit n'ouvre ni la validation ni le test. C'est
ce que mesure E4a-bis.

## Ce qui survit sans condition

**L'aveuglement de l'attribution.** Les huit colonnes ont une importance par
permutation de **exactement zero** sur la validation comme sur le test. Le
resultat methodologique central de l'article ne depend pas de la partition.
Sur les 63 colonnes, 55 ont une importance exactement nulle sur validation.

**L'ordre.** Spearman entre tau_validation et tau_test sur les 38 eligibles :
**0.876**. Les huit publiees occupent les rangs 1 a 7 et 11 sur la validation,
contre 1 a 8 sur le test. Le classement se conserve ; c'est l'echelle qui bouge.

Mais aucun seuil ne les separe sur la validation : la plus haute des huit,
`SIntPkt` a 0.777, depasse la plus basse des retenues, `DstLoad` a 0.747. Les
groupes se chevauchent. Coupe au deuxieme plus large ecart, la validation
retrouve sept des huit — les six colonnes de duree identiques plus
`SIntPktMax` — et manque `SIntPkt`, qui est precisement la colonne dont la
section 4.3 du manuscrit dit deja qu'elle n'est pas distinguee des dupliquees.

## L'avertissement sklearn n'est pas en cause

`UserWarning: X does not have valid feature names, but LGBMClassifier was
fitted with feature names` provient de la cellule d'importance par permutation.
LightGBM nomme ses colonnes `Column_0..N` quand on l'ajuste sur un tableau
numpy, puis sklearn previent a la prediction. L'ordre des colonnes est
conserve. Le balayage de tau utilise `DecisionTreeClassifier` et n'est pas
concerne. Le controle sur le test le confirme.

## Le fait nouveau

Si tau mesure une decroissance avec la distance, cette decroissance doit se
voir. E4a-bis l'echantillonne sur huit tranches d'horizon successives et en
fait une figure. C'est un resultat que ni le rapport de relecture ni nous
n'avions anticipe, et il justifie a posteriori le choix de la partition la plus
lointaine comme instrument de l'audit.
