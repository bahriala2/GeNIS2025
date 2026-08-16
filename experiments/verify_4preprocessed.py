#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcilie le manuscrit avec le module 4-preprocessed de GeNIS.

La section 3.2 du papier avance un ecart de 29 736 flux entre les 368 556 flux
de 60 s sur lesquels la baseline du corpus [6] evalue, et les 338 820 que le
module 2-flows publie. Elle en donne la decomposition et dit qu'aucune des deux
causes n'est documentee. C'est l'affirmation la plus contestable du papier,
parce qu'elle accuse le corpus d'une incoherence.

Ce script la verifie contre une TROISIEME source, independante des deux
premieres : le module 4-preprocessed, qui distribue les memes donnees 60 s sous
forme d'un couple entrainement/holdout deja encode. On n'a pas besoin de le
croire sur parole, il porte ses propres comptes.

Entree : experiments/inspection_4preprocessed.json, produit par
         inspect_4preprocessed.py sur la machine qui detient le corpus.

Il verifie aussi les sondes a une feature des sections 2.4 et 9, depuis
probe_4preprocessed.json, produit par probe_4preprocessed.py sur la meme
machine. Ces chiffres accusent le module d'etre exploitable tel quel : ils
doivent etre reproductibles depuis le depot, pas seulement cites.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "inspection_4preprocessed.json"
if not SRC.exists():
    sys.exit(f"{SRC.name} absent : lance inspect_4preprocessed.py sur la machine "
             "qui detient le corpus, puis depose son rapport ici.")

J = json.loads(SRC.read_text(encoding="utf-8"))
D = J["intervals"]["60"]
SUB = D["label_distribution"]["SubCategoryLabel"]
NTR, NTE = D["n_train"], D["n_test"]
N = NTR + NTE
RATIO = NTR / N

# --- ce que le manuscrit affirme -----------------------------------------
DIT = {
    "total 4-preprocessed 60 s": 368556,
    "total 2-flows 60 s": 338820,
    "ecart": 29736,
    "recon-nmap": 27713,
    "recon-dns": 20,
    "benign-background publie par 2-flows": 8283,
    "benign-background du descripteur": 10286,
    "manque benign-background": 2003,
    "flux benins, tableau 5": 25147,
    "colonnes": 87,
}

ok = []


def chk(nom, obtenu, attendu):
    bon = obtenu == attendu
    ok.append(bon)
    print(f"  {'OK ' if bon else 'ECART'}  {nom:<44} {obtenu:>8}  attendu {attendu:>8}")


print(f"source : {SRC.name}  ({J.get('pandas', '?')} / numpy {J.get('numpy', '?')})")
print(f"repertoire inspecte : {J['directory']}\n")

print("--- structure du module ---")
chk("train + holdout", N, DIT["total 4-preprocessed 60 s"])
chk("colonnes", D["n_columns"], DIT["colonnes"])
chk("somme des sous-categories == n_train", sum(SUB.values()), NTR)
print(f"  info   part d'entrainement                     {RATIO:.6f}  (80/20)")

# La composition complete se retrouve en remettant la partition a l'echelle.
# Le decoupage est stratifie : le total reconstitue doit retomber sur N.
EST = {k: round(v / RATIO) for k, v in SUB.items()}
print("\n--- composition reconstituee a partir de la partition d'entrainement ---")
chk("total reconstitue", sum(EST.values()), N)
chk("recon-nmap", EST["recon-nmap"], DIT["recon-nmap"])
chk("recon-dns", EST["recon-dns"], DIT["recon-dns"])
chk("benign-background", EST["benign-background"],
    DIT["benign-background du descripteur"])

print("\n--- l'ecart de la section 3.2, recompose ---")
manque = EST["benign-background"] - DIT["benign-background publie par 2-flows"]
chk("manque sur benign-background", manque, DIT["manque benign-background"])
ecart = DIT["recon-nmap"] + DIT["recon-dns"] + manque
chk("ecart total", ecart, DIT["ecart"])
chk("368 556 - ecart", N - ecart, DIT["total 2-flows 60 s"])
benin = (EST["benign-user"] + EST["benign-admin"]
         + DIT["benign-background publie par 2-flows"])
chk("flux benins attendus dans 2-flows", benin, DIT["flux benins, tableau 5"])

print("\n--- section 2.4 : ce que le module transmet ---")
absentes = set(D["blacklist_absent"])
presentes = set(D["blacklist_present"])
chk("colonnes positionnelles absentes", len(absentes & {"StartTime", "LastTime", "Rank"}), 3)
print(f"  info   absentes : {sorted(absentes)}")
print(f"  info   presentes de notre liste noire : {sorted(presentes)}")
chk("groupes de colonnes identiques", len(D["duplicate_groups"]), 1)
chk("paires identiques", D["n_duplicate_pairs"], 15)
print(f"  info   groupe : {sorted(D['duplicate_groups'][0])}")
topo = set(D["topology_like_columns"])
chk("Ssaddr et Sdaddr presents", len({"Ssaddr", "Sdaddr"} & topo), 2)
chk("Sport et Dport presents", len({"Sport", "Dport"} & topo), 2)
chk("sous-categories", len(SUB), 13)

if not D["timestamp_probes"]:
    print("\n  NOTE   timestamp_probes est vide, et c'est le resultat attendu :")
    print("         StartTime, LastTime et Rank ne sont pas dans le module,")
    print("         donc il n'y a rien a sonder la. Les sondes de la section 2.4")
    print("         sont dans probe_4preprocessed.json, verifiees ci-dessous.")

# --- les sondes a une feature des sections 2.4 et 9 ----------------------
PSRC = HERE / "probe_4preprocessed.json"
if not PSRC.exists():
    print(f"\n  {PSRC.name} absent : les sondes ne sont pas verifiees.")
else:
    P = json.loads(PSRC.read_text(encoding="utf-8"))["probes"]
    SUB13, CAT4 = P["SubCategoryLabel"], P["CategoryLabel"]
    print("\n--- section 2.4 : sondes sur les treize sous-categories ---")
    chk("taux de classe majoritaire du holdout",
        SUB13["Seq"]["majority_class_rate"], 0.1785)
    chk("Seq, accuracy", SUB13["Seq"]["accuracy"], 0.1713)
    chk("Offset, accuracy", SUB13["Offset"]["accuracy"], 0.0672)
    chk("Dur, accuracy", SUB13["Dur"]["accuracy"], 0.8957)
    chk("Sdaddr, accuracy", SUB13["Sdaddr"]["accuracy"], 0.9947)
    chk("Sdaddr, macro-F1", SUB13["Sdaddr"]["macro_f1"], 0.9102)
    chk("Sdaddr, valeurs distinctes", SUB13["Sdaddr"]["n_unique_values"], 76)
    for f in ("Seq", "Offset"):
        sous = SUB13[f]["accuracy"] < SUB13[f]["majority_class_rate"]
        ok.append(sous)
        print(f"  {'OK ' if sous else 'ECART'}  {f + ', sous le hasard':<44} "
              f"{SUB13[f]['accuracy']:>8}  <       {SUB13[f]['majority_class_rate']}")

    print("\n--- section 2.4 : sondes sur la tache a quatre classes de la baseline ---")
    chk("Sdaddr, accuracy", CAT4["Sdaddr"]["accuracy"], 0.9985)
    chk("Sdaddr, macro-F1", CAT4["Sdaddr"]["macro_f1"], 0.9950)
    chk("Dport, accuracy", CAT4["Dport"]["accuracy"], 0.9838)
    chk("Dport, macro-F1", CAT4["Dport"]["macro_f1"], 0.9652)
    chk("TotBytes (temoin), accuracy", CAT4["TotBytes"]["accuracy"], 0.9892)
    chk("TotBytes (temoin), macro-F1", CAT4["TotBytes"]["macro_f1"], 0.9758)

print(f"\n{sum(ok)}/{len(ok)} controles passes")
sys.exit(0 if all(ok) else 1)
