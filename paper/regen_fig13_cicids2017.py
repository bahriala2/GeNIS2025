#!/usr/bin/env python3
"""Figure 13 : l'audit repete sur CICIDS2017 (section 7 du manuscrit).

Trois panneaux, un par affirmation de la section :

  (a) le spectre de transferabilite des 43 features eligibles. La version
      precedente, dans e2_figures.zip, tracait les neuf features eligibles
      sous la marge en accuracy ; ce n'est pas la regle retenue. L'audit
      porte le filtre de predictivite ET le rapport sur le macro-F1, donc
      43 features eligibles et un rapport tau_F1.
  (b) le plan de l'attribution, exactement l'idiome de la figure 4 : pouvoir
      predictif seul contre importance par permutation, les quatorze colonnes
      des sept paires identiques en rouge.
  (c) la sonde d'horodatage sur les deux corpus, sous les deux protocoles.
      C'est la conclusion corrigee par le second corpus.

Meme discipline que regen_fig6.py : la figure est dessinee a sa taille finale
dans la page (6.697 in, l'extent du .docx), donc les tailles de police tenues
ici sont celles qui seront imprimees. Minimum 6 pt.
"""
import json
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = pathlib.Path(__file__).resolve().parent
E2 = json.load(open(HERE.parent / 'experiments' / 'e2' / 'e2_results_cicids2017.json'))
G = json.load(open(HERE / 'article1_results.json'))
OUT = HERE / 'figures_manuscrit' / 'figure13_cicids2017_audit.png'

WIDTH_IN = 6124575 / 914400          # extent du .docx : 6.697 in
DPI = 400
RED, ORANGE, BLUE, GREY = '#c23b34', '#e0913c', '#4a72b0', '#9a9a9a'

SF, PI, AUD = E2['single_feature'], E2['perm_importance'], E2['audit']
THR = AUD['rule']['ratio_below']                       # 0.50
F1_MIN = AUD['f1_min']                                 # 3 x macro-F1 de la classe majoritaire
DUPS = [c for pair in E2['duplicates'] for c in pair]  # les 14 colonnes des 7 paires

elig = sorted((f for f in SF if SF[f]['strat_f1'] > F1_MIN),
              key=lambda f: SF[f]['tau_f1'])
below = [f for f in elig if SF[f]['tau_f1'] < THR]
zero_dups = [c for c in DUPS if abs(PI[c]) < 1e-9]

plt.rcParams.update({'font.size': 6, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})
HEIGHT_IN = 5.30
# layout contraint : tight_layout ne sait pas placer une grille dont un axe
# porte 43 etiquettes verticales, il ecrasait les titres de la rangee du bas
fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, layout='constrained')
fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.04, hspace=0.03)
gs = fig.add_gridspec(2, 2, height_ratios=[1.30, 1.0], width_ratios=[1.42, 1.0])

# ---------------------------------------------------------------- (a) spectre
ax = fig.add_subplot(gs[0, :])
for i, f in enumerate(elig):
    c = RED if SF[f]['tau_f1'] < THR else BLUE
    ax.bar(i, SF[f]['tau_f1'], width=0.68, color=c, edgecolor=c, lw=0.3, zorder=2)

ax.axhline(THR, ls='-.', lw=0.7, color=RED, zorder=3)
ax.text(len(elig) - 0.4, THR + 0.02, f'exclusion threshold ({THR:.2f})',
        ha='right', va='bottom', fontsize=5.8, color=RED)
ax.axhline(1.0, ls='--', lw=0.6, color='0.45', zorder=3)
ax.text(len(elig) - 0.4, 1.012, 'transfers intact', ha='right', va='bottom',
        fontsize=5.8, color='0.35')

lo = elig[0]
ax.annotate(f'lowest: {SF[lo]["tau_f1"]:.4f}', xy=(0, SF[lo]['tau_f1']),
            xytext=(1.4, SF[lo]['tau_f1'] + 0.20), fontsize=5.8,
            arrowprops=dict(arrowstyle='-', lw=0.5, color='0.3'))

ax.set_xticks(range(len(elig)))
ax.set_xticklabels(elig, rotation=90, fontsize=5.2)
ax.set_xlim(-0.8, len(elig) - 0.2)
ax.set_ylim(0, 1.40)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0, 1.25])
ax.tick_params(axis='y', labelsize=6.2)
ax.set_ylabel(r'transferability $\tau_{F1}$', fontsize=7)
ax.set_title(f'(a) CICIDS2017: {len(below)} of {len(elig)} eligible behavioural features '
             f'below the exclusion threshold', fontsize=7.5, pad=3)
ax.grid(axis='y', color='0.9', lw=0.4, zorder=0)
ax.set_axisbelow(True)

# ---------------------------------------------------------------- (b) attribution
ax = fig.add_subplot(gs[1, 0])
LIN = 1e-5
for f in SF:
    dup = f in DUPS
    ax.scatter(abs(PI[f]), SF[f]['strat_f1'], s=7 if dup else 5,
               color=RED if dup else GREY, alpha=0.95 if dup else 0.6,
               edgecolor='none', zorder=3 if dup else 2)
ax.set_xscale('symlog', linthresh=LIN)
ax.axvline(1e-4, ls=':', lw=0.6, color='0.5', zorder=1)
ax.axhline(F1_MIN, ls='-.', lw=0.6, color='0.35', zorder=1)
ax.text(4.5e-3, F1_MIN + 0.015, f'predictivity filter ({F1_MIN:.4f})',
        fontsize=5.6, color='0.3', ha='center')

# etiquettes posees a cote du point : les fleches de rappel, sur une echelle
# symlog, tracent de longues droites qu'on lit comme des donnees
for name in ('Packet Length Variance', 'Bwd Packet Length Mean'):
    ax.annotate(f'  {name}', xy=(abs(PI[name]), SF[name]['strat_f1']),
                fontsize=5.4, va='center', ha='left', color='0.15')

ax.set_xlim(-LIN / 3, 5e-2)
ax.set_ylim(0, 0.66)
ax.tick_params(labelsize=6)
ax.set_xlabel('|permutation importance|  (symlog, 0 on the axis)', fontsize=6.6)
ax.set_ylabel('macro-F1 of that column alone', fontsize=6.6)
ax.set_title('(b) attribution does not separate the identical columns',
             fontsize=7.5, pad=3)
ax.grid(color='0.9', lw=0.4, zorder=0)
ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], marker='o', ls='', ms=2.6, color=RED,
                          label=f'one of the 7 identical pairs ({len(DUPS)} columns,'
                                f' {len(zero_dups)} at exactly 0)'),
                   Line2D([], [], marker='o', ls='', ms=2.2, color=GREY,
                          label='other behavioural feature')],
          loc='lower right', fontsize=5.6, framealpha=0.95, handlelength=1.0,
          borderpad=0.35, labelspacing=0.3)

# ---------------------------------------------------------------- (c) sonde
ax = fig.add_subplot(gs[1, 1])
gp = G['shortcut_probes']
tp = E2['timestamp_probe']
corpora = [('GeNIS', gp['starttime_only']['strat_mean'],
            gp['starttime_only']['temporal'], gp['chance_majority']),
           ('CICIDS2017', tp['stratifie']['accuracy'],
            tp['temporel_par_classe']['accuracy'], tp['stratifie']['majority'])]
W = 0.30
for i, (name, strat, temp, maj) in enumerate(corpora):
    ax.bar(i - W / 2, strat, width=W, color=BLUE, edgecolor=BLUE, lw=0.3, zorder=2)
    ax.bar(i + W / 2, temp, width=W, color=ORANGE, edgecolor=ORANGE, lw=0.3, zorder=2)
    ax.hlines(maj, i - 0.46, i + 0.46, ls='--', lw=0.7, color='0.3', zorder=4)
    ax.text(i + 0.44, maj + 0.015, f'majority {maj:.2f}', fontsize=5.4,
            va='bottom', ha='right', color='0.3', zorder=5,
            bbox=dict(fc='white', ec='none', pad=0.5))
    for x, v in ((i - W / 2, strat), (i + W / 2, temp)):
        ax.text(x, v + 0.02, f'{v:.4f}', ha='center', va='bottom', fontsize=5.6)

ax.set_xticks(range(len(corpora)))
ax.set_xticklabels([c[0] for c in corpora], fontsize=6.6)
ax.set_xlim(-0.62, len(corpora) - 0.38)
ax.set_ylim(0, 1.42)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.tick_params(axis='y', labelsize=6)
ax.set_ylabel('accuracy of the timestamp probe', fontsize=6.6)
ax.set_title('(c) the same probe, the two corpora', fontsize=7.5, pad=3)
ax.grid(axis='y', color='0.9', lw=0.4, zorder=0)
ax.set_axisbelow(True)
ax.legend(handles=[Patch(facecolor=BLUE, label='stratified'),
                   Patch(facecolor=ORANGE, label='per-class temporal')],
          loc='upper center', ncol=2, fontsize=5.8, framealpha=0.95,
          handlelength=1.1, borderpad=0.35, columnspacing=0.9)

fig.savefig(OUT, dpi=DPI, facecolor='white')
print(f'{OUT.relative_to(HERE.parent)}  {WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi')
print(f'   {len(elig)} eligibles (macro-F1 > {F1_MIN:.4f}), {len(below)} sous le seuil, '
      f'tau_F1 minimal {SF[elig[0]]["tau_f1"]:.4f} sur {elig[0]}')
print(f'   {len(DUPS)} colonnes dupliquees, dont {len(zero_dups)} a importance exactement nulle')
