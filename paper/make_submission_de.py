#!/usr/bin/env python3
"""Build the transfer package for Digital Engineering (Elsevier, ISSN 2950-550X).

EAAI-26-28539 is transferred from Engineering Applications of Artificial
Intelligence. Digital Engineering runs SINGLE anonymized review, so unlike
make_submission.py nothing is anonymised: the manuscript goes with its author
block, its CRediT statement and its two links (GitHub, Zenodo).

Writes into paper/submission_de/:
  manuscript.docx                      the source, unchanged
  title_page.docx                      title, authors, full addresses, e-mails
  highlights.docx                      5 bullets, <= 85 characters
  cover_letter.docx                    argues the fit with Digital Engineering
  declaration_competing_interest.docx  the guide's "nothing to declare" text
  figures/Figure_N.(pdf|png)           one file per figure, vector when we have it
  supplementary_blacklist.csv          the 90-column disposition table

Re-run after any change to GeNIS_benchmark_article.docx.
Guide for Authors read on 2026-11-15:
https://www.sciencedirect.com/journal/digital-engineering/publish/guide-for-authors
"""
import copy
import pathlib
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XMLSP = "{http://www.w3.org/XML/1998/namespace}space"
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "GeNIS_benchmark_article.docx"
OUT = HERE / "submission_de"
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "figures").mkdir(parents=True)

COURRIEL = "bahri.mohamedalaeddine@isitc.u-sousse.tn"
ADRESSE_A = ("INSIGHT Lab, Higher Institute of Computer Science and Communication "
             "Technologies of Hammam Sousse (ISITCom), University of Sousse, "
             "Hammam Sousse 4011, Tunisia")
ADRESSE_B = ("Univ. Bordeaux, CNRS, Bordeaux INP, LaBRI, UMR 5800, "
             "351 cours de la Libération, F-33400 Talence, France")
COURRIELS = [
    "Mohamed Ala Eddine Bahri: bahri.mohamedalaeddine@isitc.u-sousse.tn",
    "Farah Jemili: Farah.JMILI@isitc.u-sousse.tn",
    "Mohamed Mosbah: mohamed.mosbah@u-bordeaux.fr",
]

PUCES = [
    "Attribution-based auditing scored every shortcut we found at almost zero",
    "Isolated two-protocol testing found the eight that importance ranking missed",
    "Chronological splits alone left a timestamp probe at 98.6 percent accuracy",
    "On a second corpus that probe fell to 10.3 percent, so the fix is not general",
    "A linear model beat boosted trees on four of five measured cost and quality axes",
]
assert 3 <= len(PUCES) <= 5 and all(len(b) <= 85 for b in PUCES)


# ---------------------------------------------------------------- helpers
def texte(e):
    return "".join(t.text or "" for t in e.iter(W + "t"))


def para(modele, contenu):
    p = copy.deepcopy(modele)
    rs = p.findall(W + "r")
    for r in rs[1:]:
        p.remove(r)
    ts = rs[0].findall(W + "t")
    for t in ts[1:]:
        rs[0].remove(t)
    ts[0].text = contenu
    ts[0].set(XMLSP, "preserve")
    return p


def ouvrir():
    d = pathlib.Path(tempfile.mkdtemp())
    with zipfile.ZipFile(SRC) as z:
        z.extractall(d)
    doc = d / "word" / "document.xml"
    brut = doc.read_text(encoding="utf-8")
    tete = brut[brut.index("<w:document"):brut.index(">", brut.index("<w:document")) + 1]
    for pfx, uri in re.findall(r'xmlns:([A-Za-z0-9]+)="([^"]+)"', tete):
        if not re.fullmatch(r"ns\d+", pfx):
            ET.register_namespace(pfx, uri)
    return d, doc, ET.parse(doc), tete


def sans_entete(arbre):
    for sect in arbre.getroot().find(W + "body").iter(W + "sectPr"):
        for ref in list(sect):
            if ref.tag in (W + "headerReference", W + "footerReference"):
                sect.remove(ref)


def elaguer_media(d):
    doc = (d / "word" / "document.xml").read_text(encoding="utf-8")
    rels = d / "word" / "_rels" / "document.xml.rels"
    xml = rels.read_text(encoding="utf-8")
    gardes = []
    for m in re.finditer(r'<Relationship [^>]*?Id="(rId\d+)"[^>]*?Target="(media/[^"]+)"[^>]*?/>', xml):
        if m.group(1) in doc:
            gardes.append(m.group(2))
        else:
            xml = xml.replace(m.group(0), "")
    rels.write_text(xml, encoding="utf-8")
    for f in (d / "word" / "media").glob("*"):
        if ("media/" + f.name) not in gardes:
            f.unlink()


def refermer(d, doc, arbre, tete, cible):
    arbre.write(doc, encoding="UTF-8", xml_declaration=True)
    xml = doc.read_text(encoding="utf-8")
    i = xml.index("<w:document")
    j = xml.index(">", i)
    presentes = dict(re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', xml[i:j + 1]))
    manquantes = [f'{k}="{v}"' for k, v in re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', tete)
                  if k not in presentes]
    if manquantes:
        doc.write_text(xml[:j] + " " + " ".join(manquantes) + xml[j:], encoding="utf-8")
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
        ct = d / "[Content_Types].xml"           # must come first in the archive
        z.write(ct, ct.name)
        for f in sorted(d.rglob("*")):
            if f.is_file() and f != ct:
                z.write(f, f.relative_to(d).as_posix())
    shutil.rmtree(d)


def index(kids, debut):
    for i, e in enumerate(kids):
        if texte(e).startswith(debut):
            return i
    raise LookupError(debut)


def document_court(lignes, cible, gras_debut=None):
    """A one-to-two page document built on the manuscript's own styles."""
    d, doc, arbre, tete = ouvrir()
    body = arbre.getroot().find(W + "body")
    kids = list(body)
    corps = kids[6]                                    # abstract body paragraph
    gras = kids[index(kids, "A third criterion, and why the first two")]
    titre = kids[0]
    sectPr = [e for e in kids if e.tag == W + "sectPr"]
    for e in kids:
        if e.tag != W + "sectPr":
            body.remove(e)
    for genre, ligne in lignes:
        modele = {"titre": titre, "gras": gras}.get(genre, corps)
        p = para(modele, ligne)
        if sectPr:
            body.insert(list(body).index(sectPr[0]), p)
        else:
            body.append(p)
    sans_entete(arbre)
    arbre.write(doc, encoding="UTF-8", xml_declaration=True)
    elaguer_media(d)
    refermer(d, doc, ET.parse(doc), tete, cible)
    print("ecrit :", cible.relative_to(HERE))


# ---------------------------------------------------------------- 0. read the source
src = ET.fromstring(zipfile.ZipFile(SRC).read("word/document.xml"))
paras = [texte(p) for p in src.iter(W + "p")]
TITRE = paras[0]
abstract = paras[paras.index("Abstract") + 1]
assert len(abstract.split()) <= 250, len(abstract.split())
assert "contribution to artificial intelligence" not in abstract, "run edit_source_de.py first"
assert COURRIEL in "".join(paras[:8]), "corresponding e-mail missing from the title block"
credit = next(t for t in paras if t.startswith("Mohamed Ala Eddine Bahri: Conceptualization"))
interet = next(t for t in paras if t.startswith("The authors declare that they have no known"))
assert any(t.startswith("12. Declaration of generative AI and AI-assisted technologies "
                        "in the manuscript preparation process") for t in paras)

# ---------------------------------------------------------------- 1. manuscript
shutil.copy(SRC, OUT / "manuscript.docx")
print("ecrit : submission_de/manuscript.docx (source, non anonymised)")

# ---------------------------------------------------------------- 1b. anonymised manuscript
# The Guide for Authors says single anonymized review, but the Digital
# Engineering upload page asks for a "Manuscript WITHOUT Author Identifiers"
# next to a separate title page. Sending the anonymised file satisfies both
# readings; the full version stays in manuscript.docx.
IDENTIFIANTS = ["Bahri", "Jemili", "Mosbah", "INSIGHT", "ISITCom", "Sousse",
                "LaBRI", "Bordeaux", "Talence", "github.com/bahriala2",
                "zenodo.21910662", "zenodo.21910663", "u-sousse.tn", "u-bordeaux.fr", "@"]
TIERCE = [
    ("of our earlier comparative study [7]", "of an earlier comparative study [7]"),
    ("reproduced exactly as published in our prior comparative study [7]",
     "reproduced exactly as published in an earlier comparative study [7]"),
    ("One consequence for our own earlier work. The comparative study whose "
     "architectures we reuse [7]",
     "One consequence for the earlier work these architectures come from. The "
     "comparative study reused here [7]"),
]
S11_ANON = (
    "GeNIS is publicly archived at doi:10.5281/zenodo.14919237. Our artefact "
    "is released in two parts, a code repository and a data archive under a "
    "CC-BY 4.0 licence. Both are withheld here for anonymized review, since "
    "their addresses identify the authors, and both are given on the title "
    "page; the citations will be restored on acceptance. The archive holds the "
    "results file for the 154 runs, which also carries the feature blacklist, "
    "the transferability spectrum under both normalisations and the "
    "hyperparameter configurations, together with the frozen split indices, "
    "the per-run probability matrices and the figures, and a second file with "
    "the trained detectors of the reference configuration and their fitted "
    "preprocessing parameters.")

d, doc, arbre, tete = ouvrir()
body = arbre.getroot().find(W + "body")
kids = list(body)
for e in kids[1:5]:                         # authors, affiliations, corresponding author
    body.remove(e)
kids = list(body)
p11 = kids[index(kids, "GeNIS is publicly archived at")]
ts = list(p11.iter(W + "t"))
ts[0].text = S11_ANON
ts[0].set(XMLSP, "preserve")
for t in ts[1:]:
    t.text = ""
for vieux, neuf in TIERCE:
    vus = [p for p in body.iter(W + "p") if vieux in texte(p)]
    assert len(vus) == 1, (len(vus), vieux[:50])
    p = vus[0]
    plein = texte(p)
    k = plein.index(vieux)
    pos, reste = 0, neuf
    for t in p.iter(W + "t"):
        s_ = t.text or ""
        a, b = pos, pos + len(s_)
        pos = b
        if b <= k or a >= k + len(vieux):
            continue
        dd, ff = max(k, a) - a, min(k + len(vieux), b) - a
        t.text = s_[:dd] + reste + s_[ff:]
        reste = ""
kids = list(body)
i13 = index(kids, "13. Declaration of competing interest")
i14 = index(kids, "14. CRediT authorship contribution statement")
for e in kids[i13:i14 + 2]:
    body.remove(e)
refermer(d, doc, arbre, tete, OUT / "manuscript_anonymised.docx")

with zipfile.ZipFile(OUT / "manuscript_anonymised.docx") as z:
    plein = "".join(texte(p) for p in
                    ET.fromstring(z.read("word/document.xml")).find(W + "body").iter(W + "p"))
i_ref = plein.index("[1] G. Engelen")
restants = [s for s in IDENTIFIANTS if s in plein[:i_ref]]
assert not restants, "identifiants restants dans le corps : %s" % restants
assert "contribution to artificial intelligence" not in plein
print("ecrit : submission_de/manuscript_anonymised.docx (aucun identifiant dans le corps)")

# ---------------------------------------------------------------- 2. title page
document_court([
    ("titre", TITRE),
    ("corps", ""),
    ("corps", "Mohamed Ala Eddine Bahri a,*, Farah Jemili a, Mohamed Mosbah b"),
    ("corps", "a " + ADRESSE_A),
    ("corps", "b " + ADRESSE_B),
    ("corps", ""),
    ("gras", "Corresponding author"),
    ("corps", "* Mohamed Ala Eddine Bahri, " + ADRESSE_A + ". E-mail address: " + COURRIEL),
    ("corps", ""),
    ("gras", "Author e-mail addresses"),
] + [("corps", c) for c in COURRIELS] + [
    ("corps", ""),
    ("gras", "Funding"),
    ("corps", "This research did not receive any specific grant from funding agencies "
              "in the public, commercial, or not-for-profit sectors."),
    ("corps", ""),
    ("gras", "Declaration of competing interest"),
    ("corps", interet.split(" This research did not")[0]),
    ("corps", ""),
    ("gras", "CRediT authorship contribution statement"),
    ("corps", credit),
    ("corps", ""),
    ("gras", "Data and code availability (withheld from the anonymised manuscript)"),
    ("corps", "Code: https://github.com/bahriala2/GeNIS2025. Measurements, splits, "
              "feature blacklist and trained models: doi:10.5281/zenodo.21910662 "
              "(CC-BY 4.0)."),
], OUT / "title_page.docx")

# ---------------------------------------------------------------- 3. highlights
document_court([("titre", "Highlights")] + [("corps", "• " + b) for b in PUCES],
               OUT / "highlights.docx")

# ---------------------------------------------------------------- 4. competing interest
document_court([
    ("titre", "Declaration of interests"),
    ("corps", ""),
    ("corps", "☒ The authors declare that they have no known competing financial "
              "interests or personal relationships that could have appeared to "
              "influence the work reported in this paper."),
    ("corps", ""),
    ("corps", "Manuscript title: " + TITRE),
    ("corps", "Authors: Mohamed Ala Eddine Bahri, Farah Jemili, Mohamed Mosbah"),
], OUT / "declaration_competing_interest.docx")

# ---------------------------------------------------------------- 5. cover letter
LETTRE = [
    ("corps", "Mohamed Ala Eddine Bahri"),
    ("corps", ADRESSE_A),
    ("corps", COURRIEL),
    ("corps", ""),
    ("corps", "To the Editor-in-Chief"),
    ("corps", "Digital Engineering"),
    ("corps", ""),
    ("gras", "Transferred manuscript (from Engineering Applications of Artificial "
             "Intelligence, EAAI-26-28539): “" + TITRE + "”"),
    ("corps", ""),
    ("corps", "Dear Editor,"),
    ("corps", ""),
    ("corps",
     "Following the recommendation of the editor of Engineering Applications of "
     "Artificial Intelligence, we transfer the manuscript above to Digital "
     "Engineering through Elsevier’s Article Transfer Service and submit it "
     "for consideration as a research paper."),
    ("corps", ""),
    ("gras", "Fit with the journal"),
    ("corps",
     "Digital Engineering welcomes work on the methods and practice of "
     "digitalisation across sectors, including industrial digitalisation, "
     "smart cities and the communication technology they rely on. Every one of "
     "these digital systems is now monitored by learned network intrusion "
     "detectors, and the engineering question this paper answers is whether "
     "such a detector can be trusted before it is deployed. We study it on "
     "GeNIS 2025, a corpus captured on an Airbus CyberRange emulation of a "
     "small and medium-sized enterprise network, and check which conclusions "
     "carry to a second corpus, CICIDS2017. The contribution is an engineering "
     "procedure rather than a new model: a four-test feature-audit protocol, "
     "each test with a stated blind spot, that decides which columns of a "
     "network-flow dataset a learned detector may use, followed by an "
     "evaluation that reports calibration and single-host inference cost "
     "alongside accuracy, the quantities an engineer sizing a deployment needs."),
    ("corps", ""),
    ("gras", "Principal findings"),
    ("corps",
     "Attribution methods, the usual way of auditing a learned model, scored "
     "every one of the eight behavioural shortcuts the protocol removes at or "
     "below 0.0001, because they are mutually redundant and six of them are "
     "numerically identical columns; only isolated two-protocol testing exposed "
     "them. A timestamp-only probe survives a label-aware per-class temporal "
     "split at 98.6% accuracy against a 19.4% majority rate, so chronological "
     "evaluation alone does not remove a schedule shortcut; on CICIDS2017 the "
     "same probe falls to 10.3%, which makes the sufficiency of temporal "
     "splitting a property to measure rather than to assume. A random split "
     "saturates the nine-class task, whereas under temporal evaluation the "
     "ranking inverts, and logistic regression trails the best macro-F1 by "
     "0.0020 at 1 097 times its throughput."),
    ("corps", ""),
    ("gras", "Relation to our earlier work"),
    ("corps",
     "Three of the neural architectures evaluated here, the recurrent, "
     "convolutional and dense detectors, were first published by two of the "
     "authors in a conference paper, cited as reference [7], on a different "
     "corpus and under a single random split. The present manuscript reuses "
     "those architectures unchanged and shares no results, no corpus, no "
     "protocol and no text with that paper."),
    ("corps", ""),
    ("gras", "Open data and code"),
    ("corps",
     "The code is public at https://github.com/bahriala2/GeNIS2025 and the "
     "measurements, splits, feature blacklist and trained models are archived "
     "at doi:10.5281/zenodo.21910662 under a CC-BY 4.0 licence, as Section 11 "
     "of the manuscript states. The machine-readable blacklist is also "
     "attached as supplementary material."),
    ("corps", ""),
    ("gras", "Declarations"),
    ("corps",
     "The work is original, has not been published elsewhere, and is not under "
     "consideration by another journal. All authors have approved the "
     "submission. The authors declare no competing financial or personal "
     "interests, and the research received no specific grant from any funding "
     "agency. A generative AI assistant was used to draft and revise portions "
     "of the manuscript text and to review the analysis code; the authors "
     "reviewed and edited all content and take full responsibility for it, as "
     "declared in Section 12 of the manuscript."),
    ("corps", ""),
    ("corps", "Thank you for considering our work."),
    ("corps", ""),
    ("corps", "Yours sincerely,"),
    ("corps", ""),
    ("corps", "Mohamed Ala Eddine Bahri, on behalf of Farah Jemili and Mohamed Mosbah"),
]
document_court(LETTRE, OUT / "cover_letter.docx")

# ---------------------------------------------------------------- 6. figures, one file each
vect = HERE / "submission" / "figures"
bitm = HERE / "figures_manuscrit"
nvect = 0
for png in sorted(bitm.glob("figure[0-9][0-9]_*.png")):
    n = int(png.name[6:8])
    pdf = vect / (png.stem + ".pdf")
    if pdf.exists():
        shutil.copy(pdf, OUT / "figures" / f"Figure_{n}.pdf")
        nvect += 1
    else:
        shutil.copy(png, OUT / "figures" / f"Figure_{n}.png")
nfig = len(list((OUT / "figures").iterdir()))
assert nfig == 20, nfig
print(f"ecrit : submission_de/figures, {nfig} fichiers dont {nvect} vectoriels")

# ---------------------------------------------------------------- 7. supplementary
shutil.copy(HERE / "submission" / "supplementary_blacklist.csv", OUT / "supplementary_blacklist.csv")
print("ecrit : submission_de/supplementary_blacklist.csv")
print("abstract :", len(abstract.split()), "mots")
