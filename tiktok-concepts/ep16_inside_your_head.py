"""EP16 - 5:00 AM, INSIDE YOUR HEAD

A figure sleeps. The alarm clock hits 5:00 (red) and rings. Zoom into his head:
a meeting table with COMFORT, EGO, DISCIPLINE and OBSESSION arguing in speech
bubbles. Vote 2-2. OBSESSION kicks COMFORT's pillow away, EGO: "...FINE."
Back in the bedroom: he sits up, stands, walks out of the door.
END   EVERY MORNING IS A VOTE. / WHO WON YOURS?
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, RED, WHITE, W, Camera, build_pose, clamp, draw_spaced, ease_out, font,
                    mix, paint, run_pose, smoothstep)
from kit import (CX, GREY, Log, Video, blend, bubble, caption, draw_body, lane_cam, mirror, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep16_inside_your_head"
dt = 1 / FPS
ALARM = 0.45
ZOOM = (2.4, 3.0)
MEET = (3.0, 13.4)
BED2 = 13.4
SIT_T, STAND_T, WALK_T = 13.8, 14.8, 15.5
P1, P2 = 17.6, 18.5
DUR = 21.0
HEAD = np.array([-2.0, 0.92])

LINES = [(3.4, "COMFORT", "5 MORE MINUTES."),
         (4.6, "EGO", "YOU WENT YESTERDAY."),
         (5.8, "COMFORT", "IT'S COLD OUTSIDE."),
         (7.0, "EGO", "NOBODY'S WATCHING ANYWAY."),
         (8.2, "DISCIPLINE", "WE AGREED. 5 AM."),
         (9.4, "OBSESSION", "I'M ALREADY OUTSIDE.")]
VOTE = 10.6
KICK = 11.9
FINE = 12.5
SEATS = {"COMFORT": -2.65, "EGO": -0.95, "DISCIPLINE": 0.95, "OBSESSION": 2.65}


def lying(x0=-0.6):
    return {"hip": np.array([x0, 0.78]), "neck": np.array([x0 - 0.92, 0.84]), "head": HEAD.copy(),
            "shoulder": np.array([x0 - 0.8, 0.83]), "knee1": np.array([x0 + 0.8, 0.82]),
            "foot1": np.array([x0 + 1.6, 0.78]), "knee2": np.array([x0 + 0.78, 0.8]),
            "foot2": np.array([x0 + 1.55, 0.76]), "elbow1": np.array([x0 - 0.5, 0.95]),
            "hand1": np.array([x0 - 0.1, 0.9]), "elbow2": np.array([x0 - 0.5, 0.9]), "hand2": np.array([x0 - 0.1, 0.86])}


def bedroom(e, f_, hc, tc, cam, t, blanket_a, ring):
    # floor
    e.drawLine(80, cam.pt((0, 0))[1], W - 80, cam.pt((0, 0))[1], paint(WHITE, 0.45, 2.5))
    # bed
    l, top = cam.pt((-2.7, 0.62))
    r, bot = cam.pt((1.5, 0.25))
    e.drawRect(skia.Rect(l, top, r, bot), paint(WHITE, 0.75, 3, cap=False))
    for lx in (-2.6, 1.4):
        e.drawLine(*cam.pt((lx, 0.25)), *cam.pt((lx, 0.0)), paint(WHITE, 0.6, 3))
    e.drawLine(*cam.pt((-2.7, 0.25)), *cam.pt((-2.7, 1.45)), paint(WHITE, 0.75, 4))
    e.drawOval(skia.Rect(*cam.pt((-2.6, 0.95)), *cam.pt((-1.75, 0.62))), paint(WHITE, 0.5, 3))
    # nightstand + clock
    nl, nt = cam.pt((1.85, 0.72))
    nr, nb = cam.pt((2.55, 0.0))
    e.drawRect(skia.Rect(nl, nt, nr, nb), paint(WHITE, 0.6, 3, cap=False))
    shake = ring * 5 * math.sin(t * 70)
    cl, ct = cam.pt((1.9, 1.12))
    cr, cb = cam.pt((2.5, 0.72))
    f_.drawRoundRect(skia.Rect(cl + shake, ct, cr + shake, cb), 8, 8, paint((0, 0, 0), 1.0))
    f_.drawRoundRect(skia.Rect(cl + shake, ct, cr + shake, cb), 8, 8, paint(WHITE, 0.8, 3))
    draw_spaced(tc, "5:00", (cl + cr) / 2 + shake, cb - (cb - ct) * 0.22, font(0.3 * cam.s, "InterDisplay-Black"), 2, paint(RED, 1.0))
    if ring > 0:
        cx, cy = (cl + cr) / 2, ct - 10
        for k in range(3):
            a = 0.4 + 0.6 * abs(math.sin(t * 12 + k))
            ang = -0.9 + 0.9 * k
            f_.drawLine(cx + math.sin(ang) * 40, cy - math.cos(ang) * 40, cx + math.sin(ang) * 70, cy - math.cos(ang) * 70,
                        paint(RED, a * ring, 4))
    # door
    dl, dt_ = cam.pt((2.95, 2.6))
    dr, db = cam.pt((3.55, 0.0))
    e.drawRect(skia.Rect(dl, dt_, dr, db), paint(WHITE, 0.6, 3, cap=False))


def blanket(hc, cam, alpha, t):
    if alpha < 0.01:
        return
    p = skia.Path()
    p.moveTo(*cam.pt((-1.75, 0.62)))
    breathe = 0.03 * math.sin(t * 2)
    p.cubicTo(*cam.pt((-1.5, 1.2 + breathe)), *cam.pt((0.2, 1.15 + breathe)), *cam.pt((0.6, 0.98)))
    p.cubicTo(*cam.pt((1.0, 0.9)), *cam.pt((1.3, 1.05)), *cam.pt((1.45, 0.62)))
    p.close()
    hc.drawPath(p, paint((0, 0, 0), alpha))
    hc.drawPath(p, paint(WHITE, alpha, 3))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    for fi in range(v.n):
        t = fi * dt
        if t >= ALARM:
            log.once("alarm", t, "alarm")
        if t >= ZOOM[0]:
            log.once("zoom", t, "zoom")
        for k, (tt, who, txt) in enumerate(LINES):
            if t >= tt:
                log.once(f"line{k}", t, "line", k)
        if t >= VOTE:
            log.once("vote", t, "vote")
        if t >= KICK:
            log.once("kick", t, "kick")
        if t >= FINE:
            log.once("fine", t, "fine")
        if t >= BED2:
            log.once("back", t, "back")
        if t >= STAND_T:
            log.once("stand", t, "stand")
        if t >= WALK_T:
            log.once("walk", t, "walk")
        if t >= P1:
            log.once("p1", t, "p1")
        if t >= P2:
            log.once("p2", t, "p2")
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        white = 0.0
        if t < MEET[0] or t >= BED2:
            # ================= BEDROOM
            cam = lane_cam(128, 1360, 0.4)
            if ZOOM[0] <= t < MEET[0]:
                u = ease_out((t - ZOOM[0]) / (ZOOM[1] - ZOOM[0]))
                cam.s = 128 * (1 - u) + 1400 * u
                cam.wx = 0.4 * (1 - u) + HEAD[0] * u
                cam.wy = 0.0 * (1 - u) + HEAD[1] * u
                cam.sy = 1360 * (1 - u) + 960 * u
                white = 0.8 * smoothstep(ZOOM[1] - 0.15, ZOOM[1], t)
            ring = 1.0 if ALARM <= t < ZOOM[0] + 0.2 else 0.0
            bedroom(e, f_, hc, tc, cam, t, 1.0, ring)
            if t < BED2:
                j = lying()
                if ring:
                    j = {k: vv + [0.02 * math.sin(t * 30), 0] for k, vv in j.items()}
                draw_body(hc, j, cam, WHITE, 1.0)
                blanket(hc, cam, 1.0, t)
            else:
                if t < SIT_T + 0.4:
                    w = smoothstep(BED2, SIT_T + 0.3, t)
                    js = sit(0.75, 0.62, t, 0.3)
                    j = blend(lying(), js, w)
                    draw_body(hc, j, cam, WHITE, 1.0)
                    blanket(hc, cam, 1 - smoothstep(BED2, SIT_T, t), t)
                elif t < WALK_T:
                    w = smoothstep(STAND_T - 0.4, WALK_T, t)
                    j = blend(sit(0.75, 0.62, t, 0.3), stand(1.0, 0.05, 0.15, 0.1, 0.2, 0.15, -0.05), w)
                    draw_body(hc, j, cam, WHITE, 1.0)
                else:
                    u = (t - WALK_T)
                    x = 1.0 + 1.6 * u
                    j = run_pose(x, u * 7, 0.4)
                    a = 1 - smoothstep(WALK_T + 1.25, WALK_T + 1.6, t)
                    draw_body(hc, j, cam, WHITE, a)
                    # door light
                    lx, ly = cam.pt((2.95, 2.6))
                    lr, lb = cam.pt((3.55, 0.0))
                    f_.drawRect(skia.Rect(lx, ly, lr, lb), paint(WHITE, 0.25 * smoothstep(WALK_T, WALK_T + 0.5, t)))
                    for k in range(2):
                        sx, sy = cam.pt((x + 0.1 - 0.25 * k, 0.04))
                        hc.drawLine(sx - 10, sy, sx + 14, sy, paint(RED, a, 8))     # red sneakers
                if t >= BED2 and t < BED2 + 0.2:
                    white = 0.6 * (1 - (t - BED2) / 0.2)
        else:
            # ================= INSIDE THE HEAD
            cam = lane_cam(92, 1260, 0.0)
            u0 = t - MEET[0]
            # skull outline
            pulse = 1 + 0.01 * math.sin(t * 3)
            e.drawCircle(CX, 1010, 430 * pulse, paint(WHITE, 0.35, 4))
            e.drawCircle(CX, 1010, 445 * pulse, paint(WHITE, 0.12, 2))
            # lamp
            e.drawLine(CX, 585, CX, 690, paint(WHITE, 0.5, 2))
            lamp = skia.Path()
            lamp.moveTo(CX - 45, 720)
            lamp.lineTo(CX + 45, 720)
            lamp.lineTo(CX + 20, 690)
            lamp.lineTo(CX - 20, 690)
            lamp.close()
            e.drawPath(lamp, paint(WHITE, 0.7, 3))
            cone = skia.Path()
            cone.moveTo(CX - 45, 720)
            cone.lineTo(CX + 45, 720)
            cone.lineTo(CX + 300, 1250)
            cone.lineTo(CX - 300, 1250)
            cone.close()
            e.drawPath(cone, paint(WHITE, 0.04))
            # table
            e.drawLine(*cam.pt((-1.9, 1.05)), *cam.pt((1.9, 1.05)), paint(WHITE, 0.85, 6))
            for lx in (-1.6, 1.6):
                e.drawLine(*cam.pt((lx, 1.05)), *cam.pt((lx, 0.0)), paint(WHITE, 0.6, 4))
            # who speaks
            speaker = None
            for tt, who, txt in LINES:
                if tt <= t < tt + 1.15:
                    speaker = who
            for name, x in SEATS.items():
                face = 1 if x < 0 else -1
                talk = 1.0 if speaker == name else 0.0
                bob = 0.04 * abs(math.sin(t * 12)) * talk
                if name == "COMFORT":
                    j = stand(0, 0.15, 0.9, 0.8, 1.6, 1.7, 0.4, bob)
                elif name == "EGO":
                    j = stand(0, -0.1, 0.5 + 0.9 * talk, 0.45, 1.9 - 1.5 * talk, 1.95, -0.2, bob)
                elif name == "DISCIPLINE":
                    slam = smoothstep(8.2, 8.35, t) * (1 - smoothstep(8.6, 8.9, t))
                    j = stand(0, 0.05 + 0.25 * slam, 1.3 - 0.6 * slam, 0.1, 0.4, 0.15, 0.0, bob)
                else:
                    if t < 9.3:
                        j = stand(0, 0.05, 0.3, 0.2, 0.6, 0.6, 0.0)
                    else:
                        j = run_pose(0, t * 9, 0.55)
                if VOTE <= t < KICK:
                    up = smoothstep(VOTE, VOTE + 0.2, t)
                    jv = stand(0, 0.0, 2.9, 0.1, 0.1, 0.15, -0.1)
                    j = blend(j, jv, up)
                if name == "COMFORT" and t >= KICK + 0.15:
                    fall = ease_out(clamp((t - KICK - 0.15) / 0.35))
                    c_, s_ = math.cos(1.2 * fall), math.sin(1.2 * fall)
                    pv = np.array([0.0, 0.0])
                    j = {k: np.array([c_ * vv[0] - s_ * vv[1], s_ * vv[0] + c_ * vv[1]]) for k, vv in j.items()}
                if name == "OBSESSION" and KICK - 0.4 <= t < KICK + 0.6:
                    kick = smoothstep(KICK - 0.4, KICK, t) * (1 - smoothstep(KICK + 0.25, KICK + 0.6, t))
                    j = build_pose(np.array([0, 1.5]), np.array([0.9 * kick + 0.12, 0.02 + 0.9 * kick]), np.array([-0.15, 0.02]),
                                   -0.15 * kick, 1.2, 0.3, 0.3, 0.3, -0.1)
                j = {k: vv + [x, 0] for k, vv in j.items()}
                if face < 0:
                    j = mirror(j, x)
                col = RED if name == "EGO" else WHITE
                al = 1.0 if speaker in (None, name) or VOTE <= t else 0.55
                draw_body(hc, j, cam, col, al)
                if name == "COMFORT" and t < KICK + 0.15:          # pillow
                    px, py = cam.pt((x + 0.45, 1.65))
                    hc.drawRoundRect(skia.Rect(px - 38, py - 24, px + 38, py + 24), 18, 18, paint((0, 0, 0), 1.0))
                    hc.drawRoundRect(skia.Rect(px - 38, py - 24, px + 38, py + 24), 18, 18, paint(WHITE, 1.0, 3))
                if name == "COMFORT" and t >= KICK + 0.15:          # pillow flies away
                    u = t - KICK - 0.15
                    px, py = cam.pt((x + 0.45 - 4 * u, 1.65 + 3 * u - 6 * u * u))
                    if py < 1500:
                        hc.drawRoundRect(skia.Rect(px - 38, py - 24, px + 38, py + 24), 18, 18, paint(WHITE, 1.0, 3))
                if name == "OBSESSION":
                    for k in (1, 2):
                        sx, sy = cam.pt(j[f"foot{k}"])
                        hc.drawLine(sx - 14, sy, sx + 14, sy, paint(RED, 1.0, 9))
                sx, _ = cam.pt((x, 0))
                draw_spaced(tc, name, sx, cam.sy + 42 + (22 if name in ("EGO", "OBSESSION") else 0), font(21, "Inter-Bold"), 3, paint(RED if name == "EGO" else WHITE, 0.9))
            # speech bubbles
            for tt, who, txt in LINES:
                if tt <= t < tt + 1.15:
                    a = smoothstep(tt, tt + 0.08, t) * (1 - smoothstep(tt + 1.0, tt + 1.15, t))
                    hx, hy = cam.pt((SEATS[who], 3.0))
                    bubble(oc, txt, (hx, hy), a, RED if who == "EGO" else WHITE, 36, -0.0, 120)
            if VOTE <= t < KICK + 0.2:
                caption(oc, "VOTE.", 520, smoothstep(VOTE, VOTE + 0.1, t), WHITE, 54)
                for name, x in SEATS.items():
                    yes = name in ("DISCIPLINE", "OBSESSION")
                    hx, hy = cam.pt((x, 3.5))
                    pop = 1 + 0.4 * math.exp(-(t - VOTE - 0.15) * 10)
                    draw_spaced(oc, "YES" if yes else "NO", hx, hy - 10, font(40 * pop, "InterDisplay-Black"), 2,
                                paint(WHITE if yes else RED, smoothstep(VOTE + 0.15, VOTE + 0.25, t)))
                caption(oc, "2 - 2", 600, smoothstep(VOTE + 0.5, VOTE + 0.6, t), RED, 60, band=False)
            if FINE <= t < MEET[1]:
                hx, hy = cam.pt((SEATS["EGO"], 3.0))
                bubble(oc, "...FINE.", (hx, hy), smoothstep(FINE, FINE + 0.08, t), RED, 36, 0, 120)
        # end
        if t >= P1:
            caption(oc, "EVERY MORNING IS A VOTE.", 560, smoothstep(P1, P1 + 0.3, t), WHITE, 52)
        if t >= P2:
            caption(oc, "WHO WON YOURS?", 660, smoothstep(P2, P2 + 0.3, t), RED, 64)
        v.compose(fi, t, white=white)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=STAND_T), gain=0.35, fade_in=1.5, fade_out=2.0, stop=DUR)
    for t, kind, _, extra in events:
        if kind == "alarm":
            for k in range(12):
                m.add(t + k * 0.16, sfx.beep(1760, 0.08, 0.5), 0.7, 0.4, 0.2)
        elif kind == "zoom":
            m.add(t, sfx.whoosh(0.7, 200, 8000, 0.85, seed=3), 0.9, 0, 0.3)
            m.add(t + 0.6, sfx.text_hit(5), 0.6, 0, 0.4)
        elif kind == "line":
            pan = [-0.5, -0.2, -0.5, -0.2, 0.2, 0.5][extra]
            m.add(t, sfx.chime(600 + 90 * extra, 0.2), 0.45, pan, 0.3)
            m.add(t, sfx.tick(1400, 0.4), 0.5, pan, 0.1)
            if extra == 4:
                m.add(t + 0.15, sfx.punch_hit(1, 1.0), 0.8, 0.2, 0.3)
            if extra == 5:
                for k in range(8):
                    m.add(t + k * 0.13, sfx.step_light(k), 0.35, 0.5, 0.1)
        elif kind == "vote":
            m.add(t, sfx.text_hit(2), 0.6, 0, 0.4)
            for k in range(4):
                m.add(t + 0.15 + 0.06 * k, sfx.tick(1800 + 300 * k, 0.4), 0.5, -0.6 + 0.4 * k, 0.1)
            m.add(t + 0.5, sfx.beep(330, 0.4), 0.5, 0, 0.3)
        elif kind == "kick":
            m.add(t, sfx.punch_hit(5, 1.2), 0.9, 0.3, 0.3)
            m.add(t + 0.15, sfx.whoosh(0.5, 300, 6000, 0.4, seed=7), 0.6, -0.4, 0.2)
            m.add(t + 0.45, sfx.body_fall() * 0.6, 0.7, -0.5, 0.3)
        elif kind == "fine":
            m.add(t, sfx.power_down(0.8), 0.4, -0.2, 0.3)
        elif kind == "back":
            m.add(t - 0.1, sfx.whoosh(0.4, 300, 8000, 0.5, seed=8), 0.6, 0, 0.3)
        elif kind == "stand":
            m.add(t, sfx.power_up(110), 0.8, 0, 0.4)
        elif kind == "walk":
            for k in range(5):
                m.add(t + k * 0.32, sfx.step_heavy(k), 0.45, 0.4, 0.2)
            m.add(t + 1.0, sfx.spot_on() * 0.6, 0.5, 0.5, 0.3)
        elif kind == "p1":
            m.add(t, sfx.text_hit(1), 0.6, 0, 0.4)
        elif kind == "p2":
            m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.4, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 2.8, 3.8, 5.0, 7.4, 8.4, 9.8, 11.0, 12.2, 12.8, 14.2, 16.0, 19.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
