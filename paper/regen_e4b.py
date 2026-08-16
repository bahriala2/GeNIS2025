#!/usr/bin/env python3
"""Figures 15 et 16 : le protocole temporel repete (E4b).

Figure 15 — macro-F1 sur cinq origines glissantes. Ce que la figure etablit :
le classement de la section 6.3, observe sur une seule partition, tient sur
cinq, et il tient plus fort. Les deux ensembles boostes ne sont pas seulement
delcasses par le protocole temporel, ce sont les detecteurs les moins stables
du lot. La regression logistique est la plus stable.

Figure 16 — leave-one-family-out. Ce que la figure etablit : le renversement.
Les memes ensembles boostes, instables sur les origines, sont les seuls a
signaler 100 % des flux d'une famille absente de l'entrainement. La regression
logistique, la plus stable des dix, s'effondre sur trois familles.

Source : experiments/e4b/e4b_results.json.
"""
import json
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

HERE = pathlib.Path(__file__).resolve().parent
B = json.loads((HERE.parent / 'experiments' / 'e4b' / 'e4b_results.json')
               .read_text(encoding='utf-8'))

WIDTH_IN = 6124575 / 914400          # 6.698 in, l'extent du .docx
DPI = 400
RED, BLUE, GREY, INK = '#c23b34', '#4a72b0', '#9aa4b1', '#333333'

LABEL = {'logreg': 'logistic regression', 'nb': 'naive Bayes', 'knn': 'k-NN',
         'rf': 'random forest', 'xgboost': 'XGBoost', 'lightgbm': 'LightGBM',
         'dnn': 'DNN', 'cnn': 'CNN', 'rnn': 'RNN', 'majority': 'majority'}
ORIGINES = ['0.40', '0.45', '0.50', '0.55', '0.60']

plt.rcParams.update({'font.size': 6.5, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})


# =========================================================================
# Figure 15 : les origines glissantes
# =========================================================================
# On ecarte la ligne de base majoritaire (0.036) et le bayesien naif (0.54) :
# leur presence ecraserait la bande 0.87-1.00 ou tout se joue. Ils sont dans
# le tableau, et la legende le dit.
SERIES = [d for d in B['origines_synthese'] if d['modele'] not in ('majority', 'nb')]
SERIES.sort(key=lambda d: -d['std'])          # les instables au premier plan

# Axe brise : les huit detecteurs tiennent dans 0.97-1.00 sauf les deux
# boostes, qui descendent a 0.875. Sur un axe unique, 60 % de la hauteur
# serait vide et la dispersion du groupe de tete serait illisible.
fig, (hi, lo) = plt.subplots(2, 1, figsize=(WIDTH_IN, 3.25), dpi=DPI,
                             sharex=True,
                             gridspec_kw={'height_ratios': [3.2, 1],
                                          'hspace': 0.09})
xs = np.arange(5)
COUL = {}
for d in SERIES:
    m = d['modele']
    boost = m in ('xgboost', 'lightgbm')
    COUL[m] = RED if boost else (BLUE if m == 'logreg' else GREY)
    ys = [B['origines'][f'{m}|o{o}']['macro_f1'] for o in ORIGINES]
    for ax in (hi, lo):
        ax.plot(xs, ys, marker='o', ms=2.6,
                lw=1.3 if boost else 0.8, color=COUL[m],
                zorder=4 if boost else (3 if m == 'logreg' else 2))

# Etiquettes de fin. Les huit valeurs finales tiennent dans 0.017, donc les
# placer a leur hauteur exacte les rendrait illisibles. On les repartit
# regulierement sur la hauteur du panneau haut, dans l'ordre des valeurs, et
# une amorce relie chaque etiquette a son point.
fin = sorted(((d['modele'],
               B['origines'][f"{d['modele']}|o0.60"]['macro_f1'])
              for d in SERIES), key=lambda kv: -kv[1])
HAUT, BAS = 0.9990, 0.9715
ys_lab = [HAUT - i * (HAUT - BAS) / (len(fin) - 1) for i in range(len(fin))]
for (m, y), yl in zip(fin, ys_lab):
    hi.annotate(LABEL[m], (4, y), xytext=(4.16, yl), textcoords='data',
                fontsize=5.5, va='center', color=COUL[m],
                arrowprops=dict(arrowstyle='-', lw=0.35, color='0.75',
                                shrinkA=1, shrinkB=2))

hi.set_ylim(0.9690, 1.0016)
lo.set_ylim(0.8700, 0.8855)
lo.set_yticks([0.875, 0.885])
for ax in (hi, lo):
    ax.set_xlim(-0.25, 6.3)
    ax.grid(color='0.93', lw=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(4, color=INK, ls=':', lw=0.7, zorder=1)
hi.spines['bottom'].set_visible(False)
lo.spines['top'].set_visible(False)
hi.tick_params(bottom=False)
# les marques de rupture
for ax, y in ((hi, 0), (lo, 1)):
    ax.plot([0, 1], [y, y], transform=ax.transAxes, clip_on=False,
            marker=[(-1, -0.6), (1, 0.6)], ms=4, mew=0.6,
            color=INK, ls='none')
lo.set_xticks(xs)
lo.set_xticklabels(ORIGINES)
lo.set_xlabel('rolling origin: the fraction of each class used for fitting',
              fontsize=7)
hi.set_ylabel('macro-F1', fontsize=7)
hi.yaxis.set_label_coords(-0.055, 0.34)
lo.text(3.92, 0.8838, 'the published temporal partition ', ha='right',
        va='center', fontsize=5.5, color=INK)
fig.tight_layout(pad=0.4)
for out in (HERE / 'figures' / 'figE4b_origines.png',
            HERE / 'figures_manuscrit' / 'figure15_rolling_origins.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')
plt.close(fig)

# =========================================================================
# Figure 16 : leave-one-family-out
# =========================================================================
MODS = ['logreg', 'rf', 'dnn', 'xgboost', 'lightgbm']
FAMS = ['bruteforce-ftp', 'bruteforce-smb', 'bruteforce-ssh', 'dos-hulk',
        'dos-icmp', 'dos-pushack', 'dos-slowloris', 'dos-udp']
M = np.array([[B['lofo'][f'{m}|{f}']['recall_famille_inconnue'] for m in MODS]
              for f in FAMS])
A = np.array([[B['lofo'][f'{m}|{f}']['auroc'] for m in MODS] for f in FAMS])

cmap = LinearSegmentedColormap.from_list('rb', ['#b03a30', '#e8c9c4', '#f2f4f7',
                                                '#c3d2e8', '#3f6ba8'])
fig, ax = plt.subplots(figsize=(WIDTH_IN, 2.95), dpi=DPI)
im = ax.imshow(M, aspect='auto', vmin=0, vmax=1, cmap=cmap)
for i in range(len(FAMS)):
    for j in range(len(MODS)):
        v = M[i, j]
        txt = f'{v:.3f}'
        # l'AUROC au hasard est le vrai echec : on le marque
        chance = A[i, j] is not None and A[i, j] < 0.55
        ax.text(j, i - (0.14 if chance else 0), txt, ha='center',
                va='center', fontsize=6.0,
                color='white' if v < 0.22 or v > 0.86 else INK)
        if chance:
            ax.text(j, i + 0.22, f'AUROC {A[i, j]:.2f}', ha='center',
                    va='center', fontsize=4.8, color='white')
ax.set_xticks(range(len(MODS)))
ax.set_xticklabels([LABEL[m] for m in MODS], fontsize=6.5)
ax.set_yticks(range(len(FAMS)))
ax.set_yticklabels(FAMS, fontsize=6.2)
ax.set_xlabel('', fontsize=7)
ax.set_ylabel('family withheld from training', fontsize=7)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.015)
cb.set_label('recall on the withheld family', fontsize=6.5)
cb.ax.tick_params(labelsize=5.6, length=1.5)
cb.outline.set_linewidth(0.4)
fig.tight_layout(pad=0.4)
for out in (HERE / 'figures' / 'figE4b_lofo.png',
            HERE / 'figures_manuscrit' / 'figure16_leave_one_family_out.png'):
    fig.savefig(out, dpi=DPI, facecolor='white')
plt.close(fig)

# --- controles : les chiffres traces sont ceux du depot ------------------
assert round(B['origines']['cnn|o0.60']['macro_f1'], 4) == 0.9938
_s = {d['modele']: d for d in B['origines_synthese']}
assert round(_s['logreg']['std'], 4) == 0.0013
assert round(_s['lightgbm']['std'], 4) == round(_s['xgboost']['std'], 4) == 0.0562
assert all(B['lofo'][f'{m}|{f}']['recall_famille_inconnue'] == 1.0
           for m in ('xgboost', 'lightgbm') for f in FAMS)
assert all(B['lofo'][f'{m}|{f}']['fpr_benin'] == 0.0
           for m in ('xgboost', 'lightgbm') for f in FAMS)
print(f'{WIDTH_IN:.3f} in @ {DPI} dpi')
print(f"figure 15 : {len(SERIES)} detecteurs traces, sigma de "
      f"{min(d['std'] for d in SERIES):.4f} a {max(d['std'] for d in SERIES):.4f}")
_bas = [(f, MODS[j]) for i, f in enumerate(FAMS) for j in range(len(MODS))
        if A[i, j] is not None and A[i, j] < 0.55]
print(f"figure 16 : {len(_bas)} cellule(s) a l'AUROC du hasard : {_bas}")
