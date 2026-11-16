# Puff Stop

Appli web installable (PWA) pour arrêter la puff progressivement.
En ligne : https://puff-stop-907558.netlify.app

- `public/` : l'appli (tout l'historique reste dans le téléphone, localStorage).
- `netlify/functions/sync.mjs` : reçoit l'abonnement push + les heures des prochaines taffes autorisées.
- `netlify/functions/backup.mjs` : sauvegarde / restauration des données avec un code de 10 caractères (store `puffstop-backup`).
- `netlify/functions/tick.mjs` : tâche planifiée chaque minute, envoie la notif quand l'heure arrive.
- Variables Netlify : `VAPID_PUBLIC`, `VAPID_PRIVATE`, `VAPID_SUBJECT` (la clé publique est aussi dans `public/app.js`).

Plan par sessions : session du réveil et du coucher (10 taffes au départ), et entre les deux 5 taffes toutes les 10 min.
L'écart grandit de façon géométrique jusqu'à 4 h (10 → 11 → 12 … → 15 min à J8), les tailles baissent linéairement ; arrêt après 35 / 56 / 84 jours.

Après le plan : mode « libre » (compteur, caps, bouton SOIRÉE, notifs de soutien 14 jours puis vendredi/samedi soir pendant 4 mois).

Notifs programmées sur 6 jours (sessions, soutien après l'arrêt, suivi de l'état à 21h15). ENVIE guidé selon le déclencheur, suivi de l'état (sommeil, humeur, énergie, manque), horaires du week-end.

Redéployer : `npm install && netlify deploy --prod --dir public --functions netlify/functions --no-build`
