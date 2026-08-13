# The published Zenodo archive

This file describes **what is actually deposited on Zenodo**, which is not the layout
that `colab/zenodo_export_cell.py` builds. It is maintained by hand and is
deliberately not overwritten by that script.

- **Record title**: Reproducibility artefact for: A Leakage-Audited Benchmark of Deep
  and Ensemble Detectors on the GeNIS 2025 Corpus: Calibration, Cost, and Class
  Imbalance under the Natural Distribution
- **Concept DOI, all versions**: `10.5281/zenodo.21910662` — this is what Section 10
  of the paper cites
- **Version DOI, v1.0.0**: `10.5281/zenodo.21910663`, published 13 August 2026
- **Type**: Software · **Licence**: CC-BY 4.0 · **Authors**: three, with ORCID
- **Related work**: *is derived from* `10.5281/zenodo.14919237` (the GeNIS corpus)
- **Code**: https://github.com/bahriala2/GeNIS2025

## The two files

Version 1.0.0 was assembled by hand from Google Drive and published as two zip
archives. The names correspond to the pipeline's output directories.

| File | Size | MD5 |
|---|---|---|
| `article1_final.zip` | 182.46 MB | `e8a9689a15b314e7978be6c52afb2a28` |
| `models.zip` | 51.59 MB | `047ab02ab3e77cb45eaa40326d0bd7c1` |

Zenodo does not allow files to be changed after publication. Any correction to the
contents requires a new version, which receives its own version DOI; the concept DOI
above continues to resolve to the most recent one.

## What Section 10 promises, and where it is

Section 10 states that the artefact is released in two parts: the code on GitHub, and
the measurements on Zenodo. Two of the seven elements are code and are therefore in
the repository only, not in either zip.

| Promised in Section 10 | Where it is |
|---|---|
| the pipeline | GitHub, `colab/article1_pipeline.ipynb` — **not in the Zenodo files** |
| the scripts that regenerate every figure and table | GitHub, `paper/regen_en.py`, `paper/regenerate_figures.py`, `paper/regen_fig6.py` — **not in the Zenodo files** |
| the frozen split indices | `article1_final.zip` → `frozen_splits_60s.npz` |
| the feature blacklist | `article1_final.zip` → `article1_results.json` → `audit.blacklist` (12 columns) |
| the transferability spectrum under both normalisations | `article1_final.zip` → `article1_results.json` → `audit.transfer_table` (63 features) |
| the hyperparameter configurations | `article1_final.zip` → `article1_results.json` → `hpo.<model>.best_params` |
| the trained models | `models.zip` |

`article1_final.zip` also carries the per-run probability matrices under `probs/`, the
manuscript figures under `figures/`, the fifteen appendix figures under
`figures_annexe/`, the LaTeX tables of the frozen chain under `tables/`, and the
autoencoder reconstruction errors as `ae_scores_seed1.npz`.

`article1_results.json` is also committed to the repository at
`paper/article1_results.json`, so the blacklist, the spectrum and the hyperparameter
configurations can be read without downloading anything.

### Two points to confirm against the record's file listing

The mapping above follows the pipeline's output layout. Two details of the hand-built
zips were not verified and are worth checking in the Zenodo file preview:

1. whether `models/` also appears inside `article1_final.zip`, in which case it is
   simply duplicated and `models.zip` is the convenient copy;
2. whether `cache/slice60.npz` was included. That file is a derived feature matrix
   extracted from GeNIS. Its presence is not a licensing problem, since the record is
   CC-BY 4.0 and declares *is derived from* the corpus, but it is redundant: the
   frozen split indices and the pipeline regenerate it in about ten minutes.

## The results file

`article1_results.json` is the source of the numbers the paper reports. 154
training runs are recorded under `models`, keyed
`<detector>[#tuned]|<condition>|<split>`. Conditions are `full`, `clean` and
`audited`; splits are `strat_seed1` to `strat_seed5` and `temporal`.

Each run records accuracy, macro-F1, weighted F1, MCC, per-class F1, the binary
detection view (detection F1, FPR, FNR, PR-AUC, ROC-AUC), fit time and predict time.
Top-level keys of interest:

| Key | Contents |
|---|---|
| `audit` | permutation importance, the full single-feature transferability scan, duplicate pairs, the blacklist, and the rule that produced it |
| `hpo` | every search trial per model, with the retained configuration |
| `calibration` | temperature scaling per detector and the resulting ECE |
| `cost` | training and inference cost per detector |
| `stats` | bootstrap confidence intervals and McNemar tests |
| `meta.env` | the library versions the campaign ran under |

Both normalisations of the transferability spectrum are derivable from
`audit.transfer_table`, which stores the single-feature accuracy under both protocols.
The raw ratio is tau = acc_temporal / acc_stratified; the chance-corrected form used in
Figure 6 is tau* = (acc_temporal - p) / (acc_stratified - p), with
p = `audit.chance` = 0.1942.

## Regenerating the figures

The scripts live in the repository, not in the archive. Clone the repository and run
them from `paper/`, where `article1_results.json` is already present:

The filenames these scripts write date from the LaTeX chain and follow **its**
numbering, which the Word manuscript reordered. The mapping from manuscript figure
number to file is in `paper/figures_manuscrit/MAPPING.md`, and the thirteen images the
manuscript actually shows are committed alongside it under their figure numbers.

| Command | Manuscript figures produced |
|---|---|
| `python3 regen_en.py` | 2 capture windows, 3 per-class F1 audited, 5 transferability plane, 10 intervals |
| `python3 regenerate_figures.py` | 8 conditions and protocols, 9 bootstrap intervals, 11 autoencoder AUROC |
| `python3 regen_fig6.py` | 6 transferability spectrum, drawn at final page width |
| `make figures` | runs `regen_en.py` and `regen_fig6.py` |

**Five of the thirteen figures have no committed script.** Figures 1, 4, 7, 12 and 13
were rendered while the native Word document was being built and were never written
back to `paper/figures/`. The images are committed under
`paper/figures_manuscrit/`, so nothing is lost, and their values were re-checked
against `article1_results.json`. They cannot presently be regenerated from a script,
which is the one gap in the claim that the artefact regenerates every figure.

Two files the scripts still write, `fig5_cost.png` and
`fig9_transferability_spectrum.png`, appear in no figure of the manuscript. They are
superseded renders.

The LaTeX tables are regenerated by `paper/legacy-latex/regenerate_tables.py`. That
chain is frozen and diverges from the manuscript, which is a native Word document; it
is kept for reference only, and its own README says so.

## Reproducing the campaign

1. Obtain GeNIS from `doi:10.5281/zenodo.14919237` and place `2-flows.zip` where the
   notebook expects it.
2. Open `colab/article1_pipeline.ipynb` from the repository. It is resumable: every
   run is written to disk as soon as it finishes.
3. Extract `frozen_splits_60s.npz` from `article1_final.zip` into the output directory
   before starting. The notebook reloads it instead of drawing new splits, so the
   partitions match the ones the paper reports exactly.

The campaign comprises 154 runs. Environment of record:
Python 3.12.13, TensorFlow 2.20.0, scikit-learn 1.6.1, XGBoost 3.3.0, LightGBM 4.6.0.

One caveat the paper states in Section 8 and which matters here: the hyperparameter
search budget was capped in wall-clock seconds inside a hosted runtime whose
accelerator allocation varied between sessions. The number of trials a model received
therefore reflects hardware availability as well as model cost, and a rerun on
different hardware may allocate trials differently. Accuracies are unaffected, since
seeds are fixed and CPU and GPU fits agree up to floating-point non-determinism.

## The trained models

`models.zip` holds the reference configuration only: the audited and clean conditions
on split `strat_seed1`, in both the default and the tuned arm. `preprocessing.json`
carries the fitted RobustScaler parameters, the feature order, the class names, the
benign index and the blacklist, so a model can be applied to new flows without
rerunning the pipeline. `MANIFEST.json` lists the calibration temperatures.

Keras models load with `keras.models.load_model(path, custom_objects=...)`, passing
`FeatureTokenizer` and `ClsToken` from the pipeline notebook for the FT-Transformer.
The other detectors are joblib dumps.

## What is not in the archive

- **The corpus.** GeNIS is separately archived at `doi:10.5281/zenodo.14919237` and
  should be cited directly.
- **The code.** It is in the repository. A future version of the record may include a
  snapshot of it; see below.
- **A manifest and a README inside the archive.** Version 1.0.0 has neither. This file
  serves that purpose from the repository.
- **Trained models outside the reference configuration.** Storing all 154 would
  add little: the probability matrices in `probs/` already allow every reported metric,
  significance test and calibration curve to be recomputed without retraining.

## A canonical archive, if a new version is made

`colab/zenodo_export_cell.py` builds a single `genis2025-artefact.zip` containing all
of the above in one tree, plus a `MANIFEST.md` giving every file's size, SHA-256 and
the pipeline cell that produced it, plus a snapshot of the repository under `code/`.
It is the last cell of `colab/article1_pipeline.ipynb`. Depositing it would create
version 2 of the record, with a new version DOI; the concept DOI cited by the paper
would follow automatically, and the version 1.0.0 files would remain accessible.

## Citation

Cite the corpus as `doi:10.5281/zenodo.14919237` and this artefact by its concept DOI,
`10.5281/zenodo.21910662`, or by the version DOI `10.5281/zenodo.21910663` when the
exact state this paper reports is required.
