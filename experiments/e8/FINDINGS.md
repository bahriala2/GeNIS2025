# E8 — la condition auditée republiée sur la liste corrigée

**`verify_e8.py` : 33 contrôles sur 33.** 180 runs sur 180, coût et tests appariés compris.

---

## 1. `Offset` n'est pas positionnel — la règle tranche contre le soupçon

La règle avait été écrite **avant** de voir le résultat : si la corrélation de
rang entre `Offset` et l'ordre de capture dépasse 0,95 dans chaque fichier, il
rejoint la liste positionnelle.

**Corrélation de rang minimale : 0,126.** Très loin de 0,95.

`Offset` n'est donc pas le décalage d'enregistrement que son nom suggère. Il
reste dans la condition auditée, et la §9 rapporte son AUC binaire de 0,9379
comme une **anomalie non résolue**.

**La liste noire passe à treize entrées, `IdleTime` seul ajouté.**

C'est le résultat que je voulais de ce dispositif : le soupçon était sérieux
(AUC binaire 0,94, τ = 3,0), et c'est la mesure qui a décidé, pas la prudence.

## 2. Ce qui rend la comparaison lisible

| contrôle | résultat |
|---|---|
| modèles quasi déterministes contre le papier | **0,0019** (tolérance 0,003) ✓ |
| bande de reproductibilité **intra-session**, 3 ajustements identiques | **0,0019** |

La bande intra-session est portée entièrement par le CNN (0,9982 / 0,9963 /
0,9963). `dnn`, `rnn` et `ftt` rendent **exactement** la même valeur trois fois.

**Les deux bras ont tourné dans la même session**, donc c'est bien la bande
intra-session qui borne ce qui est attribuable à la correction — pas la
dispersion entre sessions, qui est plus large.

## 3. Ce que la correction coûte

| | écart maximal hors bayésien naïf |
|---|---:|
| stratifié | **0,0040** (k-NN) |
| temporel | **0,0263** (k-NN) |

Rapport **×7**, la même signature que les douze autres raccourcis.

Les **cinq plus gros écarts** portent sur `knn`, `lightgbm`, `knn#tuned`, `rf`
et `xgboost` — tous des modèles qui se rejouent au quatrième chiffre. Le
résultat repose sur le sol le plus ferme.

Le bayésien naïf s'effondre (`nb#tuned` : −0,2235 en stratifié), ce que la §6.2
prédit déjà : un classifieur qui suppose l'indépendance conditionnelle est le
plus sensible aux colonnes corrélées restantes.

Seul `cnn` a un écart temporel (+0,0018) **sous la bande** : non attribuable.

## 4. Le classement temporel — la conclusion du papier se renforce

| rang | liste publiée (12) | liste corrigée (13) |
|---:|---|---|
| 1 | logreg#tuned 0,9950 | logreg#tuned 0,9928 |
| 2 | logreg 0,9949 | **ftt 0,9901** |
| 3 | **lightgbm 0,9906** | logreg 0,9881 |
| 4 | rnn 0,9892 | cnn 0,9848 |
| 5 | **xgboost 0,9888** | rnn 0,9837 |
| 6 | dnn 0,9887 | dnn 0,9773 |
| 7 | knn#tuned 0,9851 | **xgboost 0,9666** |
| 8 | knn 0,9837 | **lightgbm 0,9649** |
| … | | |
| 12 | rf 0,9758 | rf 0,9530 |

**LightGBM passe de la 3ᵉ à la 8ᵉ place, XGBoost de la 5ᵉ à la 7ᵉ.** La thèse
« les ensembles boostés quittent le sommet sous protocole temporel » n'est pas
seulement préservée : elle est bien plus nette qu'avec la liste publiée.

Un modèle linéaire mène toujours, et le corpus reste saturé sous le protocole
stratifié (les trois ensembles ≥ 0,999).

## 5. La limite à écrire : le FT-Transformer

| | macro-F1 temporel |
|---|---:|
| publié | 0,9966 |
| E8, liste publiée | 0,9779 — **écart au papier 0,0187** |
| E8, liste corrigée | 0,9901 — gain intra-session **+0,0122** |

`ftt` est le **seul détecteur qui gagne** à la correction, et il remonte de la
10ᵉ à la 2ᵉ place. Mais l'écart de cette session au papier (0,0187) **dépasse
l'effet mesuré** (0,0122).

**Ce que le papier peut dire :** dans une session où les deux bras sont
comparables, retirer `IdleTime` améliore le FT-Transformer et le ramène au
sommet. **Ce qu'il ne peut pas dire :** que 0,9901 est une amélioration sur le
0,9966 publié. Les deux doivent figurer.

Cette non-reproductibilité inter-session du `ftt` est elle-même à rapporter :
le papier ne quantifie nulle part la reproductibilité de ses détecteurs
neuronaux d'un environnement à l'autre.

## 6. État des runs

**179 sur 180.** Il ne manque que `ftt|corrigee|strat_seed5`, qui demande un
GPU — le FT-Transformer coûte 228 à 610 s par ajustement sur GPU et des heures
sur CPU.

Les quatre autres manquants ont été faits sur CPU et relevés depuis la console
(`logreg#tuned` 0,9956, `nb#tuned` 0,5019, `knn#tuned` 0,9945, `dnn#tuned`
0,9836). Ils sont marqués `"source": "console, session CPU"` dans le JSON :
seul le macro-F1 en a été conservé, et la provenance doit rester traçable.

*Note de comptabilité :* j'avais signalé `nb#tuned` comme hors plage avec une
tolérance de 0,004. C'était un faux positif — l'étendue de `nb#tuned` sur cinq
graines dans la campagne publiée est de **0,0362**, dix fois celle des autres
modèles, et `GaussianNB` n'a de toute façon aucun générateur aléatoire.

**14 configurations sur 15 ont désormais leurs cinq graines**, `ftt` étant la
seule à quatre. Sa dispersion stratifiée est de 0,00008 sur ces quatre
(0,9998 / 0,9998 / 0,9998 / 1,0000), donc la cinquième ne déplacera pas sa
moyenne au quatrième chiffre — mais le tableau doit dire *n* = 4 tant qu'elle
manque.

## 6bis. Ce que la republication demande encore

| élément | disponible ? |
|---|---|
| Tableau 2, colonnes `full` et `clean` | **inchangées** — elles n'utilisent pas la liste noire |
| Tableau 2, colonnes auditées | oui, sauf le *n* de `ftt` |
| Tableau 7 (calibration + recherche) | ECE et température : oui. Essais, temps et Δval : **inchangés**, voir ci-dessous |
| Tableau 8 (ECE sous les deux protocoles) | oui, entièrement |
| Tableau 10 (coût d'inférence) | **non — la cellule de coût n'a jamais tourné** |

**Une réserve à écrire pour le bras réglé.** E8 applique à la condition
corrigée les `best_params` de la campagne publiée, qui avaient été cherchés sur
la condition à douze colonnes. Le bras `#tuned` mesure donc *les
hyperparamètres publiés appliqués à la condition corrigée*, et non un
réajustement sur celle-ci. C'est défendable — ça isole l'effet du retrait de la
colonne de celui d'un nouveau réglage — mais le papier doit le dire.

## Entrées

- `experiments/e8/e8_results.json`
- `paper/article1_results.json`


---

## 7. Un bug dans le notebook E8 : l'objectif du calage de température

Trouvé en republiant les Tableaux 7 et 8. Le pipeline ajuste la température en
minimisant la **NLL** sur une grille de 80 points
(`colab/e3_calibration_residual.py`, fonction `temperature`) ; la fonction
que j'ai écrite dans E8 minimisait l'**ECE** sur une grille de 100 points au
pas de 0,05. **Objectif différent.**

Le correctif n'a demandé aucun réentraînement : les matrices de probabilités
d'E8 étaient conservées, et la température s'y recalcule avec l'objectif du
pipeline (`colab/e8bis_recalage_temperature.py`). Les 180 runs portent
désormais `temperature` (NLL, la bonne) et `temperature_ece` (l'ancienne,
gardée pour que l'écart reste lisible).

### Le témoin s'est trompé de quantité avant de se tromper de verdict

La première version comparait **T** au Tableau 7 publié et annonçait un écart
maximal de **0,821**, donc l'échec. Les deux moitiés du contrôle étaient
fausses :

- **la cible.** Le T publié pour le bayésien naïf est 5,821. La grille du
  pipeline s'arrête à **5**. Le recalage rend exactement 5,000 — c'est-à-dire
  **la valeur d'E3-A**, la recomputation que la §6.5 déclare déjà comme la
  bonne. Tout l'écart de 0,821 est un plafond de grille ;
- **la quantité.** T est un paramètre *intermédiaire*, posé sur une surface
  très plate. Deux jeux de probabilités quasi identiques y donnent des T
  éloignés sans que rien de rapporté ne bouge. Ce qu'il faut contrôler est ce
  que le tableau **rapporte** : l'ECE après calage.

Le témoin corrigé teste l'ECE calibrée contre E3-A et écarte les T posés sur
une borne de grille, dont l'écart ne renseigne pas sur la procédure.

### Ce qu'il donne — et le contraste n'était pas attendu

`verify_e8.py`, contrôle F, calculé depuis les fichiers versionnés :

| | paires | écart max | |
|---|---:|---:|---|
| ECE **brute**, les deux protocoles | 22 | **0,0031** | `rnn\|temporal` |
| ECE **calibrée**, stratifié | 7 | **0,0002** | `rnn\|strat_seed1` |
| ECE **calibrée**, temporel | 7 | **0,0075** | `rf\|temporal` |

L'ajustement sous-jacent se rejoue partout. Ce qui ne se rejoue serré que
d'un côté, c'est l'ECE **après** calage : sur le bras temporel, l'optimum de
NLL se déplace assez pour déplacer l'ECE de 0,0075, alors que l'ajustement
qui le porte se rejoue à 0,0031.

**C'est le calage qui amplifie, pas l'ajustement.** La dernière colonne du
Tableau 8 est donc la moins stable du manuscrit, et sa légende le dit
maintenant — avec les deux chiffres, pas avec une formule prudente.

## 8. Ce qui est entré dans le manuscrit

| élément | source |
|---|---|
| **Tableau 2** | E8, condition corrigée, entièrement |
| **Tableau 7** (T, ECEraw, ECEcal) | E8 recalé, condition corrigée |
| **Tableau 8**, entièrement | E8 recalé, condition corrigée |
| **Tableau 10**, colonne macro-F1 | E8, condition corrigée |
| **Figure 14** | redessinée, axe qualité depuis E8 |
| **Tableau 13**, macro-F1, ordre des lignes, température | E8 recalé |
| **Figures 5, 10, 18** | redessinées, `paper/regen_e8_figures.py` |
| légendes des Figures 5, 10, 18 | recalculées |
| prose des §6.1, §6.3, §6.5, §8 | recalculée |

Deux réserves écrites dans les légendes, parce qu'elles ne se devinent pas :

- **Tableau 7.** T est ajusté sur une grille bornée à 0,05 et 5, donc la
  valeur du bayésien naïf est *au plafond*. Et les colonnes essais, temps et
  Δval viennent de la recherche publiée, conduite sur la condition à douze
  colonnes : le bras `#tuned` mesure *les hyperparamètres publiés appliqués à
  la condition corrigée*, pas un réajustement sur celle-ci.
- **Tableau 8.** Le chiffre de stabilité ci-dessus.
- **Tableau 10.** La colonne macro-F1 vient de la condition corrigée, sur 54
  colonnes ; latence, débit et taille ont été mesurés **avant** la correction,
  sur 55 colonnes, et ne sont pas remesurés. La légende annonçait déjà
  « audited condition » alors que sa colonne macro-F1 portait encore les
  valeurs à douze — le bayésien naïf s'y trompait de **0,1028**. Nommer la
  provenance de chaque colonne vaut mieux qu'une colonne périmée sous une
  légende qui affirme le contraire.

La §8 lisait ce tableau à voix haute et affirmait donc le contraire de ce
qu'il montre désormais. Trois phrases corrigées : XGBoost n'est plus « à
égalité en tête » (LightGBM est seul au-dessus, de 0,0001), la régression
logistique passe de 0,9990 à 0,9963, et la marge temporelle du
FT-Transformer passe de « 0,9966 contre 0,9888 » à **0,9901 contre 0,9666**
— elle *grandit*, de 0,0078 à 0,0235.

### Les trois affirmations de la §6.5 qui ont bougé

| avant | après |
|---|---|
| ECE ≤ 0,0009 « pour tout modèle sauf le bayésien naïf » | ≤ **0,0015**, sauf la régression logistique **et** le bayésien naïf — l'erreur stratifiée de la logistique passe de 0,0003 à 0,0084 quand la colonne identifiante est retirée |
| « dix des onze détecteurs » se dégradent en temporel | **neuf sur onze**. Le onzième est la régression logistique, et elle va dans l'autre sens (rapport 0,4×) — non parce que son bras temporel progresse, mais parce que son bras stratifié est monté le rejoindre |
| rapports des trois mieux calibrés : 241 à 457 | **146 à 1403** |

Les températures des ensembles d'arbres ne sont **plus au plancher** de la
grille : XGBoost 0,85, LightGBM 1,46, forêt aléatoire 0,39. Retirer la colonne
identifiante a retiré ce qui rendait leurs postérieures quasi déterministes.

Ce qui **tient** : les trois détecteurs les mieux calibrés en stratifié
(`xgboost`, `lightgbm`, `ftt`) restent exactement les trois qui se dégradent
le plus. Même ensemble des deux côtés.

## 9. Ce qui attend encore, et pourquoi les cases sont vides

Une case vide n'induit personne en erreur ; une valeur de la condition à douze
posée à côté d'une valeur de la condition à treize, si.

| bloqué par | débloque |
|---|---|
| mesure de coût sur 54 colonnes (CPU, ~10 min) | colonnes de coût du Tableau 10, colonne débit du 13, axe horizontal de la Figure 14 |
| `e8_probs/` | Figures 9 (McNemar) et 11 (bootstrap) |

**La graine 5 du `ftt` est arrivée**, donc le Tableau 2 porte ses cinq graines
partout et le marqueur *n* = 4 a disparu de lui-même : il était calculé, pas
écrit à la main.

**La Figure 14 est redessinée**, et elle n'avait aucun script de régénération
— `MAPPING.md` la listait comme un manque. Elle en a un maintenant
(`paper/regen_e8_figures.py`). C'est le cas mixte du manuscrit : axe qualité
sur 54 colonnes, axe débit sur 55 et non remesuré, la légende nommant la
provenance de chacun. Ses trois affirmations sont recalculées et non
recopiées — l'étendue de débit tient trois ordres de grandeur, l'écart
logistique–FT-Transformer est de 0,0020 à 2 600 fois le débit, et le DNN
reste dominé sur les deux axes, par la seule régression logistique.

Il reste trois figures sans script : la 9 attend les matrices de
probabilités, la 2 et la 6 ne lisent que `article1_results.json` et pourraient
être scriptées à tout moment.

## 10. Ce que la Figure 18 montre maintenant

C'est le changement le plus visible du manuscrit. Sous la liste publiée, la
perte se dispersait : « chaque détecteur perd ailleurs ». Sous la liste
corrigée elle se rassemble sur `dos-hulk` et `dos-slowloris`, où le DNN,
XGBoost, LightGBM, k-NN et la forêt aléatoire tombent tous sous 0,93. La
cellule la plus basse est la forêt aléatoire sur `dos-hulk` à **0,814**, contre
0,957 pour la pire classe du détecteur de tête — et **onze de ces douze
cellules étaient au-dessus de 0,93** sous la liste publiée.

L'échelle de couleur a dû descendre de 0,90 à 0,80 : la légende publiée
affirmait que toute valeur montrée était au-dessus de 0,90, ce qui n'est plus
vrai.

---

## 11. La mesure de coût **a tourné** — et elle ne peut pas être recopiée

Je l'avais notée comme bloquante. Elle ne l'est pas : `cout_corrige` porte les
dix détecteurs sur 54 colonnes. Ce qui bloque est autre chose, et c'est plus
sérieux.

| | débit publié (55 col.) | débit E8 (54 col.) | rapport |
|---|---:|---:|---:|
| FT-Transformer | 430 | 5 758 | **13,4×** |
| forêt aléatoire | 7 738 | 94 024 | **12,2×** |
| 1D CNN | 3 134 | 21 770 | 7,0× |
| RNN | 3 803 | 14 937 | 3,9× |
| DNN | 5 269 | 15 242 | 2,9× |
| bayésien naïf | 228 377 | 482 664 | 2,1× |
| XGBoost | 46 317 | 53 803 | 1,2× |
| LightGBM | 6 281 | 4 973 | 0,8× |
| régression logistique | 1 139 252 | 635 460 | 0,6× |
| k-NN | 1 875 | 778 | **0,4×** |

De 0,4× à 13,4×, **dans les deux sens**. Une colonne retirée sur 55 ne produit
pas ça.

### Une des causes est un artefact de mesure, et elle se mesure

`verify_cout_protocole.py`. Les deux campagnes n'emploient pas le même
protocole de débit :

```
papier   for _ in range(20): predict_proba(lot_de_512)
E8       predict_proba(lot_de_10240)          # un seul appel
```

Sur un estimateur parallèle, chaque appel paie un démarrage du backend
joblib ; la boucle du papier le paie **vingt fois**. Mesuré ici, machine
identique, modèle identique, données identiques :

| modèle | 20 × 512 | 1 × 10 240 | rapport |
|---|---:|---:|---:|
| forêt aléatoire | 5 411 f/s | 30 262 f/s | **5,6×** |
| k-NN | 15 726 f/s | 19 071 f/s | 1,2× |

Le protocole seul vaut **5,6×** sur la forêt aléatoire — l'essentiel de son
12,2× — et presque rien sur le k-NN, qui est justement celui qui va dans
l'autre sens. L'effet est propre à l'estimateur, comme les écarts observés.

La même remarque vaut pour les quatre modèles Keras, dont chaque appel à
`predict()` paie un surcoût d'API que **le manuscrit chiffre lui-même à
77 ms**. Le papier fait vingt appels de 512 lignes ; E8 en fait un de 10 240,
découpé en interne.

### Ce que ça met en cause dans le manuscrit

La légende publiée du Tableau 10 affirme que la colonne de débit

> amortises that overhead and is the one on which we base the comparison.

Pour tout estimateur qui a un surcoût par appel, c'est **l'inverse** : la
boucle le paie à chaque tour. La phrase est à revoir, et avec elle la lecture
que la §8 en fait — « a hundred times faster than the FT-Transformer » vient
de cette colonne.

### Ce que le script n'établit pas

Que le protocole explique **tout** l'écart. Les deux sessions n'ont pas tourné
sur la même machine, et le k-NN va dans l'autre sens pour une raison qui n'est
pas mesurée ici. Ce qui est établi suffit à la décision : **on ne peut ni
recopier une colonne dans l'autre, ni les mélanger.**

### La décision revient à l'auteur

Trois options, et je ne tranche pas seul parce que la troisième change le
propos de la §8 :

1. **garder les débits publiés**, la légende nommant leur condition — c'est
   l'état actuel du document, et c'est cohérent ;
2. **republier les débits d'E8** sur 54 colonnes : condition homogène avec le
   reste du tableau, mais il faut réécrire les affirmations de coût de la §8,
   dont la recommandation — sous ce protocole, la forêt aléatoire (94 024)
   dépasse XGBoost (53 803), et le FT-Transformer n'est plus 100× plus lent
   mais 9× ;
3. **remesurer les deux conditions dans une seule session, sous le protocole
   qui amortit**, ce qui est la seule façon d'avoir une colonne à la fois
   homogène et conforme à ce que la légende annonce. Coût : une cellule, une
   dizaine de minutes.

La troisième est la bonne si le temps le permet, et la cellule est écrite :
`colab/e8ter_cout_deux_conditions.py`. Elle mesure les deux conditions dans
une session, sous **les deux protocoles** — sans garder celui du papier à
côté, on ne saurait pas si un écart au Tableau 10 vient de la machine ou de
la mesure. Son témoin le tranche : si la condition publiée sous le protocole
du papier retrouve l'ordre de grandeur du Tableau 10, l'écart est bien le
protocole et la colonne amortie peut le remplacer ; sinon la machine diffère,
les deux conditions restent comparables entre elles et rien ne peut être
comparé à la campagne publiée.

---

## 12. Le GPU intermittent de Colab, et ce qu'il a contaminé

Colab attribue un GPU quand il en a un de libre, et pas autrement. La campagne
E8 a donc tourné tantôt sur GPU, tantôt sur CPU seul, **sans que rien ne le
consigne**. C'est l'explication qui manquait au FT-Transformer.

### L'indice, et pourquoi il a fallu deux essais pour le lire

La cellule 10 donne `ftt` à **5 758 flux/s** ; le papier a 430, et une mesure
CPU refaite aujourd'hui donne 464. J'avais d'abord écarté l'hypothèse GPU en
regardant la latence à une ligne : 65 ms dans la cellule 10, donc « pas un
GPU ». **C'était un mauvais raisonnement, et le manuscrit contenait déjà de
quoi le savoir** — la §8 établit que cette latence est dominée par un surcoût
fixe de l'API de prédiction, donc elle reste vers 65–80 ms sur GPU comme sur
CPU. Elle ne discrimine rien.

Ce qui discrimine est le débit par lots. Une fois l'amortissement des appels
déduit — mesuré, pas supposé :

| | papier (CPU) | e8ter (CPU) | cellule 10 | amortissement seul | reste |
|---|---:|---:|---:|---:|---:|
| `ftt` | 430 | 464 | 5 758 | 557 | **10,3×** |
| `rnn` | 3 803 | 4 744 | 14 937 | 7 590 | 2,0× |
| `cnn` | 3 134 | 3 812 | 21 770 | 28 590 | 0,8× |
| `dnn` | 5 269 | 6 693 | 15 242 | 46 851 | 0,3× |

Dix fois de trop sur le FT-Transformer, et des restes incohérents entre les
quatre — la signature d'une session où le backend n'était pas le même partout.

### Ce qui est corrigé

`colab/e8ter_cout_deux_conditions.py` épingle désormais
`tf.device("/CPU:0")` autour de la **mesure** des modèles Keras — l'ajustement
peut rester où il est rapide, c'est un coût d'inférence qu'on rapporte — comme
le fait le pipeline publié, qui avait cette précaution et dont la cellule 10
s'était écartée. Chaque mesure porte `"backend": "CPU"`, la présence d'un GPU
est consignée, et toute mesure Keras antérieure à cet épinglage est refaite
plutôt que crue sur parole.

`cout_corrige` garde ses chiffres — c'est ce que la cellule a produit — avec
une note qui dit ce qui n'y est pas tracé.

### Ce que ça vaut pour le reste de la campagne

Rien de ce qui touche à la **détection** n'est en cause : la bande de
reproductibilité intra-session (§2) a été mesurée par trois ajustements
identiques dans une même session, donc elle capture déjà le backend qui y
régnait, quel qu'il soit. Et la limite du FT-Transformer écrite en §5 — son
écart de 0,0187 au papier dépasse l'effet de 0,0122, donc le gain n'est pas
rapportable comme une amélioration sur le chiffre publié — trouve ici un
mécanisme plausible de plus : la sélection de noyaux cuDNN n'est pas la même
d'un backend à l'autre.

---

## 13. Tout est mesuré. Ce que la republication complète a changé

`e8ter` a remesuré le coût des deux conditions dans une seule session, sous
les deux protocoles, modèles Keras épinglés au CPU. `e8quater` a calculé
McNemar et le bootstrap **là où sont les 380 Mo de matrices** et n'en a
rapporté que quelques kilo-octets. Les deux témoins passent.

### Le témoin du coût, en deux lectures

**La machine ressemble à celle du papier :** sept détecteurs sur dix
retrouvent le Tableau 10 à 1,5× près sous le protocole du papier. Trois n'y
sont pas — `lightgbm` (2,08×), `cnn` (2,06×), `knn` (0,30×) — et ceux-là ne
sont pas comparables à la campagne publiée, seulement aux deux conditions
mesurées ici.

**Le protocole vaut de 1,0× à 10,7×.** Les plus gros gains vont au DNN
(10,7×), à la forêt aléatoire (8,5×) et au CNN (4,5×) : exactement les
détecteurs qui paient un surcoût par appel.

### Ce qui débloque, et ce que ça change

La colonne de débit du Tableau 10 est désormais **une vraie mesure amortie** —
un appel sur 10 240 flux à taille de lot 512 — c'est-à-dire ce que sa légende
annonçait déjà. L'ancienne bouclait vingt appels de 512 et payait le surcoût
vingt fois, ce qui écrasait le débit de tout détecteur qui en a un.

**Les deux colonnes deviennent alors informatives séparément, et elles
classent différemment :**

| | débit (lots) | latence p50 |
|---|---|---|
| 1 | logreg 601 449 | logreg 0,14 ms |
| 2 | **rf 58 151** | xgboost 1,22 ms |
| 3 | dnn 51 972 | lightgbm 1,55 ms |
| 4 | xgboost 42 687 | knn 25,79 ms |
| 5 | cnn 28 580 | **rf 55,16 ms** |

La forêt aléatoire est le cas qui sépare les deux régimes : **deuxième sur le
débit, 55 ms par flux**, soit 45 fois la latence médiane de XGBoost.

### Trois affirmations de la §8 qui tombent

- « **highest throughput among the accurate models** » pour XGBoost : faux, il
  est **quatrième**. La régression logistique, la forêt aléatoire et le DNN
  passent devant.
- « **smallest latency tail among the tree ensembles** » pour XGBoost :
  **c'était déjà faux avant cette republication**. Le Tableau 10 publié donne
  LightGBM à 1,42 ms de p99 contre 4,66 à XGBoost. L'erreur ne doit rien à la
  correction — elle était dans le manuscrit depuis le début, et aucun des
  trois vérificateurs ne pouvait la voir : ils contrôlent la cohérence, le
  style et la mise en page, pas la lecture d'un tableau.
- « **a hundred times faster than the FT-Transformer** » : c'est **78 fois**.

La recommandation est réécrite en conséquence, et elle est meilleure : elle
distingue les deux régimes au lieu de les confondre. En lots, la régression
logistique domine sans partage. À l'arrivée de chaque flux, XGBoost mène sur
la médiane, LightGBM tient la queue plus serrée.

### Deux erreurs que j'ai faites en écrivant cette section

Elles sont notées parce que le contrôle qui les attrape est maintenant dans
`verify_e8.py`, section G :

- j'ai écrit que la forêt aléatoire était « avant-dernière en latence ». Elle
  est **cinquième sur neuf** ;
- j'ai écrit qu'« aucun détecteur ne mène les deux colonnes », et **la
  régression logistique mène les deux**. Pire : le contrôle que j'avais écrit
  pour vérifier cette phrase passait **à vide**, avec un `or True` dans sa
  condition. Un contrôle qui ne peut pas échouer ne contrôle rien.

Un rang est exactement le genre d'affirmation qu'on écrit de mémoire et qui
devient faux dès que la mesure change. Ils sont tous recalculés désormais.

### Figures 9 et 11

Redessinées sur la condition corrigée depuis `stats.corrigee`. **11 paires
restent indistinguables sur 45** sous Holm — le même nombre que sous la liste
publiée, ce qui dit que la saturation du protocole stratifié survit à la
correction. Le témoin : le bras publié rejoue la campagne du papier à
**0,000768** près sur la moyenne bootstrap.

Il ne reste **aucune figure sans script de régénération** parmi celles que la
correction touche.
