#!/usr/bin/env python3
"""Figure 19 : ce que coute le choix du seuil de l'audit (E4c).

Chaque detecteur est reentraine sous cinq listes noires, de zero a seize
colonnes comportementales exclues, sous les deux protocoles. La figure trace
l'etendue du macro-F1 temporel qui en resulte.

Ce que la figure etablit : le seuil est un choix declare, et son cout est
maintenant mesure. Pour les huit detecteurs dont le papier tire des
conclusions, passer de six a seize exclusions deplace le macro-F1 temporel
d'au plus 0.023. Le seul qui bouge vraiment est le bayesien naif, la ligne de
base faible, et c'est explicable : un classifieur qui suppose l'independance
conditionnelle est le plus sensible a quelles colonnes correlees restent.

Second enseignement, visible a l'oeil : la liste publiee n'est pas celle qui
flatte. Sous le protocole temporel, tau070 fait mieux pour la plupart des
detecteurs.

Source : experiments/e4c/e4c_results.json et paper/article1_results.json,
d'ou vient la variante tau050, qui est la condition auditee publiee.
"""
import json
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
C = json.loads((HERE.parent / 'experiments' / 'e4c' / 'e4c_results.json')
               .read_text(encoding='utf-8'))
R = json.loads((HERE / 'article1_results.json').read_text(encoding='utf-8'))['models']

WIDTH_IN = 6124575 / 914400
DPI = 400
RED, BLUE, GREY, INK = '#c23b34', '#4a72b0', '#9aa4b1', '#333333'

VARIANTES = ['clean', 'tau040', 'tau050', 'tau070', 'taustar']
VLAB = {'clean': 'no behavioural exclusion (0)', 'tau040': 'τ < 0.40  (6)',
        'tau050': 'τ < 0.50  (8, published)', 'tau070': 'τ < 0.70  (16)',
        'taustar': 'τ* < 0.50  (13)'}
MARQ = {'clean': 'o', 'tau040': 's', 'tau050': 'D', 'tau070': '^', 'taustar': 'v'}
LABEL = {'logreg': 'logistic regression', 'nb': 'naive Bayes', 'knn': 'k-NN',
         'rf': 'random forest', 'xgboost': 'XGBoost', 'lightgbm': 'LightGBM',
         'dnn': 'DNN', 'cnn': 'CNN', 'rnn': 'RNN'}
MODS = ['logreg', 'cnn', 'rnn', 'lightgbm', 'xgboost', 'knn', 'dnn', 'rf', 'nb']


def val(var, mod):
    if var == 'tau050':                       # la campagne publiee
        return R[f'{mod}|audited|temporal']['macro_f1']
    return C['runs'][f'{mod}|{var}|temporal']['macro_f1']


VALS = {m: {v: val(v, m) for v in VARIANTES} for m in MODS}
ETEND = {m: max(d.values()) - min(d.values()) for m, d in VALS.items()}

plt.rcParams.update({'font.size': 6.5, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})

# Axe brise : huit detecteurs tiennent dans [0.97, 1.00], le bayesien naif
# vit entre 0.37 et 0.51. Un axe unique rendrait invisible ce que la figure
# doit montrer, qui est l'etroitesse des huit.
fig, (gauche, droite) = plt.subplots(
    1, 2, figsize=(WIDTH_IN, 2.72), dpi=DPI,
    gridspec_kw={'width_ratios': [1, 3.1], 'wspace': 0.045})
ys = np.arange(len(MODS))[::-1]

for ax in (gauche, droite):
    for m, y in zip(MODS, ys):
        d = VALS[m]
        ax.plot([min(d.values()), max(d.values())], [y, y], color='0.82',
                lw=2.6, solid_capstyle='round', zorder=1)
        for v in VARIANTES:
            pub = v == 'tau050'
            ax.plot(d[v], y, MARQ[v], ms=4.2 if pub else 3.1,
                    mfc=RED if pub else 'white',
                    mec=RED if pub else (BLUE if v == 'tau070' else '0.45'),
                    mew=0.7, zorder=3 if pub else 2)
    ax.set_yticks(ys)
    ax.grid(axis='x', color='0.93', lw=0.4, zorder=0)
    ax.set_axisbelow(True)

gauche.set_xlim(0.352, 0.556)
gauche.set_xticks([0.40, 0.50])
gauche.set_yticklabels([LABEL[m] for m in MODS], fontsize=6.3)
droite.set_xlim(0.9705, 1.0016)
droite.set_xticks([0.975, 0.985, 0.995])
droite.set_yticklabels([])
droite.tick_params(left=False)
gauche.spines['right'].set_visible(False)
droite.spines['left'].set_visible(False)
for ax, x in ((gauche, 1), (droite, 0)):
    ax.plot([x, x], [0, 1], transform=ax.transAxes, clip_on=False,
            marker=[(-0.6, -1), (0.6, 1)], ms=4, mew=0.6, color=INK, ls='none')

# l'etendue, chiffree, a droite de chaque ligne
for m, y in zip(MODS, ys):
    ax = gauche if m == 'nb' else droite
    x = max(VALS[m].values())
    ax.annotate(f'{ETEND[m]:.4f}', (x, y), xytext=(6, 0),
                textcoords='offset points', fontsize=5.4, va='center',
                color=RED if ETEND[m] > 0.05 else '0.45')

droite.set_xlabel('macro-F1 under the temporal protocol', fontsize=7)
droite.xaxis.set_label_coords(0.30, -0.135)
h = [plt.Line2D([], [], ls='none', marker=MARQ[v], ms=4.2 if v == 'tau050' else 3.1,
                mfc=RED if v == 'tau050' else 'white',
                mec=RED if v == 'tau050' else (BLUE if v == 'tau070' else '0.45'),
                mew=0.7, label=VLAB[v]) for v in VARIANTES]
gauche.legend(handles=h, loc='upper left', fontsize=5.5, framealpha=0.96,
              borderpad=0.42, labelspacing=0.32, handletextpad=0.5,
              bbox_to_anchor=(-0.02, 1.02))
droite.text(1.0, 1.028, 'spread', transform=droite.transAxes, ha='right',
            va='bottom', fontsize=5.4, color='0.45')

fig.subplots_adjust(left=0.148, right=0.985, top=0.925, bottom=0.175)
for out in (HERE / 'figures' / 'figE4c_seuil.png',
            HERE / 'figures_manuscrit' / 'figure19_threshold_cost.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')

# --- controles ------------------------------------------------------------
assert {v: len(l) for v, l in C['variantes'].items()} == {
    'clean': 0, 'tau040': 6, 'tau050': 8, 'tau070': 16, 'taustar': 13}
assert round(VALS['xgboost']['tau050'], 4) == 0.9888
_sans_nb = {m: e for m, e in ETEND.items() if m != 'nb'}
print(f'{WIDTH_IN:.3f} in @ {DPI} dpi')
print(f"etendue temporelle, huit detecteurs : "
      f"max {max(_sans_nb.values()):.4f} ({max(_sans_nb, key=_sans_nb.get)}), "
      f"mediane {np.median(list(_sans_nb.values())):.4f}")
print(f"bayesien naif : {ETEND['nb']:.4f}")
_mieux = [m for m in MODS if VALS[m]['tau070'] > VALS[m]['tau050']]
print(f"tau070 fait mieux que la liste publiee pour {len(_mieux)}/{len(MODS)} "
      f"detecteurs : {_mieux}")
