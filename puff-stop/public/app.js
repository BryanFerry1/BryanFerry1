'use strict';
/* Puff Stop — arrêt progressif de la puff.
   Tout l'état est dans localStorage ; le serveur (Netlify) ne reçoit que
   l'abonnement push + les heures des prochaines notifications. */

const VAPID_PUBLIC = 'BOyUJLsn15HycNpq7-HFcleTZ4OOidJUnvEL7ud3gukZfyhU45Ih7Xtg9719s3qzv97C7rsYeV60sxdNL6YWAjU';
const KEY = 'puffstop.v1';
const MIN = 60000, DAY = 86400000;
const I_END = 240; // écart final (min) avant l'arrêt complet : ~4 taffes/jour
const PACES = {
  doux:   { days: 84, name: 'Doux',   desc: '12 semaines · ça bouge très lentement au début' },
  normal: { days: 56, name: 'Normal', desc: '8 semaines · recommandé' },
  rapide: { days: 35, name: 'Rapide', desc: '5 semaines · si tu es très motivé' },
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

/* ---------- état ---------- */
function load() {
  try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.id) return s; } catch {}
  return { id: (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()), setup: null, log: [], holds: [], puffStart: null, notif: 'all' };
}
let S = load();
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} }

/* ---------- temps & plan ---------- */
const hm = (s) => { const [h, m] = s.split(':').map(Number); return h * 60 + m; };
function geo() {
  const wm = hm(S.setup.wake); let sm = hm(S.setup.sleep);
  if (sm <= wm) sm += 1440;
  const W = sm - wm, night = 1440 - W;
  const bnd = (sm + night / 2) % 1440;           // milieu de la nuit = changement de jour
  const off = ((wm - bnd) % 1440 + 1440) % 1440; // du changement de jour au réveil
  return { W, bnd, off };
}
function dayStart(t) {
  const { bnd } = geo(); const d = new Date(t); d.setHours(0, 0, 0, 0);
  let s = d.getTime() + bnd * MIN; if (s > t) s -= DAY; return s;
}
const ymd = (t) => { const d = new Date(t); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
const dayKey = (t) => ymd(dayStart(t) + geo().off * MIN);
function win(t) { const g = geo(); const ws = dayStart(t) + g.off * MIN; return { ws, we: ws + g.W * MIN }; }
const dayIndex = (t) => Math.round((dayStart(t) - dayStart(S.setup.start)) / DAY);
function planDay(t) { const k = dayKey(t); return dayIndex(t) - S.holds.filter((h) => h <= k).length; }
const N = () => PACES[S.setup.pace].days;
function interval(d) { // minutes entre 2 taffes au jour d du plan
  const I0 = S.setup.baseInterval, n = N();
  if (d <= 0) return I0;
  if (d >= n) return Infinity;
  const x = d / (n - 1);
  return I0 * Math.pow(Math.max(I_END, I0 * 2) / I0, Math.pow(x, 1.35)); // courbe douce au début
}
function budget(d) { if (d >= N()) return 0; return Math.max(1, Math.floor(geo().W / interval(d))); }
const baselinePerDay = () => geo().W / S.setup.baseInterval;
const mlPerTaffe = () => S.setup.mlPerPuff / (S.setup.daysPerPuff * baselinePerDay());
const taffesOf = (k) => S.log.filter((e) => dayKey(e.t) === k);

function nextAllowed(now = Date.now()) {
  for (let k = 0; k < 4; k++) {
    const ref = now + k * DAY;
    const d = planDay(ref);
    if (d >= N()) return { free: true };
    const { ws, we } = win(ref);
    if (k === 0 && we < now) continue;
    const I = interval(d), B = budget(d);
    const list = taffesOf(dayKey(ref));
    if (list.length >= B) continue;
    let t = list.length ? list[list.length - 1].t + I * MIN : ws;
    t = Math.max(t, ws);
    if (t > we) continue;
    return { t, d, I, B, left: B - list.length, sameDay: k === 0 && dayKey(t) === dayKey(now) };
  }
  return { t: null };
}

/* planning des notifs pour ~36 h (en supposant que tu prends chaque taffe autorisée) */
function schedule() {
  const now = Date.now(), items = [];
  if (S.notif === 'off' || !S.setup) return items;
  const n = nextAllowed(now);
  if (n.free || !n.t) return items;
  const horizon = now + 36 * 3600000;
  let t = n.t, k = dayKey(t), left = n.left, I = n.I, first = !n.sameDay || !taffesOf(k).length;
  let guard = 0;
  while (t < horizon && guard++ < 500) {
    const { we } = win(t);
    if (left > 0 && t <= we) {
      const morning = first;
      const wanted = S.notif === 'all' || morning || (S.notif === 'min15' && I >= 15);
      if (t > now && wanted) {
        items.push({ t, title: morning ? '☀️ Première taffe autorisée' : '🟢 Taffe autorisée',
          body: morning ? `Aujourd'hui : ${left} taffes max, une toutes les ${fmtI(I)}. Tu gères 💪`
                        : `Il t'en reste ${left} aujourd'hui. Prends-la seulement si t'en as vraiment envie.` });
      }
      first = false; left--; t += I * MIN;
    } else { // jour suivant : juste après le milieu de la nuit qui suit
      const tomorrowWs = win(we + ((1440 - geo().W) / 2 + 1) * MIN).ws;
      const d = planDay(tomorrowWs);
      if (d >= N()) break;
      t = tomorrowWs; I = interval(d); left = budget(d); first = true;
    }
  }
  return items;
}

/* ---------- formats ---------- */
function fmtI(I) {
  if (!isFinite(I)) return '—';
  if (I < 60) return (Math.round(I * 2) / 2).toString().replace('.', ',') + ' min';
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
      start: Date.now(), pace: pickedPace,
      baseInterval: +f.get('baseInterval'), daysPerPuff: +f.get('daysPerPuff'), mlPerPuff: +f.get('mlPerPuff'),
      mg: +f.get('mg'), price: +f.get('price'), wake: f.get('wake'), sleep: f.get('sleep'),
    };
    S.puffStart = Date.now(); S.mgHistory = [{ t: Date.now(), mg: S.setup.mg }];
    save(); start();
  };
}
function fillSettings() {
  const f = $('#settingsForm');
  ['wake', 'sleep', 'mg', 'price', 'mlPerPuff'].forEach((k) => (f.elements[k].value = S.setup[k]));
  let p = S.setup.pace;
  paceButtons($('#paceChoice2'), p, (x) => (p = x));
  f.onsubmit = (e) => {
    e.preventDefault(); const d = new FormData(f);
    const mg = +d.get('mg');
    if (mg !== S.setup.mg) (S.mgHistory = S.mgHistory || []).push({ t: Date.now(), mg });
    Object.assign(S.setup, { wake: d.get('wake'), sleep: d.get('sleep'), mg, price: +d.get('price'), mlPerPuff: +d.get('mlPerPuff'), pace: p });
    save(); sync(); render(); toast('Enregistré ✅');
  };
  $('#notifMode').value = S.notif;
}

/* ---------- actions ---------- */
function takePuff() {
  const now = Date.now(), n = nextAllowed(now);
  const early = !n.free && n.t && n.t > now;
  if (n.free && !confirm("Tu es censé avoir arrêté 🎉 Tu veux quand même noter une taffe ?")) return;
  if (early && n.sameDay && !confirm(`Encore ${fmtCount(n.t - now)} à attendre.\nTu veux vraiment la prendre ? (Elle compte quand même, pas de panique.)`)) return;
  if (early && !n.sameDay && !confirm("Tu as utilisé toutes tes taffes d'aujourd'hui.\nTu craques quand même ? Note-la, ça aide à rester honnête.")) return;
  S.log.push({ t: now, early: !!early });
  save(); sync(); render();
  toast(early ? 'Notée. Pas grave, on continue 💪' : 'Notée ✅');
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
const TIPS = [
  "Une envie dure 3 à 5 minutes. Si tu attends, elle redescend toute seule.",
  "Garde la puff loin de toi (sac, autre pièce) : moins tu l'as en main, moins tu tires machinalement.",
  "Associe chaque taffe autorisée à un moment : tu la prends, tu la poses. Plus de taffes « en pilote automatique ».",
  "Bois un grand verre d'eau quand l'envie arrive. Ça occupe la bouche et les mains.",
  "Les premiers jours, l'écart bouge à peine : le but est surtout de casser l'automatisme.",
  "Le manque de nicotine culmine vers 3 jours après une grosse baisse, puis diminue nettement.",
  "Si tu peux, passe à une puff 10 mg vers la moitié du plan : l'arrêt final sera beaucoup plus facile.",
  "Chewing-gum, cure-dent, élastique au poignet : trouve un truc pour les mains et la bouche.",
  "Tabac Info Service (39 89, gratuit) peut te mettre en contact avec un tabacologue.",
];
let lastSyncKey = '';
function render() {
  if (!S.setup) return;
  const now = Date.now(), k = dayKey(now), d = planDay(now), n = nextAllowed(now);
  const today = taffesOf(k), I = interval(d), B = budget(d);
  const free = d >= N();

  $('#dayLabel').textContent = free ? '🎉 Libéré' : `Jour ${dayIndex(now) + 1} · palier ${Math.max(0, d) + 1}/${N()}`;
  $('#paceLabel').textContent = `Plan ${PACES[S.setup.pace].name.toLowerCase()} · fin prévue le ${fmtDate(planEnd())}`;

  const btn = $('#puffBtn'), fg = $('#ringFg');
  btn.classList.remove('early', 'locked');
  if (free) {
    $('#ringCaption').textContent = 'Plan terminé'; $('#countdown').textContent = '0'; $('#ringSub').textContent = 'taffe autorisée. Tu es libre.';
    fg.style.strokeDashoffset = 0; btn.classList.add('locked');
  } else if (!n.t) {
    $('#ringCaption').textContent = 'Plus de taffes'; $('#countdown').textContent = '—'; $('#ringSub').textContent = '';
  } else if (n.t <= now) {
    $('#ringCaption').textContent = 'Tu as le droit'; $('#countdown').textContent = '✓';
    $('#ringSub').textContent = `depuis ${fmtClock(n.t)}`;
    fg.style.strokeDashoffset = 0; fg.style.stroke = 'var(--ac)';
  } else {
    const span = n.sameDay && today.length ? n.I * MIN : Math.max(n.t - (today.length ? today[today.length - 1].t : now), 1);
    const frac = 1 - Math.min(1, (n.t - now) / span);
    $('#ringCaption').textContent = n.sameDay ? 'Prochaine taffe dans' : 'Fini pour aujourd\'hui';
    $('#countdown').textContent = fmtCount(n.t - now);
    $('#ringSub').textContent = (n.sameDay ? 'à ' : 'reprise ') + (n.sameDay ? fmtClock(n.t) : fmtDate(n.t) + ' ' + fmtClock(n.t));
    fg.style.strokeDashoffset = 553 * (1 - (n.sameDay ? frac : 0)); fg.style.stroke = 'var(--warn)';
    btn.classList.add(n.sameDay ? 'early' : 'locked');
  }
  const last = S.log[S.log.length - 1];
  $('#undoBtn').hidden = !(last && now - last.t < 5 * MIN);

  $('#sToday').textContent = today.length;
  $('#sLeft').textContent = free ? 0 : Math.max(0, B - today.length);
  $('#sInterval').textContent = fmtI(I);
  $('#sMl').textContent = free ? '0' : n1(Math.max(0, B - today.length) * mlPerTaffe());
  $('#tipCard').textContent = '💡 ' + TIPS[(dayIndex(now) + Math.floor(now / 3600000)) % TIPS.length];
  $('#holdBtn').hidden = free || S.holds.includes(k) || d <= 0;

  renderPlan(d); renderStats(); renderNotifUi();
  const key = JSON.stringify([S.log.length, S.holds.length, S.notif, k, n.t]);
  if (key !== lastSyncKey) { lastSyncKey = key; sync(); }
}
function planEnd() { return dayStart(S.setup.start) + (N() + S.holds.length) * DAY + geo().off * MIN; }

function svgLine(points, maxY, opts = {}) {
  const w = 320, h = 140, pad = 4;
  const xs = (i) => pad + (i / Math.max(1, points.length - 1)) * (w - 2 * pad);
  const ys = (v) => h - pad - (v / maxY) * (h - 2 * pad);
  const path = points.map((v, i) => (i ? 'L' : 'M') + xs(i).toFixed(1) + ' ' + ys(v).toFixed(1)).join('');
  const mark = opts.mark != null && opts.mark < points.length ? `<circle cx="${xs(opts.mark)}" cy="${ys(points[opts.mark])}" r="5" fill="var(--warn)"/>` : '';
  return `<svg viewBox="0 0 ${w} ${h}"><path d="${path} L${xs(points.length - 1)} ${h - pad} L${pad} ${h - pad}Z" fill="#3ddc8418"/><path d="${path}" fill="none" stroke="var(--ac)" stroke-width="2.5"/>${mark}</svg>`;
}
function renderPlan(d) {
  const n = N(), pts = [];
  for (let i = 0; i <= n; i++) pts.push(budget(i));
  const pct = Math.min(100, Math.max(0, (d / n) * 100));
  $('#planBar').style.width = pct + '%';
  $('#planSummary').innerHTML = d >= n ? 'Plan terminé 🎉' :
    `Aujourd'hui : <b>${budget(d)} taffes max</b>, une toutes les <b>${fmtI(interval(d))}</b>. Départ : ${n0(baselinePerDay())}/jour. Arrêt complet le <b>${fmtDate(planEnd())}</b>.`;
  $('#planChart').innerHTML = svgLine(pts, pts[0] * 1.05, { mark: Math.max(0, d) });
  const ml = mlPerTaffe(), mg = S.setup.mg;
  let rows = '<tr><th>Semaine</th><th>Écart</th><th>Taffes/j</th><th>ml/j</th><th>mg nico/j</th></tr>';
  for (let w = 0; w * 7 < n; w++) {
    const di = w * 7, cur = d >= di && d < di + 7;
    rows += `<tr class="${cur ? 'cur' : ''}"><td>S${w + 1}</td><td>${fmtI(interval(di))}</td><td>${budget(di)}</td><td>${n1(budget(di) * ml)}</td><td>${n0(budget(di) * ml * mg)}</td></tr>`;
  }
  rows += `<tr class="${d >= n ? 'cur' : ''}"><td>Ensuite</td><td>—</td><td>0</td><td>0</td><td>0</td></tr>`;
  $('#planTable').innerHTML = rows;
}
function mgAt(t) { let mg = S.setup.mg; const h = S.mgHistory || []; for (const x of h) if (x.t <= t) mg = x.mg; return h.length ? mg : S.setup.mg; }
function renderStats() {
  const now = Date.now(), base = baselinePerDay(), ml = mlPerTaffe(), days = dayIndex(now) + 1;
  // jour courant compté au prorata du temps écoulé dans la journée
  const { ws } = win(now), W = geo().W;
  const fracToday = Math.min(1, Math.max(0, (now - ws) / (W * MIN)));
  const expected = base * (days - 1 + fracToday);
  const avoided = Math.max(0, expected - S.log.length);
  const mgAvoided = avoided * ml * S.setup.mg;
  $('#stAvoided').textContent = n0(avoided);
  $('#stMl').textContent = n1(avoided * ml);
  $('#stMg').textContent = n0(mgAvoided);
  $('#stMoney').textContent = (avoided * ml / S.setup.mlPerPuff * S.setup.price).toFixed(2).replace('.', ',') + ' €';
  // baisse sur les 7 derniers jours complets (ou ce qui existe)
  let sum = 0, cnt = 0, streak = 0, streakOn = true;
  const bars = [];
  for (let i = 0; i < 14; i++) {
    const t = now - i * DAY; if (dayIndex(t) < 0) break;
    const k = dayKey(t), c = taffesOf(k).length, b = budget(planDay(t));
    if (i > 0 && i <= 7) { sum += c; cnt++; }
    if (i > 0) { if (streakOn && c <= b) streak++; else streakOn = false; }
    bars.unshift({ k, c, b, today: i === 0 });
  }
  if (!cnt) { sum = S.log.length; cnt = fracToday || 1; }
  const reduc = Math.max(0, 1 - sum / cnt / base);
  $('#stReduc').textContent = Math.round(reduc * 100) + ' %';
  $('#stStreak').textContent = streak;
  // histogramme
  const w = 320, h = 140, maxV = Math.max(1, ...bars.map((x) => Math.max(x.c, x.b))) * 1.1, bw = w / 14;
  let svg = `<svg viewBox="0 0 ${w} ${h + 16}">`;
  bars.forEach((x, i) => {
    const X = i * bw + 3, bh = (x.c / maxV) * h, by = h - (x.b / maxV) * h;
    svg += `<rect x="${X}" y="${h - bh}" width="${bw - 6}" height="${bh}" rx="3" fill="${x.c <= x.b ? 'var(--ac)' : 'var(--bad)'}" opacity="${x.today ? .55 : 1}"/>`;
    svg += `<line x1="${X - 2}" x2="${X + bw - 4}" y1="${by}" y2="${by}" stroke="var(--mu)" stroke-dasharray="3 2"/>`;
    svg += `<text x="${X + (bw - 6) / 2}" y="${h + 12}" fill="var(--mu)" font-size="9" text-anchor="middle">${+x.k.slice(8)}</text>`;
  });
  $('#histChart').innerHTML = svg + '</svg>';
  // puff actuelle
  const since = S.log.filter((e) => e.t >= (S.puffStart || 0)).length;
  const used = since * ml, rest = Math.max(0, S.setup.mlPerPuff - used);
  const curB = budget(planDay(now)) || 1;
  $('#puffBar').style.width = Math.min(100, (used / S.setup.mlPerPuff) * 100) + '%';
  $('#puffText').innerHTML = `Environ <b>${n1(rest)} ml</b> restants sur ${S.setup.mlPerPuff} ml (${since} taffes depuis le ${fmtDate(S.puffStart)}). Au rythme du plan, elle devrait durer encore <b>~${n1(rest / (curB * ml))} jours</b>.`;
  // détail du jour
  const k = dayKey(now), today = taffesOf(k), earlyN = today.filter((e) => e.early).length;
  $('#todayDetail').innerHTML = `${today.length} taffes · ≈ ${n1(today.length * ml)} ml · ≈ ${n0(today.length * ml * mgAt(now))} mg de nicotine` +
    (earlyN ? ` · ${earlyN} en avance` : '') + `<br>Ton ancien rythme à cette heure-ci : ≈ ${n0(base * fracToday)} taffes.` +
    (today.length ? `<br>Dernière taffe à ${fmtClock(today[today.length - 1].t)}.` : '');
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
const SOS_TIPS = ['Bois un grand verre d\'eau, lentement.', 'Lève-toi, marche 2 minutes.', 'Occupe tes mains : téléphone, balle, élastique.', 'Rappelle-toi pourquoi tu arrêtes.', 'Chewing-gum ou fruit si t\'en as.'];
let sosIv;
function openSos() {
  $('#sos').hidden = false;
  $('#sosTips').innerHTML = SOS_TIPS.sort(() => Math.random() - 0.5).slice(0, 3).map((x) => `<li>${x}</li>`).join('');
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
  $('#puffBtn').onclick = takePuff;
  $('#undoBtn').onclick = undo;
  $('#holdBtn').onclick = hold;
  $('#sosBtn').onclick = openSos;
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
