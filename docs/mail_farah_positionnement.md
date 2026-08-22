# Mail à Madame Jemili — positionnement de l'article GeNIS

> Prêt à envoyer. Seule la formule de signature est à ajuster selon vos usages.

---

**Objet :** Article GeNIS — état d'avancement et positionnement par rapport à BagIDS

Madame,

Je reviens vers vous au sujet du second article, celui qui porte sur le
corpus GeNIS. Il est aujourd'hui à un état que je considère comme proche de
la soumission, et je voudrais surtout vous exposer le raisonnement qui m'a
conduit à le mener maintenant, juste après le dépôt de BagIDS, plutôt qu'à
un autre moment.

## 1. Ce que l'article établit

En une phrase : le corpus GeNIS, publié en 2025, contient un raccourci lié à
son calendrier de capture, et ce raccourci n'est pas retiré par le remède
habituel.

Le trafic bénin est capturé du 6 au 8 février, toutes les attaques du 10 au
12. La position d'un flux dans la capture prédit donc presque parfaitement sa
classe : un arbre de décision qui ne reçoit que l'horodatage classe les neuf
classes à **0,9970** d'exactitude, contre **0,1942** pour la classe
majoritaire. Huit colonnes comportementales portent la même information.

Le point qui fait l'article n'est pas ce constat, qui est attendu, mais les
deux suivants :

- **Le découpage temporel ne corrige pas le problème.** C'est pourtant la
  parade standard. Appliquée par classe, elle laisse la même sonde à
  **0,9862** : une classe occupe une seule fenêtre, donc ordonner les flux à
  l'intérieur de cette fenêtre ne peut pas casser l'association. Il faut
  exclure les colonnes, ce que fait la liste noire de treize variables que
  nous publions.
- **L'attribution ne voit pas le raccourci.** L'importance par permutation
  attribue une valeur inférieure à 1e-4 aux huit colonnes fautives, parce que
  leur information est dupliquée : perturber l'une ne coûte rien tant que sa
  jumelle reste disponible. Un audit fondé sur SHAP ou sur l'élimination
  récursive — c'est-à-dire la conception naturelle — les aurait donc
  conservées. C'est un résultat négatif, et c'est le seul qui se transporte
  hors de GeNIS.

L'article valide ce dernier point sur un second corpus, CICIDS2017 : le
raccourci d'horodatage s'y reproduit (0,9529 en stratifié, contre 0,8030 pour
la classe majoritaire), mais le découpage temporel l'y détruit (0,1028),
parce que le trafic bénin y court sur les cinq jours. La conclusion est donc
plus fine que celle que GeNIS seul permettait : *savoir si le découpage
temporel suffit est une propriété du calendrier de capture, pas de la
méthode* — et une sonde de deux lignes le mesure. On y retrouve aussi sept
paires de colonnes numériquement identiques, dont dix des quatorze scorent
exactement zéro en attribution.

Le tout repose sur 154 exécutions pour la campagne principale — onze
détecteurs supervisés plus un auto-encodeur, cinq graines, protocole gelé,
tests d'appariement — et sur 180 exécutions supplémentaires pour la
republication décrite au point 2e. L'artefact est déposé sur Zenodo sous
CC-BY 4.0.

## 2. Pourquoi cet article, et pourquoi maintenant

C'est le point sur lequel je voulais surtout votre avis. Cinq raisons, dans
l'ordre où elles pèsent pour moi.

**a. Séparer la contribution architecturale de la contribution
méthodologique.** Un article qui propose une architecture *et* redéfinit le
protocole d'évaluation sous lequel cette architecture gagne s'expose à une
objection légitime, et un relecteur la formule tôt ou tard. En publiant
l'audit comme un travail distinct, dont les conclusions ne dépendent d'aucune
de nos architectures — la liste noire est établie par une règle qui ne
connaît pas le modèle qu'elle servira —, on retire cette objection avant
qu'elle ne soit posée. C'est la raison principale, et elle impose l'ordre :
l'audit doit exister séparément, pas être un paragraphe de méthode dans
BagIDS.

**b. Les deux corpus de BagIDS sont exactement les deux que l'article audite,
et ils tombent de part et d'autre de la question.** C'est le point que je n'ai
compris qu'en écrivant la section 7, et il transforme l'argument de l'ordre en
argument de nécessité.

BagIDS est évalué sur CICIDS2017 et validé sur GeNIS. Or ce sont précisément
les deux corpus sur lesquels l'article mesure la même chose, et la réponse
n'est pas la même :

- **Sur CICIDS2017, le découpage temporel suffit.** La sonde d'horodatage y
  tombe de 0,9529 à 0,1028, sous le taux de la classe majoritaire. Nous
  pouvons donc *affirmer avec une mesure à l'appui* que les chiffres de
  détection de BagIDS ne reposent pas sur un raccourci de calendrier, à la
  condition que le protocole soit chronologique. Sous découpage aléatoire, en
  revanche, le raccourci y est bien présent — 0,9529 contre 0,8030 — et cela
  vaut pour n'importe quel travail sur ce corpus, pas seulement le nôtre.
- **Sur GeNIS, il ne suffit pas.** C'est tout le résultat de l'article. Une
  validation conduite sur GeNIS sous découpage aléatoire, ou même sous
  découpage temporel sans exclusion de colonnes, mesure en partie le
  calendrier de capture. La liste de treize colonnes s'y applique directement,
  et son coût est mesuré : au plus **0,0018** de macro-F1 sous découpage
  aléatoire pour les douze premières colonnes et **0,0038** pour la
  treizième, contre **0,0263** sous protocole temporel. C'est cette asymétrie
  d'un facteur sept qui signe le raccourci, et c'est elle qui rend la
  correction peu coûteuse là où elle compte pour la validité.

Deux vérifications concrètes en découlent, et elles prennent quelques minutes
chacune. La première : **quelle distribution de CICIDS2017 BagIDS utilise.**
La version `MachineLearningCVE` porte 79 colonnes et aucun horodatage, donc
les colonnes fautives en sont absentes par construction ; la version
`GeneratedLabelledFlows` en porte 85 et les contient. L'article note déjà que
notre étude comparative de 2023 (AMCAI) utilisait la première, et n'est donc
pas concernée. La seconde : **les sept paires de colonnes identiques de
CICIDS2017.** Si BagIDS comporte une étape de sélection de variables fondée
sur l'importance, elle les a conservées — dix des quatorze scorent exactement
zéro.

Mieux vaut que ce soit nous qui établissions tout cela, avec les chiffres,
que de le découvrir dans un rapport de relecture ou, pire, après publication.

**c. Fixer la provenance des détecteurs.** Le RNN, le CNN et le DNN
réutilisés dans BagIDS viennent de notre étude comparative de 2023 (AMCAI).
L'article GeNIS les reproduit à l'identique — architectures, hyperparamètres,
graines, découpages, coût CPU — et sert donc de **dossier de provenance
citable** pour ces trois détecteurs. Sans lui, les lignes de base de BagIDS
renvoient à un article de conférence de six pages qui ne peut pas porter ce
niveau de détail.

**d. La fenêtre sur GeNIS est ouverte maintenant.** GeNIS est sorti en 2025 ;
ses chiffres de référence ne sont pas encore fixés. À ce stade d'un corpus, le
premier protocole publié est celui que la communauté reprend. Si nous
attendons, l'une de deux choses arrive : quelqu'un d'autre publie l'audit, ou
bien des classements saturés s'accumulent et il faudra ensuite les défaire.
CICIDS2017 a mis presque une décennie à être corrigé, et c'est exactement
cette histoire que la section 2 de l'article raconte.

**e. Le travail est fait, et il a résisté à son propre audit.** Les
expériences sont mesurées, l'artefact est déposé, le rapport de relecture
interne est traité. Je dois vous signaler un épisode que l'article rapporte en
section 9 plutôt que de le taire, parce qu'il est à mon avis ce qui rend le
travail solide.

En auditant ma propre règle, j'ai découvert qu'elle avait un angle mort et que
le corpus en contenait un cas : une colonne, `IdleTime`, est en réalité un
identifiant de fichier de capture — ses valeurs séparent parfaitement le bénin
de l'attaque — et ma règle de transférabilité ne pouvait pas la voir, parce
qu'un identifiant figé à l'intérieur d'un groupe de capture ne perd rien en
passant d'un protocole à l'autre. Elle se trouvait dans la condition auditée
de la campagne publiée. J'ai donc ajouté un troisième critère, qui ne lit
aucune étiquette, **rejoué toute la campagne sans cette colonne** — 180
exécutions — et mesuré ce que l'omission coûtait plutôt que de le supposer.

Aucune conclusion de l'article ne tombe, et l'une se renforce : sous la liste
corrigée, les deux ensembles boostés quittent le sommet du classement
temporel encore plus nettement qu'avant. Trois scripts de vérification
rejouent l'ensemble depuis les fichiers de résultats et passent 37 contrôles
sur 37. Attendre davantage ne réduit plus aucun risque ; c'est plutôt le
contraire.

Autrement dit, l'ordre des deux articles n'est pas un ordre d'importance mais
un ordre de dépendance : BagIDS répond à « ce détecteur fonctionne-t-il ? »,
l'article GeNIS répond à « sur quel terrain cette question se tranche-t-elle ? ».
Le second ne dépend pas du premier et tient seul ; le premier gagne à pouvoir
citer le second.

## 3. Où en est le manuscrit

12 sections, 20 figures, 16 tableaux, un algorithme, 34 références,
~24 000 mots. Trois scripts de vérification tournent sur le document lui-même
et ne signalent plus rien : cohérence interne (toute figure et tout tableau
appelés dans le texte, numérotation continue, ordre de première citation
croissant), passe stylistique, et mise en page sur le document rendu.
Toutes les valeurs citées dans le texte sont rejouées depuis les fichiers de
résultats par des scripts versionnés.

## 4. Ce que je vous demande

1. **Votre lecture**, en particulier sur les sections 7 (validation externe
   sur CICIDS2017) et 8 (discussion), qui portent les conclusions
   méthodologiques.
2. **Une vérification bibliographique.** Sept références n'ont pas pu être
   confirmées contre les registres éditeurs depuis mon environnement de
   travail ; un passage sur Scopus ou Web of Science les lèverait. Je vous
   envoie la liste exacte si vous le souhaitez.
3. **Votre avis sur la revue visée.** Mon idée est **Computers & Security**
   (Elsevier). Trois raisons. C'est là qu'est paru en 2025 le plus proche
   parent de notre article, le panorama de Goldschmidt et Chudá sur les
   limites des corpus d'intrusion et les recommandations qui en découlent :
   le lectorat de cette revue est exactement celui que ce résultat concerne.
   Elle accueille les articles longs adossés à un artefact, ce qui compte pour
   un texte de 24 000 mots avec 20 figures et 16 tableaux. Et elle est indexée
   Scopus et Web of Science, ce qui compte pour un chapitre de thèse. En
   solution de repli chez le même éditeur, le *Journal of Information Security
   and Applications* ; et si vous préférez une revue qui sollicite
   explicitement les résultats négatifs et les artefacts de reproductibilité,
   *ACM Digital Threats: Research and Practice* conviendrait au profil de
   l'article, avec un lectorat plus étroit.

Je reste bien entendu disponible pour en discuter de vive voix.

Je vous remercie de votre suivi et vous prie d'agréer, Madame, l'expression
de ma considération respectueuse.

Mohamed Ali Elhadj Bahri
