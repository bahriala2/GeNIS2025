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
