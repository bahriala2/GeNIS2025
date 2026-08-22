# Relecture des sections 7 à 12

Cette moitié du manuscrit — 8 900 mots, de la validation externe à la
déclaration d'usage d'IA — n'avait jamais été relue. Voici ce qu'elle a donné.

**Le défaut principal était structurel, pas ponctuel.** La §8 porte une
**seconde série** d'affirmations de coût et de calibration, parallèle à celle
de la §6.7. Republier la §6.7 sans toucher à la §8 laissait le papier se
contredire d'une section à l'autre, sur les mêmes quantités, à dix pages
d'intervalle. Aucun des trois vérificateurs ne pouvait le voir : ils
contrôlent la cohérence des renvois, le style et la mise en page, pas la
lecture d'un tableau.

---

## 1. Ce qui était faux, et ne le doit rien à la correction

Trois erreurs préexistaient à toute la republication.

### « smallest latency tail among the tree ensembles » (XGBoost)

Le Tableau 10 **publié** donne LightGBM à 1,42 ms de p99 contre 4,66 à
XGBoost. La queue la plus serrée était celle de LightGBM. Sur la nouvelle
mesure aussi : 2,32 contre 5,89.

### « XGBoost leads on median latency »

Écrit par moi dans la §6.7 en republiant le coût. La régression logistique est
à **0,14 ms** contre 1,22. Le contrôle que j'avais écrit pour vérifier cette
phrase excluait explicitement la régression logistique — une exception posée
pour sauver l'affirmation, pas pour la mesurer.

### « no detector has both » (débit et latence)

Faux : la régression logistique mène les deux. Le contrôle correspondant
passait **à vide**, avec un `or True` dans sa condition.

---

## 2. Ce que la relecture a changé sur le fond

### La recommandation du papier

Sur les cinq axes mesurés pour les deux, **la régression logistique devance
XGBoost sur quatre** :

| axe | logreg | xgboost |
|---|---:|---:|
| débit (lots) | **601 449** | 42 687 |
| latence p50 | **0,14 ms** | 1,22 ms |
| latence p99 | **0,25 ms** | 5,89 ms |
| macro-F1 temporel | **0,9881** | 0,9666 |
| macro-F1 stratifié | 0,9963 | **0,9999** |

Le seul axe où XGBoost gagne est le macro-F1 stratifié — **c'est-à-dire la
quantité que ce papier passe douze sections à démontrer saturée et
statistiquement ininterprétable**. La §6.7 et la §8 recommandent désormais la
régression logistique par défaut, et réservent XGBoost au cas où l'intervalle
d'agrégation échappe au déployeur : c'est le seul détecteur dont la robustesse
à l'intervalle soit mesurée. Le papier dit maintenant explicitement que **ce
n'est pas une comparaison**, puisque l'étude par intervalle ne couvre pas la
régression logistique.

### L'argument sur les postérieures tranchantes

La §8 concluait : « c'est l'axe sur lequel les ensembles d'arbres paient leur
avantage de coût », en s'appuyant sur des températures de 0,05 à 0,09 pour les
arbres contre 0,69 à 1,13 pour les réseaux. **Les deux plages se chevauchent
maintenant** : 0,39 à 1,46 contre 0,68 à 1,35. Retirer la colonne identifiante
a supprimé ce qui rendait les postérieures des arbres quasi déterministes.
Seule la forêt aléatoire, à 0,39, reste assez sous un pour que la limitation
morde. C'est devenu une propriété d'un détecteur, pas d'une famille.

### La phrase sur le CPU et le GPU (§9)

Elle affirmait que le budget de recherche inégal « n'affecte aucune exactitude
rapportée, puisque l'entraînement sur CPU ou GPU donne le même modèle à la
non-déterminisme flottant près ». **On a la preuve du contraire, et elle est
dans ce papier** : réajuster le FT-Transformer dans une session ultérieure a
déplacé son macro-F1 temporel de 0,0187, plus que l'effet que la correction de
la §9 mesure. Et l'environnement d'exécution n'enregistre ni quel accélérateur
a servi un run, ni s'il y en avait un. Une menace à la validité qui se déclare
à tort est pire que pas de déclaration.

---

## 3. Chiffres périmés, corrigés

| où | disait | dit |
|---|---|---|
| §8, quatre axes | ftt 430 f/s, xgboost 46 317, « a hundred times » | 548, 42 687, **78 fois** |
| §8, régression logistique | 1,14 M f/s, température 0,70 | **601 449**, 0,68 |
| §8, calibration | ECE ≤ 0,0009 sauf nb ; dix sur onze ; 241 à 457 | **0,0015** sauf logreg et nb ; **neuf** sur onze ; **146 à 1403** |
| §8, déploiement | « rf dominé par xgboost sur tous les axes » | rf a le **2ᵉ** débit ; dominé seulement là où la latence ou la qualité temporelle mordent |
| §8, déploiement | knn 1 875 f/s | **621** |
| §9, coût d'IdleTime | 0,0040 / 0,0263, « eightfold » | 0,0038 / 0,0263, **7×** |
| §10, conclusion | mid-table ; dix sur onze ; 241 à 457 | bottom third ; **neuf** ; **146 à 1403** |
| résumé et points saillants | mid-table ; dix sur onze | idem |

---

## 4. Provenances qui n'étaient pas déclarées

Trois éléments viennent d'expériences antérieures à la correction et ne le
disaient pas. Depuis la republication, « audited condition » désigne 54
colonnes partout ailleurs.

- **Tableau 6** (macro-F1 par intervalle) : condition publiée, 55 colonnes,
  non rejoué. La légende le dit maintenant.
- **Figure 19** (coût du seuil) : ses cinq listes portent toutes la colonne
  identifiante, donc la comparaison entre elles tient — c'est le seuil qu'elle
  fait varier, et aucun seuil sur ce rapport n'atteint cette colonne. Ce sont
  ses macro-F1 **absolus** qui ne sont plus ceux du reste du papier.
- **Tableau 16** : sa colonne « blacklist » compte douze là où la liste
  publiée en a treize, parce qu'elle n'ajoute pas la colonne identifiante.

**§11** annonçait « les deux mesures que ce papier ajoute sans
réentraînement ». Il en ajoute une troisième qui, elle, réentraîne tout : la
republication sur la liste corrigée. E7 et E8 y sont maintenant nommés, avec
les tableaux et figures qui en sortent.

---

## 5. Ce qui a été vérifié et tient

La **§7** ne bouge pas : elle ne dépend d'aucune mesure GeNIS. Tout ce qui y
est vérifiable a été recalculé depuis `experiments/e2/` et concorde —
2 830 743 flux, 69 colonnes comportementales, sonde à 0,9529 stratifié et
0,1028 temporel, τ = 0,11, 43 colonnes éligibles, sept paires identiques dont
**dix des quatorze colonnes à exactement zéro**, transférabilité la plus basse
0,6726 sur `Bwd IAT Std`, seuil 0,1909 pour une base de 0,0636.

Deux points que j'ai soupçonnés à tort :

- **« κ = 0,4818 reproduit exactement la règle GeNIS publiée. »** Recalculé
  depuis pmax, κ vaut 0,4821, et les deux seuils diffèrent de 0,000212. Mais
  **aucune colonne n'a d'exactitude dans cet écart** : les deux règles
  retiennent les mêmes 38 colonnes. « Exactement » est vrai en effet.
- **« les huit détecteurs » puis « sept des neuf »** dans la §9. Comptage
  cohérent : neuf inclut le bayésien naïf, huit l'exclut. Vérifié sur
  `experiments/e4c/`.

---

## 6. Contrôles ajoutés

`experiments/e8/verify_e8.py` passe de 19 à **37 contrôles**. Les nouveaux,
section G, recalculent **tous les rangs que la §8 cite**. Un rang est
exactement le genre d'affirmation qu'on écrit de mémoire et qui devient faux
dès que la mesure change — les trois erreurs de la partie 1 en sont.

Le contrôle sur les deux colonnes de coût teste maintenant ce que le papier
affirme, au lieu d'être écrit pour l'accommoder.
