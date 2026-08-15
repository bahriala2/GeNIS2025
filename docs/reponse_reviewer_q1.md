# Réponse à la relecture Q1

État au 15 août 2026. Trois colonnes : ce qui est **fait** dans le manuscrit, ce qui
est **faisable sans réentraîner** et attend seulement d'être lancé, et ce qui exige une
**campagne**.

Le relecteur formule le diagnostic central ainsi : *« certaines limites doivent être
traitées expérimentalement et pas seulement déclarées »*. C'est la bonne critique. Ce
document sépare donc systématiquement ce qui a été mesuré de ce qui reste déclaré.

> **Numérotation.** L'insertion de la section 7 (second corpus) a décalé ce qui suit :
> les sections 7–11 sont devenues 8–12 et les tableaux 9–12 sont devenus 11–14. Les
> renvois écrits **avant** cette insertion, plus bas dans ce document, sont restés dans
> l'ancienne numérotation : y lire §9 pour « §8 » (*Threats to validity*) et Tableau 14
> pour « Tableau 12 » (sensibilité au seuil). L'ancienne figure 13 est devenue la 14.

---

## Fait dans cette révision

### P2, seuil τ = 0.5 (priorité 2 du relecteur)

Le manuscrit portait une phrase de §8 disant que le seuil est arbitraire. Il porte
maintenant une mesure. **Nouveau Tableau 12** et un paragraphe en §8, calculés par
`paper/sensitivity_threshold.py` depuis `audit.transfer_table`, sans réentraînement.

Trois résultats, dont un défavorable :

| | |
|---|---|
| Stabilité locale | La liste noire est **identique pour tout seuil dans ]0.49, 0.54]**. Les huit colonnes exclues ne sont pas un artefact de bord. |
| Séparation naturelle | Le plus large vide de la distribution des τ éligibles est **entre 0.67 et 0.79**, pas autour de 0.5. Un seuil placé là exclurait **seize** colonnes comportementales, pas huit. |
| Coût du choix | Le tableau donne les sept seuils de 0.3 à 0.9, sous τ et sous τ*. |

Le manuscrit dit désormais que le seuil retenu **n'est pas la séparation que les
données auraient choisie**, et pourquoi il est conservé quand même. C'est plus faible
que ce que le relecteur espérait, et plus honnête que la version précédente.

Ce qui manque toujours : le macro-F1 de chaque détecteur sous chacune des sept listes.
Sept campagnes. Le manuscrit le dit explicitement.

### P5, méthodologie statistique (priorité 5)

§4.5 réécrite. Elle distingue maintenant trois questions que le manuscrit
confondait :

- **McNemar** s'applique aux vecteurs de prédictions multiclasses appariés sur la même
  partition de test, graine 1. Il teste si deux détecteurs se trompent sur des flux
  différents, **pas** si leurs macro-F1 diffèrent.
- **Le bootstrap** à 1 000 rééchantillonnages porte l'incertitude sur le macro-F1
  lui-même.
- **Les cinq graines** rééchantillonnent le découpage, pas le corpus. Leur dispersion
  mesure la sensibilité au découpage et **ne sont pas des réplications indépendantes**.
  Elles ne sont donc pas agrégées dans le test de significativité, et leur écart-type
  est présenté comme une mesure de stabilité, pas comme une erreur type.

La demande du §17 est traitée dans la même phrase : significativité et magnitude sont
rapportées ensemble, parce que sur ce corpus un écart peut être détectable et
opérationnellement nul.

### Problème 4 et §14, taxonomie des raccourcis

Nouveau paragraphe en §4.3, *« What the rule can and cannot separate »*. Il distingue
quatre natures : positionnelle, identifiant, redondante, et **sensible à la
distribution**. Et il concède le point que le relecteur soulève :

> A low transferability ratio establishes that a feature's predictive power does not
> survive a change of protocol; it does not establish that the power was spurious to
> begin with.

Le manuscrit nomme les deux features concernées, `SIntPkt` et `SIntPktMax`, et dit
qu'il ne peut pas affirmer les avoir distinguées des six colonnes dupliquées. L'exclure
est conservateur pour un benchmark, ce n'est pas la même chose que retirer une fuite.

### §15, l'arithmétique 12 / 13 / 17

Rendue explicite en §4.3 : **4 positionnelles + 8 comportementales = 12**, la liste
publiée ; **4 + 13 = 17** sous τ*. Tout compte du manuscrit est l'un des deux.

### §10, couverture des familles de modèles

Phrase ajoutée en §5, dans les termes que le relecteur suggère : la sélection ne vise
pas l'exhaustivité mais un représentant par famille, et ajouter un second membre d'une
famille déjà représentée n'infléchirait aucune conclusion, puisque toutes portent sur le
protocole et non sur le vainqueur.

### Défaut trouvé en révisant, hors relecture

Les tableaux n'étaient **pas dans l'ordre** : l'ordre physique était 1 à 8, puis 10, 11,
et enfin 9 en §8. Renumérotés, 1 à 12 dans l'ordre d'apparition. Les références croisées
ont suivi, et « the descriptor's Table 12 » est devenue « Table 12 of the corpus
descriptor [4] » pour éviter la collision avec le nouveau Tableau 12.

---

## Deuxième passe de relecture : ce qui a bougé depuis

Le relecteur situe désormais le manuscrit à 8/10 contre 7 à 7,5, et valide la taxonomie, la
clarification statistique et l'arithmétique 12/13/17. Quatre points restaient. Deux ont été
traités depuis dans le texte, deux ont reçu leur outil.

**Formulation « attribution-based auditing failed to identify ».** Le relecteur a raison :
l'absence d'importance par permutation ne prouve pas qu'une méthode d'attribution est fausse,
elle mesure une autre quantité sous dépendance entre variables. Les quatre occurrences
deviennent « assigned near-zero importance to », et §6.2 gagne la phrase qui le dit :

> This is not evidence that the attribution measure is wrong: under dependence between
> predictors it estimates a different quantity, the loss attributable to one feature when the
> others remain available, and that quantity is genuinely near zero here.

**Pourquoi publier sous τ < 0.5 plutôt que sous la séparation naturelle.** Paragraphe ajouté en
§8. Deux raisons vérifiables : un seuil numérique unique appliqué aux deux normalisations les
garde comparables, ce qu'une frontière choisie séparément pour chacune ne ferait pas ; et la
liste noire produite est celle sous laquelle **tous les modèles de l'article ont été
entraînés**. Déplacer le seuil après la campagne reviendrait à publier un jeu de features sous
lequel aucun chiffre rapporté n'a été produit.

**Second corpus. Fait.** `colab/e2_cicids2017_audit_v5.ipynb` a tourné sur les 2 830 743 flux de
CICIDS2017 (`GeneratedLabelledFlows`, et non `MachineLearningCVE`, faute d'horodatage dans cette
dernière). Résultats bruts dans `experiments/e2/`, lecture dans son `FINDINGS.md`, et **section 7
du manuscrit**, « External validation on a second corpus », avec les tableaux 9 et 10 et la
figure 13. Les sections suivantes ont été renumérotées, 7–11 devenant 8–12, les tableaux 9–12
devenant 11–14, et l'ancienne figure 13 devenant 14.

La figure de `e2_figures.zip` n'a pas été reprise : elle traçait les **neuf** features éligibles
sous la marge en accuracy, pas les quarante-trois retenues sous le macro-F1, donc elle
contredisait la règle du texte. `paper/regen_fig13_cicids2017.py` la remplace et la régénère
depuis le JSON, en trois panneaux : le spectre des 43 éligibles, le plan de l'attribution avec
les quatorze colonnes dupliquées, et la sonde d'horodatage sur les deux corpus.

Trois choses à retenir de ce qui est écrit dans l'article :

- le mécanisme de redondance **se reproduit** : sept paires de colonnes identiques, dix des
  quatorze colonnes concernées à importance par permutation exactement nulle ;
- la deuxième conclusion est **corrigée par le second corpus**, pas confirmée : sur CICIDS2017 la
  sonde d'horodatage s'effondre à 0.1028 sous le protocole temporel, contre 0.9862 sur GeNIS. Le
  découpage temporel suffit ou ne suffit pas **selon le corpus**, et cela se mesure ;
- la règle publiée ne se transpose pas : `acc > 3 × hasard` est inapplicable à 80 % de classe
  majoritaire. Deux réexpressions sont consignées, `acc > hasard + κ(1 − hasard)` avec
  κ = 0.4818 qui reproduit exactement la règle de GeNIS, et le portage sur le macro-F1,
  `macro-F1 > 3 × 0.0636`, qui est celle retenue.

Non repris dans le manuscrit : les six runs de confirmation (LightGBM, régression logistique, DNN
sous les deux protocoles) présents dans `e2_results_cicids2017.json`. Leurs macro-F1 sont trop bas
pour être publiés tels quels et demandent un diagnostic avant d'être cités.

**Calibration temporelle et audit résiduel.** `colab/e3_calibration_residual.py` fait les deux,
sans réentraînement, depuis `probs/` et le cache. Reste à le lancer.

## Faisable sans réentraîner, à lancer

### P4, calibration sous le protocole temporel (priorité 4)

**Le relecteur a raison et c'est moins cher qu'il ne le pense.** La calibration figure
dans le titre et n'est mesurée que sous le protocole stratifié.

Or le pipeline enregistre `probs_val` et `probs_test` **pour chaque run, y compris
temporel**, dans `probs/` de `article1_final.zip`. Le calage de température s'ajuste sur
les probabilités de validation et s'évalue sur celles de test : tout est déjà sur
disque. ECE, score de Brier et diagramme de fiabilité sous le protocole temporel se
calculent **sans réentraîner un seul modèle**.

C'est la meilleure réponse par unité d'effort de toute la liste. Il faut un script et
quelques minutes de calcul.

### P6, audit résiduel après liste noire (priorité 6)

Partiellement déjà là : le balayage mono-feature couvre les 63 comportementales sous les
deux protocoles, donc aucune des 55 retenues n'a un τ sous le seuil. Ce qui manque est
la partie *conjointe* : corrélation, information mutuelle et redondance **entre** les
features retenues. Calculable depuis la matrice de features, que les indices de
découpage régénèrent en une dizaine de minutes.

---

## Exige une campagne

### P3, protocoles temporels supplémentaires (priorité 3)

Nuance : le découpage chronologique global **est déjà rapporté** en §4.2, comme propriété
du corpus, avec l'explication de sa dégénérescence. Le relecteur demande en plus un
*scenario holdout*, entraîner sur certaines campagnes et tester sur d'autres. Le module
`3-scenarios` de GeNIS existe et rendrait cela possible. Nouvelle campagne.

### §8, sensibilité de l'architecture de l'autoencodeur

Le relecteur veut écarter l'objection « ce n'est qu'un échec de cette architecture ».
Il faut au moins un AE plus profond et un modèle de reconstruction différent. Campagne
courte, sur le seul bras non supervisé.

---

## Où je ne suis pas d'accord, ou bien c'est déjà fait

### §16, conclusions de déploiement trop fortes

Le manuscrit borne déjà explicitement, deux fois : *« For a line-rate deployment **on
this corpus** »* et le titre de paragraphe *« What we would deploy **on this corpus** »*.
Rien n'a été modifié : le texte dit déjà ce que le relecteur demande qu'il dise.

### §3, découpage chronologique global absent

Il n'est pas absent. §4.2 le décrit, explique pourquoi il est dégénéré sur ce corpus, et
le rapporte comme propriété du corpus plutôt que comme protocole. Un désaccord de
présentation, pas une omission.

---

## Reste à arbitrer avec les auteurs

Trois points éditoriaux, non traités faute de décision :

**Le titre (§19).** Le relecteur préfère *« Beyond Random Splits: Leakage-Aware
Benchmarking of Network Intrusion Detectors on GeNIS »*. Le titre actuel est déjà celui
du dépôt Zenodo publié ; changer l'un impose de changer les métadonnées de l'autre, ce
qui est possible, les métadonnées Zenodo restant éditables après publication.

**Le résumé (§20).** 326 mots là où Elsevier en attend en général 250, et dense en
chiffres. Le relecteur propose de le restructurer en problème, méthode, trois
résultats, implication.

**Les contributions (§12).** Le manuscrit en liste cinq ; le relecteur en veut trois,
avec l'autoencodeur, le coût et l'intervalle d'agrégation rétrogradés en analyses
complémentaires. C'est un remaniement d'introduction, pas une réécriture du fond.
