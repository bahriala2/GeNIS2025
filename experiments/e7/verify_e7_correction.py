#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E7, second volet : la preuve directe, et ce que la correction coute.

verify_idletime.py etablissait, depuis le seul depot, qu'IdleTime avait tout
d'un identifiant de fichier de capture. Le notebook a mesure. Ce script lit ce
qu'il a rendu et verifie les trois choses qui decident de la suite :

  A. la preuve directe : une ou deux valeurs par fichier, et ce sont des
     horodatages Unix. Le plafond a 9 classes est ATTEINT, pas approche ;
  B. le temoin : le bras "publiee" rejoue-t-il le tableau 2 ? Sans lui, la
     comparaison mesurerait l'environnement et non la correction ;
  C. ce que retirer IdleTime coute, et si les conclusions du papier tiennent.

Entree : experiments/e7/e7_results.json
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
E = json.loads((HERE / "e7_results.json").read_text(encoding="utf-8"))
R = json.loads((REPO / "paper" / "article1_results.json").read_text(encoding="utf-8"))
P, BIN, RUNS = E["preuve_cardinalite"], E["auc_binaire"], E["runs"]
C = R["slice60"]["class_counts"]
N = sum(C.values())
MODS = ["logreg", "nb", "knn", "rf", "xgboost", "lightgbm", "dnn", "cnn", "rnn"]
FORTS = [m for m in MODS if m != "nb"]
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK   ' if cond else 'ECHEC'} {nom}{('  ' + detail) if detail else ''}")


def mf1(mod, var, proto):
    return RUNS[f"{mod}|{var}|{proto}"]["macro_f1"]


# =========================================================================
# A. La preuve directe
# =========================================================================
print("A. IdleTime est un identifiant de fichier de capture\n")
cmax = max(d["n_unique"] for d in P.values())
chk("au plus deux valeurs distinctes par fichier de capture", cmax <= 2,
    f"maximum {cmax} sur {len(P)} fichiers")
chk("toutes les valeurs sont des multiples de 128, le pas du float32",
    all(int(v) % 128 == 0 for d in P.values() for v in d["valeurs"]))
chk("toutes tombent dans la campagne de fevrier 2025",
    all(1738368000 <= v <= 1739923200 for d in P.values() for v in d["valeurs"]))

ben = [d for n, d in P.items() if "benign" in n]
att = [d for n, d in P.items() if "benign" not in n]
hb, ba = max(d["max"] for d in ben), min(d["min"] for d in att)
chk("les plages benigne et malveillante sont disjointes", ba > hb,
    f"fosse de {(ba - hb) / 3600:.1f} h")
chk("les trois captures bruteforce partagent une seule valeur",
    len({P[f"attack-bruteforce-{k}"]["min"] for k in ("ftp", "smb", "ssh")}) == 1)

print("\n   AUC binaire, la mesure que l'audit publie n'a jamais faite :")
for f, d in sorted(BIN.items(), key=lambda kv: -kv[1]["auc_binaire"]):
    print(f"     {f:<12} AUC {d['auc_binaire']:.4f}   arbre binaire "
          f"{d['arbre_binaire']:.4f}   arbre 9 classes {d['arbre_9_classes']:.4f}")
chk("IdleTime resout PARFAITEMENT la tache binaire",
    BIN["IdleTime"]["auc_binaire"] == 1.0 and BIN["IdleTime"]["arbre_binaire"] == 1.0)
chk("alors qu'il plafonne a 0.62 en neuf classes",
    BIN["IdleTime"]["arbre_9_classes"] < 0.65,
    f"{BIN['IdleTime']['arbre_9_classes']:.4f}")

# Le plafond que la structure impose, calcule depuis les vraies valeurs.
# Une classe ne peut etre reconnue que si sa valeur n'appartient qu'a elle,
# ou si elle est majoritaire parmi celles qui la partagent.
socle = (C["benign"] + max(C[c] for c in ("bruteforce-ftp", "bruteforce-smb",
                                          "bruteforce-ssh"))
         + max(C[c] for c in ("dos-pushack", "dos-slowloris", "dos-udp"))
         + C["dos-hulk"])
part = (BIN["IdleTime"]["arbre_9_classes"] * N - socle) / C["dos-icmp"]
print(f"\n   plafond hors dos-icmp : {socle / N:.4f}")
print(f"   part de dos-icmp qui doit etre sur sa valeur propre : {part:.3f}")
chk("le plafond est ATTEINT, avec dos-icmp presque entier sur sa valeur",
    0.90 < part < 1.0,
    "l'arbre fait exactement ce que la structure permet")
chk("dos-icmp est bien le seul fichier DoS a deux valeurs",
    P["attack-dos-icmp"]["n_unique"] == 2)

# =========================================================================
# B. Le temoin
# =========================================================================
print("\n\nB. Le temoin : la comparaison mesure-t-elle la correction ?\n")
MOD = R["models"]
ec = {m: abs(MOD[f"{m}|audited|strat_seed1"]["macro_f1"] - mf1(m, "publiee", "strat_seed1"))
      for m in MODS if f"{m}|audited|strat_seed1" in MOD}
emax = max(ec.values())
chk("le bras publie rejoue le tableau 2", emax < 0.01,
    f"ecart maximal {emax:.4f} ({max(ec, key=ec.get)})")
chk("le notebook le declare valide", E["temoin"]["valide"])

# =========================================================================
# C. Ce que la correction coute
# =========================================================================
print("\n\nC. Ce que retirer IdleTime coute\n")
print(f"   {'detecteur':<11}{'stratifie':>24}{'temporel':>24}")
print(f"   {'':11}{'publiee':>9}{'corrigee':>9}{'delta':>7}"
      f"{'publiee':>9}{'corrigee':>9}{'delta':>7}")
d_s, d_t = {}, {}
for m in MODS:
    a, b = mf1(m, "publiee", "strat_seed1"), mf1(m, "corrigee", "strat_seed1")
    c_, d_ = mf1(m, "publiee", "temporal"), mf1(m, "corrigee", "temporal")
    d_s[m], d_t[m] = b - a, d_ - c_
    print(f"   {m:<11}{a:>9.4f}{b:>9.4f}{b - a:>+7.4f}"
          f"{c_:>9.4f}{d_:>9.4f}{d_ - c_:>+7.4f}")

chk("toutes les pertes sont negatives : les modeles s'en servaient bien",
    all(d_s[m] <= 0.0001 for m in FORTS) and all(d_t[m] < 0 for m in FORTS))
ms = max(abs(d_s[m]) for m in FORTS)
mt = max(abs(d_t[m]) for m in FORTS)
chk("le cout stratifie reste faible", ms < 0.005,
    f"{ms:.4f} ({max(FORTS, key=lambda m: abs(d_s[m]))})")
chk("le cout TEMPOREL est d'un autre ordre", mt > 0.02,
    f"{mt:.4f} ({max(FORTS, key=lambda m: abs(d_t[m]))})")
chk("et il depasse ce que le papier appelle du bruit", mt > 0.01,
    "la condition auditee doit etre republiee")
print(f"\n   rapport temporel/stratifie : x{mt / ms:.0f}")
print("   C'est la meme signature que pour les douze autres raccourcis :")
print("   retirer un raccourci coute peu sous decoupage aleatoire et beaucoup")
print("   sous protocole temporel. IdleTime se comporte comme ses pairs.")

# =========================================================================
# D. Les conclusions du papier, sous la liste corrigee
# =========================================================================
print("\n\nD. Ce que les conclusions deviennent\n")
chk("le corpus reste sature sous le protocole stratifie",
    min(mf1(m, "corrigee", "strat_seed1")
        for m in ("xgboost", "lightgbm", "rf")) > 0.999,
    f"min {min(mf1(m, 'corrigee', 'strat_seed1') for m in ('xgboost','lightgbm','rf')):.4f}")

for var, lab in (("publiee", "publiee "), ("corrigee", "corrigee")):
    cls = sorted(((m, mf1(m, var, "temporal")) for m in FORTS), key=lambda kv: -kv[1])
    print(f"   ordre temporel, liste {lab} : " + " > ".join(m for m, _ in cls))
    pos = {m: i + 1 for i, (m, _) in enumerate(cls)}
    chk(f"les boostes restent hors du podium temporel ({var})",
        min(pos["xgboost"], pos["lightgbm"]) >= 4,
        f"XGBoost {pos['xgboost']}e, LightGBM {pos['lightgbm']}e")

pos_c = {m: i + 1 for i, (m, _) in enumerate(
    sorted(((m, mf1(m, "corrigee", "temporal")) for m in FORTS), key=lambda kv: -kv[1]))}
pos_p = {m: i + 1 for i, (m, _) in enumerate(
    sorted(((m, mf1(m, "publiee", "temporal")) for m in FORTS), key=lambda kv: -kv[1]))}
chk("LightGBM descend encore : la conclusion est renforcee, pas affaiblie",
    pos_c["lightgbm"] >= pos_p["lightgbm"],
    f"{pos_p['lightgbm']}e -> {pos_c['lightgbm']}e")

r = [RUNS[f"{m}|corrigee|temporal"]["ece"] / RUNS[f"{m}|corrigee|strat_seed1"]["ece"]
     for m in FORTS]
med = sorted(r)[len(r) // 2]
chk("la calibration s'effondre toujours sous le temporel", med > 10,
    f"mediane x{med:.0f}, max x{max(r):.0f}")

print("\n   Le prix a payer, qu'il faut ecrire : le taux de faux positifs")
for m in ("logreg", "knn"):
    a = RUNS[f"{m}|publiee|strat_seed1"]["fpr"]
    b = RUNS[f"{m}|corrigee|strat_seed1"]["fpr"]
    print(f"     {m:<8} stratifie {a:.4f} -> {b:.4f}  (x{b / a:.0f})")

# =========================================================================
# E. Ce que la bande d'environnement autorise a attribuer
# =========================================================================
# Ajoute apres coup, et c'est une correction de ma part : le temoin d'E7 ne
# comparait QUE le bras stratifie. Le bras temporel, qui porte le resultat,
# n'a jamais ete controle. On le controle ici, et la conclusion se resserre.
print("\n\nE. Ce qui est attribuable a la correction, et ce qui ne l'est pas\n")
MODP = R["models"]
env = {}
for m in MODS:
    k = f"{m}|audited|temporal"
    if k in MODP:
        env[m] = abs(MODP[k]["macro_f1"] - mf1(m, "publiee", "temporal"))
DET = ("logreg", "nb", "knn", "rf", "xgboost", "lightgbm")
print(f"   {'detecteur':<11}{'cout mesure':>13}{'ecart au publie':>17}   verdict")
solides = []
for m in sorted(MODS, key=lambda x: -abs(d_t.get(x, 0))):
    if m not in env:
        continue
    cout, e = abs(d_t[m]), env[m]
    det = m in DET
    sur = det or cout > 2 * e
    if sur and m != "nb":
        solides.append(m)
    print(f"   {m:<11}{d_t[m]:>+13.4f}{e:>17.4f}   "
          + ("deterministe, sur" if det else
             "au-dessus du bruit" if sur else "DANS LE BRUIT"))
chk("les quatre plus gros couts portent sur des modeles deterministes",
    all(m in DET for m in sorted(MODS, key=lambda x: -abs(d_t.get(x, 0)))[:4]))
chk("le cout de LightGBM, le plus grand, est sur un modele qui se rejoue exactement",
    env["lightgbm"] < 0.0001, f"ecart au publie {env['lightgbm']:.4f}")
neuro_dans_bruit = [m for m in ("dnn", "rnn", "cnn") if m in env and abs(d_t[m]) < 2 * env[m]]
print(f"\n   reseaux dont le cout ne se distingue pas du bruit : {neuro_dans_bruit}")
print("   Ce n'est pas un probleme pour la conclusion : les quatre ecarts les")
print("   plus grands sont sur lightgbm, knn, rf et xgboost, qui se rejouent")
print("   au quatrieme chiffre. Le resultat repose sur le sol le plus ferme.")

print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("\nLECTURE. IdleTime est un identifiant de fichier, demontre directement.\n"
          "Le retirer coute 0.004 en stratifie et jusqu'a 0.032 en temporel : les\n"
          "modeles s'en servaient. Aucune conclusion principale ne tombe, et celle\n"
          "sur les ensembles boostes se renforce. Mais 0.032 depasse ce que le\n"
          "papier traite comme du bruit : la condition auditee doit etre republiee\n"
          "sur la liste a treize entrees, et non simplement commentee.")
sys.exit(0 if all(ok) else 1)
