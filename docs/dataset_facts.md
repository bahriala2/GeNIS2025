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
2. **Discordance à vérifier** : Table 12 du descripteur donne benign-background = 10 286 à 60 s ;
   notre chargement de `2-flows` en montre 8 283 (écart 2 003). Recompter depuis les fichiers,
   trancher, et déclarer dans le papier quels chiffres font foi. (Total descripteur 60 s : 368 556
   avec recon ; notre tranche : 338 820 sans recon.)
3. Table 12 (descripteur), totaux par intervalle : 5 s = 2 806 168 ; 10 s = 1 504 184 ;
   30 s = 607 933 ; 60 s = 368 556 (recon inclus).
4. `4-preprocessed` (split shuffle+stratifié des auteurs) est le candidat naturel pour **E1**
   (comparaison ancrée avec Silva et al.) — à télécharger si E1 exact devient nécessaire.
5. `3-scenarios` = flux séquentiels réalistes par scénario : piste d'**évaluation temporelle
   réaliste** supplémentaire (option, hors périmètre v1 de l'article).
6. Limitations admises par les auteurs : attaques limitées à certaines machines, bénin sans la
   variabilité d'un réseau réel — à reprendre dans Threats to Validity.
