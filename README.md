# GeNIS2025 — Article 1 : benchmark audité sur le corpus GeNIS

Dépôt de travail pour l'article *« A Leakage-Audited Benchmark of Eleven Intrusion
Detectors on GeNIS 2025: Calibration, Cost, and Protocol Robustness »*, premier
article de provenance pour les détecteurs GeNIS de BAg-IDS.

**Soumis à *Engineering Applications of Artificial Intelligence* le 20 septembre 2026.**

**La source de l'article est `paper/GeNIS_benchmark_article.docx`** (Word natif).
Ce qui part chez l'éditeur est construit à partir d'elle par
`paper/make_submission.py`, jamais édité à la main. La chaîne LaTeX a été
abandonnée en août 2026 ; elle est archivée dans `paper/legacy-latex/` et n'est
plus tenue à jour.

## Contenu

### L'article et ce qui part avec lui

| Chemin | Rôle |
|---|---|
| `paper/GeNIS_benchmark_article.docx` | **L'article** : 47 pages, 14 sections, 20 figures, 16 tableaux, 1 algorithme, 37 références. Source unique, à éditer directement dans Word |
| `paper/submission/` | **Le package déposé chez EAAI** : page de titre, manuscrit anonymisé, highlights, lettre d'accompagnement, 15 figures vectorielles, CSV supplémentaire. Son `README.md` liste les conditions du guide et ce qui reste ouvert |
| `paper/make_submission.py` | Construit les quatre fichiers Word du package depuis le manuscrit et **revérifie l'anonymisation** à chaque passage. À relancer après toute retouche de l'article |
| `paper/blacklist.csv` | Disposition lisible par machine des 90 colonnes, générée depuis la liste **corrigée** à treize colonnes comportementales |
| `paper/highlights.md` | Les cinq puces, avec leur compte de caractères |
| `paper/figures_manuscrit/` | **Les 20 figures du manuscrit**, nommées par leur numéro, avec `MAPPING.md` |
| `paper/figures/` | Sorties des scripts, sous leurs noms hérités de LaTeX : la numérotation n'est **pas** celle du manuscrit |
| `paper/figures_annexe/` | 15 figures d'annexe pour le rapport de thèse |

### Les quatre vérificateurs

Ils lisent le `.docx` et ne remplacent pas une relecture ; ils attrapent ce
qu'une relecture laisse passer. Les trois premiers n'ont aucune dépendance.

| Script | Ce qu'il contrôle |
|---|---|
| `paper/check_coherence.py` | Figures, tableaux et références : légende sans appel, numérotation qui saute, ordre de première citation |
| `paper/check_style.py` | Typographie, orthographe `-isation`, terminologie, décimales, longueur et ouverture des phrases |
| `paper/check_claims.py` | **La prose contre les tableaux et les données** : chaque affirmation chiffrée recalculée depuis les JSON |
| `paper/check_layout.py` | Ce que donne le document une fois paginé. Exige LibreOffice Writer et PyMuPDF |

### Les résultats

| Chemin | Rôle |
|---|---|
| `paper/article1_results.json` | Campagne initiale, 154 runs. Attention : les chiffres publiés des tableaux 2, 7, 8, 10 et 13 viennent désormais de E8, pas d'ici |
| `experiments/e2/` … `experiments/e8/` | Une expérience par dossier : `FINDINGS.md` pour la lecture, un JSON pour les chiffres, un script de vérification là où il y en a un |
| `colab/` | Les notebooks qui produisent ces JSON, E1 à E9 |
| `experiments/README.md` | Plan du pipeline |

| Exp | Ce qu'elle a établi |
|---|---|
| E1 | Comparaison ancrée avec la baseline du corpus |
| E2 | **Second corpus.** L'audit rejoué sur CICIDS2017 : le mécanisme de redondance se reproduit, la suffisance du découpage temporel non — la sonde d'horodatage y tombe à 0.1028 |
| E3 | **La calibration se dégrade sous le protocole temporel**, d'un facteur 457 sur LightGBM. Elle n'était mesurée que sous le stratifié |
| E4a | L'audit calculé sur la validation n'exclut plus rien. Le contrôle sur le test reproduit exactement les huit colonnes publiées |
| E4b | Protocole temporel répété sur cinq origines, avec bootstrap apparié |
| E4c | Ce que coûte le seuil : quatre listes alternatives réentraînées, la sensibilité n'est plus descriptive |
| E5 / E9 | Cinq graines à tous les intervalles, puis six détecteurs de plus (72 runs, dont 54 nouveaux) |
| E6 | Pourquoi une graine de LightGBM s'effondre à 10 s : le mécanisme, pas la description |
| E7 | **`IdleTime` est un identifiant de fichier de capture.** Le défaut le plus sérieux trouvé sur le manuscrit, vérifié par 17 contrôles sur 17 |
| E8 | La condition auditée republiée sur la liste corrigée : **180 runs**, 33 contrôles sur 33 |

### Les documents de travail

| Chemin | Rôle |
|---|---|
| `docs/poste_de_travail.md` | **Reprendre l'article en local** : la bonne branche, l'installation, et les deux points que seul le poste débloque |
| `docs/reponse_reviewer_q1.md` | Réponse point par point à la relecture Q1, priorités 1 à 6 |
| `docs/reponse_relecture.md` | Les 21 remarques de la relecture « overgeneralisation », toutes adoptées |
| `docs/reponse_limites_v2.md` | Réponse au rapport de limites |
| `docs/relecture_sections_7_12.md` | Relecture des sections 7 à 12, qui n'avaient jamais été lues |
| `docs/revue_litterature.md` | Revue de littérature et positionnement |
| `docs/verification_proposition.md` | Vérification de la proposition initiale, corrections C1–C6 |
| `docs/plan_v2.md` | Plan expérimental révisé, protocole gelé |
| `docs/dataset_facts.md`, `docs/preliminary_findings.md` | Faits du corpus, lecture des premiers résultats |
| `docs/mail_farah_positionnement.md` | Courriel de positionnement aux co-auteurs |

## Archive Zenodo

L'artefact est déposé sous deux DOI, et la distinction compte :

| DOI | Ce qu'il désigne |
|---|---|
| `10.5281/zenodo.21910662` | **DOI de concept.** Résout toujours vers la version la plus récente. C'est celui que cite la section 11 de l'article. |
| `10.5281/zenodo.21910663` | **DOI de version, v1.0.0**, publiée le 13 août 2026. Il fige l'état exact de la campagne initiale. |

Citez le DOI de version pour reproduire précisément les chiffres de la campagne
initiale, le DOI de concept pour référencer l'artefact en général.

**Une version 2 est nécessaire, et ce n'est pas optionnel.** La 1.0.0 ne contient
que les 154 runs d'origine, alors que les tableaux 2, 7, 8, 10 et 13 et les figures
5, 9, 10, 11, 14 et 18 sont calculés depuis E8. Un lecteur qui télécharge l'archive
ne peut pas reproduire le tableau 2. Voir `paper/ARCHIVE_README.md` pour ce que la
v2 doit ajouter, élément par élément.

## État (2026-09-20)

### Fait

- [x] Proposition vérifiée et validée (avec corrections)
- [x] Campagne initiale terminée : 154/154 runs
- [x] Relecture « overgeneralisation » : les 21 points adoptés
- [x] Relecture Q1 : priorités 2 à 6 traitées dans le texte
- [x] **Second corpus (priorité 1)** : audit E2 sur CICIDS2017, section 7 de l'article
- [x] **E3 à E9** : calibration temporelle, audit hors test, temporel répété, coût du seuil, intervalles à cinq graines, mécanisme du binning, `IdleTime`, republication sur la liste corrigée
- [x] Relecture des sections 7 à 12, qui n'avaient jamais été lues
- [x] Audits systématiques : figures, tableaux, légendes, références (37, DOI résolus), et la prose contre les données, chiffre par chiffre
- [x] Package de soumission construit par script, anonymisation vérifiée à chaque passage
- [x] Les quatre conditions de rejet de bureau d'EAAI tenues
- [x] **Soumis à EAAI le 20 septembre 2026**

### Ouvert

- [ ] **Zenodo v2** : les chiffres publiés vivent hors de l'archive. C'est le point qu'un relecteur trouvera
- [ ] **Figure 12** : 1593 px de large contre 1772 exigés, et pas de version vectorielle. Elle ne peut pas être redessinée depuis ce qui est versionné — il faut l'objet `RESULTS["intervals"]` du run Colab
- [ ] Adresse postale de l'affiliation bordelaise, sans rue
- [ ] `Farah.JMILI@` dans les adresses contre *Jemili* dans la ligne d'auteurs
- [ ] Remerciements à « None. », à changer si quelqu'un doit être remercié
- [ ] La déclaration d'IA générative de la section 12 ne nomme pas l'outil ; le système de soumission le demande séparément
- [ ] `paper/highlights.md` parle encore de *Computers & Security* : la limite de 85 caractères est la même chez EAAI, seul l'en-tête est resté

### Dernière vérification : 2026-09-20

| Contrôle | Résultat |
|---|---|
| `check_coherence.py` | **passe.** 20 figures et 16 tableaux, tous appelés ; 37 références, ordre de première citation croissant |
| `check_style.py` | **passe.** 279 paragraphes de prose, aucun défaut mécanique |
| `check_claims.py` | **passe.** Aucun écart entre la prose, les tableaux et les données |
| `check_layout.py` | **non exécuté.** Demande LibreOffice Writer, indisponible dans l'environnement de vérification. Le compte de 47 pages vient du dernier rendu local |
| `make_submission.py` | **reconstruit à l'identique.** Le package versionné correspond exactement au manuscrit courant, et l'anonymisation passe : aucun identifiant dans le corps, les noms ne subsistent que dans l'auto-citation [7] |
| Limites EAAI | résumé de 250 mots pour 250 permis, 6 mots-clés, colonne simple, 3,98 Mo, 5 puces dont la plus longue à 80 caractères |

## Références clés

- Dataset : Silva et al., *Data in Brief* 60 (2025) 111487 — Zenodo `10.5281/zenodo.14919237`
- Baseline : Silva et al., FPS 2025, Springer `10.1007/978-3-032-20018-1_18` (arXiv:2511.08660)
- Détecteurs : Bahri et al., AMCAI 2023 `10.1109/AMCAI59331.2023.10431511` ; BAg-IDS §6.9
