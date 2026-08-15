# The manuscript figures

The fourteen images the manuscript shows, named by the
**figure number the manuscript uses**. This folder is the answer to the question
"what does Figure N look like"; `paper/figures/` is a different thing, the output
of the regeneration scripts under their historical names.

## Why the two folders disagree

The filenames in `paper/figures/` date from the LaTeX chain and follow **its**
numbering, which the Word manuscript reordered. The names no longer say which
figure they are. Two traps in particular:

- `fig6_per_class_f1.png` is **Figure 3**, not Figure 6.
- `fig6_spectrum_both.png` is **Figure 6**. Two files start with `fig6_` and only
  one of them is Figure 6.
- `fig5_cost.png` and `fig9_transferability_spectrum.png` are **in no figure of the
  manuscript**. They are superseded renders, kept because the scripts still write them.

## The map

| Figure | File in this folder | Source in `paper/figures/` | Script |
|---|---|---|---|
| 1 | `figure01_class_distribution.png` | **none** | none, see below |
| 2 | `figure02_capture_windows.png` | `fig1_timeline.png` | regen_en.py |
| 3 | `figure03_per_class_f1_audited.png` | `fig6_per_class_f1.png` | regen_en.py |
| 4 | `figure04_importance_vs_transferability.png` | **none** | none, see below |
| 5 | `figure05_transferability_plane.png` | `fig8_transferability.png` | regen_en.py |
| 6 | `figure06_transferability_spectrum.png` | `fig6_spectrum_both.png` | regen_fig6.py |
| 7 | `figure07_mcnemar.png` | **none** | none, see below |
| 8 | `figure08_conditions_protocols.png` | `fig2_before_after.png` | regenerate_figures.py |
| 9 | `figure09_bootstrap_ci.png` | `fig7_ranking_ci.png` | regenerate_figures.py |
| 10 | `figure10_intervals_per_class.png` | `fig3_interval_heatmap.png` | regen_en.py |
| 11 | `figure11_autoencoder_auroc.png` | `fig10_autoencoder.png` | regenerate_figures.py |
| 12 | `figure12_cost_vs_quality.png` | **none** | none, see below |
| 13 | `figure13_cicids2017_audit.png` | `figE2_cicids2017_audit.png` | regen_e2.py |
| 14 | `figure14_per_class_f1_temporal.png` | **none** | none, see below |

## The five figures with no script

Figures 1, 4, 7, 12 and 14 were rendered while the native Word document was being
built and were never written back to `paper/figures/`. The images here are the ones
the manuscript shows, extracted from the document itself, so nothing is lost. Their
underlying values were re-checked against `article1_results.json`: Figure 12's nine
points match `cost.<model>.throughput_512` and the temporal macro-F1 exactly.

They cannot currently be regenerated from a committed script. If a reviewer asks for
a regeneration path, that is the gap to close.

## Captions

- **Figure 1** (1867x1214 px): Natural class distribution of the 60-second slice
- **Figure 2** (2553x994 px): Capture windows per class
- **Figure 3** (2051x1116 px): Per-class F1 under the audited condition
- **Figure 4** (1678x1322 px): Attribution importance does not separate shortcuts from signal
- **Figure 5** (1775x1414 px): Single-feature accuracy under the two protocols
- **Figure 6** (2679x1380 px): Single-feature transferability, both normalisations
- **Figure 7** (1486x1653 px): Pairwise McNemar tests under Holm correction
- **Figure 8** (2799x1192 px): Macro-F1 across feature conditions and protocols
- **Figure 9** (1655x964 px): Bootstrap confidence intervals, stratified protocol
- **Figure 10** (1593x1114 px): Per-class F1 across aggregation intervals
- **Figure 11** (1832x934 px): Per-family AUROC of the benign-trained autoencoder
- **Figure 12** (1803x1276 px): Inference cost against detection quality, temporal protocol
- **Figure 13** (2679x1100 px): The audit re-run on CICIDS2017
- **Figure 14** (2096x1581 px): Per-class F1 under the temporal protocol
