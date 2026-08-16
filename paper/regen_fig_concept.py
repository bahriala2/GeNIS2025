#!/usr/bin/env python3
"""Figure 1 : la chaine d'argument du papier, du calendrier de capture au
benchmark audite.

Mineur 19 du rapport de relecture, qui demandait explicitement une figure
conceptuelle sur la chaine
    capture schedule -> shortcut -> random split -> temporal split
    -> audit -> audited benchmark

Rien n'est invente ici : chaque encadre porte la mesure qui l'etablit, et
chaque mesure est reprise de paper/article1_results.json ou de la section
citee. Le code couleur porte l'argument : le raccourci est present tant que
les encadres sont rouges, et le protocole temporel, qui est le remede usuel,
reste rouge. C'est le point du papier.

Sortie : paper/figures/fig_concept.png
         paper/figures_manuscrit/figure01_argument_chain.png
"""
import json
import pathlib
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch
from matplotlib.path import Path

HERE = pathlib.Path(__file__).resolve().parent
R = json.loads((HERE / 'article1_results.json').read_text(encoding='utf-8'))

WIDTH_IN = 6124575 / 914400          # 6.698 in, l'extent du .docx
HEIGHT_IN = 3.80
DPI = 400

RED, BLUE, GREY = '#c23b34', '#4a72b0', '#9aa4b1'
RED_BG, BLUE_BG = '#faeceb', '#e9eff7'
INK = '#25292e'

# --- les six etapes -------------------------------------------------------
# 'evidence' est verifiee contre les resultats publies plus bas.
STAGES = [
    dict(n='1', title='Capture schedule',
         body='Benign traffic on 6-8 February, every attack on 10-12 '
              'February. Each class occupies one contiguous window of the '
              'capture.',
         evid='40 h with no labelled traffic between the two blocks',
         sec='Section 3.3', state='shortcut'),
    dict(n='2', title='Shortcut',
         body='Position in the capture becomes a near-perfect class '
              'predictor, and eight behavioural columns carry the same '
              'information.',
         evid='StartTime alone: 0.9970 accuracy, against 0.1942 for the '
              'majority class',
         sec='Section 6.2', state='shortcut'),
    dict(n='3', title='Random split',
         body='The standard protocol hides it. The nine-class task is '
              'solved and the leaderboard carries almost no information.',
         evid='XGBoost and LightGBM at macro-F1 1.0000; 11 of 45 pairs not '
              'separable',
         sec='Section 6.1', state='shortcut'),
    dict(n='4', title='Temporal split',
         body='The usual remedy, applied within each class. It does not '
              'remove the shortcut: a class sits in one window, so ordering '
              'inside that window cannot break the association.',
         evid='the same probe still scores 0.9862',
         sec='Section 6.2', state='shortcut'),
    dict(n='5', title='Audit',
         body='Exclude what does not survive the change of protocol: '
              'transferability below 0.50 among columns that are '
              'individually predictive.',
         evid='12 of 67 columns excluded; permutation importance below '
              '1e-4 for all eight behavioural ones',
         sec='Section 4.3', state='audited'),
    dict(n='6', title='Audited benchmark',
         body='Removing them costs almost nothing under a random split, '
              'which is what shows the shortcuts were redundant. The '
              'temporal ranking is what moves.',
         evid='largest stratified loss 0.0018; both boosted ensembles leave '
              'the top',
         sec='Section 6.3', state='audited'),
]

# --- controles : les chiffres des encadres doivent etre ceux du depot ------
M, A = R['models'], R['audit']
assert R['shortcut_probes']['chance_majority'] == A['chance']
assert round(A['chance'], 4) == 0.1942
assert round(R['shortcut_probes']['starttime_only']['strat_mean'], 4) == 0.9970
assert round(R['shortcut_probes']['starttime_only']['temporal'], 4) == 0.9862
assert len(A['blacklist']) == 12 and len(R['slice60']['features_full']) == 67
assert all(abs(A['perm_importance'][f]) < 1e-4
           for f in A['blacklist'] if f in A['perm_importance'])
# le 1.0000 du tableau 2 est la moyenne sur cinq graines, pas la graine 1
assert all(round(sum(M[f'{m}|audited|strat_seed{s_}']['macro_f1']
                     for s_ in range(1, 6)) / 5, 4) == 1.0
           for m in ('xgboost', 'lightgbm'))
_MODELS = ('majority', 'logreg', 'nb', 'knn', 'rf', 'xgboost', 'lightgbm',
           'rnn', 'cnn', 'dnn', 'ftt')
_loss = max(M[f'{m}|clean|strat_seed1']['macro_f1']
            - M[f'{m}|audited|strat_seed1']['macro_f1'] for m in _MODELS)
assert round(_loss, 4) == 0.0018, _loss

# --- geometrie, en pouces -------------------------------------------------
BW, BH, GAP = 2.02, 1.44, 0.26
XS = [0.05 + i * (BW + GAP) for i in range(3)]
Y_BOT = 0.32
Y_TOP = Y_BOT + BH + 0.52             # la gouttiere ou passe le retour
HEAD = 0.245                          # bandeau de titre

fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, WIDTH_IN)
ax.set_ylim(0, HEIGHT_IN)
ax.axis('off')
fig.patch.set_facecolor('white')


def box(x, y, st):
    on = st['state'] == 'shortcut'
    edge, fill = (RED, RED_BG) if on else (BLUE, BLUE_BG)
    ax.add_patch(FancyBboxPatch((x, y), BW, BH, boxstyle='round,pad=0,rounding_size=0.05',
                                linewidth=0.7, edgecolor=edge, facecolor=fill, zorder=2))
    # bandeau de titre
    ax.add_patch(FancyBboxPatch((x, y + BH - HEAD), BW, HEAD,
                                boxstyle='round,pad=0,rounding_size=0.05',
                                linewidth=0, facecolor=edge, zorder=3))
    ax.add_patch(plt.Rectangle((x, y + BH - HEAD), BW, HEAD * 0.45,
                               linewidth=0, facecolor=edge, zorder=3))
    ax.text(x + 0.09, y + BH - HEAD / 2, st['n'], fontsize=7.2, weight='bold',
            color='white', va='center', ha='left', zorder=4)
    ax.text(x + 0.24, y + BH - HEAD / 2, st['title'], fontsize=7.2,
            weight='bold', color='white', va='center', ha='left', zorder=4)

    yy = y + BH - HEAD - 0.13
    for ln in textwrap.wrap(st['body'], 40):
        ax.text(x + 0.10, yy, ln, fontsize=5.9, color=INK, va='top',
                ha='left', zorder=4)
        yy -= 0.113
    yy -= 0.045
    for ln in textwrap.wrap(st['evid'], 41):
        ax.text(x + 0.10, yy, ln, fontsize=5.7, color=edge, va='top',
                ha='left', zorder=4, style='italic')
        yy -= 0.107
    ax.text(x + BW - 0.09, y + 0.07, st['sec'], fontsize=5.2, color=GREY,
            va='bottom', ha='right', zorder=4)


def arrow(x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>',
                                 mutation_scale=7, linewidth=0.9,
                                 color='#6b7480', zorder=1,
                                 shrinkA=0, shrinkB=0))


for i, st in enumerate(STAGES):
    box(XS[i % 3], Y_TOP if i < 3 else Y_BOT, st)

# fleches horizontales
for r, y in ((0, Y_TOP), (1, Y_BOT)):
    for i in range(2):
        arrow(XS[i] + BW, y + BH / 2, XS[i + 1] - 0.015, y + BH / 2)

# retour en serpentin de l'encadre 3 vers l'encadre 4, dans la gouttiere
y_mid = Y_TOP - 0.26
cx3, cx4 = XS[2] + BW / 2, XS[0] + BW / 2
ax.add_patch(PathPatch(
    Path([(cx3, Y_TOP), (cx3, y_mid), (cx4, y_mid), (cx4, Y_BOT + BH)],
         [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO]),
    fill=False, linewidth=0.9, edgecolor='#6b7480', zorder=1))
arrow(cx4, y_mid - 0.13, cx4, Y_BOT + BH + 0.015)
ax.text((cx3 + cx4) / 2, y_mid + 0.035,
        'the standard remedy, and on this corpus it does not remove it',
        fontsize=5.8, color='#6b7480', va='bottom', ha='center')

# legende : le code couleur porte l'argument, il doit etre nomme
for x0, col, lab in ((XS[0], RED, 'the shortcut is present'),
                     (XS[0] + 1.30, BLUE, 'the shortcut is removed, by '
                      'feature exclusion rather than by the protocol')):
    ax.add_patch(FancyBboxPatch((x0, 0.105), 0.15, 0.085,
                                boxstyle='round,pad=0,rounding_size=0.03',
                                linewidth=0.6, edgecolor=col,
                                facecolor=RED_BG if col == RED else BLUE_BG,
                                zorder=2))
    ax.text(x0 + 0.20, 0.1475, lab, fontsize=5.8, color=col, va='center',
            ha='left')

for out in (HERE / 'figures' / 'fig_concept.png',
            HERE / 'figures_manuscrit' / 'figure01_argument_chain.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')
print(f'{WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi')
print(f'plus grande perte stratifiee clean -> audited : {_loss:.4f}')
