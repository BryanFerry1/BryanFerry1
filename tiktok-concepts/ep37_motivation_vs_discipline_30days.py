"""EP37 - MOTIVATION VS DISCIPLINE  (30 days of 5 AM runs, EP19 split-screen format)

Split screen, both run from the first frame. DAY counter + progress bar of the
TOTAL KM on the divider (Motivation's red dot starts ahead, then falls behind).
TOP     MOTIVATION: days 1-3 sprints (LET'S GO!). Day 4 rain: stays in bed
        (NOT TODAY). Days 5-9: phone in bed, SKIP SKIP SKIP. Day 10: watches a
        motivational video, jumps up (NEW ME!), sprints like crazy. Day 12:
        hands on knees (TOO HARD), back to bed. Days 21-29: SKIP. Day 30: shows
        up and runs his best run ever (NEW RECORD!).
BOTTOM  DISCIPLINE: runs every single day, same pace, rain, night, snow.
        Days 21-29 he is tired, slower, head down... runs anyway.
STATS   per lane: DAYS / TOTAL / BEST PACE. Motivation wins BEST, Discipline
        wins DAYS and TOTAL.
END     MOTIVATION HAD / THE BEST DAYS. / DISCIPLINE HAD / ALL OF THEM.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import fit_font, FPS, RED, WHITE, W, clamp, draw_spaced, font, paint, rotate_pose, run_pose, smoothstep
from kit import Log, Video, blend, caption, draw_body, ending, lane_cam, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep37_motivation_vs_discipline_30days"
dt = 1 / FPS
S = 118.0
LANES = {"MOTIVATION": (330, 935, 860), "DISCIPLINE": (965, 1565, 1475)}
RUN_SX = 400.0
STRIDE = 2.6
DAY_KF = [(0, 1), (3.6, 3), (4.0, 4), (6.0, 4), (6.2, 5), (8.4, 9), (8.6, 10), (11.0, 10), (11.2, 11), (14.0, 20),
          (14.2, 21), (16.0, 29), (16.2, 30), (30, 30)]
NEWME = 9.4
GIVEUP = (12.2, 13.4)
D_FIN = 18.2
M_STOP = 19.7
STATS = 99.0
END_T = 22.4
DUR = 26.4
M_KM = [(0, 0), (3.8, 45), (9.4, 45), (11.0, 70), (12.2, 88), (16.2, 88), (M_STOP, 104)]
D_KM = [(0, 0), (16.2, 290), (D_FIN, 300)]
# full-screen zooms: (t0, t1, lane, s0, s1, dx, wy0, wy1)
FULL = [(4.3, 5.9, "MOTIVATION", 235, 265, -0.4, 1.3, 1.2),
        (8.6, 10.0, "MOTIVATION", 245, 275, 0.0, 1.5, 1.4),
        (12.3, 13.4, "MOTIVATION", 240, 265, 0.0, 1.4, 1.3),
        (14.5, 16.1, "DISCIPLINE", 230, 260, 0.0, 1.5, 1.4),
        (17.9, 19.5, "DISCIPLINE", 215, 245, 0.2, 1.5, 1.4),
        (19.5, 22.4, "MOTIVATION", 240, 70, 0.0, 1.3, 5.5)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def day(t):
    return int(keys(t, DAY_KF) + 1e-6)


def weather(d):
    if d == 4:
        return "rain"
    if 5 <= d <= 9:
        return "rain" if d % 2 else "sun"
    if 11 <= d <= 20:
        return "snow" if d % 3 == 0 else "night"
    if 21 <= d <= 29:
        return "rain" if d % 2 else "night"
    return "sun"


def m_activity(t):
    if t < 4.0:
        return "sprint"
    if t < 8.6:
        return "bed" if t < 6.0 else "phone"
    if t < NEWME:
        return "video"
    if t < 11.0:
        return "burst"
    if t < GIVEUP[0]:
        return "fade"
    if t < GIVEUP[1]:
        return "knees"
    if t < 16.2:
        return "phone"
    if t < M_STOP:
        return "record"
    return "stop"


def m_speed(a, t):
    return {"sprint": 5.5, "burst": 7.5, "fade": 5.0 - 2.5 * smoothstep(11.0, GIVEUP[0], t), "record": 7.0}.get(a, 0.0)


def d_speed(t):
    if t >= D_FIN + 0.4:
        return 1.6
    return 2.6 if 14.2 <= t < 16.2 else 3.6


def full_at(t):
    for f in FULL:
        if f[0] <= t < f[1]:
            return f
    return None


def presim():
    pos = {"MOTIVATION": 0.0, "DISCIPLINE": 0.0}
    out = []
    for fi in range(int(DUR * FPS) + 2):
        t = fi * dt
        out.append(dict(pos))
        pos["MOTIVATION"] += m_speed(m_activity(t), t) * dt
        pos["DISCIPLINE"] += d_speed(t) * dt
    return out


SIM = presim()
GATE_X = SIM[int(D_FIN * FPS)]["DISCIPLINE"] + 0.45
SIGN_X = SIM[int(M_STOP * FPS)]["MOTIVATION"] + 2.6


# ------------------------------------------------------------------ props
def bed(c, cam, x, alpha=1.0):
    w = max(3, 0.05 * cam.s)
    c.drawLine(*cam.pt((x - 2.0, 0.6)), *cam.pt((x + 1.5, 0.6)), paint(WHITE, 0.8 * alpha, w))
    c.drawLine(*cam.pt((x - 2.0, 0.0)), *cam.pt((x - 2.0, 1.3)), paint(WHITE, 0.8 * alpha, w))
    c.drawLine(*cam.pt((x + 1.5, 0.0)), *cam.pt((x + 1.5, 0.85)), paint(WHITE, 0.8 * alpha, w))
    px, py = cam.pt((x - 1.55, 0.78))
    c.drawRoundRect(skia.Rect(px - 0.32 * cam.s, py - 0.14 * cam.s, px + 0.32 * cam.s, py + 0.14 * cam.s), 10, 10,
                    paint(WHITE, 0.6 * alpha, 3))


def lying(x, t):
    j = rotate_pose(stand(x + 1.1, 0, 0.1, 0.1, 0.1, 0.1), np.array([x + 1.1, 0.0]), math.pi / 2)
    return {k: v + [0, 0.75 + 0.01 * math.sin(t * 2)] for k, v in j.items()}


def bed_phone(x, t):
    j = sit(x - 0.8, 0.62, t, 0.5)
    sh = j["shoulder"]
    from engine import L_FARM, L_UARM, ik
    ph = sh + np.array([0.6, 0.1])
    for i, o in ((1, 0.0), (2, -0.04)):
        h = ph + np.array([o, -0.12])
        j[f"hand{i}"] = h
        j[f"elbow{i}"] = ik(sh, h, L_UARM, L_FARM, -1)
    return j, ph


def draw_phone(c, cam, p, glow, fire=0.0, t=0.0):
    sx, sy = cam.pt(p)
    w, h = 0.2 * cam.s, 0.34 * cam.s
    r = skia.Rect(sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2)
    c.drawRoundRect(r, 5, 5, paint((0, 0, 0), 1.0))
    c.drawRoundRect(r, 5, 5, paint(WHITE, 1.0, 3))
    c.drawRoundRect(r, 5, 5, paint(RED if fire else WHITE, 0.35 + 0.4 * fire * (0.5 + 0.5 * math.sin(t * 30))))


def sky(e, f_, cam, y0, y1, wth, t, k):
    if wth == "sun":
        cx, cy = 190, y0 + 95
        e.drawCircle(cx, cy, 34, paint(WHITE, 0.9, 4))
        for q in range(8):
            a = q * math.pi / 4 + t * 0.5
            e.drawLine(cx + 48 * math.cos(a), cy + 48 * math.sin(a), cx + 66 * math.cos(a), cy + 66 * math.sin(a),
                       paint(WHITE, 0.7, 3))
    elif wth in ("night", "snow"):
        e.drawCircle(190, y0 + 95, 36, paint(WHITE, 0.9))
        e.drawCircle(206, y0 + 85, 33, paint((0, 0, 0), 1.0))
    if wth == "rain":
        rng = np.random.default_rng(k)
        for q in range(46):
            x0 = rng.uniform(0, W)
            yy = y0 + ((rng.uniform(0, 1) + t * 2.2) % 1.0) * (y1 - y0)
            f_.drawLine(x0, yy, x0 - 10, yy + 34, paint(WHITE, 0.4, 2))
    if wth == "snow":
        rng = np.random.default_rng(k + 5)
        for q in range(40):
            x0 = rng.uniform(0, W) + 20 * math.sin(t * 2 + q)
            yy = y0 + ((rng.uniform(0, 1) + t * 0.35) % 1.0) * (y1 - y0)
            f_.drawCircle(x0, yy, 4, paint(WHITE, 0.8))


def stamp(c, x, y, text, u, col=RED):
    if u <= 0 or u >= 1:
        return
    a = 1 - smoothstep(0.7, 1.0, u)
    sc = 1 + 0.6 * math.exp(-u * 14)
    f = font(int(54 * sc), "InterDisplay-Black")
    from engine import spaced_width
    w = spaced_width(text, f, 4) + 40
    c.save()
    c.translate(x, y)
    c.rotate(-8)
    c.drawRoundRect(skia.Rect(-w / 2, -54 * sc, w / 2, 18 * sc), 8, 8, paint(col, a, 5))
    draw_spaced(c, text, 0, 0, f, 4, paint(col, a))
    c.restore()


def render(stills=None):
    from engine import Camera
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    ph = {"MOTIVATION": 0.0, "DISCIPLINE": 0.7}
    contact = {}
    last_day = 1
    for fi in range(v.n):
        t = fi * dt
        pos = SIM[fi]
        d = day(t)
        if d != last_day:
            log.add(t, "day", d)
            last_day = d
        a = m_activity(t)
        spd = {"MOTIVATION": m_speed(a, t), "DISCIPLINE": d_speed(t)}
        for n in pos:
            ph[n] += (spd[n] / STRIDE) * 2 * math.pi * dt * (0.7 if n == "MOTIVATION" else 1.0)
            for leg in range(2):
                c = math.floor((ph[n] + leg * math.pi - 1.87) / (2 * math.pi))
                key = n + str(leg)
                if contact.get(key) is not None and c != contact[key] and spd[n] > 0.5:
                    log.add(t, "step_" + n, int(t * 100))
                contact[key] = c
        for key, tt, kind in (("go", 0.0, "go"), ("rain", 4.0, "rain"), ("video", 8.6, "video"),
                              ("newme", NEWME, "newme"), ("giveup", GIVEUP[0], "giveup"), ("tired", 14.2, "tired"),
                              ("d30", 16.2, "d30"), ("record", 17.0, "record"), ("dfin", D_FIN, "dfin"),
                              ("mstop", M_STOP, "mstop"), ("end", END_T, "end"), ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, f in enumerate(FULL):
            if t >= f[0]:
                log.once(f"full{k}", f[0], "zoom")
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        wth = weather(d)
        fz = full_at(t)
        if fz is None:
            panes = []
            for n, (y0, y1, gy) in LANES.items():
                cam = lane_cam(S, gy, pos[n])
                cam.sx = RUN_SX
                panes.append((n, y0, y1, cam, False))
        else:
            t0, t1, n, s0, s1, dx, wy0, wy1 = fz
            u = smoothstep(t0, t1, t) if n == "MOTIVATION" and t0 == 19.5 else (t - t0) / (t1 - t0)
            if t0 == 19.5:
                u = smoothstep(M_STOP + 0.7, t1 - 0.3, t)
            cam = Camera()
            cam.s = s0 + (s1 - s0) * u
            cam.wx = pos[n] + dx + (4.0 * u if t0 == 19.5 else 0.0)
            cam.wy = wy0 + (wy1 - wy0) * u
            cam.sx, cam.sy = 450, 960
            panes = [(n, 0, 2000, cam, True)]
        for n, y0, y1, cam, full in panes:
            x = pos[n]
            gy = cam.pt((0, 0))[1]
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.55, 2.5))
            k0 = math.floor(cam.wx - 600 / cam.s)
            for k in range(k0, k0 + int(1200 / cam.s) + 2):
                sx, _ = cam.pt((k * 1.0, 0))
                e.drawLine(sx, gy + 10, sx - 18, gy + 26, paint(WHITE, 0.16, 2))
            sky(e, f_, cam, y0 if not full else 330, y1 if not full else 1560, wth, t, d)
            col = RED if n == "MOTIVATION" else WHITE
            txt = None
            j = None
            if n == "DISCIPLINE" and t > 15.6:
                for px in (GATE_X - 0.45, GATE_X + 0.45):
                    e.drawLine(*cam.pt((px, 0)), *cam.pt((px, 2.9)), paint(WHITE, 0.7, 4))
                e.drawLine(*cam.pt((GATE_X - 0.45, 2.9)), *cam.pt((GATE_X + 0.45, 2.9)), paint(WHITE, 0.7, 4))
                gx_, gy_ = cam.pt((GATE_X, 2.9))
                draw_spaced(tc, "FINISH", gx_, gy_ - 12, font(0.22 * cam.s, "InterDisplay-Black"), 3, paint(WHITE, 0.9))
                if t < D_FIN:
                    f_.drawLine(*cam.pt((GATE_X - 0.45, 1.6)), *cam.pt((GATE_X + 0.45, 1.6)), paint(RED, 1.0, 6))
                else:
                    b = min(1.0, (t - D_FIN) / 0.4)
                    for side, x0 in ((-1, GATE_X - 0.45), (1, GATE_X + 0.45)):
                        f_.drawLine(*cam.pt((x0, 1.6)), *cam.pt((x0 + side * 0.1, 1.6 - 1.1 * b)), paint(RED, 1.0, 6))
            if n == "MOTIVATION" and t > 16.2:
                sx_, sy_ = cam.pt((SIGN_X, 0))
                e.drawLine(sx_, sy_, sx_, sy_ - 2.2 * cam.s, paint(WHITE, 0.7, 4))
                bw, bh = 1.9 * cam.s, 0.75 * cam.s
                r = skia.Rect(sx_ - bw / 2, sy_ - 2.9 * cam.s, sx_ + bw / 2, sy_ - 2.9 * cam.s + bh)
                e.drawRect(r, paint((0, 0, 0), 1.0))
                e.drawRect(r, paint(WHITE, 0.8, 3, cap=False))
                draw_spaced(tc, "FINISH", sx_, r.top() + bh * 0.42, font(max(10, 0.26 * cam.s), "InterDisplay-Black"), 3,
                            paint(WHITE, 0.9))
                draw_spaced(tc, "196 KM →", sx_, r.top() + bh * 0.85, font(max(10, 0.26 * cam.s), "InterDisplay-Black"), 2,
                            paint(RED, 1.0))
            if n == "MOTIVATION":
                if a in ("sprint", "burst", "record", "fade"):
                    inten = 1.0 if a != "fade" else 1.0 - 0.5 * smoothstep(11.0, GIVEUP[0], t)
                    j = run_pose(x, ph[n], inten, 0, 0.2 + (0.2 if a == "fade" else 0), 0.0)
                    if a == "sprint" and t < 2.6:
                        txt = "LET'S GO!"
                    if a == "burst":
                        txt = "NEW ME!" if t < NEWME + 0.9 else None
                    if a == "fade" and t > 11.5:
                        txt = "..."
                    if a == "record" and t > 17.0:
                        txt = "NEW RECORD!"
                    if a in ("burst", "record"):
                        for q in range(6):
                            yy = 0.4 + q * 0.35
                            sx_, sy_ = cam.pt((x - 0.9 - 0.3 * (q % 2), yy))
                            hc.drawLine(sx_, sy_, sx_ - 0.9 * cam.s, sy_, paint(RED, 0.6, 3))
                elif a == "knees":
                    j = stand(x, 0.6, 0.45, 0.4, 0.2, 0.2, 0.5, -0.12)
                    txt = "TOO HARD"
                elif a == "stop":
                    u = smoothstep(M_STOP, M_STOP + 0.4, t)
                    j = blend(run_pose(x, ph[n], 0.6), stand(x, 0.6, 0.45, 0.4, 0.2, 0.2, 0.5, -0.12), u)
                    if t > M_STOP + 1.3:
                        j = blend(j, sit(x - 0.3, 0.0, t, 0.8), smoothstep(M_STOP + 1.3, M_STOP + 1.8, t))
                    txt = "TOO FAR..." if M_STOP + 0.3 < t < M_STOP + 1.6 else None
                elif a == "bed":
                    bed(e, cam, x)
                    j = lying(x + 0.15, t)
                    txt = "NOT TODAY"
                elif a in ("phone", "video"):
                    bed(e, cam, x)
                    jb, p = bed_phone(x, t)
                    draw_body(hc, jb, cam, col, 1.0, 0.15)
                    draw_phone(hc, cam, p, 1.0, 1.0 if a == "video" else 0.0, t)
                    if a == "video":
                        hx, hy = cam.pt(p + np.array([0, 0.35]))
                        for q in range(3):
                            fl = 0.3 + 0.15 * math.sin(t * 20 + q * 2)
                            f_.drawCircle(hx + (q - 1) * 0.12 * cam.s, hy - fl * cam.s * 0.5, (0.09 + 0.05 * (q % 2)) * cam.s,
                                          paint(RED, 0.8))
                        txt = "MOTIVATIONAL VIDEO"
            else:
                tired = 14.2 <= t < 16.2
                if t < D_FIN - 0.2 or t > D_FIN + 0.3:
                    j = run_pose(x, ph[n], 0.55 if tired else 0.8, 0, 0.3 if tired else 0.15, 0.45 if tired else 0.05)
                else:
                    j = run_pose(x, ph[n], 0.9, 0, 0.55, 0.15)
                if t > D_FIN + 0.5:
                    j = blend(j, stand(x, -0.05, 2.7, 2.9, 0.2, 0.2, -0.2), smoothstep(D_FIN + 0.5, D_FIN + 0.9, t))
                if tired:
                    txt = "TIRED. RAN ANYWAY."
            if j is not None:
                draw_body(hc, j, cam, col, 1.0, 0.15)
            if txt:
                jj = j if j is not None else stand(x, 0, 0, 0, 0, 0)
                hx, hy = cam.pt(jj["head"])
                hx = min(max(hx, 250), 640)
                fs = 40 if not full else 56
                ty = min(hy, gy - 2.3 * cam.s) - 0.45 * cam.s
                if full:
                    ty = max(ty, 610)
                draw_spaced(tc, txt, hx, ty, fit_font(txt, fs, "InterDisplay-Black", 2, 600), 2,
                            paint(col, 1.0))
            lx, _ = cam.pt((x - (0.8 if a in ("bed", "phone", "video") and n == "MOTIVATION" else 0), 0))
            draw_spaced(tc, n, lx, gy + (44 if not full else 60), font(26 if not full else 36, "Inter-Bold"), 5,
                        paint(col, 1.0))
            if not full:
                tot = keys(t, M_KM if n == "MOTIVATION" else D_KM)
                draw_spaced(tc, f"{int(tot)} KM", 770, y0 + 60, font(40, "InterDisplay-Black"), 2,
                            paint(WHITE, 0.9 * smoothstep(2.4, 2.7, t)))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
            if n == "MOTIVATION" and a in ("phone", "bed") and not full:
                tday = keys(t, DAY_KF)
                u = tday - math.floor(tday)
                if (6.0 <= t < 8.6) or (14.2 <= t < 16.2):
                    stamp(oc, 640, y0 + 330, "SKIP", min(0.99, u * 1.6) if u < 0.62 else 0.99)
        if fz is None:
            y = 950
            oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
            draw_spaced(oc, f"DAY {d}", 150, 964, font(36, "InterDisplay-Black"), 3, paint(WHITE, 1.0))
            oc.drawLine(270, y, 840, y, paint(WHITE, 0.35, 3))
            oc.drawLine(840, y - 12, 840, y + 12, paint(WHITE, 0.8, 3))
            for n, c_ in (("DISCIPLINE", WHITE), ("MOTIVATION", RED)):
                px = 270 + 570 * clamp(keys(t, M_KM if n == "MOTIVATION" else D_KM) / 300)
                oc.drawCircle(px, y, 11, paint(c_, 1.0))
        else:
            n = fz[2]
            draw_spaced(oc, f"DAY {d}", 470, 420, font(60, "InterDisplay-Black"), 4, paint(WHITE, 1.0))
            tot = keys(t, M_KM if n == "MOTIVATION" else D_KM)
            draw_spaced(oc, f"{int(tot)} KM", 470, 490, font(40, "InterDisplay-Black"), 3,
                        paint(RED if n == "MOTIVATION" else WHITE, 0.9))
        if t < 2.5:
            caption(oc, "MOTIVATION VS DISCIPLINE", 405, 1 - smoothstep(2.1, 2.5, t), WHITE, 46)
            draw_spaced(oc, "30 DAYS. 5 AM.", 680, 1030, font(36, "InterDisplay-Black"), 2,
                        paint(RED, (1 - smoothstep(2.1, 2.5, t)) * smoothstep(0.2, 0.4, t)))
        ending(oc, t, END_T - 0.3, [(END_T, "MOTIVATION", RED, 110), (END_T + 0.3, "STARTS.", RED, 110),
                                    (END_T + 1.1, "DISCIPLINE", WHITE, 110), (END_T + 1.4, "FINISHES.", WHITE, 120)],
               gap=125)
        cut = 0.0
        for tt in [4.0, 8.6, NEWME, 11.0, 14.2, 16.2] + [f[0] for f in FULL] + [f[1] for f in FULL]:
            if tt <= t < tt + 0.1:
                cut = 0.07
        flash = 0.6 * math.exp(-(t - D_FIN) * 4) if t >= D_FIN else 0.0
        v.compose(fi, t, flash=flash, white=cut, dim=0.2 if wth in ("night", "snow") else 0.0, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=16.2), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add_bed(sfx.rain(2.0), gain=0.35, start=4.0, stop=6.0, fade_in=0.1, fade_out=0.3)
    last = {"MOTIVATION": -1.0, "DISCIPLINE": -1.0}
    for t, kind, _, extra in events:
        if kind.startswith("step_"):
            n = kind[5:]
            if t - last[n] < 0.08:
                continue
            last[n] = t
            m.add(t, (sfx.step_light if n == "MOTIVATION" else sfx.step_heavy)(extra), 0.22, 0.0, 0.1)
        elif kind == "day":
            m.add(t, sfx.tick(2600, 0.3), 0.5, 0, 0.1)
            if 5 <= extra <= 9 or 21 <= extra <= 29:
                m.add(t + 0.05, sfx.text_hit(extra), 0.35, 0, 0.3)
        elif kind == "go":
            m.add(0.0, sfx.beep(1320, 0.35), 0.6, 0, 0.3)
        elif kind == "rain":
            m.add(t, sfx.thunder(2), 0.6, 0, 0.5)
        elif kind == "video":
            m.add(t, sfx.riser(NEWME - t), 0.5, 0, 0.3)
        elif kind == "newme":
            m.add(t, sfx.boom(2.0), 0.8, 0, 0.5)
            m.add(t, sfx.power_up(220), 0.5, 0, 0.4)
        elif kind == "giveup":
            m.add(t, sfx.power_down(1.4), 0.6, 0, 0.4)
            m.add(t + 0.2, sfx.breath(1, 0.6), 0.5, 0, 0.3)
        elif kind == "tired":
            for q in range(3):
                m.add(t + q * 0.6, sfx.breath(q, 0.45), 0.4, 0, 0.3)
        elif kind == "d30":
            m.add(t, sfx.text_hit(5), 0.7, 0, 0.4)
        elif kind == "record":
            m.add(t, sfx.chime(1320, 0.3), 0.6, 0, 0.5)
            m.add(t, sfx.sparkle(1.2), 0.4, 0, 0.5)
        elif kind == "zoom":
            m.add(t, sfx.whoosh(0.3, 400, 8000, 0.4, seed=int(t)), 0.35, 0, 0.2)
        elif kind == "dfin":
            m.add(t, sfx.boom(2.5), 0.8, 0, 0.5)
            m.add(t, sfx.applause(2.0, 30, 4), 0.35, 0, 0.3)
        elif kind == "mstop":
            m.add(t, sfx.power_down(1.6), 0.5, 0, 0.4)
            m.add(t + 0.4, sfx.breath(2, 0.6), 0.5, 0, 0.3)
            m.add(t + 1.0, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 3.0, 5.0, 7.0, 9.0, 9.7, 11.7, 12.8, 13.8, 15.0, 17.0, 18.4, 19.0, 20.0, 21.0, 22.2, 25.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
