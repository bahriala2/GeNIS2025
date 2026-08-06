#!/usr/bin/env python3
"""Construit une version Word (.docx) a partir de main.tex + main.bbl.

Pandoc ne suit pas \input, ne lit pas les .pdf comme images et ne resout pas
les \cite d'un .bbl : on prepare donc un .tex intermediaire ou tout est resolu.
"""
import re, os, subprocess, sys

tex = open('main.tex').read()
bbl = open('main.bbl').read()

# ---- 1. numerotation des references, dans l'ordre du .bbl ----
entries = re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\\end\{thebibliography\})',
                     bbl, re.S)
num = {k: i + 1 for i, (k, _) in enumerate(entries)}

def cite(m):
    ks = [k.strip() for k in m.group(1).split(',')]
    return '[' + ', '.join(str(num.get(k, '?')) for k in ks) + ']'
tex = re.sub(r'\\cite\{([^}]+)\}', cite, tex)

# ---- 2. inliner les fragments de tableaux ----
def inline(m):
    body = open(m.group(1)).read().rstrip()
    return body + '\\\\'
tex = re.sub(r'\\input\{(tables/[^}]+)\}\\\\', inline, tex)

# ---- 3. images : Word ne rend pas le PDF -> PNG ----
tex = tex.replace('.pdf}', '.png}')

# ---- 4. constructions qui n'ont pas d'equivalent Word ----
tex = tex.replace(r'\ding{51}', 'X').replace(r'\ding{55}', '--')
tex = re.sub(r'\\rh\{([^}]*)\}', r'\1', tex)          # entetes pivotes -> horizontaux
tex = re.sub(r'\\cmidrule\(lr\)\{[^}]*\}', '', tex)   # non supporte par pandoc
tex = re.sub(r'\\multicolumn\{\d+\}\{[^}]*\}\{([^}]*)\}', r'\1', tex)
tex = tex.replace(r'\allowbreak{}', '').replace(r'\allowbreak', '')
tex = re.sub(r'\\setlength\{\\tabcolsep\}\{\d+pt\}', '', tex)
tex = re.sub(r'\\(footnotesize|small|scriptsize)\b', '', tex)
tex = re.sub(r'\\todo\{([^}]*)\}', r'\\textbf{[A COMPLETER : \1]}', tex)
tex = re.sub(r'\\emergencystretch=\S+', '', tex)

# ---- 5. preambule elsarticle -> article standard ----
head = re.search(r'\\begin\{frontmatter\}(.*?)\\end\{frontmatter\}', tex, re.S).group(1)
title = re.search(r'\\title\{(.*?)\}\s*\n\s*\n', head, re.S)
title = title.group(1) if title else re.search(r'\\title\{(.*?)\}', head, re.S).group(1)
title = ' '.join(title.split())
authors = ', '.join(re.findall(r'\\author\[[^\]]*\]\{([^}]*)\}', head))
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', head, re.S).group(1).strip()
keywords = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', head, re.S).group(1)
keywords = ' ; '.join(k.strip() for k in keywords.split(r'\sep'))

refs = '\n'.join(
    r'\item ' + ' '.join(t.replace(r'\newblock', ' ').split())
    for _, t in entries)

body = tex[tex.index(r'\section{Introduction}'):]
body = body[:body.index(r'\bibliographystyle')] if r'\bibliographystyle' in body else body

out = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,booktabs,graphicx,longtable}
\title{%s}
\author{%s}
\date{}
\begin{document}
\maketitle

\subsection*{Abstract}
%s

\subsection*{Keywords}
%s

%s

\section*{References}
\begin{enumerate}
%s
\end{enumerate}
\end{document}
""" % (title, authors, abstract, keywords, body, refs)

open('main_word.tex', 'w').write(out)
print(f"main_word.tex ecrit : {len(out.split())} mots, {len(entries)} references")

cmd = ['pandoc', 'main_word.tex', '-o', 'GeNIS_benchmark_article.docx',
       '--from', 'latex', '--to', 'docx', '--number-sections',
       '--resource-path', '.:figures']
r = subprocess.run(cmd, capture_output=True, text=True)
print("pandoc :", "OK" if r.returncode == 0 else "ECHEC")
if r.stderr.strip():
    print(r.stderr.strip()[:1500])
sys.exit(r.returncode)
