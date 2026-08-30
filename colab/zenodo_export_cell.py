#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cellule d'export Zenodo pour article1_pipeline.ipynb.

Rassemble tout ce que la section 10 de l'article promet, dans une arborescence
unique, ecrit le README que les relecteurs ouvrent en premier et un MANIFEST
qui donne pour chaque fichier sa taille, son empreinte et la cellule qui l'a
produit, puis zippe le tout.

Ce fichier a deux usages :

  * dans Colab, son contenu est la derniere cellule du pipeline (elle y est
    inseree par append_export_cell.py) ;
  * en local, `python zenodo_export_cell.py --render-readme paper/` ecrit
    paper/ARCHIVE_README_next_version.md a partir de article1_results.json.
    Il n'ecrase pas paper/ARCHIVE_README.md, qui decrit la v1.0.0 reellement
    publiee sur Zenodo, deux zips montes a la main, et qui est tenu a jour a
    la main.

Ce qui est volontairement exclu de l'archive :

  * cache/slice60.npz, la matrice de features. C'est une copie derivee du
    corpus GeNIS ; les indices de decoupage et le code la regenerent, et
    l'exclure evite toute question de redistribution.
  * le corpus lui-meme, deja archive sous doi:10.5281/zenodo.14919237.
"""

import argparse
import hashlib
import json
import pathlib
import shutil
import time

# --------------------------------------------------------------------------
# Le README de l'archive. En anglais : c'est la premiere page que lit un
# relecteur. Les champs entre accolades sont remplis a l'export.
# --------------------------------------------------------------------------
README = r"""# Artefact for *A Leakage-Audited Benchmark of Eleven Intrusion Detectors on GeNIS 2025*

This archive is the reproducibility artefact referenced in Section 10 of the paper.
It contains the pipeline, the frozen evaluation protocol, every measurement the
paper reports, and the trained detectors.

- **Paper**: A Leakage-Audited Benchmark of Eleven Intrusion Detectors on GeNIS 2025
- **Corpus**: GeNIS 2025, `2-flows` module, 60-second flows, doi:10.5281/zenodo.14919237
- **Code repository**: https://github.com/bahriala2/GeNIS2025
- **This artefact, all versions**: {archive_doi}
- **This version**: {version_doi}
- **Built**: {built}

> Version 1.0.0 of this record, doi:10.5281/zenodo.21910663, was assembled by hand
> and published as two zip files, `article1_final.zip` and `models.zip`, without the
> layout described below. The paper cites the concept DOI, which resolves to the most
> recent version. See `ARCHIVE_README.md` in the code repository for what v1.0.0
> actually contains.

## What Section 10 promises, and where it is

| Promised in Section 10 | Location in this archive |
|---|---|
| the pipeline | `code/colab/article1_pipeline.ipynb` |
| the frozen split indices | `frozen_splits_60s.npz` |
| the feature blacklist | `article1_results.json` -> `audit.blacklist` ({n_blacklist} columns) |
| the transferability spectrum under both normalisations | `article1_results.json` -> `audit.transfer_table` ({n_spectrum} features) |
| the hyperparameter configurations | `article1_results.json` -> `hpo.<model>.best_params` |
| the trained models | `models/` |
| the scripts that regenerate every figure and table | `code/paper/` |

## Layout

```
{tree}
```

## The results file

`article1_results.json` is the single source of every number in the paper.
{n_runs} training runs are recorded under `models`, keyed
`<detector>[#tuned]|<condition>|<split>`. Conditions are `full`, `clean` and
`audited`; splits are `strat_seed1` to `strat_seed5` and `temporal`.

Each run records accuracy, macro-F1, weighted F1, MCC, per-class F1, the binary
detection view (detection F1, FPR, FNR, PR-AUC, ROC-AUC), fit time and predict
time. Top-level keys of interest:

| Key | Contents |
|---|---|
| `audit` | permutation importance, the full single-feature transferability scan, duplicate pairs, the blacklist, and the rule that produced it |
| `hpo` | every search trial per model, with the retained configuration |
| `calibration` | temperature scaling per detector and the resulting ECE |
| `cost` | training and inference cost per detector |
| `stats` | bootstrap confidence intervals and McNemar tests |
| `meta.env` | the library versions the campaign ran under |

Two normalisations of the transferability spectrum are derivable from
`audit.transfer_table`, which stores the single-feature accuracy under both
protocols. The raw ratio is tau = acc_temporal / acc_stratified; the
chance-corrected form used in Figure 6 is
tau* = (acc_temporal - p) / (acc_stratified - p), with p = `audit.chance` = {chance}.

## Regenerating the figures

The scripts read `article1_results.json` and write into `figures/`. From
`code/paper/`, with that JSON in the working directory:

| Command | Figures produced |
|---|---|
| `python3 regen_en.py` | 1 timeline, 3 interval heatmap, 6 per-class F1, 8 transferability plane |
| `python3 regenerate_figures.py` | 2 before/after, 5 cost, 7 ranking with CIs, 9 transferability spectrum, 10 autoencoder |
| `python3 regen_fig6.py` | 6 spectrum under both normalisations, drawn at final page width |
| `make figures` | runs `regen_en.py` and `regen_fig6.py` |

Three figures in the manuscript are written directly by the pipeline notebook
rather than by an offline script, because they need arrays that the results file
does not carry: the reliability diagram, the confusion matrices, and the
per-detector learning curves. Their sources are `probs/` and `history` in the
results file, and the notebook cells that draw them are 30, 33 and 34. Copies as
published are in `figures/` and `figures_annexe/`.

The LaTeX tables are regenerated by `code/paper/legacy-latex/regenerate_tables.py`.
That chain is frozen and diverges from the manuscript, which is now a native
Word document; it is kept for reference only, and its README says so.

## Reproducing the campaign

1. Obtain GeNIS from doi:10.5281/zenodo.14919237 and place `2-flows.zip` where
   the notebook expects it.
2. Open `code/colab/article1_pipeline.ipynb`. It is resumable: every run is
   written to disk as soon as it finishes.
3. Copy `frozen_splits_60s.npz` into the output directory before starting. The
   notebook reloads it instead of drawing new splits, so the partitions match
   the ones the paper reports exactly.

The campaign comprises {n_runs} runs. Environment of record:
Python {py}, TensorFlow {tf}, scikit-learn {sk}, XGBoost {xgb}, LightGBM {lgb}.

One caveat the paper states in Section 8 and which matters here: the
hyperparameter search budget was capped in wall-clock seconds inside a hosted
runtime whose accelerator allocation varied between sessions. The number of
trials a model received therefore reflects hardware availability as well as
model cost, and a rerun on different hardware may allocate trials differently.
Accuracies are unaffected, since seeds are fixed and CPU and GPU fits agree up
to floating-point non-determinism.

## The trained models

`models/` holds the reference configuration only: the audited and clean
conditions on split `strat_seed1`, in both the default and the tuned arm.
`preprocessing.json` carries the fitted RobustScaler parameters, the feature
order, the class names, the benign index and the blacklist, so a model can be
applied to new flows without rerunning the pipeline. `MANIFEST.json` lists the
calibration temperatures.

Keras models load with `keras.models.load_model(path, custom_objects=...)`,
passing `FeatureTokenizer` and `ClsToken` from the pipeline notebook for the
FT-Transformer. The other detectors are joblib dumps.

## What is not in this archive, and why

- **The corpus.** GeNIS is separately archived and should be cited directly.
- **The cached feature matrix.** It is a derived copy of the corpus. The frozen
  split indices plus the pipeline regenerate it in about ten minutes.
- **Per-run trained models outside the reference configuration.** Storing all
  {n_runs} would add little: the probability matrices in `probs/` already allow
  every reported metric, significance test and calibration curve to be
  recomputed without retraining.

## Licence and citation

The corpus is redistributed nowhere in this archive; cite it as
doi:10.5281/zenodo.14919237. For this artefact, see the licence recorded in the
Zenodo record metadata.

If you use this artefact, please cite the paper and this archive.
"""

# Ce que l'archive contient, dans l'ordre d'apparition, avec la provenance
# declaree au MANIFEST. La cle est le nom dans l'archive.
LAYOUT = [
    ("article1_results.json", "file", "article1_results.json",
     "cellule 3, reecrit apres chaque run"),
    ("frozen_splits_60s.npz", "file", "frozen_splits_60s.npz",
     "cellule 11, cinq splits stratifies et un split temporel par classe"),
    ("ae_scores_seed1.npz", "file", "ae_scores_seed1.npz",
     "cellule 26, erreurs de reconstruction de l'autoencodeur"),
    ("models", "dir", "models",
     "cellules 15 et 36, configuration de reference uniquement"),
    ("probs", "dir", "probs",
     "cellule 15, probabilites de validation et de test par run, float16"),
    ("figures", "dir", "figures",
     "cellules 8, 19, 29 a 33, figures du manuscrit"),
    ("figures_annexe", "dir", "figures_annexe",
     "cellules 7 a 12 et 34, figures d'annexe"),
    ("tables", "dir", "tables",
     "cellule 28, tables LaTeX de la chaine gelee"),
]

EXCLUDED = [
    ("cache/", "copie derivee du corpus ; les indices et le code la regenerent"),
    ("2-flows.zip et les CSV", "le corpus, archive sous doi:10.5281/zenodo.14919237"),
    ("*.tmp", "ecritures atomiques en cours"),
]

REPO_URL = "https://github.com/bahriala2/GeNIS2025.git"

# DOI reels du depot Zenodo, publie le 13 aout 2026.
# Le DOI de concept ne bouge jamais et est celui que cite la section 10 ;
# le DOI de version designe un depot precis et change a chaque version.
CONCEPT_DOI = "10.5281/zenodo.21910662"
VERSION_DOI_V1 = "10.5281/zenodo.21910663"


def human(n):
    for u in ("o", "ko", "Mo", "Go"):
        if n < 1024 or u == "Go":
            return f"{n:.1f} {u}" if u != "o" else f"{int(n)} o"
        n /= 1024


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def render_readme(results, archive_doi=CONCEPT_DOI,
                  version_doi="[assigned when this version is published]"):
    """Remplit le README avec les chiffres reels du fichier de resultats."""
    audit = results.get("audit", {})
    env = results.get("meta", {}).get("env", {})
    tree = "\n".join(
        ["genis2025-artefact/", "    README.md", "    MANIFEST.md"]
        + [f"    {name}{'/' if kind == 'dir' else ''}" for name, kind, _, _ in LAYOUT]
        + ["    code/                      snapshot of the GitHub repository"])
    return README.format(
        archive_doi=archive_doi,
        version_doi=version_doi,
        built=time.strftime("%Y-%m-%d", time.gmtime()),
        n_blacklist=len(audit.get("blacklist", [])),
        n_spectrum=len(audit.get("transfer_table", [])),
        n_runs=len(results.get("models", {})),
        chance=round(float(audit.get("chance", float("nan"))), 4),
        tree=tree,
        py=env.get("python", "?"), tf=env.get("tensorflow", "?"),
        sk=env.get("sklearn", "?"), xgb=env.get("xgboost", "?"),
        lgb=env.get("lightgbm", "?"))


def build_archive(save_dir, out_dir, archive_doi=CONCEPT_DOI,
                  version_doi="[assigned when this version is published]",
                  include_code=True, include_e1=True, dry_run=False):
    """Assemble l'archive. Retourne le chemin du zip, ou du dossier si dry_run."""
    save = pathlib.Path(save_dir)
    root = pathlib.Path(out_dir) / "genis2025-artefact"
    results = json.loads((save / "article1_results.json").read_text(encoding="utf-8"))

    # --- plan, affiche avant de copier quoi que ce soit ---------------------
    print("=" * 74)
    print("PLAN D'EXPORT")
    print("=" * 74)
    plan, total, manquants = [], 0, []
    for name, kind, src, prov in LAYOUT:
        p = save / src
        if not p.exists():
            manquants.append(name)
            print(f"   {name:<26} ABSENT")
            continue
        if kind == "file":
            n, size = 1, p.stat().st_size
        else:
            fs = [f for f in p.rglob("*") if f.is_file()]
            n, size = len(fs), sum(f.stat().st_size for f in fs)
        plan.append((name, kind, p, prov, n, size))
        total += size
        print(f"   {name:<26} {n:>5} fichier(s)  {human(size):>10}")
    print(f"   {'TOTAL':<26} {sum(x[4] for x in plan):>5} fichier(s)  {human(total):>10}")
    if manquants:
        print(f"\n   absents : {', '.join(manquants)}")
        print("   (models/ vide signifie que SAVE_MODELS etait a False pendant la campagne)")
    for quoi, pourquoi in EXCLUDED:
        print(f"   exclu : {quoi:<28} {pourquoi}")
    if total > 45 * 1024 ** 3:
        print("\n   ATTENTION : au-dela de 45 Go, la limite Zenodo par depot est de 50 Go.")
    if dry_run:
        print("\ndry_run : rien n'a ete copie.")
        return None

    # --- copie --------------------------------------------------------------
    print("\ncopie...", flush=True)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for name, kind, p, prov, n, size in plan:
        if kind == "file":
            shutil.copy2(p, root / name)
        else:
            shutil.copytree(p, root / name)
        print(f"   {name}", flush=True)

    if include_e1:
        e1 = save.parent / "e1" / "e1_results.json"
        if e1.exists():
            (root / "supplementary").mkdir(exist_ok=True)
            shutil.copy2(e1, root / "supplementary" / "e1_results.json")
            figs = save.parent / "e1" / "figures"
            if figs.exists():
                shutil.copytree(figs, root / "supplementary" / "figures")
            (root / "supplementary" / "NOTE.md").write_text(
                "# Supplementary experiment E1\n\n"
                "An anchored comparison run on the corpus authors' own `4-preprocessed`\n"
                "module, under their split and their taxonomy, with the eleven detectors\n"
                "of the paper. **These results are not reported in the manuscript.** They\n"
                "are deposited so that the comparison the paper declares as indicative in\n"
                "Section 8 can be inspected. The notebook that produces them is\n"
                "`code/colab/e1_anchored_comparison_v6.ipynb`.\n",
                encoding="utf-8")
            print("   supplementary/ (E1)")

    if include_code:
        print("   code/ (clone du depot)...", flush=True)
        import subprocess
        r = subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(root / "code")],
                           capture_output=True, text=True)
        if r.returncode == 0:
            shutil.rmtree(root / "code" / ".git", ignore_errors=True)
        else:
            print("   clone impossible, a ajouter a la main :", r.stderr.strip()[:120])

    # --- README et MANIFEST -------------------------------------------------
    (root / "README.md").write_text(render_readme(results, archive_doi, version_doi),
                                    encoding="utf-8")

    print("\nempreintes...", flush=True)
    prov_of = {name: prov for name, _, _, prov in LAYOUT}
    prov_of["code"] = "clone du depot GitHub, sans l'historique git"
    prov_of["supplementary"] = "notebook E1, non rapporte dans le manuscrit"
    lines = ["# MANIFEST", "",
             f"Built {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}.",
             "SHA-256 of every file, and the pipeline cell that produced it.", ""]
    files = sorted(f for f in root.rglob("*") if f.is_file())
    grand = 0
    for i, f in enumerate(files, 1):
        rel = f.relative_to(root)
        grand += f.stat().st_size
        if i % 50 == 0:
            print(f"   {i}/{len(files)}", flush=True)
        lines.append(f"- `{rel}`  {human(f.stat().st_size)}  `{sha256(f)[:16]}`")
    top = sorted({str(f.relative_to(root)).split("/")[0] for f in files})
    lines += ["", "## Provenance", ""] + [
        f"- `{t}` : {prov_of.get(t, 'genere a l export')}" for t in top]
    lines += ["", "## Deliberately excluded", ""] + [
        f"- {quoi} : {pourquoi}" for quoi, pourquoi in EXCLUDED]
    lines += ["", f"{len(files)} files, {human(grand)} total.", ""]
    (root / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")

    # --- zip ----------------------------------------------------------------
    print("\ncompression...", flush=True)
    zp = shutil.make_archive(str(root), "zip", root_dir=root.parent, base_dir=root.name)
    print("=" * 74)
    print(f"archive : {zp}")
    print(f"          {human(pathlib.Path(zp).stat().st_size)} compresse, "
          f"{len(files)} fichiers, {human(grand)} decompresse")
    print("=" * 74)
    return zp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render-readme", metavar="DIR",
                    help="ecrit ARCHIVE_README.md a partir de DIR/article1_results.json")
    a = ap.parse_args()
    if a.render_readme:
        d = pathlib.Path(a.render_readme)
        results = json.loads((d / "article1_results.json").read_text(encoding="utf-8"))
        out = d / "ARCHIVE_README_next_version.md"
        out.write_text(render_readme(results), encoding="utf-8")
        print("ecrit :", out)
        print("note : ARCHIVE_README.md decrit la v1.0.0 reellement publiee,")
        print("       deux zips montes a la main. Il est tenu a jour a la main")
        print("       et n'est volontairement pas ecrase par ce script.")
    else:
        ap.error("rien a faire ; voir --render-readme, ou utiliser build_archive() dans Colab")


if __name__ == "__main__":
    main()
