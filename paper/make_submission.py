#!/usr/bin/env python3
"""Build the two files EAAI's double anonymized review requires, plus highlights.

The journal asks for the title page and the anonymized manuscript as separate
uploads, and the anonymized file must carry no author names, no affiliations
and no acknowledgements. Doing that by hand on a 47-page document is how a name
survives into the file a reviewer opens, so it is done here, from the built
manuscript, with an assertion at the end that none of the identifying strings
is left.

Three things identify us beyond the title block. Section 11 gives the code
repository, whose URL carries an author's account name, and the Zenodo record,
which resolves to a page bearing all three names. Section 14 is the CRediT
statement, which is a list of author names by construction. Both move to the
title page, where the journal wants them anyway, and Section 11 keeps its
substance with the two links withheld for review.

Writes into paper/submission/.
"""
import copy
import pathlib
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XMLSP = "{http://www.w3.org/XML/1998/namespace}space"
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "GeNIS_benchmark_article.docx"
OUT = HERE / "submission"
OUT.mkdir(exist_ok=True)

IDENTIFIANTS = ["Bahri", "Jemili", "Mosbah", "INSIGHT", "ISITCom", "Sousse",
                "LaBRI", "Bordeaux", "Talence", "github.com/bahriala2",
                "zenodo.21910662", "zenodo.21910663",
                "u-sousse.tn", "u-bordeaux.fr", "@"]

# La reference [7] est une auto-citation. On ne la retire pas : supprimer une
# reference reelle fausse la bibliographie et se voit. L'usage en double
# aveugle est de la garder et d'en parler a la troisieme personne, ce que les
# trois reecritures ci-dessous font. Le controle final verifie donc que les
# noms ne subsistent que dans l'entree bibliographique.
TIERCE = [
    ("of our earlier comparative study [7]",
     "of an earlier comparative study [7]"),
    ("reproduced exactly as published in our prior comparative study [7] and "
     "reused in the companion system paper",
     "reproduced exactly as published in an earlier comparative study [7] and "
     "reused in a companion system paper"),
    ("One consequence for our own earlier work. The comparative study whose "
     "architectures we reuse [7]",
     "One consequence for the earlier work these architectures come from. The "
     "comparative study reused here [7]"),
]

COURRIEL = "bahri.mohamedalaeddine@isitc.u-sousse.tn"
ADRESSE = ("INSIGHT Lab, ISITCom, University of Sousse, "
           "Hammam Sousse 4011, Tunisia")
# Le guide n'exige que l'adresse de l'auteur correspondant, mais le formulaire
# de soumission demande celle de chaque co-auteur : les trois sont ici pour
# n'avoir a les chercher qu'une fois.
COURRIELS = [
    "Mohamed Ala Eddine Bahri: bahri.mohamedalaeddine@isitc.u-sousse.tn",
    "Farah Jemili: Farah.JMILI@isitc.u-sousse.tn",
    "Mohamed Mosbah: mohamed.mosbah@u-bordeaux.fr",
]

# Ce que la section 11 devient dans le fichier anonymise. La substance reste :
# ce qui est publie, sous quelle licence, et ou chaque campagne se trouve dans
# l'arborescence. Ne partent que les deux chaines qui nous nomment.
S11_ANON = (
    "GeNIS is publicly archived at doi:10.5281/zenodo.14919237. Our artefact "
    "is released in two parts, a code repository and a data archive under a "
    "CC-BY 4.0 licence. Both are withheld here for double anonymized review, "
    "since their addresses identify the authors, and both have been supplied "
    "to the editorial office; the citations will be restored on acceptance. "
    "The archive holds the results file for the 154 runs, which also carries "
    "the feature blacklist, the transferability spectrum under both "
    "normalisations and the hyperparameter configurations, together with the "
    "frozen split indices, the per-run probability matrices and the figures, "
    "and a second file with the trained detectors of the reference "
    "configuration and their fitted preprocessing parameters.")


def texte(e):
    return "".join(t.text or "" for t in e.iter(W + "t"))


def para(modele, contenu):
    """Un paragraphe sur le modele d'un autre, reduit a un seul passage."""
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
    # Sans cela ElementTree reinvente les prefixes (ns0:document), et Word
    # refuse le fichier : on lui rend ceux du document d'origine.
    for pfx, uri in re.findall(r'xmlns:([A-Za-z0-9]+)="([^"]+)"', tete):
        if re.fullmatch(r"ns\d+", pfx):
            continue          # prefixe reserve par ElementTree
        ET.register_namespace(pfx, uri)
    return d, doc, ET.parse(doc), tete


def elaguer_media(d):
    """Retire les images qu'aucun paragraphe restant n'appelle.

    La page de titre et les highlights heritent des vingt images du manuscrit
    parce qu'ils partent de son zip. Sans elagage ils pesent quatre megaoctets
    pour une page, ce qui n'est pas faux mais donne au bureau editorial trois
    fichiers dont deux inexplicablement lourds.
    """
    doc = (d / "word" / "document.xml").read_text(encoding="utf-8")
    rels = d / "word" / "_rels" / "document.xml.rels"
    xml = rels.read_text(encoding="utf-8")
    gardes, retires = [], 0
    for m in re.finditer(r'<Relationship [^>]*?Id="(rId\d+)"[^>]*?Target="(media/[^"]+)"[^>]*?/>',
                         xml):
        if m.group(1) in doc:
            gardes.append(m.group(2))
        else:
            xml = xml.replace(m.group(0), "")
            retires += 1
    rels.write_text(xml, encoding="utf-8")
    for f in (d / "word" / "media").glob("*"):
        if ("media/" + f.name) not in gardes:
            f.unlink()
    return retires


def refermer(d, doc, arbre, tete, cible):
    arbre.write(doc, encoding="UTF-8", xml_declaration=True)
    xml = doc.read_text(encoding="utf-8")
    i = xml.index("<w:document")
    j = xml.index(">", i)
    presentes = dict(re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', xml[i:j + 1]))
    manquantes = [f'{k}="{v}"' for k, v in
                  re.findall(r'(xmlns:[A-Za-z0-9]+)="([^"]+)"', tete)
                  if k not in presentes]
    if manquantes:
        doc.write_text(xml[:j] + " " + " ".join(manquantes) + xml[j:],
                       encoding="utf-8")
    if cible.exists():
        cible.unlink()
    subprocess.run(["zip", "-Xqr", str(cible), "."], cwd=d, check=True)
    shutil.rmtree(d)


def index(kids, debut):
    for i, e in enumerate(kids):
        if texte(e).startswith(debut):
            return i
    raise LookupError(debut)


# --------------------------------------------------------------------------
# 1. la page de titre
# --------------------------------------------------------------------------
d, doc, arbre, tete = ouvrir()
body = arbre.getroot().find(W + "body")
kids = list(body)
titre, corps = kids[0], kids[6]
credit = kids[index(kids, "Mohamed Ala Eddine Bahri: Conceptualization")]
interet = kids[index(kids, "The authors declare that they have no known")]
sectPr = [e for e in kids if e.tag == W + "sectPr"]

for e in kids[5:]:
    if e.tag != W + "sectPr":
        body.remove(e)

for ligne in [
        "",
        "Corresponding author",
        "Mohamed Ala Eddine Bahri, " + ADRESSE + ". Email: " + COURRIEL + ".",
        "",
        "Author email addresses",
        "  ".join(COURRIELS),
        "",
        "Acknowledgements",
        "None.",
        "",
        "Declaration of competing interest",
        texte(interet),
        "",
        "CRediT authorship contribution statement",
        texte(credit)]:
    p = para(corps, ligne)
    if sectPr:
        body.insert(list(body).index(sectPr[0]), p)
    else:
        body.append(p)

arbre.write(doc, encoding="UTF-8", xml_declaration=True)
elaguer_media(d)
arbre = ET.parse(doc)
refermer(d, doc, arbre, tete, OUT / "title_page.docx")
print("ecrit : submission/title_page.docx")

# --------------------------------------------------------------------------
# 2. le manuscrit anonymise
# --------------------------------------------------------------------------
d, doc, arbre, tete = ouvrir()
body = arbre.getroot().find(W + "body")
kids = list(body)

for e in kids[1:5]:                       # auteurs, affiliations, auteur correspondant
    body.remove(e)

kids = list(body)
i11 = index(kids, "GeNIS is publicly archived at")
p11 = kids[i11]
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
    pos = 0
    reste = neuf
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
    plein = "".join(
        "".join(t.text or "" for t in p.iter(W + "t"))
        for p in ET.fromstring(z.read("word/document.xml")).find(W + "body").iter(W + "p"))
i_ref = plein.index("References[1]") if "References[1]" in plein else plein.index("[1] G. Engelen")
corps_seul, biblio = plein[:i_ref], plein[i_ref:]
restants = [s for s in IDENTIFIANTS if s in corps_seul]
assert not restants, "identifiants restants dans le corps : %s" % restants
hors_biblio = [s for s in IDENTIFIANTS if s in plein and s not in biblio]
assert not hors_biblio, hors_biblio
dans_biblio = sorted(s for s in IDENTIFIANTS if s in biblio)
print("ecrit : submission/manuscript_anonymised.docx")
print("  corps : aucun identifiant")
print("  bibliographie : %s, dans l'auto-citation [7], citee a la troisieme "
      "personne" % ", ".join(dans_biblio))

# --------------------------------------------------------------------------
# 3. les highlights, fichier separe portant le mot dans son nom
# --------------------------------------------------------------------------
PUCES = [
    "Attribution-based auditing scored every shortcut we found at almost zero",
    "Isolated two-protocol testing found the eight that importance ranking missed",
    "Chronological splits alone left a timestamp probe at 98.6 percent accuracy",
    "On a second corpus that probe fell to 10.3 percent, so the fix is not general",
    "A linear model beat boosted trees on four of five measured cost and quality axes",
]
for b in PUCES:
    assert len(b) <= 85, (len(b), b)
assert 3 <= len(PUCES) <= 5

d, doc, arbre, tete = ouvrir()
body = arbre.getroot().find(W + "body")
kids = list(body)
titre, corps = kids[0], kids[6]
sectPr = [e for e in kids if e.tag == W + "sectPr"]
for e in kids:
    if e.tag != W + "sectPr":
        body.remove(e)
for ligne in ["Highlights"] + ["- " + b for b in PUCES]:
    p = para(titre if ligne == "Highlights" else corps, ligne)
    if sectPr:
        body.insert(list(body).index(sectPr[0]), p)
    else:
        body.append(p)
arbre.write(doc, encoding="UTF-8", xml_declaration=True)
elaguer_media(d)
arbre = ET.parse(doc)
refermer(d, doc, arbre, tete, OUT / "highlights.docx")
print("ecrit : submission/highlights.docx, %d puces, la plus longue %d caracteres"
      % (len(PUCES), max(len(b) for b in PUCES)))
