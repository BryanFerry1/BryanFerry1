# Puff Stop

Appli web installable (PWA) pour arrêter la puff progressivement.
En ligne : https://puff-stop-907558.netlify.app

- `public/` : l'appli (tout l'historique reste dans le téléphone, localStorage).
- `netlify/functions/sync.mjs` : reçoit l'abonnement push + les heures des prochaines taffes autorisées.
- `netlify/functions/tick.mjs` : tâche planifiée chaque minute, envoie la notif quand l'heure arrive.
- Variables Netlify : `VAPID_PUBLIC`, `VAPID_PRIVATE`, `VAPID_SUBJECT` (la clé publique est aussi dans `public/app.js`).

Plan : écart entre deux taffes = écart de départ × (240 / écart de départ)^((jour/(N-1))^1.35),
N = 35 / 56 / 84 jours selon le rythme, puis arrêt complet. La courbe bouge très peu au début.

Redéployer : `npm install && netlify deploy --prod --dir public --functions netlify/functions --no-build`
