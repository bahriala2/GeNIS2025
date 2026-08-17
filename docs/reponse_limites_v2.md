# Réponse au second rapport de limites

Cinq points, vérifiés un par un contre le manuscrit courant
(`paper/GeNIS_benchmark_article.docx`, 12 sections, 300 blocs, 20 figures,
16 tableaux). Les numéros de blocs ci-dessous sont ceux de l'extraction
`word/document.xml` et permettent de retrouver chaque passage.

**Résumé.** Un seul des cinq points est ouvert. Le point 2 est un artefact de
lecture, et il explique à lui seul les points 1 et 3. Le point 4 est traité au
long dans le manuscrit et l'auteur du rapport le reconnaît. Le point 5 est
réel, et c'est le seul qui demande du travail neuf — il a d'ailleurs fait
apparaître un défaut que le rapport ne signalait pas.

| # | Point | Verdict | Action |
|---|---|---|---|
| 2 | §8 tronquée, §9 absente | **Faux** — §9 existe (blocs 234–254) | Relire en deux moitiés |
| 1 | Fuite par l'audit sur le test | **Déjà traité** — §4.3 et §9 | Rendre la réponse plus difficile à manquer |
| 3 | Seuil τ heuristique, 8 → 13 | **Déjà traité et mesuré** — §9, Fig. 19 | Renvoi depuis §4.3 |
| 4 | Découpage par classe = étiquettes | **Déjà traité** — §4.2, Fig. 4, §6.8 | Délimitation théorique explicite |
| 5 | Effondrement LightGBM à 10 s | **Ouvert** | Mécanisme + expérience E6 |

---

## Point 2 — « le manuscrit s'arrête au milieu d'une phrase et omet la §9 »

**C'est faux, et c'est le point le plus important du rapport**, parce qu'il
explique les points 1 et 3.

Le manuscrit courant compte douze sections de premier niveau :

```
    7  1. Introduction                     194  7. External validation: CICIDS2017
   21  2. Related work                     214  8. Discussion
   36  3. The GeNIS corpus                 234  9. Threats to validity
   48  4. Evaluation protocol              255 10. Conclusion
   97  5. Models                           259 11. Data and code availability
  103  6. Results                          261 12. Declaration of generative AI
```

La phrase que le rapport dit tronquée est complète dans le fichier :

> Section 7 adds one further data point: seven pairs of numerically identical
> columns among the 69 behavioural candidates of CICIDS2017, produced by a
> different exporter, **ten of whose fourteen columns again score exactly zero
> importance.**

Le paragraphe (bloc 216) fait 1 814 octets de XML, tient dans deux runs et se
termine proprement. Rien dans le document ne casse une extraction à cet
endroit.

La coupure tombe au bloc 216 sur 300, soit **72 % du document**. C'est la
signature d'une lecture tronquée par une limite de contexte, pas d'un défaut
du fichier. Ce qui a produit ce rapport n'a donc jamais vu la fin de la §8, ni
la §9, ni la conclusion.

**Or la §9 s'intitule « Threats to validity » et répond nommément aux points 1
et 3.** Le rapport signale comme découvertes deux limites que le manuscrit
déclare lui-même, dans la section qu'il n'a pas lue.

**Provenance.** Le manuscrit n'a été transmis à personne : ce rapport n'est
pas une relecture externe. Il vient donc d'un outil auquel le document a été
donné localement, et c'est cohérent — 22 500 mots dans un .docx, une lecture
qui s'arrête aux trois quarts. Il n'y a par conséquent aucun relecteur à qui
renvoyer quoi que ce soit.

*À faire :* relancer la critique sur le texte complet, **en deux moitiés**.
Le manuscrit fait 21 749 mots et la coupure naturelle est le début de la §7,
qui est une unité autonome — la validation externe sur CICIDS2017 :

| moitié | sections | mots | part |
|---|---|---:|---:|
| 1 | §1 à §6 | 13 594 | 62,5 % |
| 2 | §7 à §12 | 8 155 | 37,5 % |

La lecture qui a produit ce rapport s'est arrêtée à **74,5 %** du texte, au
milieu de la §8. Les points 1, 3 et 4 devraient donc disparaître d'eux-mêmes
sur la seconde moitié, puisqu'ils y sont traités. C'est aussi le seul moyen de
savoir si cette seconde moitié appelle des critiques que personne n'a encore
formulées : elle n'a jamais été relue.

---

## Point 1 — « l'audit a été exécuté sur la partition de test »

**Exact, et c'est le manuscrit qui le dit le premier.** §4.3 y consacre quatre
paragraphes consécutifs (blocs 83–86) :

- **bloc 83, « What the audit is computed on ».** La déclaration :
  > The blacklist was therefore selected with test-set information, and the
  > benchmark that follows was trained on a feature set that testing helped
  > choose. We state this plainly, and the three paragraphs that follow report
  > what we did about it: the obvious correction fails for a reason we
  > measure, an audit confined to the training partition works, and the
  > blacklist it returns on its own is the published blacklist, column for
  > column.

  La seconde moitié de cette phrase est nouvelle : elle annonçait auparavant
  une réponse (« we have since measured what it costs ») au lieu de la donner,
  et c'est exactement là que le lecteur du rapport s'est arrêté.

- **bloc 84, « Why moving the audit to the validation partition does not
  work ».** Le remède évident échoue, et pour une raison mesurée : la
  validation jouxte la fenêtre d'entraînement, le test est un cran plus loin.
  Les exactitudes temporelles y sont plus hautes de 0,075 en moyenne sur 53
  des 63 colonnes. Une décroissance avec la distance temporelle ne s'estime
  pas sur la partition la plus proche de l'entraînement. La Figure 20 le
  montre directement.

- **bloc 85, « The audit that does work ».** L'audit imbriqué : les flux
  d'entraînement de chaque classe ordonnés puis coupés 75/25, ce qui n'ouvre
  **ni la validation ni le test**. Il rend les huit colonnes publiées comme
  ses huit plus basses transférabilités, et le plus grand écart de toute la
  distribution (0,062) tombe exactement entre elles et le reste.

- **bloc 86, « The control on the blacklist the nested audit produces
  alone ».** Le contrôle final : en classant les 37 colonnes éligibles par
  leur transférabilité imbriquée et en coupant au plus grand écart — la règle
  énoncée plus haut, à qui on ne dit pas combien de colonnes attendre — on
  retrouve **exactement** les huit colonnes publiées. La condition auditée
  entraînée sur la liste imbriquée *est* la condition auditée du papier,
  colonne pour colonne. Encadré par les deux lectures dégradées, toutes deux
  réentraînées (E4c).

La §9 le reprend au bloc 247, « The blacklist was selected with test-set
information, **and is recoverable without it** ».

**Le point est donc traité au-delà de ce que le rapport demande** : il ne
s'agit pas d'une concordance approximative mais d'une identité, vérifiée par
`experiments/e4a/verify_nested_blacklist.py` (19 contrôles sur 19).

*Corrigé :* le bloc 83 donne désormais sa conclusion dès la déclaration, au
lieu de la promettre.

---

## Point 3 — « le seuil τ < 0,50 est heuristique ; τ* fait passer 8 à 13 »

**Exact, déclaré par le manuscrit, et — c'est le point que le rapport
manque — mesuré.**

Le rapport écrit que le choix « impacte directement les performances et
classements des modèles ». C'est précisément l'hypothèse que l'expérience E4c
a testée, en **réentraînant** tous les détecteurs sous cinq listes noires
différentes, de zéro à seize exclusions, sous les deux protocoles
(§9, bloc 244, Figure 19) :

| Mesure | Valeur |
|---|---|
| Décalage max. de macro-F1 temporel, seuil 0,40 → 0,70, huit détecteurs | **0,023** |
| Décalage max. de macro-F1 stratifié, mêmes conditions | **0,004** |
| Décalage médian, tous détecteurs et deux protocoles | **0,0017** |
| Exception : bayésien naïf | 0,129 |

L'exception est attendue et expliquée : un classifieur qui suppose
l'indépendance conditionnelle est le plus sensible aux colonnes corrélées qui
restent.

Le manuscrit va plus loin que ce que le rapport réclame : il déclare que le
choix publié **n'est pas le choix flatteur** — la liste plus stricte à 0,70
score plus haut sous le protocole temporel pour sept détecteurs sur neuf
(bloc 246). Et il retire explicitement toute prétention à un intervalle vide
intrinsèque : « we withdraw any claim that the boundary is intrinsic to the
data » (bloc 235).

Trois objets couvrent la question : le Tableau 15 (normalisations), le
Tableau 16 (sept seuils), la Figure 19 (le coût réentraîné).

*Corrigé :* la §4.3 renvoie désormais à la §9 dès l'énoncé du seuil. Le
lecteur ne rencontre plus 0,50 quarante blocs avant sa justification.

---

## Point 4 — « le découpage temporel par classe utilise les étiquettes »

**Exact, et le manuscrit le dit dans les termes mêmes du rapport**, au
paragraphe qui définit le protocole (§4.2, bloc 53) :

> Two properties of this construction must be stated before any result is read
> from it. **It uses the class label to build the partition**, since the
> ordering is applied within each class, **so it is not a model of deployment
> on future unlabelled traffic**; it answers the narrower question of whether
> a detector still recognises later flows of a family it has already seen. […]
> We therefore use it as a **diagnostic** within-class temporal protocol
> throughout, **and we do not present its results as deployment
> generalisation.**

S'y ajoutent la Figure 4, qui pose les quatre découpages côte à côte sur un
axe unique de temps de capture, et la §6.8, qui mesure les deux questions que
le découpage par classe ne pose pas :

- les **origines glissantes** (Figure 15) déplacent la coupure à cinq
  positions, dont une coupure chronologique qui n'utilise pas les étiquettes ;
- le **leave-one-family-out** (Figure 16) retire une famille entière, ce qui
  est la question de déploiement posée directement.

Le rapport le reconnaît (« Bien que les auteurs précisent le rôle
diagnostic ») et demande une meilleure délimitation *théorique*. C'est une
demande légitime : le manuscrit distingue les trois questions en pratique,
protocole par protocole, mais ne les nomme jamais ensemble.

*Corrigé :* la §4.2 nomme désormais les trois questions que « temporel »
recouvre et dit laquelle chaque protocole répond, en concluant que seule la
troisième est de la généralisation de déploiement et qu'aucun résultat des
§6.1 à 6.7 n'est offert comme réponse à celle-là.

---

## Point 5 — l'effondrement de LightGBM à 10 s

**Le seul point réellement ouvert, et le rapport a raison.** Le manuscrit
qualifie l'événement statistiquement — « an isolated failure of a single fit
rather than an instability of LightGBM at that window » — sans dire *pourquoi*
un ajustement échoue. Dans un benchmark Q1, c'est insuffisant.

En cherchant, j'ai trouvé un défaut que le rapport ne signalait pas : la §8
décrivait encore l'effondrement comme « one LightGBM seed **out of three** …
while the other two stayed near 1.0000 », alors que le Tableau 6 porte cinq
graines depuis E5. **Corrigé** (commit `d869fbc`).

### Ce que les données disent déjà

Le profil de la graine 3 à 10 s, contre 1,0000 pour les quatre autres :

| Mesure | Graine 3 | Graines 1, 2 |
|---|---|---|
| macro-F1 | 0,8374 | 0,9999 / 1,0000 |
| **exactitude globale** | **0,9893** | 0,99999 |
| ROC-AUC binaire | **0,9604** | 1,0000 |
| taux de faux positifs | 7,71 % | 0,014 % / 0 % |
| **temps d'ajustement** | **335,7 s** | 291,4 / 289,0 s |

Trois lectures :

1. **La dégradation est confinée aux classes rares et suit leur rareté**
   (Spearman ρ = 0,933 sur les neuf classes) :

   | classe | part du corpus | F1 graine 3 |
   |---|---:|---:|
   | bruteforce-ftp | 0,227 % | **0,0561** |
   | bruteforce-ssh | 0,589 % | **0,6439** |
   | bruteforce-smb | 0,679 % | 0,9565 |
   | benign | 2,378 % | 0,9202 |
   | dos-hulk | 4,607 % | 0,9787 |
   | dos-slowloris … dos-udp | ≥ 11,4 % | ≥ 0,9911 |

2. **Ce n'est pas un artefact de seuil.** Le ROC-AUC tombe de 1,0000 à 0,9604 :
   le modèle ne sait pas *ordonner* ces flux, il ne se contente pas de mal
   placer une frontière.

3. **L'ajustement a suivi un autre chemin.** +15 % de temps sur des données
   identiques, à budget d'arbres fixe.

### D'abord : ce que « graine » veut dire ici

En cherchant le mécanisme, j'ai dû vérifier ce que la graine pilote réellement,
et **ce n'était écrit nulle part** — ni dans le manuscrit, ni dans mes notes.

Le pipeline construit ses détecteurs avec `random_state=0` **fixe** et fait
varier `train_test_split(..., random_state=s)`. **Une graine, dans tout ce
papier, est une graine de découpage.** Vérifié dans
`colab/article1_pipeline.ipynb` et repris à l'identique par E5.

Cela change la question. Changer de graine change **deux choses ensemble** :

1. la composition du jeu d'entraînement et du test ;
2. la grille d'histogramme de LightGBM, dont les bornes sont posées sur un
   tirage de 200 000 lignes **de ce jeu d'entraînement**.

Sur GeNIS les deux sont confondues, et aucune analyse des résultats archivés ne
peut les séparer. Ce qui suit est donc plus modeste que ce que j'ai d'abord
écrit : deux candidats éliminés, un troisième rendu plausible, et une
expérience pour trancher.

### Deux des trois pistes du rapport sont éliminées

La campagne fixe `n_estimators=300`, `num_leaves=63`, `learning_rate=0.1`
(`DEFAULTS_SK` du pipeline) et laisse tout le reste aux défauts. La recherche
d'hyperparamètres n'a rien adopté de plus : `best_params` est vide, la
configuration déclarée atteignant déjà 1,0000 en validation. Les défauts qui
comptent :

```
    subsample         = 1.0    subsample_freq = 0   ->  pas de bagging
    colsample_bytree  = 1.0                         ->  pas de tirage de colonnes
    subsample_for_bin = 200 000                     ->  bins poses sur un tirage
```

Le rapport suggère « artéfacts de binning d'histogrammes, écrêtage de gradient
ou stochastique de sous-échantillonnage ». **Le sous-échantillonnage de lignes
et de colonnes est désactivé**, et la descente de gradient est déterministe.
Reste le binning — la première piste du rapport.

La couverture de ce tirage dépend de la taille du corpus, donc de l'intervalle
d'agrégation :

| intervalle | entraînement | couverture des bins | part de bruteforce-ftp |
|---|---:|---:|---:|
| 5 s | 1 664 146 | 12,0 % | 0,121 % |
| **10 s** | **883 279** | **22,6 %** | **0,227 %** |
| 30 s | 346 471 | 57,7 % | 0,579 % |
| 60 s | 203 292 | **98,4 %** | 0,987 % |

À 60 s, le tirage prend presque toutes les lignes : **la grille y est quasi
déterminée par les données**, et c'est le seul intervalle où aucune graine ne
s'écarte. La coïncidence rend l'hypothèse intéressante ; elle ne la démontre
pas — à 5 s la couverture est plus faible encore et aucune graine ne tombe.

### Reproduction minimale

`experiments/e6/reproduce_binning.py` construit une classe rare à 0,230 % du
corpus, séparée par un intervalle de 1/1000 de l'axe, **découpage calculé une
fois et immobile entre les deux bras**. Seul `subsample_for_bin` change, ce qui
permet d'attribuer l'écart au binning et à rien d'autre — précisément ce que
les données de GeNIS ne permettent pas.

> **Chiffres en cours de calcul** — `reproduce_binning.py` tourne (32
> ajustements, ~21 min). Le contraste est déjà établi sur une version
> allégée : écart-type 0,1141 en binning échantillonné contre **0,0000**
> en binning déterministe, les seize graines rendant alors la même valeur.

Deux choses comptent également : **l'amplitude** (le binning seul suffit) et
**la forme** (des paquets discrets séparés par un trou, pas une dispersion
autour d'une moyenne — exactement ce qu'on observe sur GeNIS, où aucun run n'a
scoré entre 0,84 et 0,99).

### Ce que cela reste, et comment trancher

Je n'ai **pas** montré que c'est ce qui est arrivé à la graine 3. Sur GeNIS,
composition du découpage et grille d'histogramme bougent ensemble.

L'expérience qui les sépare coûte **cinq ajustements**, ~45 min :
`colab/e6_binning_deterministe.ipynb` refait les cinq découpages à 10 s avec
`subsample_for_bin` porté au-delà de la taille du jeu d'entraînement.

| résultat | conclusion |
|---|---|
| l'effondrement disparaît | c'est la grille d'histogramme |
| l'effondrement persiste | c'est la composition du découpage |
| liste modifiée sans disparaître | le binning module sans causer seul |

Le notebook rejoue aussi une graine **saine** avec le binning d'origine. Sans ce
témoin, une différence entre les deux colonnes pourrait venir de
l'environnement plutôt que du binning ; s'il ne reproduit pas, le notebook
refuse de conclure.

**Aucune des trois issues n'affaiblit le papier.**

---

## Actions

| | Action | État |
|---|---|---|
| 1 | §8 : « one seed out of three » → « out of five » | **fait** (`d869fbc`) |
| 2 | §4.3 bloc 83 : donner la conclusion dès la déclaration | **fait** |
| 3 | §4.3 bloc 60 : renvoyer à la §9 depuis le seuil | **fait** |
| 4 | §4.2 : nommer les trois questions de généralisation | **fait** |
| 5 | §6.4 et §9 : le mécanisme de binning | rédigé, entre avec `e6_results.json` |
| 6 | Notebook E6 : la preuve décisive | **fait**, à exécuter sur Colab |
| 7 | Relancer la critique en deux moitiés, coupure après la §6 | **vous** |
