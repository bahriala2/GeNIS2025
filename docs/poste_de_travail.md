# Reprendre l'article sur le poste local

Note écrite depuis une session Claude Code **dans le cloud**, qui n'a accès ni à
`D:\` ni à aucun disque de la machine : elle travaille dans un conteneur Linux
jetable, et le seul pont entre les deux est ce dépôt Git. Ce fichier dit ce
qu'il faut faire une fois, sur le poste, pour que le travail reprenne là où il
s'est arrêté.

## 1. Le piège à connaître avant de cloner

Le dépôt porte **deux branches sans aucun ancêtre commun**. Se tromper de
branche donne un article qui a un mois de retard, sans que rien ne le signale.

| Branche | Ce qu'elle contient |
|---|---|
| `claude/manuscript-e2-e3-sections-87snff` | **La bonne.** L'article soumis à EAAI, le package de soumission, E3 à E9, les quatre vérificateurs |
| `claude/second-corpus-manuscript-u4dzh5` | Une ligne parallèle arrêtée au 15 août, sans le package ni E3–E9. À ignorer |

## 2. Le dossier de travail, tel qu'il est réellement

L'installation est faite. Deux dossiers voisins portent des noms proches, et les
confondre fait perdre du temps :

| Chemin | Ce que c'est |
|---|---|
| `D:\these\article_benchmark2` | **Le clone Git.** C'est ici qu'on travaille |
| `D:\these\article_benchmark` | **Pas un dépôt.** Les sorties Colab d'août : `article1_models.zip`, `article1_results (3).json`, les notes pour Farah. À ne pas confondre |

Vérifier qu'on est au bon endroit :

```powershell
cd D:\these\article_benchmark2
git status -sb                # doit afficher la branche claude/manuscript-e2-e3-sections-87snff
python paper\check_coherence.py
```

Si le clone doit être refait un jour, la branche à sortir est
`claude/manuscript-e2-e3-sections-87snff` — voir le tableau de la section 1.

## 3. Ce qu'il faut installer

Tout est installé sur le poste. La colonne de droite dit comment refaire, le cas
échéant — les commandes sont celles de Windows, pas celles du conteneur Linux.

| Outil | Pour quoi | Comment |
|---|---|---|
| Python 3.12.4 | tout | déjà là |
| `python-docx`, `matplotlib` | figures, édition du `.docx` par script | `pip install python-docx matplotlib` |
| `pymupdf` | `check_layout.py` | `pip install pymupdf` |
| LibreOffice Writer 26.8 | `check_layout.py`, `make preview` | `winget install TheDocumentFoundation.LibreOffice` — **exige l'élévation**, il faut accepter l'invite UAC, et environ 2 Go libres sur C: sous peine d'un échec MSI 1603 |
| Word | éditer l'article | déjà là |

LibreOffice ne sert qu'à produire un PDF jetable pour mesurer la pagination. Il ne
touche pas au `.docx`, qui reste édité dans Word.

`check_coherence.py`, `check_style.py`, `check_claims.py` et
`make_submission.py` n'ont **aucune dépendance** : bibliothèque standard seule.

## 4. Ce que le poste a débloqué

Ce que cette section annonçait comme ouvert l'est encore pour partie seulement.

**`check_layout.py` a tourné.** LibreOffice ne démarrait pas dans le conteneur de
vérification, pas même sur un fichier texte d'un octet ; le quatrième
vérificateur — celui qui regarde le document **une fois paginé**, une légende
coupée entre deux pages, un tableau séparé de sa légende — n'avait donc jamais
été exécuté sur l'état soumis. C'est fait, sur le poste, avec LibreOffice 26.8 :

```
rendu        48 pages de 8.27 x 11.69 in   (source)
rendu        47 pages                      (manuscript_anonymised.docx)
legendes     37 controlees
images       20 placees, aucune hors marges
aucun defaut de mise en page
```

Le compte de 47 pages n'est plus hérité d'un rendu antérieur : la lettre
d'accompagnement annonce « 47 pages and 3.8 MB » pour le manuscrit anonymisé, et
les deux chiffres sont vérifiés. La source en fait 48, le bloc auteurs et
remerciements étant retiré à l'anonymisation.

```powershell
python paper\check_layout.py
python paper\check_layout.py paper\submission\manuscript_anonymised.docx
```

**La figure 12 est réglée.** Elle a été redessinée en vectoriel par le commit
`dbad713` : les runs à 5, 10 et 30 secondes qu'elle trace étaient dans le dépôt
depuis le début, et non seulement dans `article1_final.zip`.

**La version 2 de Zenodo reste ouverte**, et c'est maintenant le seul point qui
le soit. Le fichier nécessaire est sur le poste :

```
C:\Users\ASUS\Downloads\article1_final.zip   182 Mo
MD5 e8a9689a15b314e7978be6c52afb2a28  — identique au dépôt publié
```

Cette égalité de MD5 est ce qui autorise à bâtir une v2 : Zenodo interdit de
modifier un fichier après publication, donc il faut repartir exactement du
contenu déposé. Voir `paper/ARCHIVE_README.md` pour l'inventaire, y compris les
trois copies redondantes des modèles qu'une v2 gagnerait à ne pas reconduire.

## 5. La discipline du dépôt, à ne pas casser

- La source de l'article est `paper/GeNIS_benchmark_article.docx`, éditée dans
  Word. Rien d'autre n'est la source.
- Le package de soumission n'est **jamais** édité à la main : après toute
  retouche de l'article, `python paper\make_submission.py` le reconstruit et
  revérifie l'anonymisation.
- Avant de considérer une passe terminée, les quatre vérificateurs, dans cet
  ordre : `check_coherence`, `check_style`, `check_claims`, `check_layout`.
- Ne jamais committer les CSV des corpus.

## 6. Rendre le travail visible depuis le cloud

Une session cloud ne voit que ce qui est poussé. Pour reprendre à deux :

```powershell
git add -A
git commit -m "..."
git push origin claude/manuscript-e2-e3-sections-87snff
```

Un `.docx` est un binaire : Git le versionne mais n'en montre pas le diff. Dire
dans le message de commit ce qui a changé dans le document est ce qui tient lieu
de diff.
