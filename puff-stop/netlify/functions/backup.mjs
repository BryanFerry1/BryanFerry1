// Sauvegarde / restauration des données de l'appli avec un code de récupération.
import { backupStore } from "../lib/push.mjs";

const CODE = /^[A-Z0-9]{10}$/;

export default async (req) => {
  const s = backupStore();
  if (req.method === "GET") {
    const code = (new URL(req.url).searchParams.get("code") || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (!CODE.test(code)) return new Response("Code invalide", { status: 400 });
    const rec = await s.get("bk_" + code, { type: "json" });
    return rec ? Response.json(rec) : new Response("Introuvable", { status: 404 });
  }
  if (req.method === "POST") {
    const text = await req.text();
    if (text.length > 3_000_000) return new Response("Trop gros", { status: 413 });
    let body;
    try { body = JSON.parse(text); } catch { return new Response("Bad JSON", { status: 400 }); }
    const { code, data } = body || {};
    if (!CODE.test(code || "") || !data || !data.setup) return new Response("Bad request", { status: 400 });
    await s.setJSON("bk_" + code, { at: Date.now(), data });
    return Response.json({ ok: true, at: Date.now() });
  }
  return new Response("Method not allowed", { status: 405 });
};

export const config = { path: "/api/backup" };
