# GeNIS2025 — Article 1 : benchmark audité sur le corpus GeNIS

Dépôt de travail pour l'article *« A Leakage-Audited Benchmark of Deep and
Ensemble Detectors on the GeNIS 2025 Corpus »*, premier article de provenance
pour les détecteurs GeNIS de BAg-IDS.

## Contenu

| Chemin | Rôle |
|---|---|
| `docs/verification_proposition.md` | Vérification de la proposition initiale (2026-08-02) : faits confirmés, fenêtre de nouveauté, corrections C1–C6 |
| `docs/plan_v2.md` | Plan expérimental révisé (v2), protocole gelé |
| `paper/main.tex` | Squelette LaTeX (elsarticle) — introduction rédigée, sections annotées |
| `paper/references.bib` | Références de base vérifiées |
| `experiments/README.md` | Plan du pipeline E1–E7 (une commande par expérience) |
| `colab/article1_pipeline.ipynb` | **Notebook Colab de production** : pipeline complet (EDA → prétraitement → 12 modèles → réglage d'hyperparamètres → évaluation), 8 figures article + 15 figures d'annexe, 4 tables LaTeX, sauvegarde des modèles, reprise automatique |

## État (2026-08-02)

- [x] Proposition vérifiée et validée (avec corrections)
- [x] Squelette du papier + brouillon d'introduction + Related Work
- [x] Notebook de production (split temporel par classe, recherche d'hyperparamètres à budget déclaré, persistance des modèles) — exécution en cours
- [ ] Semaine 1 : pipeline de données 4 intervalles, splits gelés, E1
- [ ] E2–E6, puis rédaction complète

## Références clés

- Dataset : Silva et al., *Data in Brief* 60 (2025) 111487 — Zenodo `10.5281/zenodo.14919237`
- Baseline : Silva et al., FPS 2025, Springer `10.1007/978-3-032-20018-1_18` (arXiv:2511.08660)
- Détecteurs : Bahri et al., AMCAI 2023 `10.1109/AMCAI59331.2023.10431511` ; BAg-IDS §6.9
