'use strict';
/* Puff Stop — arrêt progressif de la puff, par sessions.
   Une session = quelques taffes d'un coup. L'écart entre sessions s'allonge chaque jour,
   la taille des sessions baisse doucement. Session du réveil et du coucher gardées (plus grosses).
   Tout l'état est dans localStorage ; le serveur ne reçoit que l'abonnement push + les heures des notifs. */

const VAPID_PUBLIC = 'BOyUJLsn15HycNpq7-HFcleTZ4OOidJUnvEL7ud3gukZfyhU45Ih7Xtg9719s3qzv97C7rsYeV60sxdNL6YWAjU';
const KEY = 'puffstop.v1';
const MIN = 60000, DAY = 86400000;
const I_END = 240;        // écart final entre sessions (min)
const BED_BEFORE = 30;    // session du coucher : 30 min avant l'heure du coucher
const HALF_LIFE = 120;    // demi-vie de la nicotine ≈ 2 h
const PACES = {
  doux:   { days: 84, name: 'Doux',   desc: '12 semaines · ça bouge très lentement' },
  normal: { days: 56, name: 'Normal', desc: '8 semaines · recommandé' },
  rapide: { days: 35, name: 'Rapide', desc: '5 semaines · si tu es très motivé' },
};
const KIND = { wake: '☀️ Session du réveil', reg: '🟢 Session', meal: '🍽️ Session après le repas', sleep: '🌙 Session du coucher' };
const REG_STOP = 0.85; // sur la fin du plan, il ne reste que les moments clés (réveil, repas, coucher)

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

/* ---------- état ---------- */
function load() {
  try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.id) return s; } catch {}
  return { id: (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()), setup: null, log: [], holds: [], puffStart: null, notif: 'all' };
}
let S = load();
if (S.setup && !S.setup.v2) { // migration vers le mode sessions
  Object.assign(S.setup, { v2: true, baseInterval: 10, sessionSize: 5, edgeSize: 10 });
  S.log = S.log.map((e) => ({ ...e, n: e.n || 1, kind: e.kind || 'reg' }));
}
if (S.setup && S.setup.lunch === undefined) Object.assign(S.setup, { lunch: '13:00', dinner: '20:30' });
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} }
save();

/* ---------- temps ---------- */
const hm = (s) => { const [h, m] = s.split(':').map(Number); return h * 60 + m; };
function geo() {
  const wm = hm(S.setup.wake); let sm = hm(S.setup.sleep);
  if (sm <= wm) sm += 1440;
  const W = sm - wm, night = 1440 - W;
  const bnd = (sm + night / 2) % 1440;           // milieu de la nuit = changement de jour
  const off = ((wm - bnd) % 1440 + 1440) % 1440;
  return { W, night, bnd, off };
}
function dayStart(t) {
  const { bnd } = geo(); const d = new Date(t); d.setHours(0, 0, 0, 0);
  let s = d.getTime() + bnd * MIN; if (s > t) s -= DAY; return s;
}
const ymd = (t) => { const d = new Date(t); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
const dayKey = (t) => ymd(dayStart(t) + geo().off * MIN);
function win(t) { const g = geo(); const ws = dayStart(t) + g.off * MIN, we = ws + g.W * MIN; return { ws, we, ss: Math.max(ws + MIN, we - BED_BEFORE * MIN) }; }
const nextDayRef = (t) => win(t).we + (geo().night / 2 + 1) * MIN;
const dayIndex = (t) => Math.round((dayStart(t) - dayStart(S.setup.start)) / DAY);
function planDay(t) { const k = dayKey(t); return dayIndex(t) - S.holds.filter((h) => h <= k).length; }
const N = () => PACES[S.setup.pace].days;

/* ---------- plan ---------- */
function planAt(d) {
  const n = N(), st = S.setup;
  if (d >= n) return { free: true, I: Infinity, reg: 0, edge: 0 };
  const x = Math.max(0, d) / (n - 1);
  const I0 = st.baseInterval;
  const I = I0 * Math.pow(Math.max(I_END, I0 * 2) / I0, x);            // 10 → 10,6 → 11,2 → … → 4 h
  const regEnd = Math.max(1, Math.round(st.sessionSize * 0.4));
  const edgeEnd = Math.max(1, Math.round(st.edgeSize * 0.3));
  const reg = Math.max(1, Math.round(st.sessionSize + (regEnd - st.sessionSize) * x));
  const edge = Math.max(reg, Math.round(st.edgeSize + (edgeEnd - st.edgeSize) * x));
  if (x > REG_STOP) return { I: Infinity, reg: 0, edge, keyOnly: true };
  return { I, reg, edge };
}
/* moments clés de la journée : réveil (ws), après les repas, coucher (ss) */
function mealTimes(w) {
  const wm = hm(S.setup.wake);
  return ['lunch', 'dinner'].filter((k) => S.setup[k]).map((k) => w.ws + (((hm(S.setup[k]) - wm) % 1440 + 1440) % 1440) * MIN)
    .filter((t) => t > w.ws + 30 * MIN && t < w.ss - 30 * MIN).sort((a, b) => a - b);
}
function dayWin(ref) { const w = win(ref); w.meals = mealTimes(w); return w; }
function nextIn(prevT, w, p) { // prochain créneau dans la même journée
  const m = w.meals.find((x) => x > prevT);
  const half = isFinite(p.I) ? p.I * MIN / 2 : 0;
  const regT = isFinite(p.I) ? prevT + p.I * MIN : Infinity;
  const limit = m !== undefined ? m : w.ss;           // prochain moment clé
  if (regT < limit - half) return { t: regT, kind: 'reg' };
  if (m !== undefined) return { t: m, kind: 'meal' };
  return { t: Math.max(w.ss, prevT), kind: 'sleep' };
}
function daySlots(ref, p) {
  const w = dayWin(ref), out = [{ t: w.ws, kind: 'wake' }];
  for (let g = 0; g < 300; g++) { const s = nextIn(out[out.length - 1].t, w, p); out.push(s); if (s.kind === 'sleep') break; }
  return out.map((s) => ({ ...s, size: s.kind === 'reg' ? p.reg : p.edge }));
}
function dayCounts(d) { // sessions/taffes prévues sur une journée complète
  const p = planAt(d); if (p.free) return { sessions: 0, taffes: 0, regN: 0, keyN: 0, p };
  const sl = daySlots(Date.now(), p), regN = sl.filter((s) => s.kind === 'reg').length;
  return { sessions: sl.length, taffes: taffes(sl.map((s) => ({ n: s.size }))), regN, keyN: sl.length - regN, p };
}
const baselinePerDay = () => dayCounts(0).taffes;
const mlPerTaffe = () => S.setup.mlPerPuff / (S.setup.daysPerPuff * baselinePerDay());
const sessionsOf = (k) => S.log.filter((e) => dayKey(e.t) === k);
const taffes = (list) => list.reduce((s, e) => s + (e.n || 1), 0);

function mk(t, kind) {
  const p = planAt(planDay(t)); if (p.free) return { free: true };
  return { t, kind, size: kind === 'reg' ? p.reg : p.edge, I: p.I };
}
function slotAfter(prevT, prevKind) {
  if (prevKind === 'sleep') return mk(win(nextDayRef(prevT)).ws, 'wake');
  const p = planAt(planDay(prevT)); if (p.free) return { free: true };
  const s = nextIn(prevT, dayWin(prevT), p);
  return mk(s.t, s.kind);
}
function nextAllowed(now = Date.now()) {
  if (planAt(planDay(now)).free) return { free: true };
  const list = sessionsOf(dayKey(now)), { ws, we } = win(now);
  if (!list.length) return now < we ? mk(ws, 'wake') : mk(win(nextDayRef(now)).ws, 'wake');
  const last = list[list.length - 1];
  return slotAfter(last.t, last.kind);
}
function upcoming(now, horizon) {
  const out = []; let s = nextAllowed(now), g = 0;
  while (s && !s.free && s.t < horizon && g++ < 400) { out.push(s); s = slotAfter(s.t, s.kind); }
  return out;
}
const remainingToday = (now) => { const k = dayKey(now); return upcoming(now, now + 2 * DAY).filter((s) => dayKey(s.t) === k); };

/* ---------- après l'arrêt ---------- */
const H = 3600000;
const MILESTONES = [
  [24 * H, '24 heures', "La nicotine a presque entièrement quitté ton sang."],
  [72 * H, '72 heures', "Le pic du manque est derrière toi. À partir de là, ça ne fait que descendre."],
  [7 * DAY, '1 semaine', "Les envies deviennent plus courtes et plus espacées."],
  [14 * DAY, '2 semaines', "Ton sommeil et ton énergie se stabilisent."],
  [30 * DAY, '1 mois', "Ton cerveau s'est en grande partie réhabitué à vivre sans nicotine."],
  [60 * DAY, '2 mois', "C'est là que t'avais craqué la dernière fois. Cette fois, tu passes."],
  [90 * DAY, '3 mois', "Les envies sont rares. Le vrai risque, c'est les situations : reste vigilant en soirée."],
  [180 * DAY, '6 mois', "La puff ne fait plus partie de ta vie. Tu es non-vapoteur."],
  [365 * DAY, '1 an', "Un an libre. Ce que t'as fait là, peu de gens y arrivent."],
];
const FREE_QUOTES = [
  ["C'est jamais « juste une »", "Avec du 20 mg, une seule taffe suffit à relancer toute la machine. Ton meilleur allié, c'est le « non » de la première."],
  ["Le manque n'est plus là", "Ce qui reste, ce sont des réflexes : après manger, en soirée, quand t'es stressé. Ils s'effacent un peu plus chaque fois que tu ne cèdes pas."],
  ["L'envie passe", "Même après des semaines, une envie peut surgir d'un coup. Elle dure quelques minutes, puis elle repart. Laisse-la passer."],
  ["T'as déjà fait le plus dur", "Des semaines de baisse, jour après jour. Tu ne vas pas tout rendre pour une taffe en soirée."],
  ["Ton entourage", "Tu n'as pas à te justifier. « Non merci, j'ai arrêté », ça suffit."],
  ["Ta liberté", "Plus de puff à recharger, à acheter, à chercher. Plus de panique quand elle est vide."],
];
const PARTY = {
  answers: ["« Non merci, j'ai arrêté. »", "« Je suis à {d}, je vais pas tout gâcher pour une taffe. »", "« Nan, j'suis bien sans. »"],
  tips: ["Garde un verre (soft de préférence) en main : mains occupées, moins de réflexe.",
    "Si un pote vapote à côté de toi, bouge : l'odeur et le geste déclenchent l'envie.",
    "L'alcool baisse la vigilance : c'est là que « juste une taffe » arrive. Décide avant de sortir.",
    "Dis-le à un pote de confiance avant la soirée : il t'aidera à tenir.",
    "Une taffe de 20 mg relance tout. C'est jamais « juste une »."],
};
function freeSince() {
  const last = S.log[S.log.length - 1];
  return last ? last.t : planEnd();
}
const perDayCost = () => S.setup.price / S.setup.daysPerPuff;
function fmtFree(ms) {
  const d = Math.floor(ms / DAY);
  return d >= 1 ? d + (d > 1 ? ' jours' : ' jour') : Math.floor(ms / H) + ' h';
}
function supportItems(now) {
  const isFree = !!planAt(planDay(now)).free;
  if (!isFree && planEnd() - now > 2 * DAY) return [];
  const fs = isFree ? freeSince() : planEnd() - 9 * H;
  const out = [], end = now + 90 * DAY;
  for (const [ms, lab, txt] of MILESTONES) if (fs + ms > now && fs + ms < end) out.push({ t: fs + ms, title: `🏆 ${lab} sans nicotine`, body: txt });
  const at = (day, h, m) => { const d = new Date(fs + day * DAY); d.setHours(h, m, 0, 0); return d.getTime(); };
  const daily = ["Une envie ? Ouvre l'appli, bouton ENVIE. Elle passe en quelques minutes.", "Chaque jour sans, le suivant est plus facile. Tu tiens 💪",
    "Les envies de sucre sont normales : fruits, eau, chewing-gum.", "Pense à ce que t'économises : regarde le compteur.", "T'avais tenu en arrêt brutal. Là c'est plus doux, et t'es plus fort."];
  for (let i = 1; i <= 14; i++) { const t = at(i, 18, 30); if (t > now) out.push({ t, title: '💪 Toujours libre', body: daily[i % daily.length] }); }
  for (let i = 1; i <= 120; i++) {
    const t = at(i, 20, 0), wd = new Date(t).getDay();
    if ((wd === 5 || wd === 6) && t > now && t < end) out.push({ t, title: '🎉 Soirée ce soir ?', body: "Ta réponse est prête : « Non merci, j'ai arrêté. » Une seule taffe de 20 mg relance tout." });
  }
  return out;
}

/* notifications : planning des ~36 prochaines heures */
function schedule() {
  const now = Date.now();
  if (S.notif === 'off' || !S.setup) return [];
  return upcoming(now, now + 36 * 3600000).filter((s) => s.t > now).filter((s) =>
    S.notif === 'all' || s.kind === 'wake' || (S.notif === 'min15' && (s.kind !== 'reg' || s.I >= 15))
  ).map((s) => ({
    t: s.t, title: KIND[s.kind] + ' autorisée',
    body: s.kind === 'wake' ? (planAt(planDay(s.t)).keyOnly ? `${s.size} taffes. Aujourd'hui : seulement les moments clés 💪` : `${s.size} taffes pour bien démarrer. Ensuite ${planAt(planDay(s.t)).reg} taffes toutes les ${fmtI(s.I)}.`)
        : s.kind === 'meal' ? `${s.size} taffes. C'est un moment clé : lève-toi de table, prends-les, et passe à autre chose.`
        : s.kind === 'sleep' ? `${s.size} taffes avant de dormir. Bonne nuit 💪`
        : `${s.size} taffes max. Prends-les seulement si t'en as vraiment envie.`,
  })).concat(supportItems(now)).sort((a, b) => a.t - b.t);
}

/* ---------- nicotine (modèle : demi-vie 2 h) ---------- */
const K = Math.LN2 / HALF_LIFE;
const decay = (dtMs) => Math.exp(-K * dtMs / MIN);
function mgAt(t) { let mg = S.setup.mg; const h = S.mgHistory || []; if (h.length) { mg = h[0].mg; for (const x of h) if (x.t <= t) mg = x.mg; } return mg; }
const mg0 = () => ((S.mgHistory || [])[0] || { mg: S.setup.mg }).mg;
function nicotine(now) {
  const ml = mlPerTaffe();
  const cur = S.log.filter((e) => e.t <= now && now - e.t < 2 * DAY).reduce((s, e) => s + (e.n || 1) * ml * mgAt(e.t) * decay(now - e.t), 0);
  // ton ancien rythme (jour 0 du plan) aux mêmes heures, hier + aujourd'hui
  const p0 = planAt(0); let base = 0;
  for (const ref of [now - DAY, now]) {
    for (const sl of daySlots(ref, p0)) if (sl.t <= now) base += sl.size * ml * mg0() * decay(now - sl.t);
  }
  return { cur, base };
}

/* ---------- formats ---------- */
function fmtI(I) {
  if (!isFinite(I)) return '—';
  if (I < 60) return Math.round(I) + ' min';
  const h = Math.floor(I / 60), m = Math.round(I % 60); return h + 'h' + (m ? String(m).padStart(2, '0') : '');
}
const fmtClock = (t) => new Date(t).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const fmtDate = (t) => new Date(t).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
const n1 = (x) => (Math.abs(x) < 1 && x !== 0 ? Math.round(x * 100) / 100 : Math.round(x * 10) / 10).toLocaleString('fr-FR');
const n0 = (x) => Math.round(x).toLocaleString('fr-FR');
function fmtCount(ms) {
  const s = Math.max(0, Math.ceil(ms / 1000)), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}` : `${m}:${String(ss).padStart(2, '0')}`;
}
function fmtDur(min) { min = Math.max(0, Math.round(min)); return min < 60 ? min + ' min' : Math.floor(min / 60) + ' h ' + String(min % 60).padStart(2, '0'); }
function toast(msg) { const el = $('#toast'); el.textContent = msg; el.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => (el.hidden = true), 2600); }

/* ---------- onboarding / réglages ---------- */
function paceButtons(el, current, onPick) {
  el.innerHTML = Object.entries(PACES).map(([k, p]) => `<button type="button" data-p="${k}" class="${k === current ? 'on' : ''}"><b>${p.name}</b><small>${p.desc}</small></button>`).join('');
  el.onclick = (e) => { const b = e.target.closest('button'); if (!b) return; $$('#' + el.id + ' button').forEach((x) => x.classList.toggle('on', x === b)); onPick(b.dataset.p); };
}
let pickedPace = 'normal';
function showOnboarding() {
  $('#onboarding').hidden = false; $('#main').hidden = true;
  paceButtons($('#paceChoice'), pickedPace, (p) => (pickedPace = p));
  $('#setupForm').onsubmit = (e) => {
    e.preventDefault(); const f = new FormData(e.target);
    S.setup = {
      v2: true, start: Date.now(), pace: pickedPace,
      baseInterval: +f.get('baseInterval'), sessionSize: +f.get('sessionSize'), edgeSize: +f.get('edgeSize'),
      daysPerPuff: +f.get('daysPerPuff'), mlPerPuff: +f.get('mlPerPuff'),
      mg: +f.get('mg'), price: +f.get('price'), wake: f.get('wake'), sleep: f.get('sleep'), lunch: f.get('lunch'), dinner: f.get('dinner'),
    };
    S.puffStart = Date.now(); S.mgHistory = [{ t: Date.now(), mg: S.setup.mg }];
    save(); start();
  };
}
const STR = ['wake', 'sleep', 'lunch', 'dinner'];
const SETTINGS = ['wake', 'sleep', 'lunch', 'dinner', 'baseInterval', 'sessionSize', 'edgeSize', 'mg', 'price', 'mlPerPuff'];
function fillSettings() {
  const f = $('#settingsForm');
  SETTINGS.forEach((k) => (f.elements[k].value = S.setup[k]));
  let p = S.setup.pace;
  paceButtons($('#paceChoice2'), p, (x) => (p = x));
  f.onsubmit = (e) => {
    e.preventDefault(); const d = new FormData(f);
    const mg = +d.get('mg');
    if (mg !== S.setup.mg) (S.mgHistory = S.mgHistory || [{ t: S.setup.start, mg: S.setup.mg }]).push({ t: Date.now(), mg });
    SETTINGS.forEach((k) => (S.setup[k] = STR.includes(k) ? d.get(k) : +d.get(k)));
    S.setup.pace = p;
    save(); sync(); render(); toast('Enregistré ✅');
  };
  $('#notifMode').value = S.notif;
}

/* ---------- actions ---------- */
let stepN = null, stepFor = null;
function takeSession() {
  const now = Date.now(), s = nextAllowed(now), list = sessionsOf(dayKey(now));
  const n = stepN ?? (s.size || 1);
  const early = !s.free && s.t > now;
  if (s.free && !confirm("Tu es censé avoir arrêté 🎉 Tu veux quand même noter une session ?")) return;
  if (early && !confirm(`Encore ${fmtCount(s.t - now)} à attendre.\nTu veux vraiment la prendre ? (Elle compte quand même, pas de panique.)`)) return;
  let kind = s.kind || 'reg';
  if (early) kind = !list.length ? 'wake' : now >= win(now).ss ? 'sleep' : (s.kind === 'meal' && s.t - now < 20 * MIN) ? 'meal' : 'reg';
  S.log.push({ t: now, n, kind, early: !!early });
  stepN = null; save(); sync(); render();
  toast(early ? 'Notée. Pas grave, on continue 💪' : `Session notée ✅ (${n} taffes)`);
}
function undo() {
  const last = S.log[S.log.length - 1];
  if (last && Date.now() - last.t < 5 * MIN) { S.log.pop(); save(); sync(); render(); toast('Annulée'); }
}
function hold() {
  const k = dayKey(Date.now());
  if (S.holds.includes(k)) return toast('Déjà fait aujourd\'hui');
  if (planDay(Date.now()) <= 0) return toast('Tu es déjà au palier de départ');
  if (!confirm("OK, aujourd'hui tu restes au même palier qu'hier.\nLe plan est décalé d'un jour. À utiliser seulement si c'est vraiment dur 🙂")) return;
  S.holds.push(k); save(); sync(); render(); toast('Palier maintenu pour aujourd\'hui');
}

/* ---------- rendu ---------- */
const KEY_QUOTES = {
  wake: ["Le matin", "C'est la nicotine qui a baissé pendant la nuit qui te réveille avec l'envie. Chaque matin, ce manque sera un peu plus petit."],
  meal: ["Après le repas", "Ce n'est pas ton corps qui réclame, c'est une habitude collée au repas. Une habitude, ça se remplace."],
  sleep: ["Avant de dormir", "Moins de nicotine le soir, c'est un sommeil plus profond. Tu te réveilleras plus reposé, et avec moins d'envie."],
};
const QUOTES = [
  ["20 minutes sans nicotine", "Ton cœur ralentit et ta tension redescend. Ton corps commence déjà à souffler."],
  ["72 heures", "La nicotine a quasiment quitté ton corps. Le pic du manque est passé, ensuite ça ne fait que descendre."],
  ["2 à 4 semaines", "Le sommeil devient plus profond et plus réparateur. Tu te réveilles vraiment reposé."],
  ["Le stress", "La nicotine ne calme pas le stress : elle calme le manque qu'elle a créé. Sans elle, ton anxiété de fond baisse."],
  ["Ton cerveau se recâble", "En quelques semaines, tes récepteurs à nicotine se remettent au calme. Les envies deviennent rares, puis disparaissent."],
  ["Concentration", "Fini de penser à la prochaine taffe toutes les 10 minutes. Ton attention t'appartient de nouveau."],
  ["Liberté", "Plus besoin de vérifier que t'as ta puff avant de sortir. Plus de panique quand elle est vide."],
  ["Ton souffle", "Moins de produits chimiques inhalés, des poumons qui respirent mieux, plus d'endurance au sport."],
  ["Ton argent", "Chaque puff pas achetée, c'est de l'argent qui reste dans ta poche. Regarde le compteur dans Progrès."],
  ["Ton énergie", "Plus de montagnes russes nicotine / manque toute la journée. Ton énergie devient stable."],
  ["Chaque session repoussée", "C'est une victoire. Ton corps élimine la moitié de la nicotine toutes les 2 heures."],
  ["Une envie, c'est une vague", "Elle monte, elle culmine, elle redescend en 3 à 5 minutes. Tu peux la regarder passer."],
  ["Tu n'arrêtes pas un plaisir", "Tu arrêtes une dépendance qui se faisait passer pour un plaisir."],
  ["Le plus dur, c'est maintenant", "Chaque jour qui passe rend le suivant plus facile. Le toi de dans 2 mois te remercie déjà."],
  ["Ton cœur", "Sans nicotine, tes vaisseaux ne se resserrent plus à chaque taffe. Ton cœur travaille moins dur."],
  ["La fierté", "Dans quelques semaines, tu pourras dire « j'ai arrêté ». Peu de gens peuvent le dire."],
];
let lastSyncKey = '';
function render() {
  if (!S.setup) return;
  const now = Date.now(), k = dayKey(now), d = planDay(now), s = nextAllowed(now);
  const today = sessionsOf(k), p = planAt(d), free = !!p.free;
  const rem = free ? [] : remainingToday(now);

  $('#dayLabel').textContent = free ? '🎉 Libéré' : `Jour ${dayIndex(now) + 1} · palier ${Math.max(0, d) + 1}/${N()}`;
  $('#paceLabel').textContent = free ? `Plan terminé le ${fmtDate(planEnd())}. Maintenant, tu tiens.` : `Plan ${PACES[S.setup.pace].name.toLowerCase()} · fin prévue le ${fmtDate(planEnd())}`;

  const btn = $('#puffBtn'), fg = $('#ringFg');
  btn.classList.remove('early', 'locked');
  if (stepFor !== (s.t || 0)) { stepFor = s.t || 0; stepN = null; }
  $('#stepN').textContent = stepN ?? (s.size || 1);
  if (free) {
    $('#ringCaption').textContent = 'Plan terminé'; $('#countdown').textContent = '0'; $('#ringSub').textContent = 'taffe autorisée. Tu es libre.';
    $('#kindLabel').textContent = ''; fg.style.strokeDashoffset = 0; btn.classList.add('locked');
  } else if (s.t <= now) {
    $('#ringCaption').textContent = 'Tu as le droit'; $('#countdown').textContent = s.size;
    $('#ringSub').textContent = `taffes · depuis ${fmtClock(s.t)}`;
    $('#kindLabel').textContent = KIND[s.kind].replace(/^\S+ /, '') + ' disponible';
    fg.style.strokeDashoffset = 0; fg.style.stroke = 'var(--ac)';
  } else {
    const sameDay = dayKey(s.t) === k;
    const last = today[today.length - 1];
    const span = last ? s.t - last.t : s.t - now;
    const frac = 1 - Math.min(1, (s.t - now) / Math.max(span, 1));
    $('#ringCaption').textContent = sameDay ? 'Prochaine session dans' : 'Fini pour aujourd\'hui';
    $('#countdown').textContent = fmtCount(s.t - now);
    $('#ringSub').textContent = `${s.size} taffes à ` + (sameDay ? fmtClock(s.t) : fmtDate(s.t) + ' ' + fmtClock(s.t));
    $('#kindLabel').textContent = 'Prochaine : ' + KIND[s.kind].toLowerCase().replace(/^\S+ /, '');
    fg.style.strokeDashoffset = 553 * (1 - (sameDay ? frac : 0)); fg.style.stroke = 'var(--warn)';
    btn.classList.add(sameDay ? 'early' : 'locked');
  }
  const lastE = S.log[S.log.length - 1];
  $('#undoBtn').hidden = !(lastE && now - lastE.t < 5 * MIN);

  $('#sToday').textContent = taffes(today);
  $('#sLeft').textContent = taffes(rem.map((x) => ({ n: x.size })));
  $('#sInterval').textContent = fmtI(p.I);
  $('#sSize').textContent = free ? '0' : `${p.reg || '—'} · ${p.edge}`;
  const q = (!free && s.t <= now + 15 * MIN && KEY_QUOTES[s.kind]) || QUOTES[(S.log.length + dayIndex(now) * 7) % QUOTES.length];
  if ($('#quoteT').textContent !== q[0]) { $('#quoteT').textContent = q[0]; $('#quoteB').textContent = q[1]; }
  $('#holdBtn').hidden = free || S.holds.includes(k) || d <= 0;

  $('#freeView').hidden = !free; $('#planView').hidden = free;
  if (free) renderFree(now);
  renderPlan(d); renderStats(); renderNotifUi();
  const key = JSON.stringify([S.log.length, S.holds.length, S.notif, k, s.t, S.setup.start]);
  if (key !== lastSyncKey) { lastSyncKey = key; sync(); }
}
function renderFree(now) {
  const fs = freeSince(), el = now - fs, days = Math.floor(el / DAY);
  $('#freeDays').textContent = days >= 1 ? days : Math.floor(el / H);
  $('#freeUnit').textContent = days >= 1 ? (days > 1 ? 'JOURS' : 'JOUR') : 'HEURES';
  $('#freeSince').textContent = `depuis le ${fmtDate(fs)} à ${fmtClock(fs)}`;
  $('#fMoney').textContent = Math.round(el / DAY * perDayCost()) + ' €';
  $('#fYear').textContent = Math.round(365 * perDayCost()) + ' €';
  $('#fResist').textContent = S.resisted || 0;
  const next = MILESTONES.find(([ms]) => ms > el);
  $('#fNext').textContent = next ? fmtFree(next[0] - el) : '🏆';
  $('#fNextL').textContent = next ? `avant le cap des ${next[1]}` : 'tous les caps passés';
  $('#milesList').innerHTML = MILESTONES.map(([ms, lab, txt]) => {
    const cls = ms <= el ? 'done' : ms === (next && next[0]) ? 'next' : '';
    return `<li class="${cls}"><span class="ic">${ms <= el ? '✓' : '·'}</span><b>${lab}</b><span>${txt}</span></li>`;
  }).join('');
  const q = FREE_QUOTES[(days + S.log.length) % FREE_QUOTES.length];
  if ($('#fQuoteT').textContent !== q[0]) { $('#fQuoteT').textContent = q[0]; $('#fQuoteB').textContent = q[1]; }
}
function slip() {
  if (!confirm("Une taffe n'efface pas tout ce que t'as fait.\nOn la note, le compteur repart, et tu continues. OK ?")) return;
  S.log.push({ t: Date.now(), n: 1, kind: 'slip' }); save(); sync(); render();
  toast('Notée. Une taffe, pas une rechute. Tu repars 💪');
}
function restartPlan() {
  if (!confirm("Relancer un plan rapide (5 semaines) à partir d'aujourd'hui ?\nTon historique est gardé.")) return;
  Object.assign(S.setup, { start: Date.now(), pace: 'rapide' }); S.holds = []; S.puffStart = Date.now();
  save(); fillSettings(); sync(); render(); toast('Nouveau plan lancé. Tu sais le faire 💪');
}
function planEnd() { return dayStart(S.setup.start) + (N() + S.holds.length) * DAY + geo().off * MIN; }

function svgLine(points, maxY, mark) {
  const w = 320, h = 140, pad = 4;
  const xs = (i) => pad + (i / Math.max(1, points.length - 1)) * (w - 2 * pad);
  const ys = (v) => h - pad - (v / maxY) * (h - 2 * pad);
  const path = points.map((v, i) => (i ? 'L' : 'M') + xs(i).toFixed(1) + ' ' + ys(v).toFixed(1)).join('');
  const m = mark != null && mark < points.length ? `<circle cx="${xs(mark)}" cy="${ys(points[mark])}" r="5" fill="var(--warn)"/>` : '';
  return `<svg viewBox="0 0 ${w} ${h}"><path d="${path} L${xs(points.length - 1)} ${h - pad} L${pad} ${h - pad}Z" fill="rgba(232,245,58,.10)"/><path d="${path}" fill="none" stroke="var(--ac)" stroke-width="2"/>${m}</svg>`;
}
function renderPlan(d) {
  const n = N(), pts = [];
  for (let i = 0; i <= n; i++) pts.push(dayCounts(i).taffes);
  $('#planBar').style.width = Math.min(100, Math.max(0, (d / n) * 100)) + '%';
  const c = dayCounts(d);
  $('#planSummary').innerHTML = d >= n ? 'Plan terminé 🎉' :
    (c.p.keyOnly ? `Aujourd'hui : <b>plus de sessions entre les moments clés</b>. Seulement <b>${c.p.edge} taffes</b> au réveil, après les repas et au coucher (${c.taffes} max).`
    : `Aujourd'hui : <b>${c.p.edge} taffes</b> à chaque moment clé (réveil, après les repas, coucher), et entre les deux <b>${c.p.reg} taffes toutes les ${fmtI(c.p.I)}</b> (${c.taffes} max).`) + ` Au départ : ${baselinePerDay()}/jour. Arrêt complet le <b>${fmtDate(planEnd())}</b>.`;
  $('#planChart').innerHTML = svgLine(pts, pts[0] * 1.05, Math.max(0, d));
  const ml = mlPerTaffe(), mg = S.setup.mg;
  let rows = '<tr><th>Sem.</th><th>Écart</th><th>Session</th><th>Moments<br>clés</th><th>Taffes/j</th><th>mg/j</th></tr>';
  for (let w = 0; w * 7 < n; w++) {
    const di = w * 7, cur = d >= di && d < di + 7, x = dayCounts(di);
    rows += `<tr class="${cur ? 'cur' : ''}"><td>S${w + 1}</td><td>${fmtI(x.p.I)}</td><td>${x.p.reg || '—'}</td><td>${x.p.edge}</td><td>${x.taffes}</td><td>${n0(x.taffes * ml * mg)}</td></tr>`;
  }
  rows += `<tr class="${d >= n ? 'cur' : ''}"><td>Ensuite</td><td>—</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>`;
  $('#planTable').innerHTML = rows;
}
function renderNicotine(now) {
  const { cur, base } = nicotine(now);
  const ratio = base > 0 ? cur / base : 0;
  const less = Math.max(0, 1 - ratio);
  $('#nicoNow').textContent = base > 0 ? (ratio <= 1 ? '−' + Math.round(less * 100) + ' %' : '+' + Math.round((ratio - 1) * 100) + ' %') : '-';
  $('#nicoNowL').textContent = ratio <= 1 ? 'de nicotine dans ton corps par rapport à ton ancien rythme, à cette heure-ci' : 'de nicotine en plus que ton ancien rythme à cette heure-ci';
  $('#nicoBar').style.width = Math.min(100, ratio * 100) + '%';
  const last = S.log[S.log.length - 1];
  if (!last) { $('#nicoOut').textContent = '-'; $('#nicoOutBar').style.width = '0'; $('#nicoText').textContent = ''; return; }
  const dt = (now - last.t) / MIN, out = 1 - Math.pow(0.5, dt / HALF_LIFE);
  $('#nicoOut').textContent = Math.floor(out * 100) + ' %';
  $('#nicoOutBar').style.width = out * 100 + '%';
  const to = (p) => HALF_LIFE * Math.log2(1 / (1 - p)) - dt;
  const steps = [[0.5, '50 %'], [0.9, '90 %'], [0.97, '97 % (quasi plus de nicotine)']].filter(([p]) => to(p) > 0);
  $('#nicoText').innerHTML = `Dernière session il y a ${fmtDur(dt)}.` +
    (steps.length ? ' Si tu ne vapotes pas : ' + steps.map(([p, l]) => `${l} dans ${fmtDur(to(p))}`).join(', ') + '.' : ' Ton corps a quasiment éliminé la nicotine 🎉') +
    '<br>Repère : la nicotine perd la moitié de sa quantité toutes les ~2 h. Son déchet (la cotinine) met 3 à 4 jours à partir après l\'arrêt. Estimation, pas une mesure médicale.';
}
function renderStats() {
  const now = Date.now(), base = baselinePerDay(), ml = mlPerTaffe(), days = dayIndex(now) + 1;
  renderNicotine(now);
  const { ws } = win(now), W = geo().W;
  const fracToday = Math.min(1, Math.max(0, (now - ws) / (W * MIN)));
  const expected = base * (days - 1 + fracToday);
  const avoided = Math.max(0, expected - taffes(S.log));
  $('#stAvoided').textContent = n0(avoided);
  $('#stMl').textContent = n1(avoided * ml);
  $('#stMg').textContent = n0(avoided * ml * mg0());
  $('#stMoney').textContent = (avoided * ml / S.setup.mlPerPuff * S.setup.price).toFixed(2).replace('.', ',') + ' €';
  let sum = 0, cnt = 0, streak = 0, streakOn = true;
  const bars = [];
  for (let i = 0; i < 14; i++) {
    const t = now - i * DAY; if (dayIndex(t) < 0) break;
    const kk = dayKey(t), c = taffes(sessionsOf(kk)), b = dayCounts(planDay(t)).taffes;
    if (i > 0 && i <= 7) { sum += c; cnt++; }
    if (i > 0) { if (streakOn && c <= b) streak++; else streakOn = false; }
    bars.unshift({ k: kk, c, b, today: i === 0 });
  }
  if (!cnt) { sum = taffes(S.log); cnt = fracToday || 1; }
  $('#stReduc').textContent = Math.round(Math.max(0, 1 - sum / cnt / base) * 100) + ' %';
  $('#stStreak').textContent = streak;
  const w = 320, h = 140, maxV = Math.max(1, ...bars.map((x) => Math.max(x.c, x.b))) * 1.1, bw = w / 14;
  let svg = `<svg viewBox="0 0 ${w} ${h + 16}">`;
  bars.forEach((x, i) => {
    const X = i * bw + 3, bh = (x.c / maxV) * h, by = h - (x.b / maxV) * h;
    svg += `<rect x="${X}" y="${h - bh}" width="${bw - 6}" height="${bh}" rx="3" fill="${x.c <= x.b ? 'var(--ac)' : 'var(--bad)'}" opacity="${x.today ? .55 : 1}"/>`;
    svg += `<line x1="${X - 2}" x2="${X + bw - 4}" y1="${by}" y2="${by}" stroke="var(--mu)" stroke-dasharray="3 2"/>`;
    svg += `<text x="${X + (bw - 6) / 2}" y="${h + 12}" fill="var(--mu)" font-size="9" text-anchor="middle">${+x.k.slice(8)}</text>`;
  });
  $('#histChart').innerHTML = svg + '</svg>';
  const since = taffes(S.log.filter((e) => e.t >= (S.puffStart || 0)));
  const used = since * ml, rest = Math.max(0, S.setup.mlPerPuff - used);
  const curB = dayCounts(planDay(now)).taffes || 1;
  $('#puffBar').style.width = Math.min(100, (used / S.setup.mlPerPuff) * 100) + '%';
  $('#puffText').innerHTML = `Environ <b>${n1(rest)} ml</b> restants sur ${S.setup.mlPerPuff} ml (${since} taffes depuis le ${fmtDate(S.puffStart)}). Au rythme du plan, elle devrait durer encore <b>~${n1(rest / (curB * ml))} jours</b>.`;
  const today = sessionsOf(dayKey(now)), tt = taffes(today), earlyN = today.filter((e) => e.early).length;
  $('#todayDetail').innerHTML = `${today.length} sessions · ${tt} taffes · ≈ ${n1(tt * ml)} ml · ≈ ${n0(tt * ml * mgAt(now))} mg de nicotine` +
    (earlyN ? ` · ${earlyN} en avance` : '') + `<br>Ton ancien rythme à cette heure-ci : ≈ ${n0(base * fracToday)} taffes.` +
    (today.length ? `<br>Dernière session à ${fmtClock(today[today.length - 1].t)}.` : '');
}

/* ---------- notifications ---------- */
const isStandalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);
const pushSupported = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
function renderNotifUi() {
  const perm = 'Notification' in window ? Notification.permission : 'unsupported';
  const on = perm === 'granted' && S.subscribed;
  let st;
  if (!pushSupported()) st = isIOS() && !isStandalone() ? "Sur iPhone : ajoute d'abord l'appli à l'écran d'accueil (bouton Partager → « Sur l'écran d'accueil »), puis ouvre-la depuis l'icône." : 'Ton navigateur ne gère pas les notifications push.';
  else if (perm === 'denied') st = 'Notifications bloquées. Autorise-les dans les réglages du téléphone pour ce site.';
  else st = on ? '✅ Activées.' : 'Pas encore activées.';
  $('#notifStatus').textContent = st;
  $('#notifBtn').textContent = on ? 'Réactiver' : 'Activer';
  $('#notifCard').hidden = on || !pushSupported() || perm === 'denied' || S.notif === 'off';
  $('#installCard').hidden = isStandalone();
  $('#installText').innerHTML = isIOS()
    ? "Dans Safari : bouton <b>Partager</b> ⬆️ → <b>Sur l'écran d'accueil</b>. Ouvre ensuite Puff Stop depuis l'icône (obligatoire sur iPhone pour les notifs)."
    : "Dans Chrome : menu <b>⋮</b> → <b>Ajouter à l'écran d'accueil</b> / <b>Installer l'application</b>.";
}
function b64ToU8(b64) { const p = '='.repeat((4 - (b64.length % 4)) % 4); const r = atob((b64 + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...r].map((c) => c.charCodeAt(0))); }
async function enableNotifs(test) {
  if (!pushSupported()) return toast(isIOS() ? "Ajoute d'abord l'appli à l'écran d'accueil" : 'Non supporté ici');
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') { renderNotifUi(); return toast('Permission refusée'); }
  try {
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToU8(VAPID_PUBLIC) });
    S.subscribed = true; if (S.notif === 'off') S.notif = 'all'; save();
    await sync(sub.toJSON(), test !== false);
    toast('Notifications activées 🔔'); render();
  } catch (e) { toast('Erreur : ' + e.message); }
}
let syncTimer;
async function sync(sub, test) {
  if (!S.setup) return;
  const body = { id: S.id, items: schedule() };
  if (sub) body.sub = sub;
  if (test) body.test = true;
  clearTimeout(syncTimer);
  const go = async () => {
    try {
      const r = await fetch('/api/sync', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      if (test) { const j = await r.json().catch(() => ({})); if (!j.ok) toast('Échec du test : ' + (j.error || r.status)); }
    } catch {}
  };
  if (sub || test) return go();
  syncTimer = setTimeout(go, 800);
}

/* ---------- SOS envie ---------- */
const SOS_CTX = {
  meal: ["Lève-toi de table dès que t'as fini : changer de pièce casse le réflexe « fin de repas = taffe ».",
    "Brosse-toi les dents juste après manger : le goût du dentifrice coupe l'envie net.",
    "Garde le rituel mais change la fin : un café, un thé, un carré de chocolat, sans la puff.",
    "Va marcher 5 minutes dehors après le repas."],
  morning: ["Ne prends pas ta puff avant d'être levé, habillé et d'avoir bu un grand verre d'eau.",
    "Change l'ordre de ta routine : douche d'abord, session après.",
    "La nuit, laisse la puff dans une autre pièce que ta chambre."],
  night: ["Laisse la puff hors de la chambre : si elle n'est pas à portée de main, tu ne tires pas machinalement.",
    "Remplace la dernière taffe par un rituel : tisane, écran coupé, 5 respirations lentes.",
    "La nicotine stimule et fragmente le sommeil : moins tu en prends le soir, mieux tu dors."],
};
function sosContext(now) {
  const w = dayWin(now);
  if (w.meals.some((m) => now >= m - 30 * MIN && now <= m + 90 * MIN)) return 'meal';
  if (now - w.ws < 2 * 3600000) return 'morning';
  if (now > w.ss - 2 * 3600000) return 'night';
  return null;
}
const SOS_TIPS = ['Bois un grand verre d\'eau, lentement.', 'Lève-toi, marche 2 minutes.', 'Occupe tes mains : téléphone, balle, élastique.', 'Rappelle-toi pourquoi tu arrêtes.', 'Chewing-gum ou fruit si t\'en as.'];
let sosIv;
function openSos(mode) {
  $('#sos').hidden = false;
  const now = Date.now(), shuffle = (a) => [...a].sort(() => Math.random() - 0.5);
  const free = !!planAt(planDay(now)).free;
  const party = mode === 'party';
  $('#sosEyebrow').textContent = party ? 'SOS / SOIRÉE' : 'SOS / RESPIRATION';
  $('#sosTitle').textContent = party ? 'LA SOIRÉE, TU LA GÈRES.' : "L'ENVIE VA PASSER.";
  $('#breath').hidden = party; $('#sosTimer').hidden = party;
  $('#sosAnswers').hidden = !party;
  if (party) {
    const dd = free ? fmtFree(now - freeSince()) + ' sans nicotine' : `J${dayIndex(now) + 1} de mon plan`;
    $('#sosAnswers').innerHTML = '<div class="answers"><div class="eyebrow">TES RÉPONSES TOUTES PRÊTES</div>' +
      PARTY.answers.map((a) => `<p>${a.replace('{d}', dd)}</p>`).join('') + '</div>';
  }
  const ctx = sosContext(now);
  const tips = party ? shuffle(PARTY.tips).slice(0, 3)
    : free ? [...shuffle(FREE_QUOTES).slice(0, 2).map((q) => q[1]), ...shuffle(SOS_TIPS).slice(0, 1)]
    : ctx ? [...shuffle(SOS_CTX[ctx]).slice(0, 2), ...shuffle(SOS_TIPS).slice(0, 1)] : shuffle(SOS_TIPS).slice(0, 3);
  $('#sosTips').innerHTML = tips.map((x) => `<li>${x}</li>`).join('');
  let left = 180, phase = 0; const b = $('#breath'), txt = $('#breathTxt');
  const step = () => {
    $('#sosTimer').textContent = fmtCount(left * 1000);
    if (left % 4 === 0) { phase ^= 1; b.classList.toggle('in', !!phase); txt.textContent = phase ? 'Inspire' : 'Expire'; }
    if (--left < 0) { clearInterval(sosIv); $('#sosTimer').textContent = 'Bravo 👏'; }
  };
  clearInterval(sosIv); step(); sosIv = setInterval(step, 1000);
}
function closeSos() { clearInterval(sosIv); $('#sos').hidden = true; S.resisted = (S.resisted || 0) + 1; save(); toast(`Envie surmontée ! (${S.resisted} au total)`); }

/* ---------- démarrage ---------- */
function start() {
  $('#onboarding').hidden = true; $('#main').hidden = false;
  fillSettings(); render();
  clearInterval(start.iv); start.iv = setInterval(render, 1000);
}
function bind() {
  $('#puffBtn').onclick = takeSession;
  $('#minusBtn').onclick = () => { const s = nextAllowed(); stepN = Math.max(1, (stepN ?? (s.size || 1)) - 1); render(); };
  $('#plusBtn').onclick = () => { const s = nextAllowed(); stepN = Math.min(40, (stepN ?? (s.size || 1)) + 1); render(); };
  $('#undoBtn').onclick = undo;
  $('#holdBtn').onclick = hold;
  $('#sosBtn').onclick = () => openSos();
  $('#partyBtn').onclick = () => openSos('party');
  $('#slipBtn').onclick = slip;
  $('#restartBtn').onclick = restartPlan;
  $('#sosClose').onclick = closeSos;
  $('#notifBtn').onclick = () => enableNotifs(true);
  $('#notifBtn2').onclick = () => enableNotifs(true);
  $('#testBtn').onclick = () => (S.subscribed ? sync(null, true).then(() => toast('Test envoyé…')) : enableNotifs(true));
  $('#notifMode').onchange = (e) => { S.notif = e.target.value; save(); sync(); render(); };
  $('#newPuffBtn').onclick = () => { if (confirm('Nouvelle puff entamée maintenant ?')) { S.puffStart = Date.now(); save(); render(); } };
  $('#exportBtn').onclick = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(S)], { type: 'application/json' })); a.download = 'puffstop-' + ymd(Date.now()) + '.json'; a.click(); };
  $('#importBtn').onclick = () => $('#importFile').click();
  $('#importFile').onchange = async (e) => { try { const s = JSON.parse(await e.target.files[0].text()); if (!s.setup) throw 0; S = s; save(); start(); toast('Importé ✅'); } catch { toast('Fichier invalide'); } };
  $('#resetBtn').onclick = () => { if (confirm('Tout effacer et recommencer ?')) { const id = S.id; localStorage.removeItem(KEY); S = load(); S.id = id; save(); location.reload(); } };
  $$('.tabs button').forEach((b) => (b.onclick = () => {
    $$('.tabs button').forEach((x) => x.classList.toggle('on', x === b));
    ['today', 'plan', 'stats', 'settings'].forEach((t) => ($('#tab-' + t).hidden = t !== b.dataset.tab));
    scrollTo(0, 0);
  }));
  document.addEventListener('visibilitychange', () => { if (!document.hidden && S.setup) render(); });
}
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
bind();
S.setup ? start() : showOnboarding();
