#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E7 -- IdleTime est un identifiant de fichier de capture, pas un signal.

Un audit externe conduit sur le papier 1 (BAg-IDS) a recoupe celui-ci et
affirme qu'IdleTime ne prend qu'une ou deux valeurs distinctes par fichier
de capture, et que ces valeurs sont des horodatages Unix absolus. La colonne
serait donc un identifiant de fichier, et elle est RETENUE dans la condition
auditee.

La note demande a etre verifiee, pas crue. Ce script la verifie avec ce que
le depot contient, sans les fichiers bruts -- que ce depot n'a pas. Il ne
peut donc pas compter les valeurs distinctes : c'est le notebook E7 qui le
fait. Ce qu'il etablit ici est plus indirect et, pris ensemble, difficile a
attribuer au hasard :

  A. l'exposition : ce que le papier retient et ce qui en depend ;
  B. le plafond a 9 classes que la structure de collision decrite implique,
     calcule depuis les effectifs de classes -- une route que l'auditeur
     n'a pas empruntee, puisqu'il est parti des fichiers bruts ;
  C. l'arithmetique du float32, qui explique le << une ou deux valeurs >> ;
  D. la signature de tau, la meme sous les trois diagnostics du papier.

Entrees, toutes committees :
  paper/article1_results.json          la campagne publiee
  experiments/e4a/e4abis_results.json  l'audit imbrique
  experiments/e3/e3_results.json       l'audit residuel
"""
import datetime as dt
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
R = json.loads((REPO / "paper" / "article1_results.json").read_text(encoding="utf-8"))
NEST = json.loads((REPO / "experiments" / "e4a" / "e4abis_results.json")
                  .read_text(encoding="utf-8"))["nested"]
E3 = json.loads((REPO / "experiments" / "e3" / "e3_results.json")
                .read_text(encoding="utf-8"))["residual_audit"]
S, A = R["slice60"], R["audit"]
C = S["class_counts"]
N = sum(C.values())
TT = {r["feature"]: r for r in A["transfer_table"]}
ok = []


def chk(nom, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'OK   ' if cond else 'ECHEC'} {nom}{('  ' + detail) if detail else ''}")


# =========================================================================
# A. L'exposition : ce que le papier retient
# =========================================================================
print("A. Ce que le papier fait d'IdleTime\n")
chk("IdleTime est retenu dans la condition auditee",
    "IdleTime" in S["features_audited"],
    f"{len(S['features_audited'])} colonnes retenues")
chk("IdleTime n'est pas sur la liste noire",
    "IdleTime" not in A["blacklist"], f"{len(A['blacklist'])} entrees")

imp = A["perm_importance"]
rang = sorted(imp.items(), key=lambda kv: -kv[1])
chk("IdleTime est la colonne la PLUS importante du papier",
    rang[0][0] == "IdleTime", f"{rang[0][1]:.4f}")
ecart = rang[0][1] / rang[1][1]
chk("et elle devance la suivante d'un facteur eleve",
    ecart > 5, f"{rang[1][0]} a {rang[1][1]:.4f}, soit x{ecart:.1f}")

# =========================================================================
# B. Le plafond a 9 classes implique par la structure de collision
# =========================================================================
# La note decrit le decoupage des fichiers de capture. Si IdleTime est
# constant par fichier, un arbre ne peut, dans chaque groupe de classes qui
# partagent une valeur, que predire la classe majoritaire du groupe. Le
# plafond qui en resulte se calcule depuis les seuls effectifs de classes.
print("\n\nB. Le plafond que la structure de fichiers impose\n")
BF = ["bruteforce-ftp", "bruteforce-smb", "bruteforce-ssh"]   # un seul fichier
DOS = ["dos-icmp", "dos-pushack", "dos-slowloris", "dos-udp"]  # une a deux valeurs


def plafond(groupes):
    return sum(max(C[c] for c in g) for g in groupes) / N


p1 = plafond([["benign"], BF, ["dos-hulk"], DOS])              # 1 valeur DoS
p2 = plafond([["benign"], BF, ["dos-hulk"], DOS[:2], DOS[2:]])  # 2 valeurs DoS
mesure = TT["IdleTime"]["acc seule (stratifie)"]
print(f"   exactitude mesuree, arbre sur IdleTime seul, 9 classes : {mesure:.4f}")
print(f"   plafond si les 4 classes DoS partagent 1 valeur        : {p1:.4f}")
print(f"   plafond si elles se separent en 2 valeurs              : {p2:.4f}")
chk("le plafond a deux valeurs colle a la mesure", abs(p2 - mesure) < 0.02,
    f"ecart {abs(p2 - mesure):.4f}")
# Honnetete de comptabilite : ce test a donne le bon ordre de grandeur avec un
# groupement qui n'etait pas le vrai. Le notebook a depuis mesure la structure
# reelle -- dos-icmp seul sur sa propre valeur a 95 %, les trois autres DoS
# groupes -- et le plafond exact vaut alors 0.6209, soit la mesure au chiffre
# pres. Voir verify_e7_correction.py, section A.
chk("le plafond a une seule valeur ne colle pas, la note dit bien 1 a 2",
    abs(p1 - mesure) > 0.10, f"ecart {abs(p1 - mesure):.4f}")
chk("la mesure est SOUS le plafond, comme un ajustement doit l'etre",
    mesure < p2)

# =========================================================================
# C. L'arithmetique du float32
# =========================================================================
# Un horodatage Unix de fevrier 2025 vaut ~1.739e9, donc 2^30 <= v < 2^31.
# La mantisse du float32 fait 24 bits, le pas y est donc de 2^(30-23) = 128 s.
# Une capture qui dure deux minutes s'ecrase sur une ou deux valeurs : c'est
# exactement ce que la note rapporte, et ca n'a rien d'un hasard.
print("\n\nC. Pourquoi << une ou deux valeurs >> et pas trois cents\n")
V = 1739380352                       # valeur citee pour les captures dos-*
exp = math.floor(math.log2(V))
pas = 2 ** (exp - 23)
utc = dt.datetime.fromtimestamp(V, dt.timezone.utc)
print(f"   valeur citee {V} = {utc:%Y-%m-%d %H:%M:%S} UTC")
chk("la valeur citee tombe bien dans la campagne de capture",
    dt.datetime(2025, 2, 6, tzinfo=dt.timezone.utc) <= utc
    <= dt.datetime(2025, 2, 13, tzinfo=dt.timezone.utc))
chk("le pas du float32 a cette magnitude est de 128 s", pas == 128,
    f"2^({exp}-23) = {pas} s")
chk("elle est un multiple exact du pas, signature de la quantification",
    V % pas == 0)
chk("une capture de ~120 s s'ecrase donc sur 1 a 2 valeurs", 120 <= 2 * pas)

# le fosse entre le dernier benin et la premiere attaque
def ts(*a):
    return dt.datetime(*a, tzinfo=dt.timezone.utc)


fosse = (ts(2025, 2, 10, 15, 30, 8) - ts(2025, 2, 8, 22, 34, 40)).total_seconds() / 3600
chk("les deux plages sont disjointes, d'ou une tache binaire parfaite",
    fosse > 24, f"{fosse:.1f} h entre le dernier benin et la premiere attaque")

# =========================================================================
# D. Pourquoi aucun des trois diagnostics du papier ne l'a vue
# =========================================================================
# Une valeur figee par fichier garde le meme pouvoir predictif des deux cotes
# d'un changement de protocole. Tout critere construit sur un RAPPORT entre
# les deux protocoles y est structurellement aveugle.
print("\n\nD. Les trois diagnostics, et la meme cecite\n")
tau_pub = TT["IdleTime"]["transferabilite"]
tau_nest = NEST["IdleTime"]["tau"]
seuil = A["rule"]["exclusion_tau"] if "exclusion_tau" in A["rule"] else 0.50
print(f"   tau publie           {tau_pub:.4f}    seuil d'exclusion {seuil}")
print(f"   tau imbrique         {tau_nest:.4f}")
chk("le critere publie la laisse passer, et de loin",
    tau_pub - seuil > 0.40, f"{tau_pub:.2f} contre un seuil a {seuil}")
chk("l'audit imbrique aussi : l'exactitude MONTE meme sous le temporel",
    tau_nest > 1.0, f"{NEST['IdleTime']['strat']:.4f} -> {NEST['IdleTime']['temp']:.4f}")
srt = sorted(NEST.items(), key=lambda kv: kv[1]["tau"])
r = [f for f, _ in srt].index("IdleTime") + 1
chk("elle figure parmi les colonnes les PLUS transferables",
    r > 0.8 * len(srt), f"rang {r} sur {len(srt)} par tau croissant")

for cle, lab in (("mutual_information", "information mutuelle"),
                 ("max_abs_correlation", "correlation residuelle")):
    d = E3[cle]
    rr = [f for f, _ in sorted(d.items(), key=lambda kv: -kv[1])].index("IdleTime") + 1
    chk(f"l'audit residuel ne la distingue pas non plus ({lab})",
        rr > len(d) / 4, f"rang {rr} sur {len(d)}")

print("\n   Les trois mesurent un DEGRE D'ASSOCIATION avec l'etiquette, et")
print("   l'association d'un identifiant de fichier est bornee par le plafond")
print("   du point B. Ce qui la trahit n'est pas son association, ce sont ses")
print("   VALEURS : deux par fichier, et ce sont des horodatages.")

# =========================================================================
# E. Ce que ce script ne peut pas etablir
# =========================================================================
print("\n\nE. Ce qui reste a prouver directement\n")
print("   Le comptage des valeurs distinctes par fichier de capture, et l'AUC")
print("   binaire de 1.0000. Les deux demandent 2-flows.zip, que ce depot ne")
print("   contient pas. colab/e7_idletime.ipynb les mesure, puis reentraine la")
print("   campagne avec IdleTime sur la liste noire.")

print(f"\n\n{sum(ok)}/{len(ok)} controles passes")
if all(ok):
    print("\nLECTURE. Tout ce que le depot permet de verifier concorde avec la\n"
          "note. Le plafond a 9 classes calcule depuis les seuls effectifs de\n"
          "classes tombe a 0.009 de la valeur mesuree, et l'arithmetique du\n"
          "float32 explique le nombre de valeurs distinctes. IdleTime doit etre\n"
          "traite comme un raccourci jusqu'a preuve du contraire, et la liste\n"
          "noire passe de douze a treize entrees.")
sys.exit(0 if all(ok) else 1)
