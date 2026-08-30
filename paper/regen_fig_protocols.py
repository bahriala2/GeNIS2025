#!/usr/bin/env python3
"""Figure 4 : les quatre facons de decouper le corpus qui apparaissent dans ce
papier, sur un meme axe de temps de capture.

La section 4 est la plus dense du manuscrit et n'avait aucune figure. Elle
definit quatre partitions differentes, chacune en prose, et le lecteur doit
les tenir toutes en tete pour suivre les sections 6 a 9 :

  (a) le decoupage stratifie, qui ignore le temps ;
  (b) le decoupage chronologique global, qui vide des classes et que le
      papier rapporte comme une propriete du corpus, pas comme un protocole ;
  (c) le decoupage temporel PAR CLASSE, qui est le protocole evalue ;
  (d) l'audit imbrique, contenu dans la partition d'entrainement de (c), et
      les origines glissantes, qui deplacent la coupure de (c).

Une seule classe est dessinee : les quatre schemas se lisent de la meme facon
pour les neuf. Les proportions sont celles du papier, 60/20/20.

Aucune donnee n'est lue : c'est un schema de protocole, pas une mesure.
"""
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent
WIDTH_IN = 6124575 / 914400
HEIGHT_IN = 3.76
DPI = 400

TRAIN, VAL, TEST = '#4a72b0', '#9aa4b1', '#c23b34'
INK, SOFT = '#25292e', '#5d6570'

fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, WIDTH_IN)
ax.set_ylim(0, HEIGHT_IN)
ax.axis('off')
fig.patch.set_facecolor('white')

X0, X1 = 0.30, 6.42
W = X1 - X0
BH = 0.26


def bande(y, f0, f1, couleur, texte=None, h=BH, fs=6.0):
    x, w = X0 + f0 * W, (f1 - f0) * W
    ax.add_patch(Rectangle((x, y), w, h, facecolor=couleur, edgecolor='white',
                           linewidth=0.8, zorder=2))
    if texte:
        ax.text(x + w / 2, y + h / 2, texte, ha='center', va='center',
                fontsize=fs, color='white', zorder=3)


def entete(y, lettre, texte, sous, h=BH):
    """Titre AU-DESSUS de la bande : a gauche, il mangeait toute la largeur."""
    ax.text(X0, y + h + 0.195, f'({lettre})  {texte}', ha='left',
            va='baseline', fontsize=6.8, weight='bold', color=INK)
    ax.text(X0, y + h + 0.075, sous, ha='left', va='baseline', fontsize=5.7,
            color=SOFT)


# --- (a) stratifie : le temps n'intervient pas ---------------------------
y = 3.18
entete(y, 'a', 'Stratified split',
       'random, repeated over five seeds; capture time plays no part, so the three windows interleave')
for i in range(34):
    bande(y, i / 34, (i + 1) / 34, (TRAIN, VAL, TRAIN, TEST, TRAIN, VAL,
                                    TRAIN, TRAIN, TEST, VAL)[i % 10])


# --- (b) chronologique global : degenere ---------------------------------
y = 2.42
entete(y, 'b', 'Global chronological split',
       'degenerate on GeNIS: the last 20% holds classes the first 60% never '
       'contains. Reported as a property of the corpus, not used as a protocol')
# Sur un axe qui court A L'INTERIEUR d'une classe, une coupe chronologique
# globale ne coupe rien : la classe tombe entiere dans une seule fenetre, et
# c'est exactement ce qui la rend degeneree. La dessiner en 60/20/20 la
# rendait indiscernable de (c), dont elle est le contraire.
_h = 0.115
bande(y + 0.145, 0, 1.0, TRAIN, None, h=_h)
ax.text(X0 + 0.5 * W, y + 0.145 + _h / 2, 'benign, captured first',
        ha='center', va='center', fontsize=5.6, color='white', zorder=3)
bande(y, 0, 1.0, TEST, None, h=_h)
ax.text(X0 + 0.5 * W, y + _h / 2, 'an attack family captured last',
        ha='center', va='center', fontsize=5.6, color='white', zorder=3)


# --- (c) temporel par classe : le protocole evalue -----------------------
y = 1.62
entete(y, 'c', 'Per-class temporal split — the protocol evaluated here',
       'the same 60/20/20 cut applied inside each class, so all nine remain '
       'present in all three windows')
bande(y, 0, 0.60, TRAIN, 'train')
bande(y, 0.60, 0.80, VAL, 'val')
bande(y, 0.80, 1.0, TEST, 'test')
ax.add_patch(Rectangle((X0 - 0.035, y - 0.055), W + 0.07, BH + 0.11,
                       fill=False, edgecolor=INK, lw=0.9, zorder=4))

# --- (d) ce que les deux experiences deplacent ---------------------------
y = 0.66
entete(y + 0.315, 'd', 'What the two follow-up experiments move',
       'both stay inside (c), and neither opens a partition it should not',
       h=0.215)
bande(y + 0.30, 0, 0.45, TRAIN, 'inner fit', h=0.215, fs=5.6)
bande(y + 0.30, 0.45, 0.60, TEST, 'inner eval', h=0.215, fs=5.6)
ax.add_patch(Rectangle((X0 - 0.03, y + 0.30 - 0.04), 0.60 * W + 0.06,
                       0.215 + 0.08, fill=False, edgecolor=INK, lw=0.7,
                       ls=(0, (2, 1.4)), zorder=4))
ax.text(X0 + 0.60 * W + 0.08, y + 0.408,
        'nested audit (Section 4.3): 75/25 within the training window',
        ha='left', va='center', fontsize=5.3, color=INK)

ax.add_patch(Rectangle((X0, y + 0.055), W, 0.075, facecolor='#eef1f5',
                       edgecolor='none', zorder=1))
for f in (0.40, 0.45, 0.50, 0.55, 0.60):
    x = X0 + f * W
    ax.plot([x, x], [y - 0.005, y + 0.19], color=TEST, lw=1.0, zorder=3)
    ax.text(x, y - 0.05, f'{f:.2f}', ha='center', va='top', fontsize=5.0,
            color=TEST)
ax.text(X0 + 0.62 * W + 0.08, y + 0.092,
        'rolling origins (Figure 15): the (c) cut moved five times',
        ha='left', va='center', fontsize=5.3, color=TEST)

# --- l'axe de temps commun ----------------------------------------------
ya = 0.30
ax.add_patch(FancyArrowPatch((X0, ya), (X1 + 0.12, ya), arrowstyle='-|>',
                             mutation_scale=7, lw=0.8, color=INK,
                             shrinkA=0, shrinkB=0, zorder=3))
for f, lab, ha in ((0.0, 'earliest flow of the class', 'left'),
                   (1.0, 'latest', 'right')):
    ax.plot([X0 + f * W], [ya], marker='|', ms=4, color=INK, zorder=4)
    ax.text(X0 + f * W, ya - 0.075, lab, ha=ha, va='top', fontsize=5.4,
            color=SOFT)
ax.text((X0 + X1) / 2, ya + 0.055, 'capture time, within one class',
        ha='center', va='bottom', fontsize=6.2, color=INK)

# --- legende -------------------------------------------------------------
for i, (c, lab) in enumerate(((TRAIN, 'fitting window'),
                              (VAL, 'validation window'),
                              (TEST, 'evaluation window'))):
    x = X0 + i * 1.62
    ax.add_patch(Rectangle((x, 0.045), 0.155, 0.082, facecolor=c,
                           edgecolor='none'))
    ax.text(x + 0.20, 0.086, lab, ha='left', va='center', fontsize=5.6,
            color=SOFT)

for out in (HERE / 'figures' / 'fig_protocols.png',
            HERE / 'figures_manuscrit' / 'figure04_partition_schemes.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')
print(f'{WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi')
