# Concept shorts — TikTok series

Mini vidéos (15–30 s, 1080×1920, 30 fps), sans voix, avec seulement du sound design.
DA : fond noir, personnages-pictogrammes blancs lumineux, rouge en couleur d'accent
(ego, échec, douleur, ligne d'arrivée). Chaque concept est un petit bonhomme
avec son étiquette. Une punchline arrive au dénouement.

Tout est généré par code : animation vectorielle (Skia), bloom (OpenCV/numpy),
sons synthétisés (numpy), donc pas de droits d'auteur. La musique TikTok est
ajoutée ensuite dans l'app.

## Règles de la série

- Pas de phrase d'accroche : le hook est **visuel** (un moment de l'animation qui intrigue).
- Au début, seul texte : le nom du/des concept(s) (« OBSESSION » ou « EGO VS OBSESSION »).
- Punchline uniquement au dénouement.
- Pour chaque épisode : description TikTok + sondage en commentaire.

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
| 04 | Quitter vs Resilience | Hook « HE FELL 7 TIMES. WATCH WHAT HAPPENED. » Murs rouges FAILURE, REJECTION, DOUBT, BROKE, ALONE, LOSS, IMPOSSIBLE. Les deux tombent au premier, Quitter reste assis. Resilience se relève à chaque fois plus grand et lumineux, et pulvérise IMPOSSIBLE au ralenti. | FALL SEVEN TIMES. / STAND UP / EIGHT. | Every wall that knocked you down is a wall you'll break next time. #resilience #neverquit #discipline #mindset #comeback |
| 05 | Doubters vs Consistency | Titre en grand au centre. DAY 1 : un maigre rate son curl, lâche la barre sous les rires (HA rouges), reste triste tête basse, puis relève la tête et la reprend (onde de lumière). Montage jusqu'à DAY 1000 : il prend du muscle visiblement (biceps, épaules, pecs, cuisses), les doubters arrêtent de rire. Fin : photos, autographe, applaudissements. | THEY LAUGH AT DAY 1. / THEY CLAP AT / DAY 1000. | The same people who laughed will ask for a picture. #gym #glowup #consistency #gymmotivation #transformation |
| 06 | Ego vs Discipline vs Obsession | Hook visuel : caméra sur le sommet (drapeau rouge) puis plongée jusqu'au pied de 3 échelles géantes. Ego grimpe vite mais regarde en bas (lignes rouges), nargue, se fait dépasser, glisse et chute. Time-lapse jour/nuit : Discipline grimpe le jour et dort la nuit, Obsession ne s'arrête jamais et regarde le drapeau. Obsession au sommet, DAY 365, recul final. | EGO LOOKS DOWN. / DISCIPLINE LOOKS AHEAD. / OBSESSION LOOKS UP. | Ego looks down. Discipline looks ahead. Obsession looks up. #obsession #discipline #ego #mindset #stayhard |
| 07 | Ego vs Obsession — Ego gagne (boxe) | Hook visuel : noir total, un projecteur s'allume sur un ring. Round 1-2 : Obsession enchaîne les combos, uppercut au ralenti, Ego K.O. Compte rouge 1..9 : Obsession ne se repose pas, frappe dans le vide et s'épuise. À 6, la foule se moque et filme Ego au sol ; son orgueil s'allume (aura rouge), il se relève à 9. Round 3 : esquive au ralenti, un seul contre, K.O. | OBSESSION NEVER STOPS. / EGO NEVER STAYS DOWN. | Sometimes pride is the only thing that gets you back up. #ego #obsession #boxing #mindset #neverquit |
| 08 | Love vs Talent (→ Ego) | Titre LOVE (rouge) VS TALENT. LOVE offre des fleurs à HER, grand cœur rouge. TALENT arrive (étincelles), elle lâche le bouquet et part avec lui, le cœur se brise. Pluie, il tombe à genoux, tonnerre : l'étiquette LOVE glitche en EGO rouge. Montage DAY 1 → 365, prise de muscle, et des filles apparaissent une à une derrière lui. DAY 365 : il pose la barre, croise les bras, son EX arrive en courant et tombe à genoux ; Talent seul au fond. | SHE LEFT FOR TALENT. / HE CAME BACK AS / EGO. | She chose talent. He chose himself. #ego #glowup #heartbreak #gymmotivation #mindset |
| 09 | Ego vs Obsession (le miroir) | Écran partagé, chacun devant son miroir. Le reflet d'Ego est un bodybuilder parfait, celui d'Obsession petit et fissuré. Ego pose et fait des selfies pendant que son vrai corps prend du ventre ; Obsession s'entraîne, les fissures guérissent, le reflet grandit jusqu'à lui ressembler. Le miroir d'Ego glitche entre mensonge et vérité puis éclate en rouge. | EGO LOVES THE MIRROR. / OBSESSION BECOMES / THE REFLECTION. | Your mirror can lie. The scale, the bar and the years can't. #ego #obsession #glowup #gymmotivation #mindset |
| 10 | Talent vs Obsession (le prodige) | AGE 1 : bébé Talent marche déjà sous les applaudissements, bébé Obsession tombe. AGE 8/14/19 : trois courses gagnées par Talent (trophées), de plus en plus paresseux. AGE 20-24 : Talent fait la fête, ses trophées tombent et se brisent ; Obsession s'entraîne. AGE 25 : Talent abandonne, Obsession casse le ruban au ralenti, trophée rouge. | TALENT WAS BORN. / OBSESSION WAS / BUILT. | Talent gets you noticed. Obsession gets you remembered. #talent #obsession #mindset #discipline #grind |
| 11 | Comfort vs Obsession (le canapé) | Une horloge dont les aiguilles s'emballent, réveil 5h. Comfort sur son canapé avec son téléphone : le canapé l'avale un peu plus chaque année. Obsession court, soulève, travaille, grandit. YEAR 10 : Comfort ressort vieux, gris, avec une canne ; une couronne rouge apparaît au-dessus d'Obsession. | COMFORT IS / A SLOW / DEATH. | The couch never says no. That's the problem. #comfortzone #obsession #discipline #mindset #selfimprovement |
| 12 | Ego vs Discipline (l'argent) | Pluie de billets rouges, les deux reçoivent la même somme. Ego achète voiture, montre, soirées (cœurs), sa courbe monte puis s'écrase : voiture brisée, $0. Discipline met une pièce dans une boîte chaque année, un arbre pousse, sa courbe explose, une voiture arrive derrière lui. | EGO BUYS ATTENTION. / DISCIPLINE BUYS / FREEDOM. | Same money. Different decade. #money #discipline #ego #mindset #wealth |
| 13 | Fear vs Obsession (le saut) | Un caillou tombe dans le vide et n'atterrit jamais. Couronne rouge de l'autre côté. Obsession fixe la couronne, prend son élan, saute : une planche de lumière apparaît sous chaque pas, il prend la couronne. Fear s'approche du bord, des voix rouges (WHAT IF YOU FAIL?…) le font reculer ; les années passent, il vieillit au bord. | FEAR ASKS WHAT IF. / OBSESSION ASKS / WHEN. | The bridge only appears when you step. #fear #obsession #mindset #courage #stayhard |
| 14 | Dig (Motivation, Talent, Obsession, Ego) | Même déroulé que la référence, en DA noir/blanc/rouge : DIG!, Motivation abandonne (OUT), Talent s'arrête avec sa pièce (OUT), doutes sur les parois (I CAN'T / I'M A LOSER / I'M NOT BUILT FOR THIS), Obsession vire au rouge. Interlude : définition de dictionnaire « obsessed », YOU VS YOU, IT'S YOU VS YOU + Sisyphe dessiné. Obsession creuse comme un fou, Ego s'allonge sur son or, recul final sur le tas de diamants. | THEY ALL STOPPED. / OBSESSION KEPT DIGGING. | Most people quit 3 feet from the diamond. #obsession #discipline #mindset #neverquit #grind |

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
| 04 | How many times have you fallen this year? | 1–2 / 3–6 / 7+ / Lost count, still standing 💪 |
| 05 | Has anyone ever laughed at you in the gym? | Yes, and I kept going 💪 / Yes, and I quit / No, never / I was the one laughing 😬 |
| 06 | Which one are you right now? | Ego 👀 / Discipline 🧱 / Obsession 🔥 |
| 07 | Who wins in real life? | Ego 🥊 / Obsession 🔥 / Depends on the round |
| 08 | Would you take her back? | Never 🚫 / Maybe… / Depends how she asks |
| 09 | Who's in your mirror? | Ego 🪞 / Obsession 🔥 / Still cracked 😅 |
| 10 | Born with it or built it? | Talent 🧬 / Obsession 🔨 |
| 11 | How many hours on your phone today? | <2h / 2–5h / 5h+ 😬 |
| 12 | What would you do with $100K? | Car & watch 🚗 / Invest it 📈 / Start a business 🔥 |
| 13 | What's stopping your jump? | Fear of failing / What people think / Timing / Nothing, I jumped 🔥 |
| 14 | Where did you stop digging? | Motivation 💨 / Talent 🪙 / Ego 💰 / Still digging ⛏️ |
| 03 | Ever let your ego pick the weight? | Yes, and I paid for it 🤕 / Yes, still lucky / Never, form first

Sondages de réserve, réutilisables : *Which episode should be next?* (deux concepts à venir) ·
*What's stopping you right now?* (Ego / Comfort / Fear / Excuses)
