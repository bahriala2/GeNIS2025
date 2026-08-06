#!/usr/bin/env python3
"""Spectre de transferabilite sous les deux normalisations (figure 6 du Word).

La legende du papier annonce << under both normalisations >> : la figure doit donc
montrer tau ET tau*, et pas seulement le rapport brut. Dimensions conservees
(2733x948) pour que l'extent du .docx reste valide.
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R = json.load(open('article1_results.json'))
tt = R['audit']['transfer_table']
P = R['audit']['chance']                       # 0.19422, taux de la classe majoritaire
THR, KMIN = R['audit']['rule']['ratio_below'], R['audit']['rule']['min_acc_x_chance']

rows = []
for r in tt:
    s, t = r['acc seule (stratifie)'], r['acc seule (temporel)']
    rows.append({'f': r['feature'], 's': s, 't': t,
                 'tau': r['transferabilite'],
                 'star': (t - P) / (s - P) if s - P > 0 else float('nan')})
rows.sort(key=lambda d: d['tau'])

def excluded(d, key):
    return d[key] < THR and d['s'] > KMIN * P

exc_tau = [d for d in rows if excluded(d, 'tau')]
exc_str = [d for d in rows if excluded(d, 'star')]
crossing = [d['f'] for d in exc_str if d not in exc_tau]

fig, ax = plt.subplots(figsize=(13.665, 4.74), dpi=200)
x = range(len(rows))
colours = ['#c0392b' if excluded(d, 'tau')
           else '#e08a3c' if d['f'] in crossing
           else '#4a6fa5' for d in rows]
ax.bar(x, [d['tau'] for d in rows], color=colours, edgecolor='none', zorder=2)
ax.plot(x, [d['star'] for d in rows], ls='none', marker='o', ms=3.4,
        mfc='none', mec='#222222', mew=0.9, zorder=3,
        label=r'$\tau^{*}$ (chance-corrected)')
ax.axhline(THR, ls='--', lw=1.1, color='black', zorder=4,
           label='blacklist threshold (0.50)')

ax.set_xticks(list(x))
ax.set_xticklabels([d['f'] for d in rows], rotation=90, fontsize=6.5)
ax.set_xlim(-0.8, len(rows) - 0.2)
ax.set_ylim(0, 1.16)
ax.set_ylabel('transferability\n' r'$acc_{temporal}/acc_{stratified}$', fontsize=10)
ax.set_title('Single-feature transferability spectrum (63 behavioural features), '
             'raw and chance-corrected', fontsize=11)
ax.grid(axis='y', color='0.88', lw=0.6, zorder=0)
ax.set_axisbelow(True)

from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[
    Patch(facecolor='#c0392b', label=r'excluded by the operative rule ($\tau$), 8'),
    Patch(facecolor='#e08a3c', label=r'additionally excluded under $\tau^{*}$, 5'),
    Patch(facecolor='#4a6fa5', label='retained under both'),
    Line2D([], [], ls='none', marker='o', ms=3.4, mfc='none', mec='#222222',
           label=r'$\tau^{*} = (acc_{temp}-p_{max})/(acc_{strat}-p_{max})$'),
    Line2D([], [], ls='--', lw=1.1, color='black', label='threshold (0.50)'),
], loc='lower right', fontsize=7.5, framealpha=0.95, ncol=1)

fig.tight_layout()
for ext in ('png', 'pdf'):
    fig.savefig(f'figures/fig9_transferability_spectrum.{ext}', dpi=200,
                bbox_inches=None, facecolor='white')
print('exclusions tau  :', len(exc_tau))
print('exclusions tau* :', len(exc_str), '| ajoutees :', crossing)
