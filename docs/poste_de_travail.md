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

## 2. Installer le dossier de travail

Dans PowerShell. Le chemin contient une espace, d'où les guillemets.

Si `D:\these\article benchmark` est **vide ou n'existe pas** :

```powershell
git clone https://github.com/bahriala2/GeNIS2025.git "D:\these\article benchmark"
cd "D:\these\article benchmark"
git checkout claude/manuscript-e2-e3-sections-87snff
```

Si le dossier **existe déjà et contient des fichiers** qui ne sont pas un clone
(archives Colab, brouillons Word, PDF de relecture), on ne clone pas par-dessus,
on rattache :

```powershell
cd "D:\these\article benchmark"
git init
git remote add origin https://github.com/bahriala2/GeNIS2025.git
git fetch origin claude/manuscript-e2-e3-sections-87snff
git checkout -b claude/manuscript-e2-e3-sections-87snff origin/claude/manuscript-e2-e3-sections-87snff
```

Git refusera d'écraser un fichier existant qui porte le même nom qu'un fichier
suivi ; il le dira, fichier par fichier. Déplacez-les et relancez.

Vérifier qu'on est au bon endroit :

```powershell
git log --oneline -1          # doit afficher : Record the state the article was submitted in
python paper\check_coherence.py
```

## 3. Ce qu'il faut installer

| Outil | Pour quoi | Obligatoire |
|---|---|---|
| Python 3.10+ | tout | oui |
| `pip install python-docx matplotlib` | régénérer les figures, éditer le `.docx` par script | pour les figures |
| `pip install pymupdf` | `check_layout.py` | pour la pagination |
| LibreOffice Writer | `check_layout.py`, `make preview` | pour la pagination |
| Word | éditer l'article | oui |

`check_coherence.py`, `check_style.py`, `check_claims.py` et
`make_submission.py` n'ont **aucune dépendance** : bibliothèque standard seule.

## 4. Ce que le poste débloque, et que le cloud ne peut pas faire

Deux points restaient ouverts faute d'environnement, pas faute de travail.

**`check_layout.py` n'a jamais pu tourner en ligne.** LibreOffice ne démarre pas
dans le conteneur de vérification, pas même sur un fichier texte d'un octet. Le
quatrième vérificateur, celui qui regarde le document **une fois paginé** — une
légende coupée entre deux pages, un tableau séparé de sa légende — n'a donc
jamais été exécuté sur l'état soumis, et le compte de 47 pages vient du dernier
rendu local. C'est la première chose à lancer sur le poste :

```powershell
python paper\check_layout.py
```

**La figure 12 et la version 2 de Zenodo attendent un fichier qui n'est pas dans
le dépôt.** La figure 12 fait 1593 pixels de large contre 1772 exigés et n'a pas
de version vectorielle ; elle ne peut pas être redessinée depuis ce qui est
versionné, parce qu'elle trace des runs à 5, 10 et 30 secondes qui vivent dans
l'objet `RESULTS["intervals"]` du run Colab, donc dans `article1_final.zip` sur
Zenodo. Le même fichier est ce qui manque pour bâtir la v2 de l'archive, sans
laquelle un lecteur ne peut pas reproduire le tableau 2.

**Si `article1_final.zip` est sur le poste, les deux se règlent en une séance.**
C'est la raison la plus concrète de travailler en local.

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
