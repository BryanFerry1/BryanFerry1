# Concept shorts — TikTok series

Mini vidéos (15–30 s, 1080×1920, 30 fps), sans voix, avec seulement du sound design.
DA : fond noir, personnages-pictogrammes blancs lumineux, rouge en couleur d'accent
(ego, échec, douleur, ligne d'arrivée). Chaque concept est un petit bonhomme
avec son étiquette. Une punchline arrive au dénouement.

Tout est généré par code : animation vectorielle (Skia), bloom (OpenCV/numpy),
sons synthétisés (numpy), donc pas de droits d'auteur. La musique TikTok est
ajoutée ensuite dans l'app.

## Rendu

```bash
pip install skia-python opencv-python-headless numpy pillow   # + libegl1 (apt)
python ep01_motivation_vs_discipline.py --stills   # images d'aperçu dans out/
python ep01_motivation_vs_discipline.py            # vidéo finale -> out/*.mp4
```

## Épisodes

| # | Titre | Scène | Punchline | Description TikTok |
|---|-------|-------|-----------|--------------------|
| 01 | Motivation vs Discipline | Escalier. Motivation sprinte, s'éteint en rouge et se désagrège. Discipline monte marche par marche jusqu'au drapeau rouge. Compteur DAY 1 → 365. | MOTIVATION GETS YOU STARTED. / DISCIPLINE GETS YOU THERE. | Motivation fades after a week. Discipline shows up on day 365. #discipline #motivation #mindset #consistency #stayhard |
| 02 | Ego vs Obsession | Course en écran partagé. En haut, Ego fixe ses rivaux (ligne rouge), son rang change sans cesse, il trébuche en regardant derrière lui. En bas, Obsession dépasse son fantôme YESTERDAY, jour après jour, de plus en plus vite. | EGO COMPETES WITH OTHERS. / OBSESSION COMPETES WITH YESTERDAY. | Stop checking who's behind you. Start beating who you were yesterday. #obsession #ego #discipline #mindset #selfimprovement |
| 03 | Ego vs Discipline (gym) | Hook « ONE OF THEM IS ABOUT TO GET HURT. » Développé couché. En haut, Ego charge jusqu'à 180 kg devant une foule qui filme et se fait écraser par la barre. En bas, Discipline ajoute un disque par semaine jusqu'à WEEK 52 et 180 kg. | LEAVE YOUR / EGO / AT THE DOOR. | They came to watch you lift. Nobody stayed to watch you heal. #gym #ego #discipline #gymmotivation #mindset |

## Scénarios proposés (prochains épisodes)

1. **Ego vs Growth — la montagne.** Les deux grimpent. Ego, rouge, s'arrête tous les
   trois pas pour regarder derrière lui s'il est devant. Growth ne regarde que la paroi.
   Ego finit par pousser Growth : il perd l'équilibre et tombe dans le vide.
   *"EGO WANTS TO LOOK GOOD. GROWTH WANTS TO GET GOOD."*
2. **Comfort vs Obsession — les poids.** Une barre posée sur chaque épaule. Compteur de
   jours. Comfort pose la barre au premier tremblement et s'assoit sur un canapé
   lumineux qui l'absorbe peu à peu. Obsession tremble, tombe à genoux, se relève,
   et la barre s'allège (les disques disparaissent un à un). Révélation finale :
   Obsession porte maintenant le double.
   *"COMFORT IS A SLOW DEATH."*
3. **Talent vs Consistency — la course.** Talent part comme une flèche, se retourne,
   voit qu'il a de l'avance et s'endort. Consistency, au même rythme métronomique
   (tic-tac), le dépasse. Le chrono s'affiche en rouge sur Talent.
   *"TALENT IS A HEAD START. CONSISTENCY IS THE FINISH LINE."*
4. **Excuses vs Action — le mur.** Un mur gigantesque. Excuses empile des pancartes
   ("TOMORROW", "NO TIME", "TOO HARD") qui deviennent un mur encore plus haut devant
   lui. Action pose une brique, puis une autre, et en fait un escalier.
   *"EXCUSES BUILD WALLS. ACTION BUILDS STAIRS."*
5. **Fear vs Courage — le pont.** Un pont de lumière se construit sous chaque pas, mais
   seulement quand on avance. Fear attend que le pont existe avant de marcher et reste
   bloqué au bord. Courage avance dans le vide, et le pont apparaît sous ses pieds.
   *"THE BRIDGE APPEARS WHEN YOU STEP."*
6. **Patience vs Ego — la graine.** Les deux plantent une graine. Ego creuse tous les
   jours pour vérifier si elle pousse : la sienne meurt (rouge). Patience arrose
   seulement, et un arbre lumineux finit par recouvrir l'écran.
   *"GROWTH IS INVISIBLE UNTIL IT ISN'T."*
7. **The Crowd vs You — le flux.** Une foule de bonhommes gris marche vers la gauche.
   Un seul, blanc, marche à contre-courant vers une lumière rouge et se fait bousculer
   à chaque pas.
   *"IF IT FEELS LONELY, YOU'RE PROBABLY ON THE RIGHT PATH."*

## Sondages (commentaires)

| # | Question | Options |
|---|----------|---------|
| 01 | Be honest… which one are you? | Motivation 🔥 / Discipline 🧱 / Trying to become Discipline |
| 02 | Who are you racing? | Other people 👀 / Yesterday's me 👻 |
| 03 | Ever let your ego pick the weight? | Yes, and I paid for it 🤕 / Yes, still lucky / Never, form first

Sondages de réserve, réutilisables : *Which episode should be next?* (deux concepts à venir) ·
*What's stopping you right now?* (Ego / Comfort / Fear / Excuses)
