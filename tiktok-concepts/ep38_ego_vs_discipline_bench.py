"""EP38 - EGO VS DISCIPLINE  (bench press, 52 weeks, split screen + zooms)

WEEK 1   EGO loads 140 KG (LIGHT WEIGHT!), DISCIPLINE loads 60 KG.
ZOOM     EGO: bar comes down... stuck on his chest (HELP!), a spotter saves him.
ZOOM     DISCIPLINE: 8 clean reps.
WEEKS    time-lapse: EGO takes selfies / SKIP / SKIP... DISCIPLINE adds +2.5 KG
         every week.
ZOOM     WEEK 20: EGO injured, arm in a sling.
WEEKS    EGO comes back at 100 KG (lighter than week 1). DISCIPLINE keeps climbing.
WEEK 52  ZOOM EGO loads 140 again... stuck again (NOT AGAIN).
         ZOOM DISCIPLINE loads 160 KG: slow, shaking... LOCKOUT.
END      EGO STARTED HEAVY. / DISCIPLINE ENDED HEAVY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, fit_font, font, ik,
                    paint, smoothstep)
from kit import GREY, Log, Video, caption, draw_body, ending, lane_cam, sit, stand
from ep37_motivation_vs_discipline_30days import stamp
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep38_ego_vs_discipline_bench"
dt = 1 / FPS
S = 165.0
LANES = {"EGO": (330, 935, 860), "DISCIPLINE": (965, 1565, 1475)}
SX = 470.0
X0 = 0.3                         # bench hip x
WEEK_KF = [(0, 1), (7.0, 1), (11.0, 19), (11.1, 20), (13.0, 20), (13.1, 21), (16.0, 51), (16.1, 52), (40, 52)]
E_KG = [(0, 20), (2.2, 140), (11.0, 140), (11.1, 0), (13.0, 0), (13.1, 100), (16.0, 100), (16.6, 140)]
D_KG = [(0, 20), (1.4, 60), (7.0, 60), (16.0, 150), (16.6, 150), (17.6, 160)]
FULL = [(2.5, 5.0, "EGO", 230, 255), (5.0, 6.9, "DISCIPLINE", 230, 255), (11.1, 13.0, "EGO", 220, 245),
        (16.4, 18.2, "EGO", 225, 250), (18.2, 20.6, "DISCIPLINE", 225, 270)]
E_STUCK1 = (3.4, 4.3)
E_STUCK2 = (17.2, 18.2)
D_FINAL = (18.4, 20.0)
LOCK = 19.6
END_T = 21.0
DUR = 25.0


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def week(t):
    return int(keys(t, WEEK_KF) + 1e-6)


def kg_of(n, t):
    v = keys(t, E_KG if n == "EGO" else D_KG)
    return int(round(v / 2.5) * 2.5) if n == "DISCIPLINE" else int(round(v / 20) * 20)


# ------------------------------------------------------------------ props
def bench(c, cam, x):
    w = max(3, 0.05 * cam.s)
    c.drawLine(*cam.pt((x - 1.55, 0.62)), *cam.pt((x + 0.45, 0.62)), paint(WHITE, 0.75, w * 1.4))
    for lx in (x - 1.35, x + 0.25):
        c.drawLine(*cam.pt((lx, 0.62)), *cam.pt((lx, 0.0)), paint(WHITE, 0.55, w))
    rx = x - 1.75                                     # rack upright
    c.drawLine(*cam.pt((rx, 0.0)), *cam.pt((rx, 2.15)), paint(WHITE, 0.6, w))
    c.drawLine(*cam.pt((rx, 1.95)), *cam.pt((rx + 0.25, 1.95)), paint(WHITE, 0.6, w))
    c.drawLine(*cam.pt((rx + 0.25, 1.95)), *cam.pt((rx + 0.25, 2.08)), paint(WHITE, 0.6, w))


def barbell(c, cam, cx, y, kg, col, alpha=1.0, shake=0.0):
    cx += shake
    w = max(3, 0.05 * cam.s)
    c.drawLine(*cam.pt((cx - 0.95, y)), *cam.pt((cx + 0.95, y)), paint(WHITE, alpha, w))
    rest = max(0.0, kg - 20) / 2
    plates = []
    while rest >= 20 - 1e-6:
        plates.append(0.62)
        rest -= 20
    while rest >= 5 - 1e-6:
        plates.append(0.4 if rest >= 10 else 0.28)
        rest -= 10 if rest >= 10 else 5
    for side in (-1, 1):
        px = cx + side * 0.55
        for hgt in plates:
            x0, x1 = (px, px + side * 0.1)
            r = skia.Rect(*cam.pt((min(x0, x1), y + hgt / 2)), *cam.pt((max(x0, x1), y - hgt / 2)))
            c.drawRect(r, paint((0, 0, 0), alpha))
            c.drawRect(r, paint(col, alpha, max(2, 0.035 * cam.s), cap=False))
            px += side * 0.12


def press_pose(x, h, t, shake=0.0):
    """Lying on the bench, head to the left. h: 0 = bar on chest, 1 = lockout."""
    hip = np.array([x, 0.85])
    sh = np.array([x - 0.78, 0.88])
    j = {"hip": hip, "shoulder": sh, "neck": sh + [-0.12, 0.0], "head": sh + [-0.45, 0.04],
         "knee1": np.array([x + 0.6, 1.2]), "foot1": np.array([x + 0.95, 0.03]),
         "knee2": np.array([x + 0.55, 1.15]), "foot2": np.array([x + 0.85, 0.03])}
    by = 1.1 + 0.85 * h
    for i, dx in ((1, 0.05), (2, -0.05)):
        hand = np.array([x - 0.78 + dx + shake, by])
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, 1)
    return j, by


def sling_pose(x, t):
    j = sit(x, 0.62, t, 0.35)
    j["hand1"] = j["shoulder"] + np.array([0.35, -0.15])
    j["elbow1"] = j["shoulder"] + np.array([0.05, -0.5])
    return j


def selfie_pose(x):
    j = stand(x, 0.0, 0.3, 0.2, 1.6, 0.2, -0.1)
    j["hand1"] = j["head"] + np.array([0.55, 0.2])
    j["elbow1"] = j["shoulder"] + np.array([0.4, 0.25])
    return j


def flex_pose(x, t):
    return stand(x, -0.02, 1.57, 1.42, 1.55, 1.65, -0.12, 0.01 * math.sin(t * 3))


# ------------------------------------------------------------------ lane logic
def ego_state(t):
    """(kind, h, txt)"""
    if t < 2.5:
        return "load", 1.0, "LIGHT WEIGHT!" if t > 1.5 else None
    if t < 5.0:
        if t < 2.9:
            return "press", 1.0, None
        if t < E_STUCK1[0]:
            return "press", 1 - ease_out((t - 2.9) / 0.5), None
        if t < E_STUCK1[1]:
            return "stuck", 0.05 + 0.04 * math.sin(t * 30), "HELP!"
        return "spot", smoothstep(E_STUCK1[1], E_STUCK1[1] + 0.5, t), None
    if t < 7.0:
        return "sit", 0, None
    if t < 11.1:
        w = week(t)
        return ("selfie" if w % 3 == 0 else "skip"), 0, None
    if t < 13.1:
        return "sling", 0, "INJURED"
    if t < 16.1:
        return "press", 0.5 + 0.5 * math.cos(t * 4.5), None
    if t < 16.4:
        return "load", 1.0, None
    if t < 16.9:
        return "press", 1.0, None
    if t < E_STUCK2[0]:
        return "press", 1 - ease_out((t - 16.9) / 0.3), None
    if t < E_STUCK2[1]:
        return "stuck", 0.05 + 0.04 * math.sin(t * 30), "NOT AGAIN..."
    return "spot", smoothstep(E_STUCK2[1], E_STUCK2[1] + 0.5, t), None


def disc_state(t):
    if t < 2.5:
        return "load", 1.0, None
    if t < 16.1:
        return "press", 0.5 + 0.5 * math.cos((t - 2.5) * 4.0), None
    if t < D_FINAL[0]:
        return "load", 1.0, None
    # final: down slowly, grind up, lockout
    if t < 18.9:
        return "press", 1 - ease_out((t - D_FINAL[0]) / 0.5), None
    if t < LOCK:
        u = (t - 18.9) / (LOCK - 18.9)
        return "grind", 0.04 + 0.96 * u ** 1.6 + 0.03 * math.sin(t * 34) * (1 - u), None
    return "lock", 1.0, "NEW PR!"


def full_at(t):
    for f in FULL:
        if f[0] <= t < f[1]:
            return f
    return None


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    last_w = 1
    last_kg = {"EGO": 20, "DISCIPLINE": 20}
    for fi in range(v.n):
        t = fi * dt
        w = week(t)
        if w != last_w:
            log.add(t, "week", w)
            last_w = w
        for n in last_kg:
            k = kg_of(n, t)
            if k > last_kg[n] and (t < 2.5 or 16.0 < t < 17.7):
                log.add(t, "plate", 0)
            last_kg[n] = k
        for key, tt, kind in (("s1", E_STUCK1[0], "stuck"), ("sp1", E_STUCK1[1], "spot"), ("inj", 11.1, "injured"),
                              ("s2", E_STUCK2[0], "stuck"), ("sp2", E_STUCK2[1], "spot"), ("grind", 18.9, "grind"),
                              ("lock", LOCK, "lock"), ("end", END_T, "end"), ("end2", END_T + 1.3, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        for k, f in enumerate(FULL):
            if t >= f[0]:
                log.once(f"full{k}", f[0], "zoom")
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        fz = full_at(t)
        if fz is None:
            panes = []
            for n, (y0, y1, gy) in LANES.items():
                cam = lane_cam(S, gy, -0.4)
                cam.sx = SX
                panes.append((n, y0, y1, cam, False))
        else:
            t0, t1, n, s0, s1 = fz
            u = (t - t0) / (t1 - t0)
            cam = Camera()
            cam.s = s0 + (s1 - s0) * u
            cam.wx, cam.wy = -0.5, 1.2
            cam.sx, cam.sy = 470, 1000
            panes = [(n, 0, H, cam, True)]
        flash = 0.0
        for n, y0, y1, cam, full in panes:
            gy = cam.pt((0, 0))[1]
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(0, gy, W, gy, paint(WHITE, 0.5, 2.5))
            col = RED if n == "EGO" else WHITE
            kind, h, txt = (ego_state if n == "EGO" else disc_state)(t)
            kg = kg_of(n, t)
            bench(e, cam, X0)
            cx = X0 - 0.75
            j = None
            if kind == "load":
                j = stand(X0 - 2.35, 0.05, 0.4, 0.3, 0.6, 0.5, 0.1)
                barbell(hc, cam, cx, 2.02, kg, col)
            elif kind in ("press", "stuck", "grind", "lock"):
                shake = 0.02 * math.sin(t * 60) if kind in ("stuck", "grind") else 0.0
                j, by = press_pose(X0, h, t, shake)
                barbell(hc, cam, cx, by, kg, col, 1.0, shake)
                if kind == "stuck":
                    hx, hy = cam.pt(j["head"])
                    for q in range(3):
                        f_.drawCircle(hx - 0.3 * cam.s - q * 0.15 * cam.s, hy - 0.2 * cam.s + 0.1 * math.sin(t * 9 + q) * cam.s,
                                      max(3, 0.03 * cam.s), paint(WHITE, 0.8))
                if kind == "lock" and t < LOCK + 0.5:
                    flash = 0.5 * math.exp(-(t - LOCK) * 5)
            elif kind == "spot":
                j, by = press_pose(X0, 0.0, t)
                yb = by + (2.02 - by) * h
                barbell(hc, cam, cx, yb, kg, col)
                if h > 0.6:
                    j = sit(X0 - 0.4, 0.62, t, 0.6)
                js = stand(X0 - 2.25, 0.2, 1.9, 1.9, 0.3, 0.3, 0.3)
                js["hand1"] = np.array([cx - 0.2, yb + 0.02])
                js["hand2"] = np.array([cx - 0.1, yb + 0.02])
                js["elbow1"] = ik(js["shoulder"], js["hand1"], L_UARM, L_FARM, 1)
                js["elbow2"] = ik(js["shoulder"], js["hand2"], L_UARM, L_FARM, 1)
                draw_body(e, js, cam, GREY, 0.8)
                draw_spaced(tc, "SPOTTER", cam.pt((X0 - 2.25, 0))[0], gy + (44 if not full else 60),
                            font(22 if not full else 30, "Inter-Bold"), 4, paint(GREY, 0.9))
            elif kind == "sit":
                barbell(hc, cam, cx, 2.02, kg, col)
                j = sit(X0 - 0.4, 0.62, t, 0.7)
            elif kind == "selfie":
                barbell(hc, cam, cx, 2.02, 140, col, 0.5)
                j = selfie_pose(X0 - 2.35)
                hx, hy = cam.pt(j["hand1"])
                hc.drawRoundRect(skia.Rect(hx - 0.08 * cam.s, hy - 0.14 * cam.s, hx + 0.08 * cam.s, hy + 0.14 * cam.s), 4, 4,
                                 paint(WHITE, 1.0, 3))
                if int(t * 5) % 3 == 0:
                    f_.drawCircle(hx, hy, 0.45 * cam.s, paint(WHITE, 0.85))
                txt = "#GYMLIFE"
            elif kind == "skip":
                barbell(hc, cam, cx, 2.02, 140, col, 0.5)
            elif kind == "sling":
                barbell(hc, cam, cx, 2.02, 140, col, 0.4)
                j = sling_pose(X0 - 0.4, t)
                a1, a2 = cam.pt(j["shoulder"] + [0.0, 0.05]), cam.pt(j["hand1"] + [0.12, -0.05])
                p = skia.Path()
                p.moveTo(*a1)
                p.lineTo(*a2)
                p.lineTo(*cam.pt(j["elbow1"] + [0.0, -0.1]))
                p.close()
                hc.drawPath(p, paint(RED, 0.9))
            if j is not None:
                draw_body(hc, j, cam, col, 1.0, 0.25 if n == "DISCIPLINE" else 0.15)
            if txt:
                jj = j if j is not None else stand(X0, 0, 0, 0, 0, 0)
                hx, hy = cam.pt(jj["head"])
                ty = min(hy, gy - 2.6 * cam.s) - 0.25 * cam.s
                if full:
                    ty = max(ty, 640)
                fs = 42 if not full else 66
                if txt == "NEW PR!":
                    fs = 100
                    hx = 470
                    ty = 700
                hx = min(max(hx, 260), 640)
                draw_spaced(tc, txt, hx, ty, fit_font(txt, fs, "InterDisplay-Black", 2, 620), 2,
                            paint(col if txt != "#GYMLIFE" else RED, 1.0))
            lx, _ = cam.pt((X0 - 0.3, 0))
            draw_spaced(tc, n, lx, gy + (44 if not full else 60), font(26 if not full else 36, "Inter-Bold"), 5,
                        paint(col, 1.0))
            if not full:
                draw_spaced(tc, f"{kg} KG", 770, y0 + 70, font(54, "InterDisplay-Black"), 2,
                            paint(RED if n == "EGO" else WHITE, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
            if n == "EGO" and kind == "skip" and not full:
                tw = keys(t, WEEK_KF)
                uu = tw - math.floor(tw)
                stamp(oc, 470, y0 + 260, "SKIP", min(0.99, uu * 1.5) if uu < 0.62 else 0.99)
            if n == "DISCIPLINE" and 7.0 <= t < 16.0 and not full:
                tw = keys(t, WEEK_KF)
                uu = tw - math.floor(tw)
                if uu < 0.6:
                    draw_spaced(oc, "+2.5 KG", 770, y0 + 130 - 30 * uu, font(34, "InterDisplay-Black"), 2,
                                paint(WHITE, 1 - uu / 0.6))
        if fz is None:
            oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
            draw_spaced(oc, f"WEEK {week(t)}", 470, 964, font(38, "InterDisplay-Black"), 4, paint(WHITE, 1.0))
        else:
            n = fz[2]
            draw_spaced(oc, f"WEEK {week(t)}", 470, 410, font(44, "InterDisplay-Black"), 6, paint(WHITE, 0.85))
            draw_spaced(oc, f"{kg_of(n, t)} KG", 470, 520, font(100, "InterDisplay-Black"), 3,
                        paint(RED if n == "EGO" else WHITE, 1.0))
        if t < 1.5:
            caption(oc, "EGO VS DISCIPLINE", 420, 1 - smoothstep(1.2, 1.5, t), WHITE, 54)
        ending(oc, t, END_T - 0.3, [(END_T, "EGO STARTED", RED, 110), (END_T + 0.3, "HEAVY.", RED, 120),
                                    (END_T + 1.1, "DISCIPLINE", WHITE, 110), (END_T + 1.4, "ENDED HEAVY.", WHITE, 110)],
               gap=125)
        cut = 0.0
        for tt in [f[0] for f in FULL] + [f[1] for f in FULL] + [7.0]:
            if tt <= t < tt + 0.1:
                cut = 0.07
        v.compose(fi, t, flash=flash, white=cut + 0.3 * flash, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=18.2), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    for t, kind, _, extra in events:
        if kind == "plate":
            m.add(t, sfx.plate_clank(int(t * 10), 1.0), 0.6, 0, 0.2)
        elif kind == "week":
            m.add(t, sfx.tick(2600, 0.3), 0.45, 0, 0.1)
            if extra % 2 == 0 and 2 <= extra <= 51:
                m.add(t + 0.02, sfx.plate_clank(extra, 0.5), 0.3, 0, 0.2)
        elif kind == "zoom":
            m.add(t, sfx.whoosh(0.3, 400, 8000, 0.4, seed=int(t)), 0.4, 0, 0.2)
        elif kind == "stuck":
            m.add(t, sfx.breath(2, 0.8), 0.6, 0, 0.3)
            for q in range(3):
                m.add(t + 0.1 + q * 0.3, sfx.heartbeat(), 0.5, 0, 0.3)
        elif kind == "spot":
            m.add(t, sfx.plate_clank(3, 1.2), 0.7, 0, 0.3)
            m.add(t + 0.5, sfx.laugh(4, 4, 180, 0.4), 0.3, 0, 0.3)
        elif kind == "injured":
            m.add(t, sfx.power_down(1.5), 0.5, 0, 0.4)
        elif kind == "grind":
            m.add(t, sfx.riser(LOCK - t), 0.6, 0, 0.3)
            m.add(t, sfx.breath(5, LOCK - t), 0.5, 0, 0.3)
        elif kind == "lock":
            m.add(t, sfx.boom(3.0), 0.9, 0, 0.5)
            m.add(t, sfx.plate_clank(7, 1.5), 0.8, 0, 0.3)
            m.add(t + 0.1, sfx.applause(2.0, 40, 5), 0.4, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 2.2, 3.0, 3.8, 4.7, 5.8, 8.0, 9.0, 12.0, 14.5, 16.2, 17.6, 18.6, 19.3, 19.9, 23.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
