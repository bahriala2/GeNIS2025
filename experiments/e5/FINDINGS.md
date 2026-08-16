# E5 — cinq graines à tous les intervalles

`e5_results.json`. Majeur 11 du rapport de relecture, dernier point restant.

## Le témoin, d'abord

Le notebook rejoue un run déjà publié avant d'étendre quoi que ce soit : LightGBM,
graine 1, intervalle 30 s.

```
rejoué  0.9999028573780938
publié  0.9999028573780938
écart   0.0
```

Identiques **au bit près**. Les graines 1 à 3 stockées et les graines 4 et 5 calculées
viennent donc du même environnement, et peuvent figurer dans le même tableau. Sans ce
contrôle, le tableau 6 mélangerait deux campagnes sans le dire.

## Ce que les deux graines de plus tranchent

**L'effondrement de LightGBM à 10 s ne se reproduit pas.** Une graine sur cinq, pas une
sur trois :

| 10 s, LightGBM | g1 | g2 | g3 | g4 | g5 |
|---|---|---|---|---|---|
| macro-F1 | 0.9999 | 1.0000 | **0.8374** | 1.0000 | 1.0000 |

C'est l'échec isolé d'un ajustement, pas une instabilité de LightGBM à cette fenêtre. La
section 6.4 peut désormais le qualifier sur cinq observations.

**Et elles produisent l'image miroir, que personne n'attendait.** Le DNN à 30 s :

| 30 s, DNN | g1 | g2 | g3 | g4 | g5 |
|---|---|---|---|---|---|
| macro-F1 | 0.8512 | 0.8432 | 0.8488 | 0.8515 | **0.9879** |

Quatre runs serrés autour de 0.849, un cinquième à 0.988. Leur moyenne, 0.8765, ne décrit
aucun des cinq. C'est exactement le reproche que le relecteur nous faisait sur LightGBM,
et il s'applique maintenant à notre propre chiffre : le manuscrit donnait 0.8478 comme
moyenne à trois graines. Il donne désormais les runs.

## Ce qui n'a pas bougé

XGBoost est invariant sur ses **vingt** runs. Le déclin du DNN avec la fenêtre est porté
par toutes les graines à tous les intervalles : 0.9968 à 60 s, ~0.849 à 30 s, 0.5120 à
10 s, 0.5235 à 5 s. La conclusion de la section 6.4 est intacte, elle repose simplement
sur des effectifs égaux.

## Ce qui a changé dans le manuscrit

- **Tableau 6** : cinq graines partout, plus aucun tiret. Toujours aucune moyenne.
- **§6.4, corps** : « quatre de ses cinq runs à 0.9999 ou plus, le cinquième à 0.8374 ».
- **§6.4, paragraphe final** : remplace la déclaration de limite par ce que les deux
  graines ont tranché.
- **Figure 11** : elle précède E5 et reste un rendu à trois graines. Plutôt que de laisser
  une figure à trois graines côtoyer un tableau à cinq sans le dire, la légende l'indique
  et le texte donne la valeur à cinq graines de la cellule concernée : `bruteforce-ftp` à
  10 s passe de 0.685 à **0.811**, ce qui change sa valeur et pas la lecture.

## Coût réel

Deux graines × trois intervalles = 18 runs. Les temps d'ajustement enregistrés donnent
environ 1 h 30 de calcul pur, contre ~4 h 30 pour un rejeu intégral des cinq graines.
Le contrôle témoin coûte deux minutes et évite le rejeu.
