# =========================================================================
# Lanceur — recupere les cellules E8 depuis le depot et les execute
# =========================================================================
# A coller dans une NOUVELLE cellule du notebook e8_republication, apres
# avoir execute les cellules 1 a 6 (Execution > Tout executer suffit).
#
# Pourquoi un lanceur plutot qu'un copier-coller : ces cellules ont ete
# corrigees plusieurs fois (objectif du calage, epinglage du CPU, temoins).
# Coller une version datee et ne pas savoir laquelle tourne est exactement le
# genre d'incertitude que ce travail cherche a eliminer. Ici la source est le
# depot, la revision est affichee, et une correction se reprend en relancant.
#
# Les scripts s'executent dans l'espace de noms du notebook : ils y trouvent
# STATE, save_state, kfile, SPLITS, X, y, COLS, make_sk, NEURAL, tf, keras.
import time
import urllib.request

DEPOT = "bahriala2/GeNIS2025"
BRANCHE = "claude/manuscript-e2-e3-sections-87snff"
# Les deux premieres appartiennent au notebook e8_republication ; la
# troisieme au notebook e5_intervalles_cinq_graines, et elle echouera si on
# la lance depuis l'autre. Lancez-la separement, depuis le bon notebook.
ETAPES = [
    ("e8ter_cout_deux_conditions",
     "cout d'inference, les deux conditions, mesure sur CPU"),
    ("e8quater_stats_mcnemar_bootstrap",
     "McNemar et bootstrap, pour les figures 9 et 11"),
]
ETAPES_E5 = [
    ("e9_intervalles_six_detecteurs",
     "robustesse a l'intervalle, six detecteurs de plus"),
]

for nom, quoi in ETAPES:
    url = (f"https://raw.githubusercontent.com/{DEPOT}/{BRANCHE}/colab/"
           f"{nom}.py?t={int(time.time())}")          # ?t= : evite le cache
    code = urllib.request.urlopen(url).read().decode("utf-8")
    print("=" * 70)
    print(f"{nom} — {quoi}")
    print(f"{len(code.splitlines())} lignes recuperees")
    print("=" * 70, flush=True)
    exec(compile(code, nom, "exec"), globals())
    print()

print("Termine. Renvoie e8_results.json.")
print()
print("Pour E9, meme cellule mais dans le notebook e5_intervalles_cinq_graines,")
print("en remplacant ETAPES par ETAPES_E5. Elle renvoie e5_results.json.")
