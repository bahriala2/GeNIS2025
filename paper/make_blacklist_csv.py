#!/usr/bin/env python3
"""Emit paper/blacklist.csv : the machine-readable disposition of every column.

Reviewer minor 14. The blacklist is stated three times in the manuscript, in
prose in Section 4.3, as Table 3, and as a spectrum in Figure 6. None of those
can be read by a script, so anyone wanting to reproduce the audited condition
has to retype twelve names and trust their eyes. This writes the whole
disposition out once, with the measurements that produced it.

Sources, all committed:
  paper/article1_results.json            the published campaign (audit block)
  experiments/e4a/e4abis_results.json    the nested audit that re-derives the
                                         list without opening the test set

One row per column of the released 2-flows module that the audit had an
opinion about: 23 identifiers excluded by name, 4 positional columns excluded
by name, and the 63 behavioural columns the rule actually scans. The 23
constant columns dropped before the audit are NOT listed: cell 1.3 of the
pipeline discards them by inspection and the released results record their
count but not their names.
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "blacklist.csv"

# Cellule 1.3 du pipeline, IDENT_LIST. Les 23 sont toutes presentes dans le
# corpus : slice60.identifiers_excluded vaut 23.
IDENTIFIERS = ["FlowID", "AutoId", "SrcAddr", "DstAddr", "Ssaddr", "Sdaddr",
               "SrcMac", "DstMac", "SrcOui", "DstOui", "Sport", "Dport",
               "sIpId", "dIpId", "sMpls", "dMpls", "sAS", "dAS", "iAS",
               "sCo", "dCo", "sVid", "dVid"]

R = json.loads((HERE / "article1_results.json").read_text(encoding="utf-8"))
B = json.loads((REPO / "experiments" / "e4a" / "e4abis_results.json")
               .read_text(encoding="utf-8"))

A = R["audit"]
P_MAX = A["chance"]                      # 0.19422112035889263
R_THR = A["rule"]["ratio_below"]         # 0.50
K_MIN = A["rule"]["min_acc_x_chance"]    # 3.0
BLACK = A["blacklist"]
POSITIONAL = [c for c in BLACK if c not in
              {r["feature"] for r in A["transfer_table"]}]
ROWS = {r["feature"]: r for r in A["transfer_table"]}
NESTED = B["nested"]

# groupes de colonnes numeriquement identiques, reconstruits depuis les paires
# que l'audit a signalees (cellule 5.2, np.allclose a 1e-5 relatif)
groups, seen = [], {}
for a, b in A["duplicate_pairs"]:
    ga, gb = seen.get(a), seen.get(b)
    if ga is None and gb is None:
        g = {a, b}
        groups.append(g)
        seen[a] = seen[b] = g
    elif ga is None:
        gb.add(a)
        seen[a] = gb
    elif gb is None:
        ga.add(b)
        seen[b] = ga
    elif ga is not gb:
        ga |= gb
        for k in gb:
            seen[k] = ga
        groups.remove(gb)
GROUP = {c: f"identical-{i + 1}" for i, g in enumerate(groups) for c in sorted(g)}


def tau_star(s, t):
    return (t - P_MAX) / (s - P_MAX)


# rang de l'audit imbrique, parmi les seules colonnes eligibles au filtre de
# predictivite : c'est le classement dont la section 4.3 dit qu'il retrouve
# les huit publiees aux rangs 1 a 8.
elig = [f for f, v in NESTED.items() if v["strat"] > K_MIN * P_MAX]
RANK = {f: i + 1 for i, f in
        enumerate(sorted(elig, key=lambda f: NESTED[f]["tau"]))}

FIELDS = ["column", "category", "disposition", "excluded_by",
          "perm_importance", "acc_stratified", "acc_temporal", "tau",
          "tau_star", "flagged_tau", "flagged_tau_star", "predictive",
          "nested_acc_stratified", "nested_acc_temporal", "nested_tau",
          "nested_rank", "identical_group"]


def blank(col, category, why):
    d = {k: "" for k in FIELDS}
    d.update(column=col, category=category, disposition="excluded",
             excluded_by=why)
    return d


out = [blank(c, "identifier", "name") for c in IDENTIFIERS]
out += [blank(c, "positional", "name") for c in POSITIONAL]

for f, r in ROWS.items():
    s, t = r["acc seule (stratifie)"], r["acc seule (temporel)"]
    ts = tau_star(s, t)
    predictive = s > K_MIN * P_MAX
    flag = predictive and r["transferabilite"] < R_THR
    flag_star = predictive and ts < R_THR
    assert flag == (r["raccourci"] == "OUI"), f
    n = NESTED.get(f)
    out.append({
        "column": f,
        "category": "behavioural",
        "disposition": "excluded" if flag else "retained",
        "excluded_by": "transferability rule" if flag else "",
        "perm_importance": f'{r["importance"]:.4f}',
        "acc_stratified": f"{s:.3f}",
        "acc_temporal": f"{t:.3f}",
        "tau": f'{r["transferabilite"]:.2f}',
        "tau_star": f"{ts:.4f}",
        "flagged_tau": "yes" if flag else "no",
        "flagged_tau_star": "yes" if flag_star else "no",
        "predictive": "yes" if predictive else "no",
        "nested_acc_stratified": f'{n["strat"]:.4f}' if n else "",
        "nested_acc_temporal": f'{n["temp"]:.4f}' if n else "",
        "nested_tau": f'{n["tau"]:.4f}' if n else "",
        "nested_rank": RANK.get(f, ""),
        "identical_group": GROUP.get(f, ""),
    })

with OUT.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(out)

# --- controles : le fichier doit reproduire les comptes du manuscrit --------
n_excl = sum(1 for d in out if d["disposition"] == "excluded")
n_beh = sum(1 for d in out if d["category"] == "behavioural")
n_flag = sum(1 for d in out if d["flagged_tau"] == "yes")
n_star = sum(1 for d in out if d["flagged_tau_star"] == "yes")
n_kept = sum(1 for d in out if d["disposition"] == "retained")
ranks = sorted(int(d["nested_rank"]) for d in out
               if d["flagged_tau"] == "yes" and d["nested_rank"] != "")
assert len(out) == 90, len(out)
assert n_beh == 63 and n_kept == 55 and n_excl == 35
assert n_flag == 8 and n_star == 13
assert set(d["column"] for d in out if d["disposition"] == "excluded"
           and d["category"] != "identifier") == set(BLACK)
assert ranks == [1, 2, 3, 4, 5, 6, 7, 8], ranks
print(f"ecrit : {OUT}")
print(f"  {len(out)} colonnes : 23 identifiants, {len(POSITIONAL)} "
      f"positionnelles, {n_beh} comportementales")
print(f"  liste noire publiee : {len(BLACK)} colonnes "
      f"({len(POSITIONAL)} par nom + {n_flag} par la regle)")
print(f"  variante tau* : {n_star} comportementales, "
      f"liste noire {len(POSITIONAL) + n_star}")
print(f"  rangs des huit publiees dans l'audit imbrique : {ranks} "
      f"sur {len(elig)} eligibles")
print(f"  groupes de colonnes identiques : "
      f"{ {g: sorted(c for c in GROUP if GROUP[c] == g) for g in set(GROUP.values())} }")
