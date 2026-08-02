# Plan expérimental v2 — Article 1 : Benchmark audité sur GeNIS 2025

*Révision du plan initial après vérification (voir `verification_proposition.md`).
Les changements par rapport à la v1 sont marqués **[v2]**.*

**Titre de travail :** *A Leakage-Audited Benchmark of Deep and Ensemble Detectors on the GeNIS 2025 Corpus: Calibration, Cost, and Class Imbalance under the Natural Distribution*

**Rôle stratégique :** référence de provenance des détecteurs GeNIS de BAg-IDS et premier benchmark indépendant audité sur GeNIS.

**Narration éditoriale [v2] :** l'audit de raccourcis (E3) et l'analyse
multi-intervalles (E4) portent le papier ; le benchmark stratifié (E2) n'est que
le point d'ancrage, car ses scores satureront vers 99,9 % (démontré dans
BAg-IDS §6.9). Les figures phares sont le « classement avant/après audit » et la
courbe difficulté-par-famille vs intervalle.

---

## 1. Positionnement

Baseline officielle : Silva et al., FPS 2025 (Springer chap. 978-3-032-20018-1_18,
arXiv:2511.08660) — 5 méthodes de sélection de caractéristiques (IG, Chi², RFE,
MAD, Dispersion Ratio), 3 ensembles d'arbres + 2 DNN, binaire + multiclasse,
accuracy/F1. **Vérifié le 2026-08-02 :** ils ne couvrent ni audit de fuites, ni
calibration, ni split temporel, ni coût d'inférence, ni comparaison
systématique des intervalles. Seul autre utilisateur externe connu :
XGBoost-Forget (unlearning, arXiv:2606.19220) — orthogonal.

Cinq axes différenciants (inchangés) :
1. **Audit de fuites et de séparabilité temporelle** — timestamp seul : 99,3 %
   (hasard 11 %). Livrable : liste noire de caractéristiques **par intervalle** [v2],
   en trois catégories : (i) positionnelles/horodatage, (ii) quasi-identifiants
   (IP, ports, identifiants de flux), (iii) comportementales dont l'importance
   s'effondre sous split temporel [v2].
2. **Calibration** — ECE, diagrammes de fiabilité, températures par modèle.
3. **Distribution naturelle** — macro-F1, MCC, PR-AUC par classe, FPR/FNR
   opérationnels ; accuracy rapportée mais reléguée.
4. **Coût d'inférence** — flux/s par cœur CPU, latence p50/p99, taille modèle.
5. **Multi-intervalles** — 5/10/30/60 s, détectabilité par famille vs coût.

**[v2] Vocabulaire :** GeNIS simule le trafic d'une **PME** (SME), pas d'une
grande entreprise — reprendre le terme du papier dataset.

---

## 2. Questions de recherche (inchangées)

- **RQ1** — Quels modèles (profonds vs arbres boostés) dominent sur GeNIS sous protocole propre, en binaire et en multiclasse (9 classes) ?
- **RQ2** — Quelle part des performances publiées sur GeNIS est attribuable à des raccourcis plutôt qu'à des motifs de trafic ? Que devient le classement après audit ?
- **RQ3** — Comment l'intervalle d'agrégation (5/10/30/60 s) affecte-t-il la détectabilité par famille d'attaque et le coût ?
- **RQ4** — Quel compromis performance / calibration / coût, et quel modèle recommander pour un déploiement temps réel ?

---

## 3. Données et protocole

### 3.1 Corpus
- GeNIS (Zenodo, doi:10.5281/zenodo.14919237), CSV filtrés, 4 intervalles ;
  9 classes après fusion des 3 variantes bénignes : benign,
  bruteforce-{ftp, smb, ssh}, dos-{hulk, icmp, pshack, slowloris, udp}.
- **[v2]** Recalculer la part de bénin pour chaque intervalle (7,4 % vaut pour 60 s seulement).
- Tâches : binaire et multiclasse 9 classes.

### 3.2 Protocole propre (validé dans BAg-IDS §6.9)
- Split stratifié 60/20/20, scaler ajusté sur le train uniquement, distribution
  naturelle conservée, 5 graines, moyenne ± écart-type.

### 3.3 Protocole temporel (cœur de RQ2)
- Split chronologique en plus du stratifié.
- Audit : (i) classifieur timestamp seul ; (ii) importance par permutation ;
  (iii) réévaluation après exclusion. Livrable : liste noire par intervalle [v2].

---

## 4. Modèles

| Famille | Modèles | Statut |
|---|---|---|
| Profonds | RNN, CNN 1D, DNN (architectures GeNIS, Table 3 de BAg-IDS) | déjà entraînés |
| Arbres | Random Forest, XGBoost, LightGBM | à entraîner |
| Profond tabulaire | FT-Transformer (repli : TabNet) | à entraîner |
| Non supervisé | Autoencodeur — **[v2] section séparée, métriques propres (AUROC sur erreur de reconstruction) ; option leave-one-family-out pour l'angle « attaque inconnue »** | à entraîner |
| Baselines | Régression logistique + classe majoritaire | contexte |

**[v2]** Budget égalisé : ~30 essais aléatoires **et** plafond de temps de calcul
identique par modèle, les deux déclarés dans le papier.

---

## 5. Métriques et tests statistiques (inchangés)

- Détection : accuracy (reléguée), macro-F1, F1/classe, MCC, PR-AUC, FPR
  opérationnel, courbes ROC/PR.
- Calibration : ECE (15 bacs), fiabilité avant/après temperature scaling.
- Coût : temps d'entraînement, flux/s CPU (batch 1 et 512), taille, latence p50/p99.
- Statistique : McNemar apparié, bootstrap 95 % (10 000), correction de Holm.

---

## 6. Plan d'expériences

- **E1 — Comparaison ancrée avec Silva et al. [v2]** (et non réplication exacte) :
  même intervalle, même tâche, mêmes familles de modèles ; rapporter et analyser
  l'écart. Chercher d'abord leur code public — s'il existe, réplication vraie.
- **E2 — Benchmark principal** (60 s, stratifié) : 9 modèles × 2 tâches × 5 graines.
- **E3 — Audit de raccourcis** (temporel + exclusions) : figure phare
  « classement avant/après ». **Jamais sacrifiée.**
- **E4 — Multi-intervalles** : top 3–4 modèles sur 5/10/30 s.
  **[v2] Ne pas sacrifier entièrement** (seconde protection contre la saturation) ;
  réduction minimale admise : 2 intervalles (5 s et 60 s).
- **E5 — Calibration** : tous les modèles d'E2.
- **E6 — Coût d'inférence** : banc CPU standardisé documenté.
- **E7 (optionnel) — Ablation top-k caractéristiques** vs Silva et al.

---

## 7. Calendrier (6 semaines)

| Semaine | Travail |
|---|---|
| 1 | Pipeline 4 intervalles, stats par intervalle [v2], splits, gel du protocole ; E1 |
| 2 | E2 : arbres + baselines ; lancement FT-Transformer et autoencodeur |
| 3 | Fin E2 ; E5 ; E6 |
| 4 | E3 (le gros morceau analytique) |
| 5 | E4 ; figures et tableaux définitifs |
| 6 | Rédaction complète, relecture Pr Jemili, arXiv + soumission |

Règle de sacrifice [v2] : E7 d'abord, puis réduction d'E4 à 2 intervalles —
jamais E3, jamais E4 en entier.

---

## 8. Menaces à la validité (inchangées + C5, C6)

- Interne : fuite scaler/split (contrôlée) ; fuite temporelle (objet d'E3).
- Externe : corpus de testbed (CyberRange), floods volumétriquement séparables ;
  part de bénin faible → granularité FPR grossière ; **[v2]** profil PME.
- Construction : budget fini ; autoencodeur non comparable — section séparée [v2].

---

## 9. Cibles de soumission

**[v2] Vérifier d'abord quel référentiel (Scimago vs JCR) fait foi pour la thèse.**
- JISA (Elsevier) : **Scimago Q1, mais JCR Q2 (IF 4,4)**.
- Si JCR exigé : remonter *Computers & Security* (Elsevier) en cible 1.
- *Computers & Electrical Engineering* : repli — vérifier son quartile dans le
  référentiel applicable.
- Conférence FPS/ARES si besoin d'une référence citable rapidement.
- arXiv dès la soumission (compatible politique Elsevier — vérifié).

---

## 10. Livrables et reproductibilité (inchangés)

- Dépôt public : pipeline, configs, graines, liste noire par intervalle,
  scripts de figures, checkpoints.
- README : une commande par expérience (E1–E7).
- Répercussion vers BAg-IDS §6.9 avant sa soumission.
