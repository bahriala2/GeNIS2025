#!/usr/bin/env python3
"""Figure 15 : decroissance du pouvoir predictif avec l'horizon temporel.

Source : experiments/e4a/e4abis_results.json, partie B du notebook E4a-bis.

Un arbre par feature, ajuste une seule fois sur la partition d'entrainement du
protocole temporel, puis evalue sur huit tranches successives de la portion
[60 %, 100 %] de chaque classe. Les tranches 1 a 4 forment l'ancienne partition
de validation, les tranches 5 a 8 l'ancienne partition de test.

Ce que la figure etablit : les colonnes de la liste noire perdent en moyenne
0.393 d'accuracy entre la premiere et la derniere tranche, les colonnes
retenues 0.137. C'est la justification mesuree du choix de la partition la plus
lointaine comme instrument de l'audit, et l'explication de pourquoi la
validation, adjacente au train, n'exclut rien.

Les six colonnes de duree numeriquement identiques se superposent : une seule
courbe est tracee pour elles.
"""
import json
import pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / 'experiments' / 'e4a' / 'e4abis_results.json'
REF = HERE / 'article1_results.json'

WIDTH_IN = 6124575 / 914400          # 6.697 in, l'extent du .docx
HEIGHT_IN = 3.10
DPI = 400
RED, GREY, BLACK = '#c23b34', '#9aa4b1', '#333333'

B = json.load(open(SRC, encoding='utf-8'))
R = json.load(open(REF, encoding='utf-8'))
H = B['horizons']
CHANCE = R['audit']['chance']
NOIRE = {f for f in R['audit']['blacklist'] if f in B['nested']}

DUPES = ['Dur', 'RunTime', 'Mean', 'Sum', 'Min', 'Max']
serie = {f: a for f, a in H.items() if f not in DUPES[1:]}   # une seule courbe
LABEL = {'Dur': 'Dur and its five duplicates'}

plt.rcParams.update({'font.size': 6.5, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})
fig, ax = plt.subplots(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)

xs = list(range(1, 9))
ordre = sorted(serie.items(), key=lambda kv: -kv[1][7])
# ecarter les etiquettes de fin de courbe qui se recouvriraient
MIN_ECART, ys = 0.031, []
for _, accs in ordre:
    y = accs[7]
    if ys and ys[-1] - y < MIN_ECART:
        y = ys[-1] - MIN_ECART
    ys.append(y)
for (f, accs), y_lab in zip(ordre, ys):
    noire = f in NOIRE
    ax.plot(xs, accs, marker='o', ms=2.4,
            lw=1.1 if noire else 0.7,
            color=RED if noire else GREY,
            zorder=3 if noire else 2)
    ax.annotate(LABEL.get(f, f), (8, accs[7]), xytext=(8.28, y_lab),
                textcoords='data', fontsize=5.4, va='center',
                color=RED if noire else '0.45',
                arrowprops=dict(arrowstyle='-', lw=0.35, color='0.7',
                                shrinkA=1, shrinkB=1))

ax.axvline(4.5, color=BLACK, ls=':', lw=0.7, zorder=1)
ax.text(4.42, 1.005, 'validation partition ', ha='right', va='bottom',
        fontsize=5.8, color=BLACK)
ax.text(4.58, 1.005, ' test partition', ha='left', va='bottom',
        fontsize=5.8, color=BLACK)
ax.axhline(CHANCE, color='0.55', ls='--', lw=0.6, zorder=1)
ax.text(7.9, CHANCE + 0.014, 'majority-class rate', fontsize=5.4,
        color='0.45', ha='right')

ax.set_xlim(0.7, 10.4)
ax.set_ylim(0.15, 1.02)
ax.set_xticks(xs)
ax.set_xlabel('horizon slice, from nearest the training window to farthest',
              fontsize=7)
ax.set_ylabel('single-feature accuracy', fontsize=7)
ax.grid(color='0.93', lw=0.4, zorder=0)
ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], color=RED, lw=1.1, marker='o', ms=2.4,
                          label='blacklisted columns (8)'),
                   Line2D([], [], color=GREY, lw=0.7, marker='o', ms=2.4,
                          label='retained columns (6 controls)')],
          loc='lower left', fontsize=6, framealpha=0.95, handlelength=2.0,
          borderpad=0.4, labelspacing=0.35)

fig.tight_layout(pad=0.4)
for out in (HERE / 'figures' / 'figE4_horizons.png',
            HERE / 'figures_manuscrit' / 'figure15_horizons.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')

chute = lambda s: sum(a[0] - a[7] for f, a in H.items() if (f in NOIRE) == s) / \
                  sum(1 for f in H if (f in NOIRE) == s)
print(f'{WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi')
print(f'chute moyenne tranche 1 -> 8 : liste noire {chute(True):+.3f}, '
      f'retenues {chute(False):+.3f}')
