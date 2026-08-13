#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensibilite de la liste noire au seuil de transferabilite.

Repond a la demande d'un relecteur : pourquoi 0.5 et pas 0.4 ou 0.7 ?
Tout se calcule depuis article1_results.json, sans reentrainement, parce que
audit.transfer_table contient l'accuracy mono-feature sous les deux protocoles
pour les 63 features comportementales.

Trois choses sont mesurees :

  1. le nombre de features exclues pour chaque seuil, sous tau et sous tau* ;
  2. l'intervalle de seuils sur lequel la liste noire ne change pas du tout,
     c'est-a-dire la marge de robustesse du choix ;
  3. les separations naturelles dans la distribution des tau, pour repondre a
     la question de savoir si 0.5 tombe dans un vide ou au milieu d'un amas.

Usage :  python3 sensitivity_threshold.py [--json chemin] [--md]
"""

import argparse
import json
import pathlib

SEUILS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def charger(chemin):
    R = json.loads(pathlib.Path(chemin).read_text(encoding="utf-8"))
    A = R["audit"]
    return A, A["chance"], A["rule"]["min_acc_x_chance"], A["rule"]["ratio_below"]


def eligibles(A, p, K):
    # La regle ne juge que les features individuellement predictives.
    return [r for r in A["transfer_table"] if r["acc seule (stratifie)"] > K * p]


def valeur(r, p, star):
    s, t = r["acc seule (stratifie)"], r["acc seule (temporel)"]
    return (t - p) / (s - p) if star else r["transferabilite"]


def exclues(elig, p, seuil, star=False):
    return sorted(r["feature"] for r in elig if valeur(r, p, star) < seuil)


def marge(elig, p, seuil, star=False):
    """Intervalle de seuils sur lequel la liste noire est exactement la meme."""
    v = sorted(valeur(r, p, star) for r in elig)
    bas = max([x for x in v if x < seuil], default=0.0)
    haut = min([x for x in v if x >= seuil], default=1.0)
    return bas, haut


def separations(elig, p, star=False):
    v = sorted(valeur(r, p, star) for r in elig)
    g = [(v[i + 1] - v[i], v[i], v[i + 1]) for i in range(len(v) - 1)]
    return sorted(g, reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(pathlib.Path(__file__).parent / "article1_results.json"))
    ap.add_argument("--md", action="store_true", help="sortie en tableau Markdown")
    a = ap.parse_args()

    A, p, K, THR = charger(a.json)
    elig = eligibles(A, p, K)
    n_pos = len(A["blacklist"]) - len(exclues(elig, p, THR))
    tot = len(A["transfer_table"])

    print(f"p_max = {p:.4f}   regle : acc_strat > {K}x p_max  et  tau < {THR}")
    print(f"{tot} features comportementales, {len(elig)} eligibles "
          f"(acc_strat > {K * p:.4f})")
    print(f"{n_pos} colonnes positionnelles exclues par nom, avant tout calcul\n")

    lignes = []
    for s in SEUILS:
        b, bs = exclues(elig, p, s), exclues(elig, p, s, star=True)
        lignes.append((s, len(b), len(b) + n_pos, len(bs), len(bs) + n_pos))

    if a.md:
        print("| Threshold | Behavioural, tau | Blacklist, tau | Behavioural, tau* | Blacklist, tau* |")
        print("|---|---|---|---|---|")
        for s, nb, tb, ns, ts in lignes:
            gras = " **" if abs(s - THR) < 1e-9 else " "
            print(f"|{gras}{s:.1f}{gras.rstrip()} | {nb} | {tb} | {ns} | {ts} |")
    else:
        print(f"{'seuil':>7}{'compt. tau':>12}{'liste tau':>11}"
              f"{'compt. tau*':>13}{'liste tau*':>12}")
        for s, nb, tb, ns, ts in lignes:
            marque = "  <- regle operative" if abs(s - THR) < 1e-9 else ""
            print(f"{s:>7.1f}{nb:>12}{tb:>11}{ns:>13}{ts:>12}{marque}")

    bas, haut = marge(elig, p, THR)
    print(f"\nMarge de robustesse : la liste noire est identique pour tout seuil "
          f"dans ]{bas:.4f}, {haut:.4f}]")
    print(f"   soit une largeur de {haut - bas:.4f} autour de {THR}")

    print("\nSeparations naturelles dans la distribution des tau eligibles :")
    for g, x, y in separations(elig, p)[:3]:
        print(f"   ecart {g:.3f} entre {x:.2f} et {y:.2f}, milieu {(x + y) / 2:.3f}")

    print("\nFeatures exclues par la regle operative :")
    for f in exclues(elig, p, THR):
        r = next(x for x in elig if x["feature"] == f)
        print(f"   {f:<14} acc_strat {r['acc seule (stratifie)']:.3f}  "
              f"acc_temp {r['acc seule (temporel)']:.3f}  tau {r['transferabilite']:.2f}")


if __name__ == "__main__":
    main()
