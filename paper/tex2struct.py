#!/usr/bin/env python3
"""main.tex -> content.json : structure neutre (titres, paragraphes, tables, figures).

Sert une seule fois, a produire le .docx natif. Ensuite le .docx est la source.
"""
import re, json, os

tex = open('main.tex').read()
bbl = open('main.bbl').read()

# ---------- references ----------
entries = re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\\end\{thebibliography\})', bbl, re.S)
CITE = {k: i + 1 for i, (k, _) in enumerate(entries)}
ACCENT = {"'a": 'á', "'e": 'é', "'i": 'í', "'o": 'ó', "'u": 'ú', "'c": 'ć',
          '`a': 'à', '`e': 'è', '`i': 'ì', '`o': 'ò', '`u': 'ù',
          '"a': 'ä', '"e': 'ë', '"i': 'ï', '"o': 'ö', '"u': 'ü',
          '^a': 'â', '^e': 'ê', '^i': 'î', '^o': 'ô', '^u': 'û',
          '~a': 'ã', '~n': 'ñ', '~o': 'õ', 'c c': 'ç', 'c C': 'Ç',
          "'A": 'Á', "'E": 'É', '~A': 'Ã', 'v s': 'š', 'v c': 'č', 'v z': 'ž'}

def clean_ref(t):
    """Une entree .bbl -> texte lisible (accents, tirets, liens dedupliques)."""
    t = t.replace(r'\newblock', ' ')
    # \href {url} {\path{...}} -> url (le second argument redit la meme chose)
    t = re.sub(r'\\href\s*\{([^}]*)\}\s*\{(?:\\path)?\{?([^{}]*)\}?\}', r'\1', t)
    t = re.sub(r'\\(?:path|url)\{([^}]*)\}', r'\1', t)
    for k, v in ACCENT.items():                       # {\'e} / {\c c} / \'{e}
        t = t.replace('{\\' + k + '}', v).replace('\\' + k, v)
        t = t.replace('{\\' + k[0] + '{' + k[-1] + '}}', v)
    t = re.sub(r'\\[a-zA-Z]+\s*', '', t)
    t = t.replace('~', ' ').replace('---', '—').replace('--', '–')
    t = t.replace('{', '').replace('}', '').replace('\\', '')
    t = re.sub(r'\s+([,.;])', r'\1', t)
    return ' '.join(t.split()).rstrip(' .') + '.'

REFS = [clean_ref(t) for _, t in entries]

# ---------- inliner les fragments de tables ----------
tex = re.sub(r'\\input\{(tables/[^}]+)\}\\\\',
             lambda m: open(m.group(1)).read().rstrip() + '\\\\', tex)

body = tex[tex.index(r'\section{Introduction}'):tex.index(r'\bibliographystyle')]

# ---------- numerotation des flottants (ordre d'apparition) ----------
NUM, nfig, ntab = {}, 0, 0
for m in re.finditer(r'\\begin\{(figure|table)\}.*?\\label\{([^}]+)\}', body, re.S):
    if m.group(1) == 'figure':
        nfig += 1; NUM[m.group(2)] = nfig
    else:
        ntab += 1; NUM[m.group(2)] = ntab
SEC = {}
s1 = s2 = 0
for m in re.finditer(r'\\(sub)?section\{[^}]*\}\s*(?:%[^\n]*\n\s*)?\\label\{([^}]+)\}', body):
    if m.group(1):
        s2 += 1; SEC[m.group(2)] = f'{s1}.{s2}'
    else:
        s1 += 1; s2 = 0; SEC[m.group(2)] = str(s1)

GREEK = {r'\tau':'τ', r'\alpha':'α', r'\Delta':'Δ', r'\pm':'±', r'\times':'×',
         r'\approx':'≈', r'\leq':'≤', r'\geq':'≥', r'\to':'→', r'\rightarrow':'→',
         r'\in':'∈', r'\cdot':'·', r'\mathrm':'', r'\text':'', r'\,':' ', r'\;':' '}

def demath(s):
    for k, v in GREEK.items(): s = s.replace(k, v)
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    return s.replace('{', '').replace('}', '').replace('$', '')

SUP = str.maketrans('0123456789-+', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺')
SUB = str.maketrans('0123456789-+', '₀₁₂₃₄₅₆₇₈₉₋₊')

def math_inline(s):
    """$...$ -> texte unicode ; exposants/indices numeriques en caracteres dedies."""
    s = re.sub(r'\^\{([-0-9+]+)\}', lambda m: m.group(1).translate(SUP), s)
    s = re.sub(r'\^([0-9])', lambda m: m.group(1).translate(SUP), s)
    s = re.sub(r'_\{\s*(\\pm[^}]*)\}', r' \1', s)          # 1.0000_{\pm 0.0002} -> 1.0000 ± 0.0002
    s = re.sub(r'_\{([-0-9+.]+)\}', lambda m: m.group(1).translate(SUB), s)
    # indices litteraux -> vrai indice Word (marqueurs \x03 ... \x04)
    s = re.sub(r'_\{\\?[a-zA-Z]*\{?([a-zA-Z]+)\}?\}', '\x03' + r'\1' + '\x04', s)
    return demath(s)

def runs(t):
    """LaTeX inline -> liste de runs [{text, b, i, code}]."""
    t = re.sub(r'\\cite\{([^}]+)\}',
               lambda m: '[' + ', '.join(str(CITE.get(k.strip(), '?')) for k in m.group(1).split(',')) + ']', t)
    t = re.sub(r'\\ref\{(fig:[^}]+)\}', lambda m: str(NUM.get(m.group(1), '?')), t)
    t = re.sub(r'\\ref\{(tab:[^}]+)\}', lambda m: str(NUM.get(m.group(1), '?')), t)
    t = re.sub(r'\\ref\{(sec:[^}]+)\}', lambda m: str(SEC.get(m.group(1), '?')), t)
    t = re.sub(r'\\todo\{([^}]*)\}', '\x05' + r'[A COMPLETER : \1]' + '\x06', t)
    t = t.replace('~', ' ').replace('---', '—').replace('--', '–')
    t = t.replace(r'\%', '%').replace(r'\&', '&').replace(r'\_', '_')
    t = t.replace(r'\{', '\x01').replace(r'\}', '\x02')
    t = re.sub(r'\\[ ,;!]', ' ', t)
    t = t.replace(r'\ding{51}', '\u2713').replace(r'\ding{55}', '\u2717')
    t = t.replace("``", '\u201c').replace("''", '\u201d')
    t = re.sub(r'\\(emergencystretch|allowbreak|centering|small|footnotesize)\b\S*', '', t)
    t = t.replace(r'\-', '')
    out, pos = [], 0
    pat = re.compile(r'\\(textbf|emph|textit|texttt)\{((?:[^{}]|\{[^{}]*\})*)\}|\$([^$]*)\$')
    for m in pat.finditer(t):
        if m.start() > pos:
            out.append({"t": demath(t[pos:m.start()])})
        if m.group(1):
            inner = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', m.group(2))
            style = {"textbf": "b", "emph": "i", "textit": "i", "texttt": "code"}[m.group(1)]
            out.append({"t": inner.replace('{', '').replace('}', ''), style: True})
        else:
            out.append({"t": math_inline(m.group(3))})
        pos = m.end()
    if pos < len(t): out.append({"t": demath(t[pos:])})
    # eclatement des marqueurs d'indice en runs dedies
    split = []
    for r in out:
        r["t"] = r["t"].replace('\x01', '{').replace('\x02', '}')
        if '\x03' not in r["t"] and '\x05' not in r["t"]:
            split.append(r); continue
        for i, part in enumerate(re.split('([\x03\x04\x05\x06])', r["t"])):
            if part in ('\x03', '\x04', '\x05', '\x06') or not part: continue
            nr = dict(r); nr["t"] = part
            j = r["t"].index(part)
            prev = [c for c in r["t"][:j] if c in '\x03\x04\x05\x06']
            if prev and prev[-1] == '\x03': nr["sub"] = True
            if prev and prev[-1] == '\x05': nr["warn"] = True; nr["b"] = True
            split.append(nr)
    return [r for r in split if r["t"].strip() or r["t"] == ' ']

def cells(row, ncol):
    """Une ligne de tabular -> cellules, avec fusions (\\multicolumn)."""
    out = []
    for c in row.split('&'):
        c = c.strip()
        m = re.match(r'\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}$', c)
        if m: out.append({"runs": runs(m.group(2)), "span": int(m.group(1))})
        else: out.append({"runs": runs(c), "span": 1})
    while sum(x["span"] for x in out) < ncol: out.append({"runs": [], "span": 1})
    return out

def parse_table(blk):
    cap = re.search(r'\\caption\{(.*?)\}\s*\n\s*\\label', blk, re.S)
    cap = cap.group(1) if cap else re.search(r'\\caption\{(.*)\}', blk, re.S).group(1)
    lab = re.search(r'\\label\{([^}]+)\}', blk).group(1)
    spec = re.search(r'\\begin\{tabular\}\{([^}]*)\}', blk).group(1)
    align = [{'l':'left','c':'center','r':'right'}[c] for c in spec if c in 'lcr']
    inner = blk[blk.index('\\toprule') + 8: blk.index('\\bottomrule')]
    head, sep, bodyrows = inner.partition('\\midrule')
    def rows_of(chunk):
        chunk = re.sub(r'\\cmidrule\(lr\)\{[^}]*\}', '', chunk)
        chunk = chunk.replace('\\midrule', '')
        return [r for r in (x.strip() for x in chunk.split('\\\\')) if r]
    return {"type": "table", "label": lab, "num": NUM[lab],
            "caption": runs(' '.join(cap.split())), "align": align,
            "head": [cells(r, len(align)) for r in rows_of(head)],
            "body": [cells(r, len(align)) for r in rows_of(bodyrows)]}

def parse_figure(blk):
    cap = re.search(r'\\caption\{(.*?)\}\s*\n\s*\\label', blk, re.S)
    cap = cap.group(1) if cap else re.search(r'\\caption\{(.*)\}', blk, re.S).group(1)
    lab = re.search(r'\\label\{([^}]+)\}', blk).group(1)
    src = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', blk).group(1)
    w = re.search(r'width=([\d.]+)\\linewidth', blk)
    return {"type": "figure", "label": lab, "num": NUM[lab],
            "src": src.replace('.pdf', '.png'), "width": float(w.group(1)) if w else 1.0,
            "caption": runs(' '.join(cap.split()))}

# ---------- balayage ----------
items, i = [], 0
FLOAT = re.compile(r'\\begin\{(table|figure)\}.*?\\end\{\1\}', re.S)
tokens = []
for m in FLOAT.finditer(body):
    tokens.append((m.start(), m.end(), m.group(0), m.group(1)))
prev = 0
chunks = []
for s, e, blk, kind in tokens:
    chunks.append(("text", body[prev:s])); chunks.append((kind, blk)); prev = e
chunks.append(("text", body[prev:]))

for kind, chunk in chunks:
    if kind == "table": items.append(parse_table(chunk)); continue
    if kind == "figure": items.append(parse_figure(chunk)); continue
    chunk = re.sub(r'(?<!\\)%.*', '', chunk)
    chunk = re.sub(r'(\\begin\{(?:enumerate|itemize)\})', r'\n\n\1', chunk)
    chunk = re.sub(r'(\\end\{(?:enumerate|itemize)\})', r'\1\n\n', chunk)
    for blk in re.split(r'\n\s*\n', chunk):
        blk = blk.strip()
        if not blk: continue
        m = re.match(r'\\section\{(.*?)\}', blk, re.S)
        if m:
            items.append({"type": "h1", "runs": runs(' '.join(m.group(1).split()))})
            blk = blk[m.end():].strip()
            blk = re.sub(r'^\\label\{[^}]*\}', '', blk).strip()
            if not blk: continue
        m = re.match(r'\\section\*\{(.*?)\}', blk, re.S)
        if m:
            items.append({"type": "h1", "runs": runs(m.group(1))}); blk = blk[m.end():].strip()
            if not blk: continue
        m = re.match(r'\\subsection\{(.*?)\}', blk, re.S)
        if m:
            items.append({"type": "h2", "runs": runs(' '.join(m.group(1).split()))})
            blk = blk[m.end():].strip()
            blk = re.sub(r'^\\label\{[^}]*\}', '', blk).strip()
            if not blk: continue
        if blk.startswith(r'\begin{enumerate}') or blk.startswith(r'\begin{itemize}'):
            ordered = blk.startswith(r'\begin{enumerate}')
            for it in re.findall(r'\\item\s+(.*?)(?=\\item|\\end\{(?:enumerate|itemize)\})', blk, re.S):
                items.append({"type": "li", "ord": ordered, "runs": runs(' '.join(it.split()))})
            continue
        # equation hors-texte : coupe le paragraphe en trois (avant / equation / apres)
        m = re.search(r'\\\[(.*?)\\\]', blk, re.S)
        if m:
            before, after = blk[:m.start()].strip(), blk[m.end():].strip()
            if before: items.append({"type": "p", "runs": runs(' '.join(before.split()))})
            items.append({"type": "math", "runs": runs('$' + ' '.join(m.group(1).split()) + '$')})
            if after: items.append({"type": "p", "runs": runs(' '.join(after.split()))})
            continue
        m = re.match(r'\\paragraph\{(.*?)\}\s*(.*)', blk, re.S)
        if m:
            items.append({"type": "p", "lead": ' '.join(m.group(1).split()),
                          "runs": runs(' '.join(m.group(2).split()))}); continue
        blk = re.sub(r'\\label\{[^}]*\}', '', blk).strip()
        if blk: items.append({"type": "p", "runs": runs(' '.join(blk.split()))})

# ---------- front matter ----------
fm = re.search(r'\\begin\{frontmatter\}(.*?)\\end\{frontmatter\}', tex, re.S).group(1)
title = ' '.join(re.search(r'\\title\{(.*?)\}\s*\n\s*\n', fm, re.S).group(1).split())
authors = re.findall(r'\\author\[[^\]]*\]\{([^}]*)\}', fm)
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', fm, re.S).group(1)
kw = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', fm, re.S).group(1)

doc = {"title": title, "authors": authors,
       "abstract": runs(' '.join(abstract.split())),
       "keywords": ' · '.join(k.strip() for k in kw.split(r'\sep')),
       "items": items, "refs": REFS}
json.dump(doc, open('content.json', 'w'), ensure_ascii=False, indent=1)
print(f"content.json : {len(items)} blocs | {ntab} tables | {nfig} figures | {len(REFS)} refs")
from collections import Counter
print(" ", Counter(x['type'] for x in items).most_common())
