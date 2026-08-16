# The manuscript figures

The sixteen images the manuscript shows, named by the
**figure number the manuscript uses**. This folder is the answer to the question
"what does Figure N look like"; `paper/figures/` is a different thing, the output
of the regeneration scripts under their historical names.

## Why the two folders disagree

The filenames in `paper/figures/` date from the LaTeX chain and follow **its**
numbering, which the Word manuscript reordered. The names no longer say which
figure they are. Three traps in particular:

- `fig6_per_class_f1.png` is **Figure 4**, not Figure 6.
- `fig6_spectrum_both.png` is **Figure 7**. Two files start with `fig6_` and
  neither of them is Figure 6.
- `fig5_cost.png` and `fig9_transferability_spectrum.png` are **in no figure of the
  manuscript**. They are superseded renders, kept because the scripts still write them.

Everything below shifted by one when the conceptual figure entered at 1. If you
are reading a draft that predates it, subtract one from every number here.

## The map

| Figure | File in this folder | Source in `paper/figures/` | Script |
|---|---|---|---|
| 1 | `figure01_argument_chain.png` | `fig_concept.png` | regen_fig_concept.py |
| 2 | `figure02_class_distribution.png` | **none** | none, see below |
| 3 | `figure03_capture_windows.png` | `fig1_timeline.png` | regen_en.py |
| 4 | `figure04_per_class_f1_audited.png` | `fig6_per_class_f1.png` | regen_en.py |
| 5 | `figure05_importance_vs_transferability.png` | **none** | none, see below |
| 6 | `figure06_transferability_plane.png` | `fig8_transferability.png` | regen_en.py |
| 7 | `figure07_transferability_spectrum.png` | `fig6_spectrum_both.png` | regen_fig6.py |
| 8 | `figure08_mcnemar.png` | **none** | none, see below |
| 9 | `figure09_conditions_protocols.png` | `fig2_before_after.png` | regenerate_figures.py |
| 10 | `figure10_bootstrap_ci.png` | `fig7_ranking_ci.png` | regenerate_figures.py |
| 11 | `figure11_intervals_per_class.png` | `fig3_interval_heatmap.png` | regen_en.py |
| 12 | `figure12_autoencoder_auroc.png` | `fig10_autoencoder.png` | regenerate_figures.py |
| 13 | `figure13_cost_vs_quality.png` | **none** | none, see below |
| 14 | `figure14_cicids2017_audit.png` | `figE2_cicids2017_audit.png` | regen_e2.py |
| 15 | `figure15_per_class_f1_temporal.png` | **none** | none, see below |
| 16 | `figure16_horizons.png` | `figE4_horizons.png` | regen_e4.py |

## The five figures with no script

Figures 2, 5, 8, 13 and 15 were rendered while the native Word document was being
built and were never written back to `paper/figures/`. The images here are the ones
the manuscript shows, extracted from the document itself, so nothing is lost. Their
underlying values were re-checked against `article1_results.json`: Figure 13's nine
points match `cost.<model>.throughput_512` and the temporal macro-F1 exactly.

They cannot currently be regenerated from a committed script. If a reviewer asks for
a regeneration path, that is the gap to close.

## Captions

- **Figure 1** (2679x1520 px): The chain of argument, capture schedule to audited benchmark
- **Figure 2** (1867x1214 px): Class distribution of the 60-second slice
- **Figure 3** (2553x994 px): Capture windows per class
- **Figure 4** (2051x1116 px): Per-class F1 under the audited condition
- **Figure 5** (1678x1322 px): Attribution importance does not separate shortcuts from signal
- **Figure 6** (1775x1414 px): Single-feature accuracy under the two protocols
- **Figure 7** (2679x1380 px): Single-feature transferability, both normalisations
- **Figure 8** (1486x1653 px): Pairwise McNemar tests under Holm correction
- **Figure 9** (2799x1192 px): Macro-F1 across feature conditions and protocols
- **Figure 10** (1655x964 px): Bootstrap confidence intervals, stratified protocol
- **Figure 11** (1593x1114 px): Per-class F1 across aggregation intervals
- **Figure 12** (1832x934 px): Per-family AUROC of the benign-trained autoencoder
- **Figure 13** (1803x1276 px): Inference cost against detection quality, temporal protocol
- **Figure 14** (2679x1100 px): The audit re-run on CICIDS2017
- **Figure 15** (2096x1581 px): Per-class F1 under the temporal protocol
- **Figure 16** (2679x1240 px): Single-feature accuracy against temporal horizon
