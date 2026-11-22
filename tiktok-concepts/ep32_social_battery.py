"""EP32 - EXTROVERT VS INTROVERT  (the social battery)

Split screen, big characters, a BIG battery next to each one, a clock on the
divider. Same day, four moments:
  8 AM  alone at home   Extrovert slumped on the couch: battery drains (15%).
                        Introvert reads in his armchair: battery charges (100%).
  1 PM  lunch with colleagues  Extrovert laughs: 70%. Introvert stiff: 55%.
  9 PM  the party       Extrovert dances under the strobes: 100% FULL.
                        Introvert in the corner: 4% LOW BATTERY... he slips out.
  11 PM back home       Extrovert alone again: drains. Introvert with his book:
                        charging bolt, 100%.
END (black, centred) NEITHER IS BROKEN. / THEY JUST CHARGE / DIFFERENTLY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, font, ik, mix,
                    paint, run_pose, smoothstep)
from kit import CX, GREY, Log, Video, blend, caption, draw_body, draw_phone_small, ending, lane_cam, mirror, sit, stand
import ep24_friday_night as e24
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep32_social_battery"
dt = 1 / FPS
S = 120.0
LANES = {"EXTROVERT": (330, 935, 860), "INTROVERT": (965, 1565, 1495)}
PX = -0.6                     # character x (world)
ACTS = [(0.0, "8:00 AM", "home"), (4.0, "1:00 PM", "lunch"), (8.0, "9:00 PM", "party"), (12.5, "11:00 PM", "home2")]
FLEE = (11.2, 12.3)
END_T = 16.0
DUR = 20.0
BAT = {"EXTROVERT": [(0, 55), (3.8, 15), (4.2, 15), (7.8, 70), (8.2, 70), (11.5, 100), (12.5, 100), (15.5, 35)],
       "INTROVERT": [(0, 60), (3.8, 100), (4.2, 100), (7.8, 55), (8.2, 55), (11.0, 4), (12.5, 6), (15.5, 100)]}


def lin(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return kf[-1][1]


def act(t):
    cur = ACTS[0]
    for a in ACTS:
        if t >= a[0]:
            cur = a
    return cur


def battery(c, x, y, val, t, charging=False, label=None):
    """Big readable battery (screen px), top-left at (x, y)."""
    w, h = 150, 260
    low = val < 25
    col = RED if low else WHITE
    blink = 1.0 if not (val < 10) else (0.4 + 0.6 * (int(t * 4) % 2))
    r = skia.Rect(x, y, x + w, y + h)
    c.drawRoundRect(r, 18, 18, paint((0, 0, 0), 0.9))
    c.drawRoundRect(r, 18, 18, paint(col, blink, 6))
    c.drawRoundRect(skia.Rect(x + w * 0.32, y - 22, x + w * 0.68, y + 2), 6, 6, paint(col, blink))
    fill_h = (h - 24) * clamp(val / 100)
    c.drawRoundRect(skia.Rect(x + 12, y + h - 12 - fill_h, x + w - 12, y + h - 12), 8, 8, paint(col, 0.9 * blink))
    if charging:
        b = skia.Path()
        cx, cy = x + w / 2, y + h / 2
        for k, (dx, dy) in enumerate(((10, -70), (-35, 10), (0, 10), (-10, 70), (35, -10), (0, -10))):
            (b.moveTo if k == 0 else b.lineTo)(cx + dx, cy + dy)
        b.close()
        c.drawPath(b, paint((0, 0, 0), 1.0))
        c.drawPath(b, paint(WHITE, 1.0, 4))
    draw_spaced(c, f"{int(round(val))}%", x + w / 2, y + h + 58, font(52, "InterDisplay-Black"), 2, paint(col, blink))
    if label:
        draw_spaced(c, label, x + w / 2, y - 40, font(30, "InterDisplay-Black"), 2, paint(col, blink))


def couch(c, cam, x, alpha=1.0):
    p = skia.Path()
    pts = [(x - 1.1, 0.1), (x - 1.1, 1.35), (x - 0.85, 1.45), (x - 0.7, 0.78), (x + 0.9, 0.78), (x + 1.05, 1.0), (x + 1.15, 0.1)]
    p.moveTo(*cam.pt(pts[0]))
    for q in pts[1:]:
        p.lineTo(*cam.pt(q))
    p.close()
    c.drawPath(p, paint((0, 0, 0), alpha))
    c.drawPath(p, paint(WHITE, 0.7 * alpha, 4))


def lamp(c, f_, cam, x, on):
    c.drawLine(*cam.pt((x, 0)), *cam.pt((x, 2.3)), paint(WHITE, 0.6, 3))
    sh = skia.Path()
    sh.moveTo(*cam.pt((x - 0.35, 2.2)))
    sh.lineTo(*cam.pt((x + 0.35, 2.2)))
    sh.lineTo(*cam.pt((x + 0.2, 2.65)))
    sh.lineTo(*cam.pt((x - 0.2, 2.65)))
    sh.close()
    c.drawPath(sh, paint(WHITE, 0.8, 3))
    if on:
        cone = skia.Path()
        cone.moveTo(*cam.pt((x - 0.35, 2.2)))
        cone.lineTo(*cam.pt((x + 0.35, 2.2)))
        cone.lineTo(*cam.pt((x + 1.4, 0)))
        cone.lineTo(*cam.pt((x - 0.4, 0)))
        cone.close()
        f_.drawPath(cone, paint(WHITE, 0.06))


def reading(x, t):
    j = sit(x - 0.3, 0.72, t, 0.2)
    sh = j["shoulder"]
    for i, off in ((1, 0.0), (2, -0.05)):
        hand = sh + np.array([0.48 + off, -0.12])
        j[f"hand{i}"] = hand
        j[f"elbow{i}"] = ik(sh, hand, L_UARM, L_FARM, -1)
    j["head"] = j["head"] + [0.05, -0.06]
    return j


def book(c, cam, j, alpha=1.0):
    hx, hy = cam.pt((j["hand1"] + j["hand2"]) / 2)
    w, h = 0.5 * cam.s, 0.38 * cam.s
    c.drawRect(skia.Rect(hx - w / 2, hy - h, hx + w / 2, hy), paint((0, 0, 0), alpha))
    c.drawRect(skia.Rect(hx - w / 2, hy - h, hx + w / 2, hy), paint(WHITE, alpha, 3, cap=False))
    c.drawLine(hx, hy - h, hx, hy, paint(WHITE, alpha, 2))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    for fi in range(v.n):
        t = fi * dt
        for k, (ta, clk, kind) in enumerate(ACTS):
            if t >= ta:
                log.once(f"act{k}", ta, "act", k)
        for key, tt, kind in (("full", 11.5, "full"), ("low", 10.4, "low"), ("flee", FLEE[0], "flee"),
                              ("charge", 13.0, "charge"), ("end", END_T, "end"), ("end2", END_T + 1.0, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        ta, clk, kind = act(t)
        u_act = t - ta
        for n, (y0, y1, gy) in LANES.items():
            cam = lane_cam(S, gy, 0.0)
            cam.sx = 380
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.save()
                L.canvas.clipRect(skia.Rect(0, y0, W, y1))
            e.drawLine(60, gy, W - 60, gy, paint(WHITE, 0.45, 2.5))
            col = RED if n == "EXTROVERT" else WHITE
            val = lin(t, BAT[n])
            j = None
            if kind in ("home", "home2"):
                if n == "EXTROVERT":
                    couch(e, cam, PX)
                    j = sit(PX - 0.35, 0.78, t, 0.9)
                    j["hand1"] = j["shoulder"] + np.array([0.55, 0.15])
                    j["elbow1"] = ik(j["shoulder"], j["hand1"], L_UARM, L_FARM, -1)
                    draw_body(hc, j, cam, col, 1.0)
                    draw_phone_small(f_, cam, j["hand1"] + [0.05, 0.12], 1.0)
                    hx, hy = cam.pt(j["head"])
                    draw_spaced(tc, "...", hx + 70, hy - 50, font(50, "InterDisplay-Black"), 6, paint(WHITE, 0.6))
                else:
                    couch(e, cam, PX, 0.8)
                    lamp(e, f_, cam, PX - 1.6, True)
                    j = reading(PX, t)
                    draw_body(hc, j, cam, col, 1.0)
                    book(hc, cam, j)
                    hx, hy = cam.pt(j["head"])
                    draw_spaced(tc, "♪", hx + 60, hy - 60 - 10 * math.sin(t * 3), font(46, "Inter-Bold"), 0, paint(WHITE, 0.0))
            elif kind == "lunch":
                tl, tt_ = cam.pt((PX - 0.2, 1.05))
                tr, _ = cam.pt((PX + 2.0, 1.05))
                e.drawLine(tl, tt_, tr, tt_, paint(WHITE, 0.7, 4))
                for lx in (PX - 0.1, PX + 1.9):
                    e.drawLine(*cam.pt((lx, 1.05)), *cam.pt((lx, 0)), paint(WHITE, 0.5, 3))
                for k, cx_ in enumerate((PX + 0.85, PX + 1.55, PX + 2.25)):
                    jg = sit(cx_ - 0.3, 0.72, t, 0.1)
                    jg = mirror(jg, cx_) if k > 0 else jg
                    draw_body(e, jg, cam, GREY, 0.45)
                if n == "EXTROVERT":
                    bob = 0.06 * abs(math.sin(t * 9))
                    j = sit(PX - 0.6, 0.72, t, 0.0)
                    j = {k: vv + [0, bob] for k, vv in j.items()}
                    j["hand1"] = j["shoulder"] + np.array([0.4, 0.55 + 0.15 * math.sin(t * 8)])
                    j["elbow1"] = ik(j["shoulder"], j["hand1"], L_UARM, L_FARM, 1)
                    j["head"] = j["head"] + [0.0, 0.05]
                    if int(t * 2) % 2 == 0:
                        hx, hy = cam.pt(j["head"])
                        draw_spaced(tc, "HAHA", hx + 10, hy - 55, font(44, "InterDisplay-Black"), 2, paint(RED, 1.0))
                else:
                    j = sit(PX - 0.6, 0.72, t, 0.05)
                    j["hand1"] = j["shoulder"] + np.array([0.35, -0.35])
                    j["hand2"] = j["shoulder"] + np.array([0.3, -0.4])
                    j["elbow1"] = ik(j["shoulder"], j["hand1"], L_UARM, L_FARM, -1)
                    j["elbow2"] = ik(j["shoulder"], j["hand2"], L_UARM, L_FARM, -1)
                    j = {k: vv + [0.012 * math.sin(t * 40), 0] for k, vv in j.items()}
                    hx, hy = cam.pt(j["head"])
                    draw_spaced(tc, "*SMILES*", hx + 10, hy - 55, font(34, "InterDisplay-Black"), 2, paint(WHITE, 0.8))
                draw_body(hc, j, cam, col, 1.0)
            else:  # party
                if int(t * 6) % 2 == 0:
                    e.drawRect(skia.Rect(0, y0, W, y1), paint(RED, 0.08))
                bx, by = cam.pt((PX + 1.0, 3.9))
                e.drawLine(bx, y0, bx, by - 26, paint(WHITE, 0.4, 2))
                e.drawCircle(bx, by, 26, paint(WHITE, 0.85, 3))
                for k, fx in enumerate((PX + 0.85, PX + 1.5, PX + 2.15)):
                    draw_body(e, e24.dance(fx, t, k * 1.3), cam, GREY, 0.45)
                if n == "EXTROVERT":
                    j = e24.dance(PX, t * 1.2, 0.0)
                else:
                    if t < FLEE[0]:
                        j = stand(PX - 0.9, 0.12, 0.9, 0.1, 1.5, 0.15, 0.45)
                        j = {k: vv + [0.01 * math.sin(t * 45), 0] for k, vv in j.items()}
                        hx, hy = cam.pt(j["hand1"])
                        hc.drawRect(skia.Rect(hx - 9, hy - 28, hx + 9, hy), paint(WHITE, 1.0, 3, cap=False))
                    else:
                        u = (t - FLEE[0]) / (FLEE[1] - FLEE[0])
                        xx = PX - 0.9 - 1.0 * u
                        j = mirror(run_pose(xx, t * 9, 0.6), xx)
                        ja = 1 - smoothstep(0.75, 1.0, u)
                    dl, dt_ = cam.pt((PX - 2.2, 2.6))
                    dr, db = cam.pt((PX - 1.55, 0.0))
                    e.drawRect(skia.Rect(dl, dt_, dr, db), paint(WHITE, 0.6, 3, cap=False))
                    draw_spaced(tc, "EXIT", (dl + dr) / 2, dt_ - 12, font(26, "InterDisplay-Black"), 3, paint(RED, 0.9))
                draw_body(hc, j, cam, col, 1.0)
            # label
            if j is not None:
                sx, _ = cam.pt((j["hip"][0], 0))
                draw_spaced(tc, n, sx, gy + 42, font(26, "Inter-Bold"), 4, paint(col, 1.0))
            for L in (v.env, v.fig, v.hero, v.txt):
                L.canvas.restore()
            # battery (overlay, readable)
            charging = n == "INTROVERT" and kind in ("home", "home2") or n == "EXTROVERT" and kind in ("lunch", "party")
            lab = None
            if val >= 99.5:
                lab = "FULL"
            elif val < 10:
                lab = "LOW!"
            battery(oc, 705, y0 + 120, val, t, charging and val < 99.5, lab)
        # divider + clock
        oc.drawRect(skia.Rect(0, 935, W, 965), paint((0, 0, 0), 1.0))
        pop = 1 + 0.3 * math.exp(-(t - ta) * 8)
        draw_spaced(oc, clk, CX, 966, font(40 * pop, "InterDisplay-Black"), 3, paint(WHITE, 1.0))
        if t < 1.8:
            caption(oc, "EXTROVERT VS INTROVERT", 405, 1 - smoothstep(1.4, 1.8, t), WHITE, 48)
        ending(oc, t, END_T - 0.3, [(END_T, "NEITHER", WHITE, 100), (END_T + 0.25, "IS BROKEN.", WHITE, 100),
                                    (END_T + 1.0, "THEY JUST CHARGE", RED, 84), (END_T + 1.25, "DIFFERENTLY.", RED, 92)],
               gap=120)
        cut = 0.0
        for ta_, _, _ in ACTS[1:]:
            if ta_ <= t < ta_ + 0.15:
                cut = 0.35 * (1 - (t - ta_) / 0.15)
        v.compose(fi, t, white=cut, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR), gain=0.35, fade_in=0.3, fade_out=2.0, stop=DUR)
    t_ = 8.0
    k = 0
    while t_ < 12.5:                                              # party beat
        m.add(t_, sfx.step_heavy(k) * 0.9, 0.35, -0.3, 0.05)
        if k % 2:
            m.add(t_, sfx.tick(5000, 0.15), 0.2, -0.3, 0.05)
        t_ += 0.25
        k += 1
    for t, kind, _, extra in events:
        if kind == "act":
            m.add(t, sfx.whoosh(0.35, 400, 8000, 0.5, seed=extra), 0.5, 0, 0.3)
            m.add(t + 0.05, sfx.text_hit(extra), 0.55, 0, 0.4)
            if extra == 1:
                m.add(t + 0.3, sfx.laugh(5, 5, 170, 0.5), 0.4, -0.3, 0.4)
                m.add(t + 1.6, sfx.laugh(6, 4, 150, 0.5), 0.35, -0.2, 0.4)
            if extra in (0, 3):
                m.add(t + 0.4, sfx.power_down(2.4), 0.3, -0.4, 0.4)
                m.add(t + 0.4, sfx.chime(660, 0.25), 0.4, 0.4, 0.6)
        elif kind == "full":
            m.add(t, sfx.power_up(110), 0.8, -0.3, 0.4)
            m.add(t + 0.5, sfx.chime(1320, 0.3), 0.5, -0.3, 0.5)
        elif kind == "low":
            for q in range(5):
                m.add(t + q * 0.25, sfx.beep(880, 0.12), 0.5, 0.4, 0.2)
        elif kind == "flee":
            for q in range(5):
                m.add(t + 0.1 + q * 0.2, sfx.step_light(q), 0.4, 0.4, 0.1)
            m.add(t + 0.9, sfx.punch_block(3), 0.5, 0.4, 0.3)
        elif kind == "charge":
            m.add(t, sfx.riser(2.4), 0.4, 0.4, 0.3)
            m.add(t + 2.4, sfx.chime(1320, 0.3), 0.6, 0.4, 0.5)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 2.5, 3.8, 5.5, 7.5, 9.0, 10.8, 11.6, 12.0, 13.4, 15.2, 18.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
