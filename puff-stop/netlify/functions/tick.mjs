// Tourne chaque minute : envoie la notif "taffe autorisée" quand l'heure est arrivée.
import { store, push } from "../lib/push.mjs";

export default async () => {
  const s = store();
  const now = Date.now();
  const { blobs } = await s.list();
  const wp = push();
  for (const { key } of blobs) {
    const rec = await s.get(key, { type: "json" });
    if (!rec || !rec.sub || !rec.items?.length) continue;
    const due = rec.items.filter((i) => i.t <= now && i.t > (rec.lastSent || 0));
    if (!due.length) continue;
    const it = due[due.length - 1];
    rec.lastSent = it.t;
    rec.items = rec.items.filter((i) => i.t > now);
    if (now - it.t < 10 * 60000) {
      try {
        await wp.sendNotification(
          rec.sub,
          JSON.stringify({ title: it.title || "Taffe autorisée", body: it.body || "" }),
          { TTL: 600, urgency: "high" }
        );
      } catch (e) {
        if (e.statusCode === 404 || e.statusCode === 410) rec.sub = null;
      }
    }
    await s.setJSON(key, rec);
  }
};

export const config = { schedule: "* * * * *" };
