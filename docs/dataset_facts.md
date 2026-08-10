# Faits vérifiés sur GeNIS (source : Silva et al., Data in Brief 60 (2025) 111487)

Référentiel pour la rédaction — chaque fait ci-dessous est tiré du descripteur officiel.

## Génération

- **Plateforme** : Airbus CyberRange (32 GHz CPU, 112 Go RAM, 4 To), digital twin d'un réseau PME.
- **Capture** : `dumpcap` via SPAN/port mirroring vers une machine d'observation isolée.
- **Dates** : bénin (user+admin) jeudi 6 et vendredi 7 février 2025 ; background le samedi 8 ; **toutes les attaques du 10 au 12 février**. → *Ségrégation temporelle complète bénin/attaque.*
- **Topologie** : 6 LANs — Admin `192.168.131.0/24`, User `.132`, Serveurs `.130`, DMZ `.128` (web/FTP/mail/DNS/proxy publics), Remote-VPN `.141`, attaquants Kali-User et Kali-Remote.
- **Bénin** : Benign User Profiler (BUP, Shafi et al. 2024), 3 profils : user (IMAP/HTTP/SMTP, pause déjeuner 12–13 h), admin (SSH/FTP/SMB/DNS/HTTP), background passif (ARP, NBNS/AD, DNS).
- **Attaques** : 8 scénarios séquentiels, squelette commun « DNS → pause 5 min → Nmap → pause 5 min → action » :
  - SC1–SC5 (disrupt) : DoS Hulk (Go), Slowloris (Metasploit), UDP/ICMP/PSH-ACK (hping3) contre le serveur web DMZ ;
  - SC6–SC8 (authtest) : brute force SMB, SSH, SSH+FTP (Hydra, dictionnaire 10 000 mots de passe).
- **Extraction** : HERA (basé Argus), intervalles 5/10/30/60 s ; labels hiérarchiques (binaire / catégorie / sous-catégorie).

## Structure (5 modules Zenodo)

`0-info` (features + ground truth) · `1-packets` (PCAPNG, 37 681 001 paquets) ·
`2-flows` (CSV par sous-catégorie × intervalle — **ce que le benchmark utilise**) ·
`3-scenarios` (flux recomposés par scénario, avec bénin aux bonnes heures) ·
`4-preprocessed` (train/holdout des auteurs, features sélectionnées — base probable de Silva et al. FPS).

## Points critiques pour notre papier

1. **recon-nmap (27 713 flux) et recon-dns (20) existent dans le corpus mais PAS dans `2-flows`**
   (aucun CSV standalone) — ils ne vivent que dans `3-scenarios`. Notre tâche = 8 familles d'attaque + bénin.
2. **Discordance RÉSOLUE** (2026-08-03, via le texte intégral de Silva et al. FPS) :
   descripteur 60 s = 368 556 flux ; notre chargement de `2-flows` = 338 820. L'écart de
   **29 736** se décompose exactement en :
   - recon absent de `2-flows` : recon-nmap 27 713 + recon-dns 20 = **27 733**
   - benign-background manquant : 10 286 (Table 12) − 8 283 (fichier) = **2 003**
   - total : 27 733 + 2 003 = **29 736** ✓
   Aucune des deux causes n'est documentée par les auteurs. Le papier déclare les comptages
   **recomptés depuis les fichiers publiés**, et signale l'écart.
   Silva et al. utilisent donc `4-preprocessed` (368 556 flux, recon inclus).
3. Table 12 (descripteur), totaux par intervalle : 5 s = 2 806 168 ; 10 s = 1 504 184 ;
   30 s = 607 933 ; 60 s = 368 556 (recon inclus).
4. `4-preprocessed` (split shuffle+stratifié des auteurs) est le candidat naturel pour **E1**
   (comparaison ancrée avec Silva et al.) — à télécharger si E1 exact devient nécessaire.
5. `3-scenarios` = flux séquentiels réalistes par scénario : piste d'**évaluation temporelle
   réaliste** supplémentaire (option, hors périmètre v1 de l'article).
6. Limitations admises par les auteurs : attaques limitées à certaines machines, bénin sans la
   variabilité d'un réseau réel — à reprendre dans Threats to Validity.


---

# Silva et al., FPS 2025 — analyse du texte intégral (2026-08-03)

## Ce qu'ils font (à ne pas sous-estimer)

- **Sélection de caractéristiques** : 5 méthodes (IG, Chi², RFE, MAD, Dispersion Ratio),
  scores normalisés puis sommés, **16 features** retenues (~70 % de l'importance cumulée).
- **Modèles** : RF, XGB, LGBM, LSTM, MLP (5).
- **Réglage** : *grid search* exhaustif avec **validation croisée 5 blocs** → notre bras
  « réglé » était bien nécessaire pour être comparables.
- **Exclusions de features** : IP, MAC, VLAN, et `Ssaddr`/`Sdaddr` (compteurs HERA
  dépendants de la topologie) ; ils notent que 6 features Argus (`FlowID`, `Rank`, `Seq`,
  `AutoId`, `TcpOpt`, `Cause`) « ne contribuent pas ».
- **Coût mesuré** : temps d'entraînement, temps par époque, temps d'inférence. ⚠️ Notre
  Related Work affirmait le contraire — **corrigé**.
- **Distribution naturelle** : 7,37 % de bénin, aucun rééquilibrage.
- **Explicabilité** : SHAP, agrégée par type de feature (quantité / temps / hybride).
- **Résultats** : F1 ≈ 99,98 % (binaire) et 99,98 % (multiclasse 4 classes) ; RF meilleur
  en multiclasse ; FPR 0,09–1,01 %.
- **Leur propre réserve, non instruite** : « overreliance on traffic volume or packet
  counts ».

## Ce qu'ils NE font PAS (notre espace)

| Dimension | Silva et al. | Nous |
|---|---|---|
| Taxonomie multiclasse | **CategoryLabel, 4 classes** (benign/DoS/recon/bruteforce) | **SubCategoryLabel, 9 classes** (5 familles DoS séparées) |
| Audit de raccourcis | aucun | sonde temporelle + transférabilité mono-feature + liste noire |
| Protocole temporel | aucun (split aléatoire unique) | split temporel par classe + diagnostic chronologique |
| Répétitions | 1 seul split, aucun IC, aucun test | 5 graines, bootstrap, McNemar + Holm |
| Calibration | aucune | températures, ECE, diagrammes de fiabilité |
| Intervalles | **60 s uniquement** | 5/10/30/60 s |
| Modèles | 5 | 12 + autoencodeur (FT-Transformer, NB, k-NN, logreg, RNN/CNN/DNN) |
| Anomalie / non supervisé | aucun | autoencodeur (AUROC global et par famille) |

**Conclusion** : recouvrement réel sur le zoo d'arbres, le réglage et la mesure du coût ;
aucun recouvrement sur les quatre contributions du papier (audit, protocole temporel,
calibration, multi-intervalles) ni sur la granularité de la tâche.

## Conséquence actionnable : expérience E1 « comparaison ancrée »

`4-preprocessed` fournit les train/test officiels par intervalle. Rejouer nos 12 modèles
sur **leurs données et leur taxonomie 4 classes** coûte ~1–2 h et permet d'écrire :
« nous reproduisons le protocole de Silva et al., puis montrons ce que l'audit y change ».
À faire dans un notebook séparé, après la campagne principale.

---

# Module `4-preprocessed` : inspection mesurée (2026-08-06)

Inspection faite sur les fichiers locaux (Zenodo inaccessible depuis l'environnement
d'exécution), via `experiments/inspect_4preprocessed.py` et `experiments/probe_4preprocessed.py`.
Intervalle 60 s.

## Structure

- `genis-60-sec-train.csv` 294 844 lignes · `genis-60-sec-test.csv` 73 712 · **total 368 556**,
  soit exactement le compte de la Table 12 du descripteur. La reconnaissance est incluse :
  confirmation au flux près de notre explication de l'écart de 29 736 avec `2-flows`.
- **87 colonnes**, dont les one-hot `Proto_*` (5), `Flgs_e*` (7) et `State_*` (11). C'est bien la
  version prétraitée manuellement décrite en §3.3 du papier FPS, pas un jeu de features
  sélectionnées.
- Split 80/20 mélangé et stratifié. Aucune colonne constante.
- **13 sous-catégories**, pas 9 : les trois profils bénins restent séparés (`benign-user` 10 281,
  `benign-background` 8 229, `benign-admin` 3 210) et la reconnaissance est présente
  (`recon-nmap` 22 170, `recon-dns` 16). Part bénigne 7,37 %.
- `benign-background` = 8 229 en train, cohérent avec les 8 283 de `2-flows` : le déficit de
  2 003 flux face à la Table 12 est présent dans les deux modules.

## Ce que le prétraitement a corrigé

`StartTime`, `LastTime` et `Rank` sont **absents**. Le raccourci d'horodatage, qui atteint 0,9970
sur `2-flows`, n'est pas transmissible par ce module.

`Seq` et `Offset` subsistent mais sont **inoffensifs** : compteurs par fichier de capture,
réinitialisés à chaque PCAPNG, donc sans ordre global. Mesuré, et c'est net :

| feature | accuracy (13 classes) | × hasard |
|---|---|---|
| `Seq` | 0,1713 | **0,96** |
| `Offset` | 0,0672 | 0,38 |

contre un taux de classe majoritaire de 0,1785. Les deux sont **sous le hasard**. Une hypothèse
inverse avait été formulée avant mesure ; elle est fausse.

## Ce que le prétraitement n'a pas corrigé

**1. Les six colonnes numériquement identiques sont intactes.**
`Max = Mean = Min = Sum = Dur = RunTime`, **15 paires**, détectées par `np.allclose` sur les
294 844 lignes d'entraînement. Identique à `2-flows`. `Dur` seule classe les 13 sous-catégories
à **0,8957**, soit 5,0 fois le hasard.

Conséquence directe : la sélection à cinq méthodes du papier FPS (Table 10) a retenu **six de ces
six colonnes** parmi ses seize features multiclasses, et cinq parmi les seize binaires (Table 7).
Plus d'un tiers du budget retenu porte sur une seule quantité répétée.

**2. Les colonnes liées à la topologie sont intactes**, et c'est la fuite la plus forte du module.

| feature | 13 classes | 4 classes | binaire | valeurs distinctes |
|---|---|---|---|---|
| `Sdaddr` | **0,9947** (macro-F1 0,9102) | 0,9985 | 0,9985 | 76 |
| `Ssaddr` | 0,6192 | 0,8907 | 0,9398 | 85 |
| `Dport` | 0,5085 | 0,9838 | 0,9873 | 1 056 |
| `Sport` | 0,4530 | 0,8460 | 0,9058 | 63 705 |

`Sdaddr`, compteur HERA de connexions par service et adresse, **résout quasiment la tâche à 13
classes à elle seule**, avec 76 valeurs distinctes. Le papier FPS écrit pourtant que ces colonnes
« should be excluded to ensure model generalization across different environments », et les
exclut effectivement de ses expériences : le défaut porte sur **le module tel que distribué**,
pas sur leur protocole.

**3. Les cinq features de la zone grise τ\* sont présentes** (`SrcLoad`, `SrcRate`, `DstLoad`,
`Rate`, `Load`). `SrcLoad` seule : 0,8625.

## Témoin

`TotBytes`, feature comportementale légitime, atteint **0,9190**, au-dessus de `Dur`. Même
observation que sur `2-flows` (`DstBytes` 0,961 contre 0,922–0,963 pour les raccourcis) : le
pouvoir prédictif isolé ne sépare pas le raccourci du signal. Seul le comportement entre deux
protocoles le fait, et ce module ne permet pas de le mesurer, faute d'horodatage.

## Limite de cette inspection

Toutes les valeurs ci-dessus sont mesurées sous **le split aléatoire du module**, le seul
disponible. On peut donc rapporter un pouvoir prédictif isolé, mais pas une transférabilité τ :
sans horodatage, aucun protocole temporel n'est constructible sur `4-preprocessed`.

## Recommandation d'usage

Quiconque entraîne sur `4-preprocessed` devrait au minimum retirer
`Ssaddr`, `Sdaddr`, `Sport`, `Dport` et cinq des six colonnes de la famille de durée.
