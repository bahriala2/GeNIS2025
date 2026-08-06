# GeNIS2025 — Article 1 : benchmark audité sur le corpus GeNIS

Dépôt de travail pour l'article *« A Leakage-Audited Benchmark of Deep and
Ensemble Detectors on the GeNIS 2025 Corpus »*, premier article de provenance
pour les détecteurs GeNIS de BAg-IDS.

**La source de l'article est `paper/GeNIS_benchmark_article.docx`** (Word natif).
La chaîne LaTeX a été abandonnée en août 2026 ; elle est archivée dans
`paper/legacy-latex/` et n'est plus tenue à jour.

## Contenu

| Chemin | Rôle |
|---|---|
| `paper/GeNIS_benchmark_article.docx` | **L'article** (26 pages, 13 figures, 11 tables, 27 références) : source unique, à éditer directement dans Word |
| `paper/article1_results.json` | Résultats de la campagne (154 runs), source de tous les chiffres |
| `paper/figures/` | Figures au format PNG, telles qu'insérées dans le Word |
| `paper/figures_annexe/` | 15 figures d'annexe pour le rapport de thèse |
| `paper/regen_en.py`, `paper/regen_fig6.py` | Régénèrent les figures depuis les résultats |
| `paper/Makefile` | `make preview` (rendu PDF + images de pages) · `make figures` · `make clean` |
| `paper/legacy-latex/` | Ancienne chaîne LaTeX, **gelée et obsolète** (voir son README) |
| `docs/reponse_relecture.md` | Réponse point par point aux 21 remarques de relecture, avec le rebuttal en anglais |
| `docs/verification_proposition.md` | Vérification de la proposition initiale : faits confirmés, corrections C1–C6 |
| `docs/plan_v2.md` | Plan expérimental révisé (v2), protocole gelé |
| `docs/preliminary_findings.md` | Lecture des premiers résultats |
| `colab/article1_pipeline.ipynb` | **Notebook Colab de production** : EDA → prétraitement → 12 modèles → réglage d'hyperparamètres → évaluation, sauvegarde des modèles, reprise automatique |
| `experiments/README.md` | Plan du pipeline E1–E7 |

## État (2026-08-06)

- [x] Proposition vérifiée et validée (avec corrections)
- [x] Campagne terminée : 154/154 runs
- [x] Article rédigé de bout en bout avec les chiffres réels
- [x] Relecture « overgeneralisation » traitée : 12 points acceptés, 7 refusés avec argument
- [x] Affiliations et URL du dépôt renseignées
- [x] Word natif vérifié page par page, sans tiret cadratin
- [ ] DOI d'archivage du dépôt
- [ ] Relecture Pr Jemili
- [ ] Soumission

## Références clés

- Dataset : Silva et al., *Data in Brief* 60 (2025) 111487 — Zenodo `10.5281/zenodo.14919237`
- Baseline : Silva et al., FPS 2025, Springer `10.1007/978-3-032-20018-1_18` (arXiv:2511.08660)
- Détecteurs : Bahri et al., AMCAI 2023 `10.1109/AMCAI59331.2023.10431511` ; BAg-IDS §6.9
