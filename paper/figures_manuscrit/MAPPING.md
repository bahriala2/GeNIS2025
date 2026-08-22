# The manuscript figures

The twenty images the manuscript shows, named by the
**figure number the manuscript uses**. This folder is the answer to the question
"what does Figure N look like"; `paper/figures/` is a different thing, the output
of the regeneration scripts under their historical names.

## Why the two folders disagree

The filenames in `paper/figures/` date from the LaTeX chain and follow **its**
numbering, which the Word manuscript reordered twice. The names no longer say which
figure they are. Three traps in particular:

- `fig6_per_class_f1.png` is **Figure 5**, not Figure 6.
- `fig6_spectrum_both.png` is **Figure 8**. Two files start with `fig6_` and
  neither of them is Figure 6.
- `fig5_cost.png` and `fig9_transferability_spectrum.png` are **in no figure of the
  manuscript**. They are superseded renders, kept because the scripts still write them.

The numbering moved twice: once when the conceptual figure entered at 1, and again
when the partition schemes entered at 4 and the three result figures of E4b and E4c
entered at 15, 16 and 19. If you are reading an older draft, this table is the map.

## The map

| Figure | File in this folder | Source in `paper/figures/` | Script |
|---|---|---|---|
| 1 | `figure01_argument_chain.png` | `fig_concept.png` | regen_fig_concept.py |
| 2 | `figure02_class_distribution.png` | **none** | none, see below |
| 3 | `figure03_capture_windows.png` | `fig1_timeline.png` | regen_en.py |
| 4 | `figure04_partition_schemes.png` | `fig_protocols.png` | regen_fig_protocols.py |
| 5 | `figure05_per_class_f1_audited.png` | `fig6_per_class_f1.png` | regen_en.py |
| 6 | `figure06_importance_vs_transferability.png` | **none** | none, see below |
| 7 | `figure07_transferability_plane.png` | `fig8_transferability.png` | regen_en.py |
| 8 | `figure08_transferability_spectrum.png` | `fig6_spectrum_both.png` | regen_fig6.py |
| 9 | `figure09_mcnemar.png` | **none** | regen_e8_figures.py |
| 10 | `figure10_conditions_protocols.png` | `fig2_before_after.png` | regenerate_figures.py |
| 11 | `figure11_bootstrap_ci.png` | `fig7_ranking_ci.png` | regenerate_figures.py |
| 12 | `figure12_intervals_per_class.png` | `fig3_interval_heatmap.png` | regen_en.py |
| 13 | `figure13_autoencoder_auroc.png` | `fig10_autoencoder.png` | regenerate_figures.py |
| 14 | `figure14_cost_vs_quality.png` | **none** | regen_e8_figures.py |
| 15 | `figure15_rolling_origins.png` | `figE4b_origines.png` | regen_e4b.py |
| 16 | `figure16_leave_one_family_out.png` | `figE4b_lofo.png` | regen_e4b.py |
| 17 | `figure17_cicids2017_audit.png` | `figE2_cicids2017_audit.png` | regen_e2.py |
| 18 | `figure18_per_class_f1_temporal.png` | **none** | none, see below |
| 19 | `figure19_threshold_cost.png` | `figE4c_seuil.png` | regen_e4c.py |
| 20 | `figure20_horizons.png` | `figE4_horizons.png` | regen_e4.py |

## The figures with no script

Figures 2, 6, 9, 14 and 18 were rendered while the native Word document was being
built and were never written back to `paper/figures/`. The images here are the ones
the manuscript shows, extracted from the document itself, so nothing is lost.

**Three of the five now have one.** `regen_e8_figures.py` draws Figures 9, 14 and 18
(and redraws 5, 10 and 11) on the audited condition as corrected in Section 9. Both of
Figure 14's axes now come from the same session and the same condition.

Figures 9 and 11 need the pairwise tests, which need the probability matrices — 380 MB
that cannot leave Colab. They did not have to: `colab/e8quater_stats_mcnemar_bootstrap.py`
computes them there and returns 45 p-values, 45 corrected, ten means and ten intervals,
under `stats` in `e8_results.json`. That is what these two figures read.

**Two remain: 2 and 6.** Both read only `article1_results.json` and could be scripted at
any time; that is the gap left to close.

## Captions

- **Figure 1** (2679x1520 px): The chain of argument, capture schedule to audited benchmark
- **Figure 2** (1867x1214 px): Class distribution of the 60-second slice
- **Figure 3** (2553x994 px): Capture windows per class
- **Figure 4** (2679x1504 px): The four partition schemes, on one axis of capture time
- **Figure 5** (2051x1116 px): Per-class F1 under the audited condition
- **Figure 6** (1678x1322 px): Attribution importance does not separate shortcuts from signal
- **Figure 7** (1775x1414 px): Single-feature accuracy under the two protocols
- **Figure 8** (2679x1380 px): Single-feature transferability, both normalisations
- **Figure 9** (1486x1653 px): Pairwise McNemar tests under Holm correction
- **Figure 10** (2799x1192 px): Macro-F1 across feature conditions and protocols
- **Figure 11** (1655x964 px): Bootstrap confidence intervals, stratified protocol
- **Figure 12** (1593x1114 px): Per-class F1 across aggregation intervals
- **Figure 13** (1832x934 px): Per-family AUROC of the benign-trained autoencoder
- **Figure 14** (1803x1276 px): Inference cost against detection quality, temporal protocol
- **Figure 15** (2679x1300 px): Macro-F1 at five rolling origins
- **Figure 16** (2679x1180 px): Leave-one-family-out
- **Figure 17** (2679x1100 px): The audit re-run on CICIDS2017
- **Figure 18** (2096x1581 px): Per-class F1 under the temporal protocol
- **Figure 19** (2679x1088 px): What the threshold costs
- **Figure 20** (2679x1240 px): Single-feature accuracy against temporal horizon
