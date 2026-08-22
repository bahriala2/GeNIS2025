#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_claims.py doit ECHOUER quand on lui remet les fautes qu'il a trouvees.

Un controle qui ne peut pas echouer ne controle rien, et cette relecture en a
trouve un dans verify_e8.py : il portait un `or True` dans sa condition et
passait a vide sur une phrase fausse. On ne se fie donc pas au fait que
check_claims.py passe sur le document propre.

Ce script reintroduit chacune des cinq fautes dans une COPIE du .docx et
verifie que le verificateur les rattrape. Il ne touche pas au manuscrit.

    python test_check_claims.py
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "GeNIS_benchmark_article.docx"
TMP = pathlib.Path(tempfile.mkdtemp(prefix="genis_claims_"))
FAUTES = [
    ("6.1 : XGBoost a 1.0000",
     "LightGBM reaches macro-F1 1.0000 ± 0.0001 across five seeds, and XGBoost, random forest and the FT-Transformer 0.9999 ± 0.0001",
     "XGBoost and LightGBM reach macro-F1 1.0000 ± 0.0000 across five seeds, random forest and the FT-Transformer 0.9999"),
    ("tableau 13 : >= 0.9999", "≥ 0.9998 at every interval", "≥ 0.9999 at every interval"),
    ("figure 5 : onze detecteurs",
     "nine of the ten detectors shown are uniformly strong",
     "Ten of the eleven detectors are uniformly strong"),
    ("figure 14 : 2 600", "1 097 times the throughput",
     "2 600 times the throughput"),
    ("6.3 : le CNN perd au reglage",
     "logistic regression inverts the same way", "the CNN loses 0.0067 despite no"),
    ("6.4 : borne DoS a 0.993", "never falling below 0.992",
     "never falling below 0.993"),
    ("6.4 : FPR a 0.01 %", "against 0.0143% at worst for",
     "against at most 0.01% for"),
    # La 6.5 ouvre desormais une phrase sur ce chiffre, d'ou la majuscule.
    ("6.5 : nb gagne +0.1668", "Naive Bayes gains +0.0462",
     "Naive Bayes gains +0.1668"),
    ("6.5 : le calage repare le ftt", "The clearest repair is k-NN",
     "It repairs the FT-Transformer decisively"),
    ("figure 2 : 87.3 %", "floods account for 87.26% of the flows",
     "floods account for 87.3% of the flows"),
]
ok = []
for nom, bon, casse in FAUTES:
    dst = TMP / "casse.docx"
    zin = zipfile.ZipFile(SRC); xml = zin.read("word/document.xml").decode("utf-8")
    if bon.replace(" ", " ") in xml: bon = bon.replace(" ", " ")
    if bon not in xml:
        print(f"  RATE  {nom} : chaine introuvable, le test lui-meme est faux")
        ok.append(False)
        continue
    neuf = xml.replace(bon, casse, 1)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, neuf.encode("utf-8") if it.filename == "word/document.xml"
                        else zin.read(it.filename))
    r = subprocess.run([sys.executable, "/home/user/GeNIS2025/paper/check_claims.py", str(dst)],
                       capture_output=True, text=True)
    attrape = r.returncode != 0
    ok.append(attrape)
    print(f"  {'OK   ' if attrape else 'RATE '} {nom} -> "
          + ("le verificateur echoue, comme il doit" if attrape
             else "PASSE ALORS QUE LA FAUTE EST LA"))

shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if all(ok) else 1)
