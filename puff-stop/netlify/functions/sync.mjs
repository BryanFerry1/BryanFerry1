// Reçoit l'abonnement push + le planning des prochaines taffes autorisées.
import { store, push } from "../lib/push.mjs";

const clean = (items) =>
  (Array.isArray(items) ? items : [])
    .filter((i) => i && Number.isFinite(i.t))
    .slice(0, 500)
    .map((i) => ({ t: i.t, title: String(i.title || "").slice(0, 80), body: String(i.body || "").slice(0, 200) }));

export default async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  let data;
  try { data = await req.json(); } catch { return new Response("Bad JSON", { status: 400 }); }
  const { id, sub, items, test } = data || {};
  if (typeof id !== "string" || !/^[\w-]{8,64}$/.test(id)) return new Response("Bad id", { status: 400 });

  const s = store();
  const prev = (await s.get(id, { type: "json" })) || {};
  const rec = {
    sub: sub && sub.endpoint ? sub : prev.sub || null,
    items: items ? clean(items) : prev.items || [],
    lastSent: prev.lastSent || 0,
    updated: Date.now(),
  };
  if (sub === false) rec.sub = null; // désactivation
  await s.setJSON(id, rec);

  if (test && rec.sub) {
    try {
      await push().sendNotification(
        rec.sub,
        JSON.stringify({ title: "Notifications OK ✅", body: "Tu seras prévenu quand tu as droit à une taffe." }),
        { TTL: 300, urgency: "high" }
      );
    } catch (e) {
      return Response.json({ ok: false, error: String(e.statusCode || e.message) }, { status: 502 });
    }
  }
  return Response.json({ ok: true, scheduled: rec.items.length });
};

export const config = { path: "/api/sync" };
