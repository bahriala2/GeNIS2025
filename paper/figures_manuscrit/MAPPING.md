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
| 2 | `figure02_class_distribution.png` | **none** | regen_figures_2_6.py |
| 3 | `figure03_capture_windows.png` | `fig1_timeline.png` | regen_en.py |
| 4 | `figure04_partition_schemes.png` | `fig_protocols.png` | regen_fig_protocols.py |
| 5 | `figure05_per_class_f1_audited.png` | `fig6_per_class_f1.png` | regen_en.py |
| 6 | `figure06_importance_vs_transferability.png` | **none** | regen_figures_2_6.py |
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
| 18 | `figure18_per_class_f1_temporal.png` | **none** | regen_e8_figures.py |
| 19 | `figure19_threshold_cost.png` | `figE4c_seuil.png` | regen_e4c.py |
| 20 | `figure20_horizons.png` | `figE4_horizons.png` | regen_e4.py |

## Every figure now has a regeneration script

Figures 2, 6, 9, 14 and 18 were rendered while the native Word document was being
built and were never written back to `paper/figures/`, so the column above records **none**
as their source. That is a statement about where the original image came from, not about
whether one can be produced today: each of the five now has a script, and the images in this
folder are what those scripts draw.

`regen_e8_figures.py` draws 9, 14 and 18 (and redraws 5, 10 and 11) on the audited condition
as corrected in Section 9. `regen_figures_2_6.py` draws 2 and 6 from `article1_results.json`
alone.

Redrawing the last two corrected three errors the images carried:

- Figure 2 gave 5 029 benign test flows. The smallest non-zero false-positive rate in the
  whole campaign is exactly 1/5030, so the partition holds 5 030 — which the caption and
  Sections 4.5 and 9 already said.
- Figure 2's title rounded one of three shares to a coarser precision than the other two, so
  the three displayed values summed to 100.04.
- Figure 6 drew `IdleTime` in the colour reserved for retained columns. Section 9 excludes it,
  and it now carries its own marker, because it is excluded by a criterion neither of the
  other two reaches.

This matters beyond tidiness: the contributions list in Section 1 promises "the scripts
regenerating every figure and table", and until now that sentence was false.

## What the figure audit found

A full pass over the twenty images, hash-compared against the ones the `.docx`
actually embeds, found **two figures the manuscript showed that this folder had
already superseded**, and the build script was not swapping them in:

- **Figure 9** carried the original campaign. It gave `ftt`–`logreg` as a
  non-significant pair where the corrected condition gives `logreg`–`rnn`, so it
  contradicted Section 6.1's own list, and it ordered XGBoost ahead of LightGBM
  under a title that reads "ordered by macro-F1", which Table 2 contradicts.
- **Figure 11** placed logistic regression at 0.9991 where Section 6.7 reads
  0.9963, and again put XGBoost first.

Both are now in `REDESSINEES`, and every one of the twenty images in the `.docx`
is byte-identical to the file of the same name here. Section 11 claims Figures 5,
9, 10, 11, 14 and 18 are computed from the corrected campaign; until this pass
that sentence was true of four of the six.

**Figure 1** carried two numbers from the published campaign: "XGBoost and
LightGBM at macro-F1 1.0000", which the correction moves to 0.9999 for XGBoost,
and "12 of 67 columns excluded", which Table 3 gives as 13. `regen_fig_concept.py`
now reads `experiments/e8/e8_results.json` for both and asserts them.

**Figure 8** still draws `IdleTime` in the colour of the retained columns, which
is what Figure 6 was redrawn to stop doing. Here it is correct as drawn — the
transferability rule does retain that column, and the legend says "retained under
both" rules, not "retained by the paper" — so the caption now says which test
excludes it instead.

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
