# Expériences E1–E9 — pipeline GeNIS

Une expérience par dossier, les chiffres en JSON, la lecture dans un
`FINDINGS.md`, et un script de vérification là où il y en a un.

> **La numérotation a changé de sens en route.** Le plan initial, gelé dans
> `docs/plan_v2.md`, prévoyait sept expériences E1–E7 exécutées par un paquet
> `bench` en ligne de commande. Ce paquet n'a jamais été écrit : la campagne
> principale a tourné dans `colab/article1_pipeline.ipynb`, et les expériences
> qui ont suivi sont nées une par une des relectures, avec leur propre
> numérotation. **Les E1–E9 ci-dessous sont celles qui existent** ; les E1–E7 du
> plan désignent autre chose et n'ont pas de code.

## Ce qui a tourné

| Exp | Notebook ou script | Résultats | Ce qu'elle établit |
|---|---|---|---|
| E1 | `colab/e1_anchored_comparison_v6.ipynb` | — | Comparaison ancrée avec la baseline du corpus, les onze détecteurs repris tels quels |
| E2 | `colab/e2_cicids2017_audit_v5.ipynb` | `e2/` | **Second corpus.** L'audit rejoué sur les 2 830 743 flux de CICIDS2017. Le mécanisme de redondance se reproduit ; la suffisance du découpage temporel non |
| E3 | `colab/e3_calibration_residual_v3.ipynb` | `e3/` | La calibration sous les **deux** protocoles. Elle se dégrade d'un facteur 457 sur LightGBM sous le temporel |
| E4a | `colab/e4a_audit_sans_test.ipynb` | `e4a/` | L'audit calculé sur la validation n'exclut plus rien ; sur le test il reproduit exactement les huit colonnes publiées |
| E4a bis | `colab/e4abis_audit_imbrique.ipynb` | `e4a/` | Audit imbriqué, et `verify_nested_blacklist.py` qui le contrôle |
| E4b | `colab/e4b_temporel_repete.ipynb` | `e4b/` | Protocole temporel répété sur cinq origines, bootstrap apparié |
| E4c | `colab/e4c_listes_alternatives.ipynb` | `e4c/` | Ce que coûte le seuil : quatre listes alternatives réentraînées |
| E5 | `colab/e5_intervalles_cinq_graines.ipynb` | `e5/` | Cinq graines à tous les intervalles, après un témoin qui rejoue un run publié au chiffre près |
| E6 | `colab/e6_binning_deterministe.ipynb` | `e6/` | Le mécanisme derrière l'effondrement d'une graine de LightGBM à 10 s |
| E7 | `colab/e7_idletime.ipynb` | `e7/` | **`IdleTime` est un identifiant de fichier de capture.** Le défaut le plus sérieux trouvé sur le manuscrit, 17 contrôles sur 17 |
| E8 | `colab/e8_republication.ipynb` et les quatre scripts `e8*.py` | `e8/` | La condition auditée republiée sur la liste corrigée : 180 runs, 33 contrôles sur 33 |
| E9 | `colab/e9_intervalles_six_detecteurs.py` | `e5/e5_results_e9.json` | Six détecteurs de plus aux intervalles courts : 72 runs, dont 54 nouveaux |

Les chiffres publiés des tableaux 2, 7, 8, 10 et 13 et des figures 5, 9, 10, 11,
14 et 18 viennent de **E8**, pas de `paper/article1_results.json`, qui porte la
campagne initiale de 154 runs.

## Données

GeNIS : Zenodo `doi:10.5281/zenodo.14919237` — les CSV filtrés des 4 intervalles.
CICIDS2017 pour E2 : distribution `GeneratedLabelledFlows`, et non
`MachineLearningCVE`, qui est livrée sans colonne d'horodatage. **Ne jamais
committer les CSV.**

## Règles de protocole (gelées — voir `docs/plan_v2.md` §3)

1. Scaler ajusté sur le train uniquement, par split et par graine.
2. Distribution naturelle : aucune rééquilibration, nulle part.
3. Fusion des 3 variantes bénignes → 9 classes.
4. Les splits (stratifiés × 5 graines + temporel par classe) sont générés une
   fois, gelés, et réutilisés par toutes les expériences.
5. Budget d'hyperparamètres : ~30 essais aléatoires ET plafond de temps
   identique par modèle.
