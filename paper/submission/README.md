# Submission package — Engineering Applications of Artificial Intelligence

Built by `paper/make_submission.py` from `paper/GeNIS_benchmark_article.docx`.
Re-run it after any change to the manuscript; it rebuilds all three files and
re-checks the anonymisation.

| File | Upload as | Notes |
|---|---|---|
| `title_page.docx` | Title page | Authors, affiliations, corresponding author and email, acknowledgements, competing interests, CRediT |
| `manuscript_anonymised.docx` | Manuscript | 47 pages, no author name, affiliation or acknowledgement in the body |
| `highlights.docx` | Highlights | 5 bullets, longest 80 characters |
| `figures/*.pdf` | Artwork | Vector versions of 15 of the 20 figures |
| `cover_letter.docx` | Cover letter | Names the AI contribution and the engineering application, and discloses the prior conference paper |

## The four desk-rejection conditions

The guide lists four conditions whose breach is a desk rejection without peer
review. All four are met:

- No metaphor-based metaheuristic. Not applicable.
- The abstract names the contribution in AI, a four-test feature-audit
  protocol, and the application in engineering, network intrusion detection.
- No undefined acronym in the title or the abstract. `CICIDS2017`,
  `FT-Transformer` and `XGBoost` remain, as proper names of a corpus and two
  models rather than acronyms to expand.
- Single-column format, verified in the document XML.

## The other limits

| Requirement | Ours |
|---|---|
| 50 pages maximum | 47 |
| 100 MB maximum | 3.8 MB |
| Abstract 250 words maximum | 250 |
| 1 to 6 keywords | 6 |
| Highlights, 3 to 5 bullets of 85 characters | 5, longest 80 |
| Reference format | Any consistent style is accepted at submission; the journal applies its own at proof |

## What anonymisation removed

The title block, Section 13 and Section 14 move to the title page. Section 11
keeps its substance and withholds the repository URL and the Zenodo DOI, both
of which resolve to pages bearing the authors' names; the text says they were
supplied to the editorial office and will be restored on acceptance.

Reference [7] is a self-citation. It stays, because deleting a real reference
distorts the bibliography and is visible; the three sentences that referred to
it in the first person now refer to it in the third.

## Still open


- Figure 12 is 1593 pixels wide against a 1772-pixel minimum for a
  single-column bitmap, and has no vector version because the script that drew
  it is not in the repository. The other nineteen are either above the minimum
  or supplied as vector.
- The affiliation on the title page gives no street address. The guide asks for
  the full postal address of each affiliation; the Tunisian one is complete,
  the Bordeaux one is the laboratory's standard form and may need a street.
- Farah Jemili's address reads `Farah.JMILI@`, while the author line spells the
  surname Jemili. The address is the address, so nothing to change there, but
  the guide asks that names be checked carefully and this is the kind of
  variant worth a second look.
- Acknowledgements read "None." Change if anyone should be thanked.
- The generative-AI declaration in Section 12 does not name the tool. The
  submission system asks for it separately; name it there.
