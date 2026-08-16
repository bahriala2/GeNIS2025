#!/usr/bin/env python3
"""Figure 17 : l'audit rejoue sur CICIDS2017.

Source : experiments/e2/e2_results_cicids2017.json (empreinte 2830743|69|15).

Deux panneaux, qui repondent aux deux questions de la section 7 :

  (a) le spectre de transferabilite des 43 features eligibles. Il se lit a cote
      de la Figure 8, qui est le meme spectre sur GeNIS. Aucune barre ne passe
      sous le seuil : l'audit ne fabrique pas de raccourcis la ou il n'y en a
      pas.
  (b) l'importance par permutation contre le pouvoir predictif mono-feature,
      pour les 69 colonnes. Les quatorze colonnes des sept paires identiques
      sont en rouge ; dix d'entre elles ont une importance exactement nulle.
      C'est la meme cecite que sur GeNIS, sur un autre corpus.

Le panneau (a) porte tau sur le MACRO-F1, pas sur l'accuracy, parce que c'est
sous cette forme que la regle a ete appliquee ici : sur un corpus a 80.3 % de
classe majoritaire l'accuracy mono-feature est saturee et le filtre de
predictivite publie, acc > 3 x hasard, depasse 1 (section 7). Une version
anterieure de cette figure tracait tau sur l'accuracy et ne montrait donc pas
la quantite que le texte discute.

Comme regen_fig6.py, la figure est construite a sa largeur finale dans la page,
6.698 in, pour que les tailles de police declarees survivent a l'insertion.
"""
import json
import pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / 'experiments' / 'e2' / 'e2_results_cicids2017.json'

WIDTH_IN = 6124575 / 914400          # extent du .docx : 6.697 in
HEIGHT_IN = 2.75
DPI = 400
RED, GREY, BLUE = '#c23b34', '#9aa4b1', '#4a72b0'

R = json.load(open(SRC, encoding='utf-8'))
SF = R['single_feature']
PI = R['perm_importance']
A = R['audit']
THR = A['rule']['ratio_below']
F1_MIN = A['f1_min']

# --- eligibilite : la meme forme que la regle publiee, portee sur le macro-F1
elig = sorted((f for f in SF if SF[f]['strat_f1'] > F1_MIN),
              key=lambda f: SF[f]['tau_f1'])
below = [f for f in elig if SF[f]['tau_f1'] < THR]
assert len(elig) == A['n_eligible'], (len(elig), A['n_eligible'])
assert len(below) == len(A['blacklist_behavioural'])

# --- les quatorze colonnes des sept paires numeriquement identiques
dup = sorted({c for pair in R['duplicates'] for c in pair})
n_zero = sum(1 for c in dup if PI.get(c, 1.0) == 0.0)

plt.rcParams.update({'font.size': 6, 'axes.linewidth': 0.5,
                     'xtick.major.width': 0.4, 'ytick.major.width': 0.4,
                     'xtick.major.size': 1.8, 'ytick.major.size': 1.8})
fig, ax = plt.subplots(1, 2, figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI)

# ---------------- (a) spectre de transferabilite ----------------
tau = [SF[f]['tau_f1'] for f in elig]
ax[0].bar(range(len(elig)), tau, width=0.85, color=BLUE, edgecolor=BLUE, lw=0.3,
          zorder=2)
ax[0].axhline(THR, ls='-.', lw=0.7, color=RED, zorder=3)
ax[0].axhline(1.0, ls='--', lw=0.6, color='black', zorder=3)
ax[0].text(len(elig) - 0.6, THR - 0.05, 'threshold (0.50)', ha='right',
           va='top', fontsize=5.8, color=RED)
ax[0].text(0.4, 1.29, f'lowest τ = {tau[0]:.2f}  ({elig[0]})', ha='left',
           va='top', fontsize=6)
ax[0].set_xlim(-0.9, len(elig) - 0.1)
ax[0].set_ylim(0, 1.35)
ax[0].set_xlabel('eligible behavioural features, sorted', fontsize=7)
ax[0].set_ylabel('transferability  τ  (macro-F1)', fontsize=7)
ax[0].set_title(f'(a) {len(below)} of {len(elig)} eligible features below the '
                'threshold', fontsize=7, pad=4)
ax[0].grid(axis='y', color='0.9', lw=0.4, zorder=0)
ax[0].set_axisbelow(True)

# ---------------- (b) attribution contre pouvoir predictif ----------------
feats = list(SF)
is_dup = [f in dup for f in feats]
x = [abs(PI.get(f, 0.0)) for f in feats]
y = [SF[f]['strat_f1'] for f in feats]
ax[1].scatter([v for v, d in zip(x, is_dup) if not d],
              [v for v, d in zip(y, is_dup) if not d],
              s=8, c=GREY, edgecolor='none', zorder=2, label='other columns')
ax[1].scatter([v for v, d in zip(x, is_dup) if d],
              [v for v, d in zip(y, is_dup) if d],
              s=12, c=RED, edgecolor='none', zorder=3,
              label=f'in an identical pair ({len(dup)})')
ax[1].set_xscale('symlog', linthresh=1e-5)
ax[1].axvline(1e-4, color='0.55', ls=':', lw=0.7, zorder=1)
ax[1].axhline(F1_MIN, color='0.55', ls=':', lw=0.7, zorder=1)
ax[1].text(1.3e-4, 0.02, 'importance 10⁻⁴', fontsize=5.5, color='0.35')
ax[1].text(1.7e-4, F1_MIN + 0.018, 'predictivity filter', fontsize=5.5,
           color='0.35')
ax[1].annotate('Bwd Packet Length Mean:\nmacro-F1 0.385, importance 0.00000',
               xy=(0, SF['Bwd Packet Length Mean']['strat_f1']),
               xytext=(1.4e-5, 0.61), fontsize=5.8, va='bottom', ha='left',
               arrowprops=dict(arrowstyle='-', lw=0.5, color='0.35',
                               shrinkA=1, shrinkB=2))
ax[1].set_ylim(-0.02, 0.86)
ax[1].set_xlabel('|permutation importance|', fontsize=7)
ax[1].set_ylabel('single-feature macro-F1 (stratified)', fontsize=7)
ax[1].set_title(f'(b) {n_zero} of the {len(dup)} duplicated columns score '
                'exactly zero', fontsize=7, pad=4)
ax[1].grid(color='0.9', lw=0.4, zorder=0)
ax[1].set_axisbelow(True)
ax[1].legend(handles=[Patch(facecolor=RED, label=f'in an identical pair ({len(dup)})'),
                      Patch(facecolor=GREY, label=f'other columns ({len(feats)-len(dup)})')],
             loc='upper right', fontsize=5.8, framealpha=0.95,
             handlelength=1.2, handleheight=0.9, borderpad=0.4,
             labelspacing=0.35)

fig.tight_layout(pad=0.4)
for out in (HERE / 'figures' / 'figE2_cicids2017_audit.png',
            HERE / 'figures_manuscrit' / 'figure17_cicids2017_audit.png'):
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor='white')

print(f'{WIDTH_IN:.3f} x {HEIGHT_IN} in @ {DPI} dpi')
print(f'(a) {len(elig)} eligibles, {len(below)} sous le seuil, '
      f'minimum {tau[0]:.4f} sur {elig[0]}')
print(f'(b) {len(dup)} colonnes dupliquees, {n_zero} a importance exactement nulle')
