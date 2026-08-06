# Réponse à la relecture « overgeneralisation » (21 points)

Document de travail. La partie en anglais est rédigée pour être collée telle quelle dans
une *response to reviewers*. Chaque point renvoie à la numérotation de la relecture.

**Bilan** : 12 points acceptés (dont 5 reformulés autrement que proposé), 7 points refusés
avec argument, 2 points déjà couverts par le texte existant.

---

## Acceptés tels quels (7)

| # | Objet | Ce qui a changé dans `main.tex` |
|---|---|---|
| 4, 7, 21 | Autoencodeur | « a benign-trained autoencoder » → « the benign-trained autoencoder evaluated here », partout (abstract, contribution 4, conclusion). Titre §6.6 : « Reconstruction-based anomaly detection fails » → « The benign-trained autoencoder fails ». |
| 13 | Mécanisme de l'autoencodeur | « The mechanism is » → « The mechanism we observe is » ; « for this architecture and corpus » ajouté avant la conclusion sur la règle de décision ; phrase ajoutée : une seule architecture testée, la revendication porte sur la nécessité de vérifier la polarité par classe de menace. |
| 10 | Bascule du classement | « once evaluation respects time » → « under the per-class temporal protocol », et « outranks them » → « outranks them on this corpus ». |
| 11 | Titre §6.5 | « Calibration is already solved » → « Calibration has nothing to repair on the saturated task ». |
| 12 | Rien à recalibrer | « nothing left to repair » → « little left to repair », + renvoi explicite à la limite de §8. |
| 17 | Corpus CyberRange | « which includes most CyberRange-produced datasets » **supprimé**. Remplacé par : « How common that configuration is across CyberRange-produced corpora is an open empirical question that one dataset cannot settle. » C'était la meilleure prise de la relecture. |

## Acceptés mais reformulés autrement (5)

| # | Pourquoi pas la formulation proposée | Ce qui a été écrit à la place |
|---|---|---|
| 1, 18 | « may extend beyond this corpus, pending validation » est du hedging non informatif : le lecteur ne sait pas *lesquels* transfèrent ni *pourquoi*. | « Two of our findings follow from structural properties of the data rather than from measurement alone, and therefore hold wherever those properties hold; a third is specific to the model and corpus evaluated here. » Plus précis **et** plus fort. |
| 2, 5, 19 | « attribution-based auditing failed on GeNIS » perd le mécanisme, qui est la contribution. | Portée resserrée sur ce qui est vrai par construction : « attribution scores cannot isolate **redundant** shortcuts, by construction: permuting one copy of a repeated quantity costs a model nothing ». Magnitude mesurée annoncée séparément (« On GeNIS this appears as permutation importance below 10⁻⁴ »). |
| 9, 15 | Le « only … exposes them » devait sauter (voir ci-dessous) ; c'était une **erreur factuelle**, pas un excès de prudence. | « Only evaluating each feature in isolation exposes them » → « Evaluating each feature in isolation under two protocols exposes them. A duplicate-column check exposes six of the eight independently, and we recommend running both. » |

### Correction d'une erreur factuelle que la relecture a permis de trouver

Le manuscrit affirmait quatre fois que **seule** l'évaluation isolée à deux protocoles
révèle les raccourcis. C'est contredit par le manuscrit lui-même : §6.2 rapporte que la
vérification de colonnes dupliquées identifie six des huit raccourcis (`Dur = RunTime =
Mean = Sum = Min = Max`, 15 paires). Les quatre occurrences de « only » ont été retirées
et la complémentarité des deux tests est maintenant énoncée.

## Déjà couverts avant la relecture (2)

- **#12** : §8 contenait déjà *« Calibration is measured under one protocol only … may not
  extend to the temporal protocol »*. Un renvoi explicite depuis §6.5 a été ajouté.
- **#1/#18, volet corpus** : §8 contenait déjà *« Our conclusions about protocol and audit
  methodology are corpus-independent by construction; our conclusions about which detector
  wins are not. »* La phrase a été précisée (« in the sense that they follow from
  properties of the data that we state and verify rather than from the measurements
  alone ») et remontée dans l'abstract.

## Renforcement apporté en plus

La cécité de l'importance par permutation aux prédicteurs redondants est un résultat
connu, que le manuscrit affirmait sans le citer. Ajout de deux références
(`references.bib`) et de la phrase correspondante en §6.2 et §7 :

- Strobl, Boulesteix, Kneib, Augustin, Zeileis, *Conditional variable importance for
  random forests*, BMC Bioinformatics 9:307, 2008.
- Hooker, Mentch, Zhou, *Unrestricted permutation forces extrapolation*, Statistics and
  Computing 31:82, 2021.

L'argument passe ainsi de « nous prétendons que » à « propriété documentée, appliquée
ici », ce qui neutralise à la racine les objections 2, 5, 9, 14, 15 et 19.

---

## Refusés avec argument (7) : texte de rebuttal en anglais

> **Points 3, 6, 8, 16, 20 and the first half of 15.**
>
> We have adopted the reviewer's framing wherever our claim was inductive, and we thank
> them for a reading that led us to correct a factual error (see our response to point 9).
> For six statements, however, we respectfully maintain the unqualified form, because the
> claim is deductive rather than an extrapolation from a single corpus, and we have made
> the deduction explicit in the revised text rather than hedging it.
>
> **On temporal splitting (points 3, 6, 8, 16, 20).** The statement is a conditional whose
> antecedent is a checkable property of a corpus. If the flows of class A occupy
> [t₁, t₂] and those of class B occupy [t₃, t₄] with the two intervals disjoint, then any
> split that preserves capture order within each class yields a training partition in
> which a single timestamp threshold separates the two classes, and a test partition in
> which the same threshold separates them. The probe therefore transfers, for every such
> split. This is a proof, not an observation; what is corpus-specific is whether the
> antecedent holds, and we verify it for GeNIS in Figure 1 and quantify the consequence at
> 0.9862. Restating the conclusion as "on GeNIS, no time-based split neutralised the
> shortcut" would present a theorem as an anecdote and would deprive readers of the one
> thing that lets them decide whether their own corpus is affected. The revised text now
> reads: *"The conclusion is therefore deductive rather than observed: no split that
> respects capture order neutralises a shortcut whose classes occupy disjoint windows. Its
> antecedent is a checkable property of a corpus, not an assumption about corpora in
> general, and on GeNIS we verify it directly."* We have separately removed the one
> genuinely inductive claim in this family, that the configuration covers "most
> CyberRange-produced datasets" (point 17).
>
> **On attribution (first half of point 15).** Permutation importance answers "how much
> does the model lose when this feature is disturbed". When a second feature carries
> identical information, the answer is near zero regardless of how predictive the feature
> is. This is a documented property of attribution under dependent predictors
> [Strobl et al. 2008; Hooker et al. 2021], now cited, not a peculiarity of our data. We
> have accordingly narrowed the claim from "attribution cannot support a shortcut audit"
> to "attribution cannot isolate *redundant* shortcuts", which is the precise and
> defensible statement, and we have removed the uniqueness claim ("only") that the
> reviewer rightly challenged. We have also softened "by construction" to a description of
> the ranking mechanism, since a tree ensemble that distributes splits across duplicated
> columns does lose a little under permutation; the empirical magnitude (< 10⁻⁴) is
> reported as a measurement.

---

## Note de style

Les révisions proposées ajoutaient une vingtaine de « on GeNIS » et basculaient le texte
au passé. Nous avons anchré les énoncés inductifs (« on GeNIS », « in this corpus », « the
autoencoder evaluated here ») sans généraliser le procédé : un texte qui se protège vingt
fois en trois pages signale qu'il ne croit pas à ses propres résultats. Le présent est
conservé pour les propriétés des données, qui n'ont pas cessé d'être vraies : les colonnes
`Dur`, `RunTime`, `Mean`, `Sum`, `Min`, `Max` *sont* identiques.
