"""EP33 - SECURITY VS RISK  (debate bait: survivorship)

Same start: two guys at two desks. One stays, one kicks his desk over and leaves.
Shots alternate (one situation at a time, push-in zooms), split screen for the
comparisons, a money counter + YEAR on top.
  Y0  split   both typing. RISK kicks the desk over and walks out (visual hook).
  Y1  RISK    builds a rocket (his business), launch... explodes.     -$30K
  Y2  SECURITY  paychecks drop in, +$4K +$4K...                          $96K
  Y3  RISK    rocket #2, bigger, higher... explodes. On his knees.     -$120K
  Y5  SECURITY  a house rises, a partner walks in, heart.               $250K
  Y6  RISK    alone in the dark... stands up, builds rocket #3, huge.
  Y7  split   RISK launches: it does not explode, $ counter goes crazy -> $10M.
              SECURITY watches it fly, from his garden.
  Y10 SECURITY  house, partner, two kids. Home by 6.                     $600K
  Y10 RISK    rich, sports car, alone with his phone... the camera pulls
              way back: 9 other crashed rockets, 9 broke founders.  THE OTHER 9.
END  1 MADE IT. / 9 DIDN'T. / STILL WORTH / THE RISK?
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, clamp, draw_spaced, ease_out, font, ik, paint,
                    rotate_pose, run_pose, smoothstep)
from kit import (CX, GREY, Log, Shards, Video, arms_up, blend, caption, draw_body, draw_car, draw_heart,
                 ending, kneel, lane_cam, mirror, phone_pose, sad, scale_pose, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep33_security_vs_risk"
dt = 1 / FPS
LANES = {"SECURITY": (330, 935, 860), "RISK": (965, 1565, 1495)}
S_LANE = 138
SHOTS = [(0.0, 2.6, "BOTH", 0), (2.6, 5.4, "RISK", 1), (5.4, 7.8, "SECURITY", 2), (7.8, 10.8, "RISK", 3),
         (10.8, 13.2, "SECURITY", 5), (13.2, 15.8, "RISK", 6), (15.8, 18.8, "BOTH", 7),
         (18.8, 21.2, "SECURITY", 10), (21.2, 25.6, "RISK", 10)]
KICK = 1.15
R1_LAUNCH, R1_BOOM = 4.0, 4.6
R2_LAUNCH, R2_BOOM = 9.0, 9.75
R3_UP = 13.9
R3_LAUNCH = 16.4
PULL = (23.0, 25.0)
END_T = 25.8
DUR = 29.8
MONEY = {"SECURITY": [(0, 0), (5.6, 0), (7.6, 96), (11.0, 96), (12.4, 250), (15.8, 250), (18.9, 250),
                      (19.8, 600)],
         "RISK": [(0, 0), (2.6, 0), (2.8, 20), (3.9, -10), (R1_BOOM, -30), (8.0, -30), (R2_BOOM, -120), (16.6, -120),
                  (17.6, 10000)]}
RX = -0.9      # risk-taker x (world) in his shots
SX_ = -0.6     # security x
ROCKET_X = 1.3
GRAVE = [(-2.3, 0.5), (-3.25, -0.45), (-4.2, 0.4), (-5.15, -0.5), (-6.05, 0.45),
         (2.5, -0.45), (3.45, 0.5), (4.4, -0.4), (5.35, 0.45)]


def lin(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            if v1 > 1000:
                u = u ** 3
            return v0 + (v1 - v0) * u
    return kf[-1][1]


def fmt(v):
    sgn = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1000:
        return f"{sgn}${a / 1000:.1f}M"
    return f"{sgn}${int(round(a))}K"


def shot(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]


# ------------------------------------------------------------------ props
def desk(c, cam, x, ang=0.0, alpha=1.0, laptop=True):
    """Desk with its left leg at x (world), rotates around its right foot by ang."""
    piv = np.array([x + 1.25, 0.0])
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])

    def P(p):
        return cam.pt(piv + R @ (np.array(p) - piv))
    w = max(3, 0.05 * cam.s)
    c.drawLine(*P((x - 0.05, 1.0)), *P((x + 1.3, 1.0)), paint(WHITE, 0.8 * alpha, w))
    c.drawLine(*P((x + 0.05, 1.0)), *P((x + 0.05, 0.0)), paint(WHITE, 0.6 * alpha, w * 0.7))
    c.drawLine(*P((x + 1.2, 1.0)), *P((x + 1.2, 0.0)), paint(WHITE, 0.6 * alpha, w * 0.7))
    if laptop:
        c.drawLine(*P((x + 0.15, 1.04)), *P((x + 0.6, 1.04)), paint(WHITE, alpha, w))
        c.drawLine(*P((x + 0.6, 1.04)), *P((x + 0.72, 1.5)), paint(WHITE, alpha, w))


def chair(c, cam, x, alpha=1.0):
    w = max(2, 0.04 * cam.s)
    c.drawLine(*cam.pt((x - 0.35, 0.75)), *cam.pt((x + 0.3, 0.75)), paint(WHITE, 0.5 * alpha, w))
    c.drawLine(*cam.pt((x - 0.35, 0.75)), *cam.pt((x - 0.4, 1.6)), paint(WHITE, 0.5 * alpha, w))
    c.drawLine(*cam.pt((x, 0.75)), *cam.pt((x, 0.0)), paint(WHITE, 0.4 * alpha, w))


def typing(x, t):
    j = sit(x, 0.75, t, 0.05)
    for i, ph in ((1, 0.0), (2, 1.7)):
        hand = j["shoulder"] + np.array([0.62, -0.32 + 0.03 * math.sin(t * 22 + ph)])
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(j["shoulder"], hand, L_UARM, L_FARM, -1)
    return j


def rocket_path(cam, base, hr, ang=0.0):
    """Rocket outline, base centre at world `base`, height hr, tilted by ang."""
    w = hr * 0.24
    pts = [(-w / 2, 0.15 * hr), (-w / 2, 0.72 * hr), (0, hr), (w / 2, 0.72 * hr), (w / 2, 0.15 * hr)]
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    p = skia.Path()
    for k, q in enumerate(pts):
        (p.moveTo if k == 0 else p.lineTo)(*cam.pt(base + R @ np.array(q)))
    p.close()
    fins = skia.Path()
    for sgn in (-1, 1):
        f = [(sgn * w / 2, 0.42 * hr), (sgn * w * 1.05, 0.12 * hr), (sgn * w * 1.05, 0.0), (sgn * w / 2, 0.15 * hr)]
        for k, q in enumerate(f):
            (fins.moveTo if k == 0 else fins.lineTo)(*cam.pt(base + R @ np.array(q)))
        fins.close()
    win = cam.pt(base + R @ np.array([0, 0.6 * hr]))
    return p, fins, win, w


def draw_rocket(c, cam, base, hr, col, alpha=1.0, build=1.0, ang=0.0, flame=0.0, t=0.0):
    p, fins, win, w = rocket_path(cam, base, hr, ang)
    sw = max(3, 0.05 * cam.s)
    if build < 1.0:
        c.drawPath(p, paint(col, 0.22 * alpha, sw * 0.6))
        c.drawPath(fins, paint(col, 0.22 * alpha, sw * 0.6))
    c.save()
    if build < 1.0:
        top = cam.pt((0, base[1] + hr * 1.05 * build))[1]
        c.clipRect(skia.Rect(0, top, W, H))
    c.drawPath(p, paint((0, 0, 0), alpha))
    c.drawPath(fins, paint((0, 0, 0), alpha))
    c.drawPath(p, paint(col, alpha, sw))
    c.drawPath(fins, paint(col, alpha, sw))
    c.drawCircle(win[0], win[1], w * 0.22 * cam.s, paint(col, alpha, sw * 0.8))
    c.restore()
    if flame > 0:
        fl = flame * (0.8 + 0.35 * math.sin(t * 47) + 0.15 * math.sin(t * 91))
        R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        for k, (ww, ll, cc) in enumerate(((w * 0.45, hr * 0.55, RED), (w * 0.22, hr * 0.32, WHITE))):
            q = skia.Path()
            q.moveTo(*cam.pt(base + R @ np.array([-ww, 0.15 * hr])))
            q.lineTo(*cam.pt(base + R @ np.array([0, 0.15 * hr - ll * fl])))
            q.lineTo(*cam.pt(base + R @ np.array([ww, 0.15 * hr])))
            q.close()
            c.drawPath(q, paint(cc, alpha * (0.95 if k else 0.85)))


def hammer_pose(x, t):
    o = 0.5 + 0.5 * math.sin(t * 14)
    j = stand(x, 0.12, 1.0 + 1.3 * o, 0.5, 0.4 + 1.2 * o, 0.6, 0.15)
    return j


def draw_hammer(c, cam, j, col):
    h, e = j["hand1"], j["elbow1"]
    d = (h - e) / (np.linalg.norm(h - e) + 1e-6)
    tip = h + d * 0.38
    c.drawLine(*cam.pt(h - d * 0.05), *cam.pt(tip), paint(col, 1.0, max(3, 0.05 * cam.s)))
    n = np.array([-d[1], d[0]])
    c.drawLine(*cam.pt(tip - n * 0.13), *cam.pt(tip + n * 0.13), paint(col, 1.0, max(5, 0.11 * cam.s)))


def house(c, cam, x0, x1, grow=1.0, alpha=1.0):
    if grow <= 0:
        return
    hgt = 1.9 * grow
    roof = 3.0 * grow
    p = skia.Path()
    for k, q in enumerate(((x0, 0), (x0, hgt), ((x0 + x1) / 2, roof), (x1, hgt), (x1, 0))):
        (p.moveTo if k == 0 else p.lineTo)(*cam.pt(q))
    p.close()
    c.drawPath(p, paint((0, 0, 0), alpha))
    c.drawPath(p, paint(WHITE, 0.85 * alpha, max(3, 0.05 * cam.s)))
    if grow > 0.9:
        a = alpha * smoothstep(0.9, 1.0, grow)
        dx = x0 + 0.35 * (x1 - x0)
        c.drawRect(skia.Rect(*cam.pt((dx - 0.25, 1.1)), *cam.pt((dx + 0.25, 0))), paint(WHITE, 0.7 * a, 3, cap=False))
        wx = x0 + 0.72 * (x1 - x0)
        r = skia.Rect(*cam.pt((wx - 0.3, 1.5)), *cam.pt((wx + 0.3, 0.95)))
        c.drawRect(r, paint(WHITE, 0.25 * a))
        c.drawRect(r, paint(WHITE, 0.8 * a, 3, cap=False))


def wave(x, t, ph=0.0):
    o = math.sin(t * 6 + ph)
    return stand(x, -0.03, 2.6 + 0.25 * o, 0.12, 0.3 + 0.3 * o, 0.1, -0.15)


def holding(x, t):
    return stand(x, 0.0, 0.5, 0.12, 0.2, 0.1, 0.05, 0.006 * math.sin(t * 3))


# ------------------------------------------------------------------ main
def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    shards = Shards(3)
    shard_cam_key = None
    for fi in range(v.n):
        t = fi * dt
        for k, sh in enumerate(SHOTS):
            if t >= sh[0]:
                log.once(f"shot{k}", sh[0], "shot", k)
        for key, tt, kind in (("kick", KICK, "kick"), ("l1", R1_LAUNCH, "launch"), ("b1", R1_BOOM, "boom"),
                              ("l2", R2_LAUNCH, "launch"), ("b2", R2_BOOM, "boom"), ("up", R3_UP, "up"),
                              ("l3", R3_LAUNCH, "launch3"), ("rich", 17.0, "rich"), ("house", 11.0, "house"),
                              ("heart", 12.2, "heart"), ("pull", PULL[0], "pull"), ("other", 23.9, "other"),
                              ("end", END_T, "end"), ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        # shards physics (always stepped)
        for tb, hr, key in ((R1_BOOM, 2.3, "s1"), (R2_BOOM, 2.8, "s2")):
            if tb <= t < tb + dt * 0.99 + 1e-9 or (key not in log.seen and t >= tb):
                pass
        if abs(t - R1_BOOM) < dt / 2:
            shards.burst(ROCKET_X - 0.5, ROCKET_X + 0.5, 2.2, 3.2, 40, vx=(-4, 4), vy=(0, 3.5), size=(0.1, 0.3))
        if abs(t - R2_BOOM) < dt / 2:
            shards.burst(ROCKET_X - 0.6, ROCKET_X + 0.6, 2.9, 4.0, 55, vx=(-5, 5), vy=(0, 3.5), size=(0.1, 0.35))
        shards.step(dt)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        t0, t1, who, year = shot(t)
        u = (t - t0) / (t1 - t0)
        flash = 0.0
        if who == "BOTH":
            panes = [(n, LANES[n][:2], lane_cam(S_LANE, LANES[n][2], 0.0, 400), False) for n in ("SECURITY", "RISK")]
        else:
            s_ = 172 + 28 * ease_out(u)
            cam = lane_cam(s_, 1300, 0.0, 430)
            if who == "RISK" and year == 3:       # tilt up to follow rocket #2
                k = smoothstep(R2_LAUNCH, R2_BOOM, t) * (1 - smoothstep(R2_BOOM + 0.3, R2_BOOM + 0.9, t))
                cam.sy = 1300 + 140 * k
            if who == "RISK" and year == 10:
                k = ease_out(smoothstep(PULL[0], PULL[1], t))
                cam.s = s_ * (1 - k) + 62 * k
                cam.sx = 430 * (1 - k) + 470 * k
                cam.sy = 1300 * (1 - k) + 1180 * k
            panes = [(who, (0, H), cam, True)]
        for n, clip, cam, full in panes:
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, clip[0], W, clip[1]))
            col = WHITE if n == "SECURITY" else RED
            e.drawLine(0, cam.sy, W, cam.sy, paint(WHITE, 0.45, 2.5))
            j = None
            lx = None
            if year == 0:
                if n == "SECURITY":
                    chair(e, cam, -1.2)
                    desk(e, cam, -0.75)
                    j = typing(-1.25, t)
                else:
                    ang = 0.0
                    if t >= KICK:
                        ang = -1.45 * ease_out(clamp((t - KICK) / 0.45))
                    desk(e, cam, -0.75, ang)
                    chair(e, cam, -1.2, 1.0 - 0.6 * smoothstep(KICK, KICK + 0.3, t))
                    if t < KICK - 0.35:
                        j = typing(-1.25, t)
                    elif t < KICK + 0.25:
                        w_ = smoothstep(KICK - 0.35, KICK - 0.05, t)
                        js = stand(-1.0, 0.05, 0.2, 0.1, 0.2, 0.1)
                        js["foot1"] = js["foot1"] + np.array([0.75, 0.6]) * smoothstep(KICK - 0.1, KICK, t)
                        js["knee1"] = ik(js["hip"], js["foot1"], 0.88, 0.86, 1) if False else (js["hip"] + js["foot1"]) / 2 + [0.2, 0.15]
                        j = blend(typing(-1.25, t), js, w_)
                    else:
                        xx = -1.0 + 2.2 * (t - KICK - 0.25)
                        j = run_pose(xx, t * 7, 0.35)
                    if t >= KICK and t < KICK + 0.6:
                        flash = 0.0
            elif n == "RISK" and year == 1:
                b = smoothstep(t0 + 0.1, R1_LAUNCH - 0.3, t)
                if t < R1_LAUNCH - 0.25:
                    j = hammer_pose(RX, t)
                    draw_hammer(hc, cam, j, col)
                    if int(t * 7) % 2 == 0:
                        lx, ly = cam.pt((ROCKET_X, 2.3 * b))
                        f_.drawCircle(lx - 0.3 * cam.s, ly, 6, paint(WHITE, 0.9))
                    lx = None
                elif t < R1_BOOM:
                    j = stand(RX, -0.05, 0.3, 0.2, 0.3, 0.2, -0.3)
                else:
                    tt = t - R1_BOOM
                    j = blend(stand(RX, -0.1, 1.2, 1.4, 0.6, 0.5, -0.2), sad(RX, t), smoothstep(0.3, 0.9, tt))
                if t < R1_BOOM:
                    lift = 1.5 * ((max(0, t - R1_LAUNCH) / (R1_BOOM - R1_LAUNCH)) ** 2)
                    wob = 0.12 * math.sin(t * 25) * smoothstep(R1_LAUNCH, R1_BOOM, t)
                    draw_rocket(hc, cam, np.array([ROCKET_X, lift]), 2.3, col, 1.0, b, wob,
                                1.0 if t >= R1_LAUNCH - 0.1 else 0.0, t)
                else:
                    flash = 0.6 * math.exp(-(t - R1_BOOM) * 6)
                    if t - R1_BOOM < 1.4:
                        draw_spaced(tc, "BOOM", *cam.pt((ROCKET_X, 3.0)), font(int(0.6 * cam.s), "InterDisplay-Black"), 4,
                                    paint(RED, 1 - smoothstep(0.8, 1.4, t - R1_BOOM)))
                    shards.draw(hc, cam, RED)
            elif n == "SECURITY" and year == 2:
                chair(e, cam, SX_ - 0.45)
                desk(e, cam, SX_)
                j = typing(SX_ - 0.5, t)
                for q in range(6):
                    tq = t0 + 0.3 + q * 0.33
                    if tq <= t < tq + 0.9:
                        a = 1 - smoothstep(0.5, 0.9, t - tq)
                        px, py = cam.pt((SX_ + 1.6 + 0.3 * (q % 2), 2.0 + 1.6 * (t - tq)))
                        draw_spaced(tc, "+$4K", px, py, font(int(0.42 * cam.s), "InterDisplay-Black"), 2, paint(WHITE, a))
            elif n == "RISK" and year == 3:
                b = smoothstep(t0 + 0.1, R2_LAUNCH - 0.3, t)
                if t < R2_LAUNCH - 0.25:
                    j = hammer_pose(RX, t)
                    draw_hammer(hc, cam, j, col)
                elif t < R2_BOOM:
                    j = stand(RX, -0.08, 2.6, 0.3, 0.3, 0.2, -0.35)
                else:
                    tt = t - R2_BOOM
                    j = blend(stand(RX, -0.1, 1.2, 1.4, 0.6, 0.5, -0.3), kneel(RX, t, 0.9), smoothstep(0.4, 1.0, tt))
                if t < R2_BOOM:
                    lift = 2.6 * ((max(0, t - R2_LAUNCH) / (R2_BOOM - R2_LAUNCH)) ** 2)
                    wob = 0.15 * math.sin(t * 22) * smoothstep(R2_LAUNCH + 0.3, R2_BOOM, t)
                    draw_rocket(hc, cam, np.array([ROCKET_X, lift]), 2.8, col, 1.0, b, wob,
                                1.0 if t >= R2_LAUNCH - 0.1 else 0.0, t)
                else:
                    flash = 0.7 * math.exp(-(t - R2_BOOM) * 6)
                    shards.draw(hc, cam, RED)
                    if t - R2_BOOM < 1.0:
                        draw_spaced(tc, "BOOM", *cam.pt((ROCKET_X, 3.0)), font(int(0.75 * cam.s), "InterDisplay-Black"), 4,
                                    paint(RED, 1 - smoothstep(0.6, 1.0, t - R2_BOOM)))
            elif n == "SECURITY" and year == 5:
                g = ease_out(smoothstep(t0 + 0.15, t0 + 0.9, t))
                house(e, cam, SX_ + 0.6, SX_ + 2.6, g)
                j = holding(SX_, t)
                px = SX_ + 3.2 - 2.4 * ease_out(smoothstep(t0 + 0.7, t0 + 1.4, t))
                jp = mirror(run_pose(px, t * 7, 0.25 * (1 - smoothstep(t0 + 1.3, t0 + 1.45, t))), px)
                jp = scale_pose(jp, px, 0.93)
                draw_body(hc, jp, cam, GREY, 1.0)
                if t > 12.2:
                    hx, hy = cam.pt(((SX_ + px) / 2, 2.35 + 0.08 * math.sin(t * 5)))
                    draw_heart(tc, hx, hy, 0.28 * cam.s * (1 + 0.25 * math.exp(-(t - 12.2) * 6)), 1.0)
            elif n == "RISK" and year == 6:
                if t < R3_UP:
                    j = kneel(RX, t, 0.9)
                    b = 0.0
                else:
                    w_ = smoothstep(R3_UP, R3_UP + 0.5, t)
                    j = blend(kneel(RX, t, 0.9), hammer_pose(RX, t), w_)
                    if w_ > 0.6:
                        draw_hammer(hc, cam, j, col)
                    b = smoothstep(R3_UP + 0.3, t1 - 0.2, t)
                draw_rocket(hc, cam, np.array([ROCKET_X + 0.1, 0.0]), 3.4, col, 1.0, max(b, 0.001))
                if b > 0 and int(t * 8) % 2 == 0:
                    sx_, sy_ = cam.pt((ROCKET_X + 0.1, 3.4 * b * 1.05))
                    f_.drawCircle(sx_ + 0.35 * cam.s, sy_, 7, paint(WHITE, 1.0))
                dark = 1 - smoothstep(R3_UP - 0.2, R3_UP + 0.6, t)
                if dark > 0:
                    hx, hy = cam.pt((RX + 0.4, 2.2))
                    draw_spaced(tc, "ALONE.", hx, hy, font(int(0.33 * cam.s), "InterDisplay-Black"), 6, paint(WHITE, 0.7 * dark))
            elif year == 7:
                if n == "SECURITY":
                    house(e, cam, 0.9, 2.9, 1.0)
                    j = stand(-0.5, -0.12, 0.3, 0.2, 0.2, 0.1, -0.45)
                    draw_body(hc, scale_pose(stand(-1.6, -0.1, 0.3, 0.2, 0.2, 0.1, -0.45), -1.6, 0.93), cam, GREY, 1.0)
                    # tiny rocket crossing his sky
                    rr = clamp((t - (R3_LAUNCH + 0.6)) / 1.6)
                    if 0 < rr < 1:
                        draw_rocket(hc, cam, np.array([3.5 - 1.0 * rr, 2.0 + 3.0 * rr]), 0.8, RED, 1.0, 1.0, -0.3, 1.0, t)
                else:
                    if t < R3_LAUNCH:
                        j = stand(RX, -0.05, 0.3, 0.2, 0.3, 0.2, -0.3)
                    else:
                        j = arms_up(RX, t)
                    lift = 8.0 * (max(0, t - R3_LAUNCH) ** 2)
                    shake = 0.03 * math.sin(t * 60) * (t < R3_LAUNCH + 0.4) * (t > R3_LAUNCH - 0.5)
                    draw_rocket(hc, cam, np.array([ROCKET_X + shake, lift]), 3.4, col, 1.0, 1.0, 0.0,
                                1.0 if t > R3_LAUNCH - 0.5 else 0.0, t)
            elif n == "SECURITY" and year == 10:
                house(e, cam, SX_ + 1.5, SX_ + 3.5, 1.0)
                j = holding(SX_, t)
                jp = scale_pose(mirror(holding(SX_ + 1.1, t), SX_ + 1.1), SX_ + 1.1, 0.93)
                draw_body(hc, jp, cam, GREY, 1.0)
                for k, kx in enumerate((SX_ + 0.55, SX_ - 0.7)):
                    jk = scale_pose(wave(kx, t, k * 1.5) if k == 0 else holding(kx, t), kx, 0.55)
                    jk = {kk: vv + [0, 0.12 * abs(math.sin(t * 6 + k))] for kk, vv in jk.items()}
                    draw_body(hc, jk, cam, GREY, 1.0)
                if t > t0 + 0.4:
                    hx, hy = cam.pt((SX_ + 0.55, 2.45 + 0.08 * math.sin(t * 5)))
                    draw_heart(tc, hx, hy, 0.26 * cam.s, smoothstep(t0 + 0.4, t0 + 0.7, t))
                if t > t0 + 0.9:
                    hx, hy = cam.pt((SX_ + 0.3, -0.75))
            elif n == "RISK" and year == 10:
                draw_car(e, cam, RX + 0.45, 1.0, RED, 0.42)
                j, = (phone_pose(RX, t),)
                hx, hy = cam.pt(j["hand1"])
                f_.drawRoundRect(skia.Rect(hx - 0.09 * cam.s, hy - 0.3 * cam.s, hx + 0.09 * cam.s, hy), 4, 4, paint(WHITE, 0.9))
                # the graveyard
                ga = smoothstep(PULL[0] - 0.2, PULL[0] + 0.6, t)
                if ga > 0:
                    for k, (gx, ga_) in enumerate(GRAVE):
                        draw_rocket(e, cam, np.array([gx + (0.25 if gx > 0 else -0.25), -0.35]), 2.0, GREY, ga, 1.0,
                                    ga_)
                        fx = gx - 0.3 if gx > 0 else gx + 0.3
                        jg = sad(fx, t + k)
                        draw_body(e, jg if gx > 0 else mirror(jg, fx), cam, GREY, 0.85 * ga)
            if j is not None:
                draw_body(hc, j, cam, col, 1.0)
                if not (n == "RISK" and year == 10 and t > PULL[0]):
                    sx_, _ = cam.pt((j["hip"][0], 0))
                    if year == 0 and n == "RISK" and t > KICK + 0.6:
                        sx_ = None
                    if sx_ is not None:
                        draw_spaced(v.txt.canvas, n, sx_, cam.sy + (40 if not full else 66),
                                    font(26 if not full else 38, "Inter-Bold"), 6, paint(col, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
            # money
            m = lin(t, MONEY[n])
            mcol = RED if (m < 0 or m > 1000) else WHITE
            pop = 1.0
            if full:
                draw_spaced(oc, f"YEAR {year}", CX, 372, font(30, "Inter-SemiBold"), 10, paint(WHITE, 0.75))
                draw_spaced(oc, fmt(m), CX, 480, font(int(104 * pop), "InterDisplay-Black"), 3, paint(mcol, 1.0))
            elif year == 7:
                draw_spaced(oc, fmt(m), 700, clip[0] + 130, font(64, "InterDisplay-Black"), 2, paint(mcol, 1.0))
        if who == "BOTH":
            oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
            draw_spaced(oc, f"YEAR {year}", CX, 964, font(36, "InterDisplay-Black"), 6, paint(WHITE, 1.0))
        if t < 2.0:
            caption(oc, "SECURITY VS RISK", 420, 1 - smoothstep(1.6, 2.0, t), WHITE, 56)
        if 23.9 <= t < END_T:
            caption(oc, "THE OTHER 9", 640, smoothstep(23.9, 24.2, t), GREY, 60)
        ending(oc, t, END_T - 0.3, [(END_T, "1 MADE IT.", WHITE, 110), (END_T + 0.5, "9 DIDN'T.", WHITE, 110),
                                    (END_T + 1.3, "STILL WORTH", RED, 96), (END_T + 1.55, "THE RISK?", RED, 110)],
               gap=125)
        cut = 0.0
        for sh in SHOTS[1:]:
            if sh[0] <= t < sh[0] + 0.12:
                cut = 0.08 * (1 - (t - sh[0]) / 0.12)
        v.compose(fi, t, flash=flash, white=cut + 0.15 * flash, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=15.0), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    for t0 in np.arange(0.1, KICK - 0.3, 0.09):                 # typing
        m.add(t0, sfx.tick(3200 + 400 * (int(t0 * 50) % 3), 0.12), 0.25, -0.2, 0.05)
    for a, b in ((2.7, R1_LAUNCH - 0.3), (7.9, R2_LAUNCH - 0.3), (R3_UP + 0.4, 15.7)):   # hammering
        q = 0
        for t0 in np.arange(a, b, 2 * math.pi / 14):
            m.add(t0, sfx.plate_clank(q, 0.6), 0.35, 0.2, 0.15)
            q += 1
    for q in range(6):                                           # paychecks
        m.add(5.7 + q * 0.33, sfx.chime(1320 + 60 * q, 0.2), 0.35, 0.2, 0.3)
        m.add(5.7 + q * 0.33, sfx.tick(5000, 0.2), 0.3, 0.2, 0.1)
    for t, kind, _, extra in events:
        if kind == "shot":
            m.add(t, sfx.whoosh(0.35, 400, 8000, 0.5, seed=extra), 0.45, 0, 0.3)
            m.add(t + 0.05, sfx.text_hit(extra), 0.4, 0, 0.4)
        elif kind == "kick":
            m.add(t, sfx.punch_hit(1, 1.2), 0.8, 0, 0.3)
            m.add(t + 0.4, sfx.body_fall(), 0.7, 0, 0.4)
            m.add(t + 0.45, sfx.shatter(2, 0.6), 0.5, 0, 0.4)
        elif kind == "launch":
            m.add(t - 0.1, sfx.bandnoise(1.0, 80, 900, 4) * sfx.env_ad(int(1.0 * sfx.SR), 0.15, 0.85, 1.0), 0.6, 0, 0.3)
            m.add(t - 0.1, sfx.riser(0.8), 0.4, 0, 0.3)
        elif kind == "boom":
            m.add(t, sfx.boom(3.0), 0.95, 0, 0.5)
            m.add(t, sfx.shatter(5, 1.0), 0.6, 0, 0.5)
            m.add(t + 0.6, sfx.power_down(1.5), 0.3, 0, 0.4)
        elif kind == "up":
            m.add(t, sfx.breath(2, 0.6), 0.6, 0, 0.3)
            m.add(t + 0.2, sfx.power_up(110), 0.5, 0, 0.4)
        elif kind == "launch3":
            m.add(t - 0.6, sfx.riser(0.7), 0.6, 0, 0.3)
            m.add(t - 0.3, sfx.bandnoise(2.5, 60, 1200, 7) * sfx.env_ad(int(2.5 * sfx.SR), 0.1, 2.4, 1.5), 0.8, 0, 0.4)
            m.add(t, sfx.boom(2.5), 0.6, 0, 0.5)
        elif kind == "rich":
            for q in range(14):
                m.add(t + q * 0.05, sfx.tick(4000 + 150 * q, 0.2), 0.35, 0.2, 0.1)
            m.add(t + 0.7, sfx.chime(1760, 0.35), 0.6, 0, 0.6)
            m.add(t + 0.7, sfx.sparkle(1.5), 0.5, 0, 0.5)
        elif kind == "house":
            m.add(t, sfx.sparkle(1.0, 60, 3), 0.4, 0, 0.4)
        elif kind == "heart":
            m.add(t, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "pull":
            m.add(t, sfx.whoosh(1.6, 200, 3000, 0.5, seed=9), 0.6, 0, 0.5)
            m.add(t + 0.3, sfx.heartbeat(), 0.6, 0, 0.3)
        elif kind == "other":
            m.add(t, sfx.text_hit(4), 0.7, 0, 0.5)
            m.add(t + 0.1, sfx.heartbeat(), 0.5, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
            m.add(t + 0.5, sfx.text_hit(2), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t + 0.3, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t + 0.3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.8, 1.35, 1.9, 3.2, 4.3, 4.9, 6.6, 8.5, 9.5, 10.3, 12.5, 13.5, 15.3, 16.9, 18.2, 20.0, 22.0, 23.5,
              24.8, 28.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
