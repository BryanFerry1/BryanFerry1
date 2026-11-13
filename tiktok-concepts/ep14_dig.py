"""EP14 - DIG  (same storyline as the user's reference, redrawn in our DA)

 0.0  "DIG!"  Four figures at the surface: MOTIVATION, TALENT, OBSESSION, EGO.
 1.2  They dig. MOTIVATION quits first, sits head down (OUT).
 4.2  TALENT finds a glowing red coin, sits and stares at it (OUT).
 6.5  OBSESSION and EGO keep going (EGO deeper). Doubts appear on the walls:
      I CAN'T / I'M A LOSER / I'M NOT BUILT FOR THIS. OBSESSION curls up, turns red.
12.0  Interlude (our own visuals): dictionary card "obsessed" -> zoom on the word
      -> "YOU VS YOU" -> "IT'S YOU VS YOU" + Sisyphus pushing his boulder.
16.0  OBSESSION digs like crazy. EGO hits a pile of red coins, a heart pops,
      he lies down on it. OBSESSION passes him (red flash).
19.6  Pull back: his shaft is just a thread, a huge pile of diamonds at the bottom.
PUNCH THEY ALL STOPPED. / OBSESSION KEPT DIGGING.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, RED, WHITE, W, H, Camera, Particles, build_pose, clamp, draw_spaced,
                    ease_out, font, mix, paint, smoothstep, spaced_width)
from kit import CX, GREY, Log, Video, blend, draw_body, draw_heart, kneel, sad, sit, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep14_dig"
dt = 1 / FPS
ORDER = ["MOTIVATION", "TALENT", "OBSESSION", "EGO"]
XS = {"MOTIVATION": -2.85, "TALENT": -0.95, "OBSESSION": 0.95, "EGO": 2.85}
SERIF = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
SERIF_I = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf")
MONO = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf")


def sfont(size, tf=None):
    f = skia.Font(tf or SERIF, size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


GO = 1.2
STOP = {"MOTIVATION": (3.3, 2.2), "TALENT": (5.4, 4.3)}
EGO_GOLD = 18.4
EGO_D = 15.5
DOUBTS = [(8.6, "I CAN'T"), (9.3, "I'M A LOSER"), (10.0, "I'M NOT BUILT FOR THIS")]
DOUBT = (8.4, 12.0)
RED_T = 10.6
INTER = (12.0, 15.9)
PASS = 19.6
PILE = 34.0
BOTTOM_T = 22.0
P1, P2 = 22.9, 23.7
DUR = 27.0


def ego_depth(t):
    if t < GO:
        return 0.0
    if t < EGO_GOLD:
        return EGO_D * (1 - (1 - (t - GO) / (EGO_GOLD - GO)) ** 1.25)
    return EGO_D


def obs_depth(t):
    if t < GO:
        return 0.0
    if t < DOUBT[0]:
        return 0.95 * (t - GO)
    d0 = 0.95 * (DOUBT[0] - GO)
    if t < INTER[1]:
        return d0 + 0.1 * (min(t, DOUBT[1]) - DOUBT[0])
    d1 = d0 + 0.1 * (DOUBT[1] - DOUBT[0])
    # furious digging after the interlude, reaches the pile at BOTTOM_T
    u = clamp((t - INTER[1]) / (BOTTOM_T - INTER[1]))
    return d1 + (PILE - 0.6 - d1) * (u ** 1.35)


def depth(n, t):
    if n in STOP:
        ts, d = STOP[n]
        if t < GO:
            return 0.0
        return d * (1 - (1 - min(1.0, (t - GO) / (ts - GO))) ** 1.6)
    return ego_depth(t) if n == "EGO" else obs_depth(t)


def dig_pose(x, y, t, speed, ph=0.0):
    c = 0.5 + 0.5 * math.sin(t * (6 + 9 * speed) + ph)
    j = build_pose(np.array([x - 0.05, y + 1.42 - 0.12 * c]), np.array([x + 0.25, y + 0.02]), np.array([x - 0.25, y + 0.02]),
                   0.35 + 0.3 * c, 0.9 - 0.5 * c, 0.75 - 0.5 * c, 0.6, 0.7, 0.3 + 0.2 * c)
    hand = (j["hand1"] + j["hand2"]) / 2
    tip = hand + np.array([0.25 + 0.1 * c, -1.0 + 0.3 * (1 - c)])
    return j, tip


def lie_relax(x, y):
    hip = np.array([x, y + 0.45])
    neck = np.array([x + 0.88, y + 0.62])
    sh = hip + (neck - hip) * 0.86
    return {"hip": hip, "neck": neck, "head": np.array([x + 1.2, y + 0.75]), "shoulder": sh,
            "knee1": np.array([x - 0.55, y + 0.85]), "foot1": np.array([x - 1.05, y + 0.45]),
            "knee2": np.array([x - 0.7, y + 0.6]), "foot2": np.array([x - 1.3, y + 0.42]),
            "elbow1": sh + [0.35, 0.45], "hand1": sh + [0.5, 0.2],
            "elbow2": sh + [0.25, 0.5], "hand2": sh + [0.42, 0.25]}


def diamond_pile(c, cx, cy, w, alpha, t, rng_seed=4):
    """A glittering triangular pile of diamonds (base centre at cx, cy)."""
    r = np.random.default_rng(rng_seed)
    h = w * 0.62
    c.drawCircle(cx, cy - h * 0.4, w * 0.8, paint(WHITE, 0.025 * alpha))
    for _ in range(420):
        u, v_ = r.random(), r.random()
        if u + v_ > 1:
            u, v_ = 1 - u, 1 - v_
        px = cx - w / 2 + u * w + v_ * w / 2 - v_ * w / 2 * 0 + (v_ * 0)
        px = cx + (u - v_) * w / 2
        py = cy - (1 - u - v_) * 0 - (u * 0) - (1 - (u + v_)) * 0
        py = cy - h * (1 - abs(px - cx) / (w / 2)) * r.random()
        tw = 0.5 + 0.5 * math.sin(t * 9 + px * 0.3 + py * 0.2)
        s = r.uniform(2, 5)
        c.drawRect(skia.Rect(px - s, py - s, px + s, py + s), paint(WHITE, alpha * (0.15 + 0.5 * tw)))
    for k in range(5):
        gx = cx + math.sin(t * 1.3 + k * 2) * w * 0.3
        gy = cy - h * (0.3 + 0.12 * k)
        L = 14 * (0.5 + 0.5 * math.sin(t * 6 + k))
        c.drawLine(gx - L, gy, gx + L, gy, paint(WHITE, alpha, 2))
        c.drawLine(gx, gy - L, gx, gy + L, paint(WHITE, alpha, 2))


def doubt_tag(c, tc, x, y, text, alpha):
    f = sfont(24, MONO)
    w = spaced_width(text, f, 1) + 24
    r = skia.Rect(x - w / 2, y - 26, x + w / 2, y + 8)
    c.drawRect(r, paint((0.75, 0.75, 0.78), 0.9 * alpha))
    draw_spaced(tc, text, x, y - 2, f, 1, paint((0, 0, 0), alpha))
    # black text on a light tag: draw it into the fig layer too so it reads after compositing
    c.drawRect(r, paint((0, 0, 0), 0.0))


def sisyphus(c, t, alpha, zoom):
    """Our own drawing: a figure pushing a scribbled boulder up a slope."""
    if alpha < 0.01:
        return
    c.save()
    c.translate(CX, 1050)
    c.scale(zoom, zoom)
    sl0, sl1 = (-420, 380), (420, -120)
    c.drawLine(*sl0, *sl1, paint(WHITE, 0.7 * alpha, 4))
    for k in range(30):        # slope hatching
        u = k / 30
        x0 = sl0[0] + (sl1[0] - sl0[0]) * u
        y0 = sl0[1] + (sl1[1] - sl0[1]) * u
        c.drawLine(x0, y0, x0 - 25, y0 + 40, paint(WHITE, 0.18 * alpha, 2))
    bx, by, br = 90, -150, 170
    r = np.random.default_rng(11)
    for k in range(140):
        a0 = r.uniform(0, 6.28)
        rr = br * math.sqrt(r.uniform(0.2, 1.0))
        p = skia.Path()
        p.moveTo(bx + math.cos(a0) * rr, by + math.sin(a0) * rr)
        a1 = a0 + r.uniform(0.6, 2.4)
        rr2 = br * math.sqrt(r.uniform(0.2, 1.0))
        p.quadTo(bx + math.cos((a0 + a1) / 2) * br * 1.1, by + math.sin((a0 + a1) / 2) * br * 1.1,
                 bx + math.cos(a1) * rr2, by + math.sin(a1) * rr2)
        c.drawPath(p, paint(WHITE, 0.32 * alpha, 1.6))
    c.drawCircle(bx, by, br, paint(WHITE, 0.6 * alpha, 3))
    cam = Camera()
    cam.s, cam.sx, cam.sy, cam.wx, cam.wy = 115, -165, 155, 0.0, 0.0
    push = 0.03 * math.sin(t * 3)
    j = build_pose(np.array([0.0, 1.25 + push]), np.array([0.55, 0.42]), np.array([-0.75, -0.25]),
                   0.95, 1.75, 1.6, 0.25, 0.35, -0.35)
    draw_body(c, j, cam, WHITE, alpha, 0.55)
    c.restore()


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    dirt = Particles(3)
    rng = np.random.default_rng(6)
    cam = Camera()
    cam.sx, cam.wx, cam.s, cam.wy, cam.sy = CX, 0.0, 82.0, 1.0, 900.0
    for fi in range(v.n):
        t = fi * dt
        D = {n: depth(n, t) for n in ORDER}
        inter = INTER[0] <= t < INTER[1]
        # ---------------- events
        if t >= 0.05:
            log.once("dig_word", t, "dig_word")
        for n in ORDER:
            stopped = n in STOP and t >= STOP[n][0]
            ego_done = n == "EGO" and t >= EGO_GOLD
            obs_idle = n == "OBSESSION" and DOUBT[0] + 0.3 < t < INTER[1]
            if t >= GO and not stopped and not ego_done and not obs_idle and not (n == "OBSESSION" and t >= BOTTOM_T):
                fast = n == "OBSESSION" and t >= INTER[1]
                k = int((t - GO) * (6.5 if fast else 2.2))
                log.once(f"dig{n}{k}", t, "dig", (ORDER.index(n), fast))
                if rng.random() < (0.7 if fast else 0.4):
                    dirt.emit(np.array([[XS[n] + 0.3, -D[n] + 0.1]]) + rng.normal(0, 0.1, (3, 2)), vel=(0.0, 4 if fast else 2.5),
                              spread=0.8, life=(0.3, 0.6), size=(0.03, 0.06))
        for n, (ts, d) in STOP.items():
            if t >= ts:
                log.once(f"out{n}", t, "out", ORDER.index(n))
        for k, (tt, s_) in enumerate(DOUBTS):
            if t >= tt:
                log.once(f"doubt{k}", t, "doubt", k)
        if t >= RED_T:
            log.once("red", t, "red")
        if t >= INTER[0]:
            log.once("inter", t, "inter")
        if t >= 13.75:
            log.once("youvsyou", t, "youvsyou")
        if t >= 14.6:
            log.once("sisy", t, "sisy")
        if t >= INTER[1]:
            log.once("back", t, "back")
        if t >= EGO_GOLD:
            log.once("gold", t, "gold")
        if t >= PASS:
            log.once("pass", t, "pass")
        if t >= BOTTOM_T:
            log.once("bottom", t, "bottom")
        dirt.step(dt)

        # ---------------- camera
        dO = D["OBSESSION"]
        if t < 2.6:
            ty, s, sy = 1.0, 82.0, 900.0                                  # wide on the surface
        elif t < 4.2:
            ty, s, sy = -1.6, 105.0, 900.0                                # on motivation / talent
        elif t < 6.8:
            ty, s, sy = -3.6, 105.0, 900.0
        elif t < PASS + 0.4:
            ty, s, sy = -dO + 2.4, 105.0, 900.0
        else:
            u = smoothstep(PASS + 0.4, BOTTOM_T - 0.4, t)
            s_full = (1560 - 380) / (PILE + 3.0)
            ty = (-dO + 2.4) * (1 - u) + (-(PILE + 3) / 2 + 1.0) * u
            s = math.exp(math.log(105) * (1 - u) + math.log(s_full) * u)
            sy = 900 * (1 - u) + 980 * u
        k_ = 0.12 if t > 2.6 else 1.0
        cam.wy += (ty - cam.wy) * k_
        cam.s += (s - cam.s) * (0.12 if t < PASS + 0.4 else 1.0)
        cam.sy += (sy - cam.sy) * k_
        cam.wx = 0.0 if t < 6.8 else 0.35
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        if not inter:
            # ground
            l, top = cam.pt((-4.2, 0))
            r, bot = cam.pt((4.2, -PILE - 4))
            e.drawRect(skia.Rect(max(60, l), top, min(W - 60, r), bot), paint(WHITE, 0.07))
            for k in range(1, 40):
                y = -k * 1.0
                a0, a1 = cam.pt((-4.2, y)), cam.pt((4.2, y + 0.06 * math.sin(k * 1.7)))
                e.drawLine(max(60, a0[0]), a0[1], min(W - 60, a1[0]), a1[1], paint(WHITE, 0.03, 2))
            e.drawLine(max(60, l), top, min(W - 60, r), top, paint(WHITE, 0.55, 3))
            # shafts
            for n in ORDER:
                x = XS[n]
                d = D[n]
                sl, st_ = cam.pt((x - 0.55, 0.02))
                sr, sb = cam.pt((x + 0.55, -d - 0.05))
                if sb > st_:
                    e.drawRect(skia.Rect(sl, st_, sr, sb), paint((0, 0, 0), 1.0))
                if n == "EGO" and t >= EGO_GOLD - 0.3:
                    cl, ct = cam.pt((x - 1.4, -d + 1.2))
                    cr, cb = cam.pt((x + 1.4, -d - 0.05))
                    e.drawRoundRect(skia.Rect(cl, ct, cr, cb), 30, 30, paint((0, 0, 0), 1.0))
            # diamond pile at the very bottom
            px, py = cam.pt((XS["OBSESSION"], -PILE))
            diamond_pile(f_, px, py, 4.2 * cam.s, 1.0, t)
            dirt.draw(f_, cam, WHITE, GREY)
            # figures
            for i, n in enumerate(ORDER):
                x = XS[n]
                y = -D[n]
                col, alpha = WHITE, 1.0
                tip = None
                if t < GO:
                    wave = 0.4 + 0.3 * math.sin(t * 6 + i) if n == "OBSESSION" else 0.3
                    j = stand(x - 0.1, 0.0, 0.3, 0.25, 0.4, 0.4, 0.0)
                    tip = (j["hand1"] + j["hand2"]) / 2 + np.array([0.15, -1.2])
                elif n in STOP and t >= STOP[n][0]:
                    w = smoothstep(STOP[n][0], STOP[n][0] + 0.4, t)
                    jd, _ = dig_pose(x, y, t, 0)
                    if n == "MOTIVATION":
                        js = {k: vv + [0, y] for k, vv in sit(x - 0.35, 0.05, t, 0.95).items()}
                    else:
                        js = {k: vv + [0, y] for k, vv in sit(x - 0.35, 0.05, t, 0.15).items()}
                        js["hand1"] = js["shoulder"] + [0.45, 0.3]
                    j = blend(jd, js, w)
                    col, alpha = mix(WHITE, GREY, 0.6 * w), 1 - 0.3 * w
                elif n == "EGO" and t >= EGO_GOLD:
                    jd, _ = dig_pose(x, y, t, 0)
                    j = blend(jd, lie_relax(x - 0.15, y + 0.2), smoothstep(EGO_GOLD + 0.4, EGO_GOLD + 0.9, t))
                    col = mix(WHITE, GREY, 0.4)
                elif n == "OBSESSION" and DOUBT[0] <= t < INTER[1]:
                    jd, tip = dig_pose(x, y, t, 0)
                    w = smoothstep(DOUBT[0], DOUBT[0] + 0.5, t)
                    j = blend(jd, {k: vv + [0, y] for k, vv in sad(x, t).items()}, w)
                    col = mix(WHITE, RED, smoothstep(RED_T - 0.3, RED_T + 0.4, t))
                    tip = None
                elif n == "OBSESSION" and t >= BOTTOM_T:
                    j = {k: vv + [0, y] for k, vv in stand(x, -0.05, 2.75, 2.95, 0.15, 0.1, -0.25).items()}
                    col = RED
                else:
                    fast = n == "OBSESSION" and t >= INTER[1]
                    j, tip = dig_pose(x, y, t, 1.0 if fast else 0.3, i * 1.7)
                    if n == "OBSESSION" and t >= INTER[1]:
                        col = RED
                        for k in range(5):             # speed scratches above him
                            sx, sy = cam.pt((x - 0.35 + 0.17 * k, y + 3.0 + 0.3 * math.sin(t * 20 + k)))
                            hc.drawLine(sx, sy, sx, sy - 70, paint(RED, 0.4, 2))
                draw_body(hc, j, cam, col, alpha, 0.2 if n == "OBSESSION" and t >= INTER[1] else 0.0)
                if tip is not None:
                    hand = (j["hand1"] + j["hand2"]) / 2
                    hc.drawLine(*cam.pt(hand + [0, 0.25]), *cam.pt(tip), paint(col, alpha, max(2, 0.05 * cam.s)))
                    hc.drawLine(*cam.pt(tip + [-0.1, 0]), *cam.pt(tip + [0, -0.2]), paint(col, alpha, max(3, 0.12 * cam.s)))
                if n == "TALENT" and t >= STOP[n][0]:
                    cx_, cy_ = cam.pt(j["hand1"] + [0.05, 0.1])
                    f_.drawCircle(cx_, cy_, 0.15 * cam.s, paint(RED, 1.0))
                    f_.drawCircle(cx_, cy_, 0.5 * cam.s, paint(RED, 0.12))
                if n == "EGO" and t >= EGO_GOLD - 0.3:
                    pr = np.random.default_rng(9)
                    for k in range(60):
                        gx_ = x + pr.uniform(-1.3, 1.3)
                        gy_ = y + 0.06 + abs(pr.normal(0, 0.16)) * (1 - abs(gx_ - x) / 1.4)
                        f_.drawCircle(*cam.pt((gx_, gy_)), 0.08 * cam.s, paint(RED, 0.9))
                    if t >= EGO_GOLD + 0.2:
                        hx, hy = cam.pt(j["head"] + [0.1, 0.6])
                        pop = 1 + 0.6 * math.exp(-(t - EGO_GOLD - 0.2) * 8)
                        draw_heart(f_, hx, hy, 16 * pop, 0.95)
                # labels
                if t < BOTTOM_T - 0.6:
                    hx, hy = cam.pt(j["head"])
                    lab_col = RED if n == "OBSESSION" else WHITE
                    draw_spaced(tc, n, hx, hy - 0.5 * cam.s, sfont(20, MONO), 2, paint(lab_col, 0.9))
                    if n in STOP and t >= STOP[n][0]:
                        po = 1 + 0.5 * math.exp(-(t - STOP[n][0]) * 8)
                        draw_spaced(tc, "OUT", hx, hy - 0.5 * cam.s - 26, sfont(20 * po, MONO), 2, paint(RED, 0.95))
            # doubts: readable tags (opaque overlay) stacked above his head
            oc = v.over.canvas
            hx_o, hy_o = cam.pt(stand(XS["OBSESSION"]).get("head") + [0, -D["OBSESSION"]])
            for k, (tt, s_) in enumerate(DOUBTS):
                if tt <= t < INTER[0]:
                    pop = 1 + 0.25 * math.exp(-(t - tt) * 10)
                    f = sfont(30 * pop, MONO)
                    wdt = spaced_width(s_, f, 1) + 34
                    cx_ = min(max(hx_o, 80 + wdt / 2), 880 - wdt / 2)
                    cy_ = hy_o - 120 - 74 * k
                    rr = skia.Rect(cx_ - wdt / 2, cy_ - 38, cx_ + wdt / 2, cy_ + 14)
                    oc.drawRect(rr, paint((0, 0, 0), 0.92))
                    oc.drawRect(rr, paint(WHITE, 1.0, 3, cap=False))
                    draw_spaced(oc, s_, cx_, cy_, f, 1, paint(WHITE, 1.0))
            # "DIG!"
            if t < 1.6:
                a = smoothstep(0.0, 0.15, t) * (1 - smoothstep(1.2, 1.6, t))
                pop = 1 + 0.15 * math.exp(-t * 8)
                draw_spaced(tc, "DIG!", CX, 470, sfont(110 * pop, MONO), 14, paint(WHITE, a))
            # pass flash
            if PASS <= t < PASS + 0.35:
                f_.drawRect(skia.Rect(0, 0, W, H), paint(RED, 0.1 * (1 - (t - PASS) / 0.35)))
        else:
            # =========== INTERLUDE ===========
            u = t - INTER[0]
            if u < 1.75:                       # dictionary card, slow zoom, then into the word
                z = 1 + 0.08 * u + 2.5 * smoothstep(1.35, 1.75, u) ** 2
                a = smoothstep(0, 0.2, u)
                c = tc
                c.save()
                c.translate(300, 670)
                c.scale(z, z)
                c.translate(-300, -670)
                draw_spaced(c, "obsessed", 300, 700, sfont(88), 1, paint(WHITE, a))
                c.drawString("[əbˈsɛst]  adjective • English", 160, 760, sfont(30, SERIF_I), paint(WHITE, 0.75 * a))
                c.drawLine(160, 800, 500, 800, paint(WHITE, 0.6 * a, 2))
                lines = ["what the comfortable call the committed.",
                         "one thought, every single day,",
                         "until it becomes real.",
                         "",
                         "obsession beats talent. every time."]
                for k, ln in enumerate(lines):
                    c.drawString(ln, 160, 860 + 44 * k, sfont(30), paint(WHITE, 0.85 * a))
                c.restore()
            elif u < 2.6:                      # YOU VS YOU, huge, zooming
                uu = u - 1.75
                z = 1.6 - 0.5 * ease_out(uu / 0.85)
                a = smoothstep(0, 0.12, uu) * (1 - smoothstep(0.7, 0.85, uu))
                tc.save()
                tc.translate(CX, 960)
                tc.scale(z, z)
                draw_spaced(tc, "YOU VS YOU", 0, 40, sfont(150), 2, paint(WHITE, a))
                tc.restore()
            else:                              # IT'S YOU VS YOU + Sisyphus
                uu = u - 2.6
                a = smoothstep(0, 0.2, uu) * (1 - smoothstep(1.0, 1.3, uu))
                draw_spaced(tc, "IT'S YOU VS YOU", CX, 560, sfont(70), 2, paint(WHITE, a))
                sisyphus(f_, t, a, 0.95 + 0.06 * uu)
        if t >= BOTTOM_T - 0.2:
            pass
        # punchline
        if t >= P1:
            oc = v.over.canvas
            ba = smoothstep(P1 - 0.2, P1 + 0.2, t)
            oc.drawRect(skia.Rect(0, 700, W, 960), paint((0, 0, 0), 0.88 * ba))
            for t0, txt, col, y in ((P1, "THEY ALL STOPPED.", WHITE, 805), (P2, "OBSESSION KEPT DIGGING.", RED, 895)):
                if t >= t0:
                    a = smoothstep(t0, t0 + 0.4, t)
                    ff = sfont(54 if t0 == P1 else 48, MONO)
                    draw_spaced(oc, txt, CX, y, ff, 4, paint(col, a))
        flash = math.exp(-(t - BOTTOM_T) * 2.5) if t >= BOTTOM_T else 0.0
        dark = 0.4 * smoothstep(DOUBT[0], RED_T, t) * (1 - smoothstep(INTER[1] - 0.1, INTER[1] + 0.3, t)) if not inter else 0.0
        v.compose(fi, t, flash=flash, glow=0.3 * (t >= INTER[1]), dim=dark)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    bed = sfx.drone(DUR, rise_at=BOTTOM_T)
    tt = np.arange(len(bed)) / sfx.SR
    bed *= 1 - 0.85 * ((tt > INTER[0]) & (tt < INTER[1]))   # near silence for the interlude
    m.add_bed(bed, gain=0.45, fade_in=0.5, fade_out=2.5, stop=DUR)
    for t, kind, _, extra in events:
        if kind == "dig_word":
            m.add(t, sfx.text_hit(5), 0.8, 0, 0.4)
        elif kind == "dig":
            idx, fast = extra
            pan = -0.6 + 0.4 * idx
            if idx == 2:
                m.add(t, sfx.dig(int(t * 100), 1.2 if fast else 0.9), 0.7 if fast else 0.55, pan, 0.25)
            else:
                m.add(t, sfx.dig(int(t * 100) + idx, 0.5), 0.3, pan, 0.2)
        elif kind == "out":
            m.add(t, sfx.power_down(1.0), 0.3, -0.6 + 0.4 * extra, 0.3)
            if extra == 1:
                m.add(t, sfx.chime(990, 0.3), 0.6, -0.2, 0.5)
        elif kind == "doubt":
            m.add(t, sfx.tick(900, 0.6), 0.6, 0.0, 0.2)
            m.add(t, sfx.punch_block(extra), 0.5, 0.0, 0.3)
        elif kind == "red":
            m.add(t, sfx.heartbeat(), 0.8, 0, 0.3)
            m.add(t + 0.75, sfx.heartbeat(), 0.85, 0, 0.3)
        elif kind == "inter":
            m.add(t, sfx.whoosh(0.5, 300, 6000, 0.4, seed=9), 0.4, 0, 0.5)
            m.add(t + 0.1, sfx.chime(440, 0.3), 0.5, 0, 0.7)
        elif kind == "youvsyou":
            m.add(t, sfx.boom(2.5), 0.8, 0, 0.6)
            m.add(t, sfx.text_hit(2), 0.7, 0, 0.6)
        elif kind == "sisy":
            m.add(t, sfx.riser(1.3), 0.5, 0, 0.4)
            m.add(t, sfx.heartbeat(), 0.7, 0, 0.3)
        elif kind == "back":
            m.add(t, sfx.power_up(70), 1.0, 0, 0.4)
            m.add(t + 0.5, sfx.boom(2.0), 0.6, 0, 0.4)
        elif kind == "gold":
            for k in range(10):
                m.add(t + k * 0.04, sfx.chime(900 + 60 * k, 0.15), 0.4, 0.5, 0.4)
        elif kind == "pass":
            m.add(t, sfx.whoosh(0.5, 300, 8000, 0.4, seed=4), 0.6, 0, 0.3)
            m.add(t, sfx.punch_hit(3, 1.0), 0.6, 0, 0.3)
        elif kind == "bottom":
            m.add(t, sfx.boom(4.5), 1.0, 0, 0.5)
            m.add(t, sfx.sparkle(2.4, 120, 4), 0.8, 0, 0.6)
            for k, f in enumerate((660, 880, 1320)):
                m.add(t + 0.05 * k, sfx.chime(f, 0.3), 0.6, 0, 0.6)
    m.add(BOTTOM_T - 2.5, sfx.riser(2.5), 0.55, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.5, 0, 0.4)
    m.add(P2, sfx.text_hit(3), 0.9, 0, 0.5)
    m.add(P2, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 2.0, 3.8, 5.8, 8.0, 10.2, 11.4, 12.6, 13.6, 14.2, 15.2, 17.0, 18.9, 19.7, 21.0, 22.4, 24.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
