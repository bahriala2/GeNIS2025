# E2 sur CICIDS2017 : ce que l'audit trouve

Source : `e2_results_cicids2017.json`, empreinte `2830743|69|15`, notebook E2 v5.
2 830 743 flux, le compte canonique du corpus. 15 classes, 69 features
comportementales, 8 colonnes constantes retirees, 6 identifiants et 1 colonne
positionnelle exclus par nom.

## 1. Le raccourci d'horodatage se reproduit, et se comporte autrement

| | GeNIS | CICIDS2017 |
|---|---|---|
| horodatage seul, protocole stratifie | 0.9970 | **0.9529** |
| horodatage seul, temporel par classe | 0.9862 | **0.1028** |
| tau | 0.99 | **0.11** |

Les deux corpus portent un raccourci d'horodatage massif sous decoupage
aleatoire. Ils different sur ce que le protocole temporel en fait.

Sur GeNIS il survit : 0.9862 apres reordonnancement, parce que le trafic benin
et les attaques occupent des fenetres disjointes, si bien qu'ordonner a
l'interieur de chaque classe ne detruit pas la separation entre classes. C'est
la deuxieme conclusion de l'article, le decoupage temporel est necessaire mais
pas suffisant.

Sur CICIDS2017 il s'effondre : 0.1028, sous le hasard. Le benin y tourne les
cinq jours en meme temps que les attaques, donc ordonner par classe suffit a
detruire le signal.

La lecon pour l'article est plus forte que prevu : **l'adequation du decoupage
temporel depend du corpus**, elle ne se decrete pas. Il faut la mesurer, ce qui
est exactement l'argument pour un audit.

## 2. Le chronologique global est degenere sur les deux corpus

`p2_shared_classes` ne contient que BENIGN : chaque famille d'attaque de
CICIDS2017 n'apparait qu'un seul jour. La degenerescence rapportee sur GeNIS
n'est donc pas une bizarrerie de GeNIS, c'est une propriete des captures
scriptees. Le choix du temporel par classe vaut pour les deux.

## 3. Sept paires de colonnes identiques, invisibles a l'attribution

| paire | importance de l'une | importance de l'autre |
|---|---|---|
| Total Fwd Packets / Subflow Fwd Packets | -0.00004 | **0.00000** |
| Total Backward Packets / Subflow Bwd Packets | +0.00009 | **0.00000** |
| Fwd Packet Length Mean / Avg Fwd Segment Size | +0.02497 | **0.00000** |
| Bwd Packet Length Mean / Avg Bwd Segment Size | **0.00000** | **0.00000** |
| Fwd PSH Flags / SYN Flag Count | **0.00000** | **0.00000** |
| Fwd URG Flags / CWE Flag Count | **0.00000** | **0.00000** |
| Fwd Header Length / Fwd Header Length.1 | +0.00421 | **0.00000** |

Dix des quatorze colonnes concernees ont une importance par permutation
exactement nulle. Le cas le plus net est `Bwd Packet Length Mean` : macro-F1 de
0.3849 a elle seule, importance +0.00000.

C'est le mecanisme central de l'article, reproduit sur le corpus le plus utilise
du domaine, sur des colonnes que personne n'avait signalees.

## 4. Aucun raccourci comportemental, et c'est un resultat

43 features eligibles, zero exclue. Le tau minimal est 0.6726 sur `Bwd IAT Std`,
loin au-dessus du seuil de 0.5. Sur CICIDS2017 le seul raccourci est
positionnel, et il est ecarte par nom avant toute mesure.

L'audit ne fabrique donc pas de raccourcis la ou il n'y en a pas. C'est la
reponse au soupcon inverse.

## 5. La regle publiee ne se transpose pas telle quelle

Le filtre de predictivite de l'article, acc > 3 x hasard, est inapplicable ici :
3 x 0.803 depasse 1. Et l'accuracy mono-feature est saturee, predire tout en
BENIGN donne deja 0.803. Le filtre a donc ete porte sur le macro-F1, avec la
meme forme, trois fois la baseline, la baseline etant le macro-F1 mesure du
classifieur de classe majoritaire, soit 0.0636. Seuil retenu 0.1909.

C'est une limite de la regle publiee que seul un second corpus pouvait reveler.

## 6. La question de l'article AMCAI 2023 est tranchee

Les fichiers charges portent 85 colonnes, dont Flow ID, les adresses IP, les
ports, le protocole et l'horodatage. Le compte de 79 colonnes annonce dans
Bahri et al. 2023 correspond donc a la distribution MachineLearningCVE, d'ou ces
colonnes sont deja retirees. La formulation de cet article est ambigue, elle ne
decrit pas une conservation des identifiants.
