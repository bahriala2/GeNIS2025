# Revue de littérature — réponse au majeur 14

Le rapport de relecture demande un positionnement systématique contre huit corps de
littérature, et exige qu'aucune référence ne soit inventée. Ce document trace ce qui a
été cherché, ce qui a été trouvé, **à quel niveau chaque entrée a pu être vérifiée**, et
ce qui reste ouvert.

## La contrainte de vérification, et pourquoi elle est écrite ici

Le proxy réseau de l'environnement de travail bloque arXiv, ACM DL, IEEE Xplore,
SciteSeer, SciTePress, Semantic Scholar (site et API), dblp, HAL et core.ac.uk. La
recherche fonctionne ; **la lecture des notices éditeur, non**.

Les six entrées ci-dessous ont donc été retenues sur un critère explicite : n'est
insérée dans le manuscrit qu'une référence dont **le DOI ou le couple volume + pages**
ressort de façon concordante d'au moins deux sources indépendantes. Une entrée qui n'a
pas atteint ce seuil est listée en fin de document comme candidate, pas insérée.

Cette précaution n'est pas théorique : sur Rosay et al., la reconstruction par recherche
donnait la bonne liste de paires dupliquées mais la mauvaise attribution, et seule la
lecture du PDF l'a corrigée.

## Les sept références ajoutées

| # | Référence | Manque comblé | Placement | Vérification |
|---|---|---|---|---|
| 10 | Rosay, Cheval, Carlier, Leroux, ICISSP 2022, pp. 25–36 | défauts documentés de CICIDS2017 | §2.1, §7 | **PDF lu** — §3.2.1 et §3.2.2 |
| 13 | Goldschmidt, Chudá, *Computers & Security* 156 (2025) 104510 | biais et défauts des corpus NIDS, état de l'art | §2.1 | DOI + volume + article |
| 14 | Cantone, Marrocco, Bria, *IEEE Access* 12 (2024) 144489–144508 | généralisation inter-corpus | §2.1 | volume + pages, bibcode ADS concordant |
| 19 | Kapoor, Narayanan, *Patterns* 4 (9) (2023) 100804 | fuite comme défaut de reproductibilité, taxonomie | §2.2 | DOI + volume + numéro |
| 20 | Aas, Jullum, Løland, *Artificial Intelligence* 298 (2021) 103502 | attribution sous dépendance, **SHAP** | §2.2 | DOI + volume + article |
| 29 | Minderer et al., NeurIPS 2021, arXiv:2106.07998 | calibration sous décalage, effet d'architecture | §2.3 | notice NeurIPS + liste d'auteurs |
| 34 | Snoek et al., NeurIPS 2019, arXiv:1906.02530 | calibration sous décalage de distribution | §6.5 | notice NeurIPS + arXiv |

### Ce que chacune apporte, au-delà du remplissage

**Goldschmidt & Chudá (13).** Quatre-vingt-neuf corpus inspectés en téléchargeant chacun
plutôt qu'en lisant sa documentation. C'est exactement la posture de ce papier, appliquée
à l'échelle du domaine, et cela publie le constat que les défauts sont la règle. Publié
dans la revue même que le papier vise en repli.

**Cantone et al. (14).** La mesure complémentaire de la nôtre : parfait en intra-corpus,
proche du hasard en inter-corpus. C'est l'argument externe le plus fort pour la limite
que la section 9 déclare — notre classement de détecteurs est un résultat mono-corpus.
La citer nous coûte quelque chose, et c'est pour ça qu'elle doit y être.

**Kapoor & Narayanan (19).** Taxonomie de huit types de fuite sur 294 articles et 17
disciplines. Elle **répond aussi au mineur 2** du rapport, qui reproche l'emploi trop
large du mot *leakage* : le manuscrit situe désormais ses raccourcis dans leur catégorie
« caractéristique illégitime » et emploie le terme dans ce sens restreint.

**Aas, Jullum, Løland (20).** Le manuscrit affirmait que SHAP est aveugle « par le même
mécanisme » que l'importance par permutation, en ne citant que Strobl et Hooker, qui
portent sur les forêts et la permutation. C'était un trou. Aas et al. démontrent le
défaut sur Kernel SHAP lui-même et donnent les estimateurs conditionnels qui le corrigent.

**Minderer et al. (29).** Cette référence **complique** notre résultat au lieu de le
confirmer : la dégradation sous décalage est nettement moins marquée sur les
architectures récentes non convolutives. Nos propres mesures montrent les deux régimes,
et la section 2.3 le dit maintenant.

## Ce qui a été cherché et n'a pas été retenu

**Wu & Keogh, benchmarks d'anomalies faussés, IEEE TKDE.** Pertinent pour l'évaluation de
l'autoencodeur et pour la thèse « illusion de progrès ». Non insérée : l'année est
ambiguë entre les sources (arXiv 2020–2021, volume 35 correspondant à 2023) et je n'ai
pas pu trancher sur une notice éditeur. **À vérifier puis insérer en §2.3 ou §6.6** si
vous voulez couvrir l'évaluation de la détection d'anomalies.

**Généralisation à une famille d'attaque non vue (majeur 8).** Le protocole
*leave-one-attack-family-out* est employé dans le domaine, mais la recherche n'a ramené
que des préprints récents non vérifiables et des sources de qualité douteuse. **Aucune
référence méthodologique canonique n'a été trouvée par ce canal.** Je préfère l'écrire
que d'insérer une citation faible. C'est aussi la raison pour laquelle E4b **mesure**
ce protocole plutôt que de s'appuyer sur une autorité : le résultat vaudra mieux que la
citation.

## Ce que le rapport demandait et qui reste hors de portée d'une recherche

Trois des huit corps demandés — conception robuste de benchmarks, standards de
reproductibilité, évaluation de la détection d'anomalies — sont partiellement couverts
par Kapoor & Narayanan et par les entrées existantes. Un traitement vraiment systématique
supposerait une recherche bibliographique avec accès aux bases, que l'environnement ne
permet pas. **Une passe sur Scopus ou Web of Science côté auteurs reste nécessaire avant
soumission**, et les sept entrées ci-dessus doivent y être recontrôlées.

---

# Vérification des sept entrées — faite

La recherche web fonctionne dans cet environnement même quand les notices
éditeur sont bloquées : `doi.org`, `dblp.org` et `papers.nips.cc` refusent la
connexion, mais l'index de recherche restitue les notices. Les sept entrées
ont donc été recontrôlées ici, chacune contre au moins deux sources
indépendantes.

## Résultat

| # | Entrée | Verdict |
|---|---|---|
| 10 | Rosay et al., ICISSP 2022, pp. 25–36 | **confirmée** — SciTePress 107740, HAL hal-03563228, researchr `RosayCCL22` |
| 13 | Goldschmidt & Chudá, *Computers & Security* 156 (2025) 104510 | **confirmée** — ScienceDirect `S0167404825001993`, dépôt officiel des auteurs |
| 14 | Cantone, Marrocco, Bria, *IEEE Access* 12 (2024) 144489–144508 | **corrigée — le titre était celui du préprint** |
| 19 | Kapoor & Narayanan, *Patterns* 4 (9) (2023) 100804 | **confirmée** — Cell Press `S2666-3899(23)00159-9`, PubMed 37720327 |
| 20 | Aas, Jullum, Løland, *Artificial Intelligence* 298 (2021) 103502 | **confirmée** — ACM DL sur le DOI, ScienceDirect `S0004370221000539` |
| 29 | Minderer et al., NeurIPS 2021 | **confirmée** — huit auteurs dans l'ordre exact des actes |
| 34 | Snoek et al., NeurIPS 2019 | **confirmée** ; identifiant arXiv retiré, voir plus bas |

## La seule erreur, et ce qu'elle était

**[14] portait deux titres à la fois.** Le manuscrit citait *On the
cross-dataset generalization of machine learning for network intrusion
detection*, qui est le titre du **préprint** arXiv:2402.10974, avec le volume
et les pages de la **revue**. Le titre publié dans *IEEE Access* est *Machine
learning in network intrusion detection: A cross-dataset generalization
study* (dblp `journals/access/CantoneMB24`). Auteurs, volume et pages étaient
justes ; seul le titre venait de l'autre version. Corrigé.

C'est exactement le défaut qu'une passe bibliographique existe pour attraper :
rien dans le manuscrit ne pouvait le signaler, puisque l'entrée est
parfaitement cohérente avec elle-même.

## La réserve sur [34], qui n'est pas une erreur

L'ordre des auteurs de *Can you trust your model's uncertainty?* **diffère
entre le préprint et les actes** :

- **actes NeurIPS 2019** : Snoek, Ovadia, Fertig, Lakshminarayanan, Nowozin,
  Sculley, Dillon, Ren, Nado ;
- **arXiv:1906.02530** : Ovadia, Fertig, Ren, Nado, Sculley, Nowozin, Dillon,
  Lakshminarayanan, Snoek.

Le manuscrit suit **l'ordre des actes**, qui est le bon puisque c'est les
actes qu'il cite. Mais il donnait aussi l'identifiant arXiv dans la même
entrée, et un relecteur qui suit ce lien voit un premier auteur différent de
celui qu'il vient de lire. **L'identifiant a été retiré de cette entrée.**

Les autres entrées gardent le leur — [5], [6], [12], [29] et [30] — parce
qu'aucune n'a cet écart. Vérifié pour la [29] : Minderer, Djolonga,
Romijnders, Hubis, Zhai, Houlsby, Tran, Lucic, dans le même ordre des deux
côtés. L'asymétrie n'est donc pas un oubli de mise en forme, elle a un motif.

## Ce qui reste hors de portée

La confirmation contre **Scopus ou Web of Science** reste utile pour un motif
que cette passe ne couvre pas : ces deux bases sont celles que les éditeurs et
les comités de thèse interrogent, et une entrée absente de leur index est un
problème même si elle est parfaitement exacte. Les sept entrées ci-dessus sont
désormais exactes ; ce qui n'est pas établi, c'est leur indexation.
