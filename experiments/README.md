# Expériences E1–E7 — pipeline GeNIS

Objectif : une commande par expérience, résultats en JSON, figures régénérées
par script (même discipline que BAg-IDS).

## Arborescence cible

```
experiments/
  data/            # CSV GeNIS (non versionnés) — voir data/README.md
  configs/         # une config YAML par (modèle, tâche, intervalle)
  splits/          # index des splits gelés (stratifié 5 graines + chronologique)
  results/         # JSON par run : metrics, calibration, coût
  figures/         # scripts de figures (matplotlib), sortie 300 dpi
  blacklist/       # liste noire de caractéristiques, un fichier par intervalle
```

## Commandes prévues (à implémenter, semaine 1)

| Exp | Commande | Description |
|---|---|---|
| E1 | `python -m bench.e1_anchor` | Comparaison ancrée avec Silva et al. (60 s) |
| E2 | `python -m bench.e2_main --interval 60` | 9 modèles × 2 tâches × 5 graines, stratifié |
| E3 | `python -m bench.e3_audit` | Split temporel, sonde timestamp, permutation, exclusions, liste noire |
| E4 | `python -m bench.e4_intervals --intervals 5 10 30` | Top modèles sur les autres tranches |
| E5 | `python -m bench.e5_calibration` | ECE, diagrammes, temperature scaling |
| E6 | `python -m bench.e6_cost` | Banc CPU : flux/s (batch 1/512), latence p50/p99 |
| E7 | `python -m bench.e7_topk` | (optionnel) ablation top-k caractéristiques |

## Données

GeNIS : Zenodo `doi:10.5281/zenodo.14919237` — télécharger les CSV filtrés des
4 intervalles dans `experiments/data/`. Ne jamais committer les CSV.

## Règles de protocole (gelées — voir docs/plan_v2.md §3)

1. Scaler ajusté sur le train uniquement, par split et par graine.
2. Distribution naturelle : aucune rééquilibration, nulle part.
3. Fusion des 3 variantes bénignes → 9 classes.
4. Les splits (stratifiés × 5 graines + chronologique) sont générés une fois,
   gelés dans `splits/`, et réutilisés par toutes les expériences.
5. Budget d'hyperparamètres : ~30 essais aléatoires ET plafond de temps
   identique par modèle.
