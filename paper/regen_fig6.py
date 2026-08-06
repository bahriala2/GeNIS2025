#!/usr/bin/env python3
"""Figure 6 : spectre de transferabilite sous les deux normalisations.

Reprend le codage choisi par l'auteur (barres appariees, pleines pour tau et
hachurees pour tau*, rouge / orange / bleu) mais construit la figure a sa
taille finale dans la page. C'est le point important : matplotlib exprime les
polices en points par rapport a figsize, donc une figure dessinee a 6.70 in de
large et placee a 6.70 in dans le .docx conserve exactement les tailles
demandees. Dessiner large puis reduire, comme la version precedente, divisait
les etiquettes par le facteur de reduction et les ramenait sous 4 pt.

Cible : 6 pt minimum a la taille imprimee (regle Elsevier).
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

WIDTH_IN = 6124575 / 914400          # extent du .docx : 6.697 in
HEIGHT_IN = 3.45
DPI = 400

R = json.load(open('article1_results.json'))
P = R['audit']['chance']
THR = R['audit']['rule']['ratio_below']
KMIN = R['audit']['rule']['min_acc_x_chance']

rows = []
for r in R['audit']['transfer_table']:
    s, t = r['acc seule (stratifie)'], r['acc seule (temporel)']
    rows.append({'f': r['feature'], 's': s, 'tau': r['transferabilite'],
                 'star': (t - P) / (s - P) if s - P > 0 else float('nan')})
rows.sort(key=lambda d: d['tau'])

def exc(d, k):
    return d[k] < THR and d['s'] > KMIN * P

RED, ORANGE, BLUE = '#c23b34', '#e0913c', '#4a72b0'
def colour(d):
    if exc(d, 'tau'):  return RED
    if exc(d, 'star'): return ORANGE
    return BLUE
n_red = sum(1 for d in rows if exc(d, 'tau'))
n_org = sum(1 for d in rows if exc(d, 'star') and not exc(d, 'tau'))
n_blue = len(rows) - n_red - n_org

plt.rcParams.update({'font.size': 6, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})
fig, ax = plt.subplots(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)

W = 0.40
for i, d in enumerate(rows):
    c = colour(d)
    ax.bar(i - W / 2, d['tau'], width=W, color=c, edgecolor=c, lw=0.3, zorder=2)
    ax.bar(i + W / 2, d['star'], width=W, facecolor='white', edgecolor=c,
           lw=0.3, hatch='////', zorder=2)

ax.axhline(THR, ls='--', lw=0.7, color='black', zorder=3)
# a droite les barres montent jusqu'a 1.2 : l'etiquette va a gauche, ou seules
# les huit barres rouges (0.33 au plus haut) occupent la zone sous le seuil
ax.text(0.1, THR + 0.02, 'threshold (0.50)', ha='left', va='bottom', fontsize=5.8)

ax.set_xticks(range(len(rows)))
ax.set_xticklabels([d['f'] for d in rows], rotation=90, fontsize=6)
ax.set_xlim(-0.9, len(rows) - 0.1)
ax.set_ylim(0, 1.2)
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
ax.tick_params(axis='y', labelsize=6.5)
ax.set_ylabel('transferability', fontsize=7.5)
ax.set_title('Single-feature transferability spectrum under both normalisations '
             '(63 behavioural features)', fontsize=7.5, pad=4)
ax.grid(axis='y', color='0.9', lw=0.4, zorder=0)
ax.set_axisbelow(True)

hatch_tau = Patch(facecolor='0.62', edgecolor='0.35', lw=0.3, label=r'$\tau$  (raw ratio, operative rule)')
hatch_str = Patch(facecolor='white', edgecolor='0.35', lw=0.3, hatch='////',
                  label=r'$\tau^{*}$  (above chance)')
ax.legend(handles=[hatch_tau, hatch_str,
                   Patch(facecolor=RED, label=f'excluded under both rules ({n_red})'),
                   Patch(facecolor=ORANGE, label=f'excluded only under $\\tau^{{*}}$ ({n_org})'),
                   Patch(facecolor=BLUE, label=f'retained under both ({n_blue})')],
          loc='upper left', ncol=3, fontsize=6, framealpha=0.95,
          handlelength=1.5, handleheight=0.9, columnspacing=1.0,
          borderpad=0.4, labelspacing=0.35)

fig.tight_layout(pad=0.3)
fig.savefig('figures/fig6_spectrum_both.png', dpi=DPI, facecolor='white')
print(f'{WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi | rouge {n_red}, orange {n_org}, bleu {n_blue}')
