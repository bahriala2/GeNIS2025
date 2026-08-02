# Vérification de la proposition « Article 1 : Benchmark moderne sur GeNIS 2025 »

**Date de vérification : 2 août 2026.**
Sources : Silva et al., *Data in Brief* 60 (2025) 111487 ; Silva et al., FPS 2025 (Springer, chapitre 978-3-032-20018-1_18, arXiv:2511.08660) ; Zenodo 10.5281/zenodo.14919237 ; BAg-IDS version 3 (§4.2.1, §6.1, §6.9, §8.3.7) ; recherches web du jour.

## Verdict global

**La proposition est solide et cohérente : validée, avec 6 corrections/points d'attention.**
Les cinq axes de différenciation par rapport à Silva et al. tiennent, la fenêtre de
nouveauté est encore ouverte (mais commence à se refermer), et le plan est
entièrement cohérent avec les faits établis dans BAg-IDS §6.9. Les corrections
ci-dessous sont à intégrer avant de geler le protocole.

## 1. Faits vérifiés — confirmés

| Affirmation du plan | Statut | Source |
|---|---|---|
| GeNIS : 2,8 M de flux CSV, 4 intervalles (5/10/30/60 s), >37 M paquets PCAPNG | ✅ Confirmé | Data in Brief 2025 |
| Généré sur Airbus CyberRange par GECAD (ISEP/IPP), exporteur HERA, capture février 2025 | ✅ Confirmé | Data in Brief 2025 ; BAg-IDS §6.9 |
| Silva et al. FPS : 5 méthodes de sélection de caractéristiques (Information Gain, Chi², RFE, MAD, Dispersion Ratio), 3 ensembles d'arbres + 2 DNN, binaire + multiclasse, accuracy/F1 | ✅ Confirmé | Springer chap. 18 / arXiv:2511.08660 |
| Silva et al. ne couvrent **ni** calibration, **ni** audit de fuites, **ni** split temporel, **ni** coût d'inférence détaillé, **ni** analyse multi-intervalles systématique | ✅ Confirmé (résumés et abstract ; à re-vérifier sur le texte intégral avant soumission) | idem |
| Tranche 60 s : 338 820 flux, test 67 764 flux, 7,4 % bénin, 9 classes après fusion des variantes bénignes, F = 59 après audit | ✅ Cohérent | BAg-IDS §6.9, Table 11 |
| Timestamp seul → 99,3 % (hasard ≈ 11 % pour 9 classes) ; fenêtres d'attaque étroites et disjointes | ✅ Cohérent | BAg-IDS §6.9, Figure (chronologie) |
| Protocole propre déjà validé : scaler sur train seul, distribution naturelle, split stratifié 60/20/20 | ✅ Cohérent | BAg-IDS §4.2.1, §6.9 |
| Liste des 9 classes : benign, bruteforce-{ftp, smb, ssh}, dos-{hulk, icmp, pshack, slowloris, udp} | ✅ Cohérent | BAg-IDS §6.9 |

## 2. Fenêtre de nouveauté (état au 2 août 2026)

Utilisateurs de GeNIS identifiés à ce jour :

1. **Groupe GECAD** (papier dataset + papier classification FPS) — la baseline officielle.
2. **XGBoost-Forget** (Magalhães et al., arXiv:2606.19220, juin 2026) — *machine
   unlearning* sur IoT-23 et GeNIS. **Orthogonal** au benchmark proposé (aucun
   recouvrement avec les RQ1–RQ4), mais c'est le signal que des équipes externes
   commencent à adopter le corpus.

**Conclusion : la fenêtre est ouverte. Aucun benchmark indépendant avec audit de
fuites, calibration, coût ou multi-intervalles n'existe.** La consigne du plan
(re-vérifier Scopus/Scholar la semaine de la soumission) est maintenue et
d'autant plus importante que l'adoption externe a commencé.

## 3. Corrections et points d'attention

### C1 — Quartile de JISA : Scimago Q1 mais JCR Q2 ⚠️
*Journal of Information Security and Applications* est **Q1 Scimago (SJR 2025 : 0,905)**
mais **Q2 JCR** (IF 4,4, données 2025). Si l'exigence « Q1 » de la thèse se réfère
au classement JCR (Web of Science), JISA ne convient pas comme cible n°1 —
vérifier quel référentiel fait foi pour l'école doctorale, et le cas échéant
remonter *Computers & Security* (Elsevier) ou *IEEE TIFS* dans la liste.
*Computers & Electrical Engineering* : vérifier de même son quartile dans le
référentiel applicable avant d'en faire le repli.

### C2 — E1 « reproduire Silva et al. » : viser l'ancrage, pas la réplication exacte
Leur pipeline passe par une sélection de caractéristiques combinant 5 méthodes ;
sans leurs graines, splits et seuils exacts, une réplication au point près est
improbable. Reformuler E1 en « **comparaison ancrée** » : même intervalle, même
tâche, mêmes familles de modèles, et rapporter l'écart avec analyse. Vérifier
d'abord si leur code est public (dépôts GECAD/GitHub) — s'il l'est, E1 redevient
une vraie réplication et se fait en quelques jours.

### C3 — Risque de saturation : le benchmark stratifié sera écrasé vers ~100 %
BAg-IDS obtient déjà 99,96 % sur la tranche 60 s en protocole propre stratifié.
Un tableau central où 9 modèles font tous >99,9 % est un résultat *faible* pour
un Q1. Conséquence éditoriale : **E3 (audit de raccourcis + split temporel) et
E4 (multi-intervalles) doivent porter la narration**, E2 n'étant que le point de
référence. Le titre de travail va déjà dans ce sens ; la structure du papier
doit suivre (le « classement avant/après audit » et la courbe
difficulté-vs-intervalle sont les figures phares, pas le tableau E2). La règle
de sacrifice du §7 du plan (« jamais E3 ») est donc confirmée — et il faut la
durcir : **E4 ne doit pas non plus être sacrifié entièrement**, car c'est la
seconde protection contre la saturation.

### C4 — Préciser ce que « timestamp » recouvre dans l'audit
Les CSV GeNIS exposent des colonnes positionnelles/identifiantes (BAg-IDS en
exclut cinq). L'audit doit distinguer trois catégories et les nommer dès le
protocole : (i) horodatage et colonnes dérivées de la position dans la capture ;
(ii) quasi-identifiants (IP, ports, identifiants de flux) ; (iii)
caractéristiques comportementales légitimes dont l'importance s'effondre sous
split temporel. La « liste noire » livrée doit être publiée par intervalle
(5/10/30/60 s), car les colonnes diffèrent potentiellement entre tranches.

### C5 — Positionnement du corpus : PME, pas grande entreprise
Le papier dataset positionne GeNIS sur le trafic d'**une PME simulée** (small and
medium-sized enterprises). Reprendre ce vocabulaire dans le papier pour éviter
un point de révision facile.

### C6 — L'autoencodeur : cadrer l'asymétrie dès le protocole
Le plan le note en menace de validité ; le durcir : l'AE doit être rapporté dans
une **sous-section séparée avec ses propres métriques** (AUROC sur score de
reconstruction, pas macro-F1 au même seuil), sinon un reviewer demandera de le
retirer. Alternative défendable : le présenter comme détecteur « attaques
inconnues » en excluant une famille du train (leave-one-family-out), ce qui lui
donne une vraie raison d'être plutôt qu'une ligne de plus dans le tableau.

## 4. Points mineurs

- « 7,4 % de trafic bénin » : exact pour la tranche 60 s uniquement ; les
  proportions aux autres intervalles sont à recalculer (elles diffèrent).
- Budget d'hyperparamètres (~30 essais) : ajouter la contrainte « même budget
  *temps GPU/CPU* » en plus du nombre d'essais, sinon FT-Transformer consomme
  un ordre de grandeur de plus que LightGBM à essais égaux.
- Dépôt arXiv à la soumission : compatible avec la politique de partage
  d'Elsevier (préprint autorisé). ✅
- Calendrier 6 semaines : tenable **si** les données 5/10/30 s ne réservent pas
  de surprises de nettoyage en semaine 1 ; prévoir la semaine 1 comme seule
  variable d'ajustement avant d'entamer la règle de sacrifice.

## 5. Décisions actées pour la suite

1. Plan validé avec les corrections C1–C6 intégrées (voir `docs/plan_v2.md`).
2. La rédaction commence par le squelette LaTeX (`paper/`), sections gelées sur
   les RQ1–RQ4 ; l'introduction se rédige en parallèle des expériences E1–E2.
3. Re-vérification de nouveauté et du texte intégral de Silva et al.
   programmée pour la semaine de soumission.
