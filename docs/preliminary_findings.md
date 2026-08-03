# Lecture des premiers résultats (2026-08-03) — conditions `full` et `clean`, graine 1 + temporel

Source : exécution partielle de l'ancien notebook. Chiffres provisoires (une seule graine),
mais les tendances sont nettes et plusieurs sont déjà exploitables pour la rédaction.

---

## 1. Découverte méthodologique : l'importance par permutation est aveugle aux raccourcis

Quatre features — `Max`, `Min`, `Sum`, `Dur` — présentent :

| | accuracy seule (stratifié) | accuracy seule (temporel) | ratio | importance par permutation |
|---|---|---|---|---|
| `Max`, `Min`, `Sum`, `Dur` | **0,922** | **0,304** | **0,33** | **0,0000** |

Leur pouvoir prédictif individuel est le plus élevé de tout le corpus (0,922 contre un
hasard de 0,194), et il **s'effondre des deux tiers** sous le protocole temporel : ce sont
des raccourcis. Pourtant leur **importance par permutation est nulle**.

**Explication** : ces quatre colonnes sont mutuellement redondantes (statistiques de durée
d'agrégation Argus ; pour un flux à un seul enregistrement, `Dur = Min = Max = Sum`).
Permuter l'une d'elles ne coûte rien au modèle, qui retrouve l'information dans les trois
autres. L'importance par permutation — **la méthode utilisée par toute la littérature, y
compris SHAP dans Silva et al.** — ne peut structurellement pas les voir.

**Conséquence pour le papier** : c'est un résultat à part entière, et sans doute le plus
fort de l'article. *L'audit des raccourcis ne peut pas reposer sur l'importance
d'attribution ; il faut évaluer chaque feature **seule** sous deux protocoles.* Cela
explique aussi pourquoi Silva et al., qui ont pourtant utilisé SHAP et signalé une
« overreliance on traffic volume », n'ont pas pu identifier le mécanisme.

**Correction apportée au notebook (audit v3)** : le balayage de transférabilité porte
désormais sur **toutes** les features de la condition `clean`, et non plus sur les
20 premières par importance de permutation — un classement qui, ces features étant à
importance nulle, était arbitraire au-delà des huit premières. Ajout d'une détection des
colonnes dupliquées et d'un spectre trié des ratios.

---

## 2. Le spectre de transférabilité est net, avec un seuil bien placé

| ratio | features |
|---|---|
| **0,33** | `Max`, `Min`, `Sum`, `Dur` ← écartées |
| 0,60–0,67 | `Load`, `DstRate`, `SIntPktIdl` ← zone grise |
| 0,94–1,01 | `TotBytes`, `IdleTime`, `TotPkts`, `DstBytes`, `pLoss`, `dTtl`, `SrcPkts`, `DstPkts`, `sMaxPktSz` |

Le vide entre 0,33 et 0,60 justifie empiriquement le seuil à 0,50 — argument à faire
figurer dans le papier (Figure 9, spectre trié). La zone grise 0,60–0,67 doit être
**discutée honnêtement** : ces trois features perdent 35–40 % de leur pouvoir prédictif
sous protocole temporel sans être écartées ; une analyse de sensibilité au seuil est à
prévoir.

---

## 3. `IdleTime` : la feature la plus importante, et elle transfère bien

Importance par permutation **0,2278** — sept fois la suivante (`dTtl`, 0,0338) — avec un
ratio de transférabilité de 0,94. C'est un signal comportemental légitime et dominant.

**Point de provenance** : le pipeline BAg-IDS initial supprimait `IdleTime` par accident
(le motif de filtrage `"id"` capturait `IdleTime`, `SIntPktIdl`, `DIntPktIdl`…). Les
détecteurs GeNIS de BAg-IDS §6.9 ont donc été entraînés **sans leur feature la plus
informative**. À corriger dans BAg-IDS avant soumission, et à mentionner ici comme
illustration du risque des filtres par motif de chaîne.

---

## 4. Le protocole temporel départage réellement les modèles

Condition `clean`, macro-F1 :

| modèle | stratifié | temporel | écart |
|---|---|---|---|
| `ftt` | 0,9999 | — | — |
| `xgboost` | 1,0000 | 0,9888 | −0,011 |
| `lightgbm` | 0,9999 | 0,9897 | −0,010 |
| `rf` | 0,9999 | **0,9752** | **−0,025** |
| `logreg` | 0,9996 | **0,9902** | −0,009 |
| `knn` | 0,9976 | 0,9835 | −0,014 |

En stratifié, quatre modèles sont indiscernables à 0,9999–1,0000 : **le classement est
vide de sens**. En temporel, l'ordre change : `logreg` passe devant `rf`, qui décroche
nettement. C'est exactement la démonstration attendue pour RQ2 — à confirmer sur 5 graines.

**Observation à vérifier** : en temporel, la condition `full` fait *mieux* que `clean`
pour les arbres (rf 0,9892 vs 0,9752 ; xgb 0,9927 vs 0,9888). Contre-intuitif ; à
réexaminer avec les 5 graines avant toute interprétation.

---

## 5. La granularité du FPR est d'exactement un flux

Le test contient **~5 029 flux bénins** (7,4 %), donc **un seul faux positif = 0,0199 %**.
Tous les FPR observés sont des multiples exacts : 0,0199 % = 1 FP, 0,0398 % = 2,
0,0795 % = 4, 1,1730 % = 59, 3,4394 % = 173.

À écrire tel quel dans les *Threats to Validity* : sous la distribution naturelle de GeNIS,
**la résolution du FPR est de 0,02 point** ; annoncer un FPR à quatre décimales serait
trompeur. Argument précis et vérifiable, très apprécié en Q1.

---

## 6. Le benchmark discrimine — le zoo n'est pas décoratif

- `nb` (bayésien naïf) : accuracy 0,703, **FPR 61 %** (stratifié) et **90 %** (temporel).
  Échec franc — justifie l'inclusion d'une baseline probabiliste.
- `rnn` : FPR 3,44 % en `clean` contre 0,08 % pour `dnn`. Le trio BAg-IDS n'est pas homogène.
- `ftt` : le plus coûteux (605 s en `full`, 322 s en `clean`) pour un gain nul en stratifié
  → nourrit directement la Figure 5 (coût vs performance).
- `knn` : temps d'entraînement nul (paresseux), coût entièrement à l'inférence — le banc de
  coût §6.5 le mettra en évidence.

---

## 7. À surveiller dans la suite

1. Le balayage complet (audit v3) va-t-il révéler d'autres raccourcis hors des 20 premières
   features ? Probable, puisque le critère de sélection précédent était biaisé.
2. Les 5 graines confirment-elles l'inversion `logreg` / `rf` en temporel ?
3. `Max`/`Min`/`Sum`/`Dur` sont-elles littéralement des colonnes dupliquées ? Le nouvel
   audit le teste (`np.allclose`) — si oui, c'est un défaut du corpus à signaler aux auteurs.
