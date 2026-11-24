# CPTS Entre Doubs et Jura – « Trouver un médecin traitant avec Doctolib »

Tutoriel vidéo 16:9 (1920×1080, 30 fps, environ 54 s). C'est la version réanimée du projet Canva
« Étapes Recherche Médecin Traitant ».

- **Visuels** : personnages animés, captures Google / Doctolib, bulles, fond et logos, repris du
  design Canva. Ils sont exportés sur fond vert depuis une copie de travail (le design original n'a
  pas été modifié), puis détourés par `extract_layers.py`.
- **Voix off** : ElevenLabs, voix « Bella » (multilingual v2, réglage plus dynamique), générée
  phrase par phrase avec l'horodatage mot à mot (`assets/voice/`). Tout est synchronisé sur ces
  horodatages : texte, clics, frappe au clavier, zooms.
- **Motion design et sons** : `make_video.py` (caméra avec zooms, curseur, frappe, coches,
  confettis, sous-titres, badge « ÉTAPE n », petite musique ukulélé synthétisée, bruitages).
- **Police** : Fredoka (SIL Open Font License, `assets/fonts/OFL.txt`).

## Rendu

```bash
python cpts-video/extract_layers.py         # une seule fois : assets/raw -> assets/layers (environ 420 Mo, non versionné)
python cpts-video/make_video.py --stills    # planche de contrôle -> out/stills.png
python cpts-video/make_video.py             # -> out/cpts_medecin_traitant.mp4 (+ version sans musique)
```

## Texte de la voix off

1. Vous recherchez un médecin traitant ?
2. Prenez votre ordinateur et suivez-moi ! Nous allons vous expliquer comment effectuer votre demande en quelques étapes simples.
3. Tout d'abord, ouvrez votre navigateur Internet et tapez « Doctolib » dans la barre de recherche.
4. Une fois sur le site Doctolib, recherchez « CPTS Entre Doubs et Jura ».
5. Cliquez ensuite sur « Faire une autre demande ».
6. Attention, pour poursuivre votre démarche, vous devez vous connecter à votre compte Doctolib ou en créer un si vous n'en possédez pas encore.
7. Vous accéderez ensuite à un questionnaire. Prenez le temps de répondre à toutes les questions, puis validez votre demande.
8. Et voilà ! Votre demande est envoyée.
9. Notre équipe va maintenant la traiter afin de vous accompagner dans votre recherche de médecin traitant.
10. À bientôt !
