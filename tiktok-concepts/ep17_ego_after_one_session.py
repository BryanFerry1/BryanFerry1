"""EP17 - EGO AFTER 1 GYM SESSION  (self-irony, series format)

EGO walks into the gym: red headband, giant shaker. One rep with a tiny
dumbbell -> "DONE." 47 selfies. The mirror shows a bodybuilder. Posts a story
"NEW ME." (3 views). Buys $240 of gear. DAY 2: walks like a robot, can't lift
his arms, collapses on the couch: "NEVER AGAIN."
Meanwhile, in the back, DISCIPLINE has been doing his sets the whole time.
END   SEE YOU NEXT JANUARY.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, draw_spaced, ease_out, font, mix, paint, run_pose, smoothstep
from kit import (CX, GREY, Log, Video, blend, bubble, caption, curl, draw_body, draw_heart,
                 draw_phone_small, flex, lane_cam, mirror, phone_pose, scale_pose, sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep17_ego_after_one_session"
dt = 1 / FPS
S = 138.0
GROUND = 1390.0
EX = -0.9
CH = [(0.0, "walkin"), (2.2, "rep"), (4.6, "selfies"), (7.4, "mirror"), (9.6, "story"),
      (11.8, "gear"), (13.9, "day2"), (16.9, "meanwhile"), (19.0, "end")]
DUR = 22.0


def chapter(t):
    cur = CH[0]
    for c in CH:
        if t >= c[0]:
            cur = c
    return cur


def headband(c, cam, j, col=RED):
    hx, hy = cam.pt(j["head"])
    r = 0.29 * cam.s
    c.drawLine(hx - r * 0.95, hy - r * 0.25, hx + r * 0.95, hy - r * 0.35, paint(col, 1.0, 7))
    c.drawLine(hx - r * 0.95, hy - r * 0.25, hx - r * 1.5, hy + r * 0.2, paint(col, 1.0, 5))


def shaker(c, cam, pos, alpha=1.0):
    x, y = cam.pt(pos)
    w, h = 0.22 * cam.s, 0.62 * cam.s
    r = skia.Rect(x - w / 2, y - h, x + w / 2, y)
    c.drawRoundRect(r, 8, 8, paint((0, 0, 0), 1.0))
    c.drawRoundRect(r, 8, 8, paint(WHITE, alpha, 3))
    c.drawRect(skia.Rect(x - w / 2 - 3, y - h - 14, x + w / 2 + 3, y - h), paint(RED, alpha))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    rng = np.random.default_rng(3)
    for fi in range(v.n):
        t = fi * dt
        ct, name = chapter(t)
        u = t - ct
        log.once(name, ct, "chapter", [c[1] for c in CH].index(name))
        if name == "selfies":
            k = int(u / 0.16)
            log.once(f"shot{k}", t, "shutter", k)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        cam = lane_cam(S, GROUND)
        e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.45, 2.5))
        # ---------------- DISCIPLINE in the back, always doing his sets
        bc = lane_cam(S * 0.72, GROUND - 120)
        e.drawLine(80, bc.sy, W - 80, bc.sy, paint(WHITE, 0.12, 1.5))
        rep_p = 1.25
        c_ = math.sin(math.pi * ((t % rep_p) / rep_p))
        jd = scale_pose(curl(3.0, c_), 3.0, 1.18)
        focus = smoothstep(CH[7][0], CH[7][0] + 0.5, t) * (1 - smoothstep(CH[8][0] + 1.2, CH[8][0] + 1.8, t))
        if name in ("meanwhile",):
            bc = lane_cam(S * (0.72 + 0.4 * ease_out(min(1, u / 0.6))), GROUND - 120 + 80 * ease_out(min(1, u / 0.6)),
                          3.0 * ease_out(min(1, u / 0.6)) * 0.6)
        da = 0.45 + 0.55 * focus
        draw_body(e if focus < 0.5 else hc, jd, bc, WHITE, da, 0.75)
        bar = (jd["hand1"] + jd["hand2"]) / 2
        for kk, rr in enumerate([0.13, 0.22, 0.22]):
            cx, cy = bc.pt(bar + np.array([0.06, -0.04]) * kk)
            (e if focus < 0.5 else hc).drawCircle(cx, cy, rr * bc.s, paint((0, 0, 0), 1.0))
            (e if focus < 0.5 else hc).drawCircle(cx, cy, rr * bc.s, paint(WHITE, da, 3))
        sets = int(t / rep_p) + 1 + (int(1286 * smoothstep(CH[7][0], CH[7][0] + 1.2, t)) if t >= CH[7][0] else 0)
        sx, sy = bc.pt((3.0, 0))
        draw_spaced(tc, "DISCIPLINE", sx, sy + 34, font(20 + 8 * focus, "Inter-Bold"), 3, paint(WHITE, 0.5 + 0.5 * focus))
        draw_spaced(tc, f"SET {sets:,}", sx, sy - 3.9 * bc.s, font(20 + 14 * focus, "InterDisplay-Bold"), 2, paint(WHITE, 0.45 + 0.55 * focus))

        # ---------------- EGO
        ea = 1 - 0.7 * focus
        if name == "walkin":
            x = -4.2 + 3.3 * ease_out(min(1, u / 1.6))
            je = run_pose(x, u * 8, 0.35 if u < 1.6 else 0.0)
            je = blend(je, stand(x, -0.12, 0.6, 0.15, 1.7, 0.2, -0.3), smoothstep(1.4, 1.9, u))
            draw_body(hc, je, cam, WHITE, ea)
            shaker(hc, cam, je["hand1"] + [0.05, 0.35])
            headband(hc, cam, je)
        elif name == "rep":
            if u < 1.4:
                c2 = 0.6 * math.sin(math.pi * min(1, u / 1.2)) ** 0.6
                je = curl(EX, c2)
                je["hand1"] = je["hand1"] + [0.02 * math.sin(t * 50), 0.02 * math.sin(t * 43)]
            else:
                je = blend(curl(EX, 0), stand(EX, -0.1, 0.5, 0.45, 1.9, 1.95, -0.2), smoothstep(1.4, 1.7, u))
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            if u < 1.5:
                b = (je["hand1"] + je["hand2"]) / 2
                hc.drawCircle(*cam.pt(b), 0.07 * S, paint(WHITE, 1.0, 3))
            else:
                hc.drawCircle(*cam.pt((EX + 0.5, 0.08)), 0.07 * S, paint(WHITE, 0.8, 3))
            caption(oc, "1 REP.", 560, smoothstep(1.2, 1.3, u), WHITE, 56)
            if u > 1.6:
                hx, hy = cam.pt(je["head"])
                bubble(oc, "DONE.", (hx, hy - 20), smoothstep(1.6, 1.7, u), RED, 40, 60, 80)
        elif name == "selfies":
            k = int(u / 0.55) % 3
            je = [phone_pose(EX, t), flex(EX, t), stand(EX, -0.1, 2.6, 0.5, 0.5, 1.9, -0.3)][k]
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            ph = je["hand1"] if k != 2 else je["hand1"]
            draw_phone_small(f_, cam, ph + [0.05, 0.12], 1.0)
            if (u % 0.16) < 0.06:
                f_.drawCircle(*cam.pt(ph + [0.05, 0.2]), 0.35 * S, paint(WHITE, 0.9))
            n = min(47, int(1 + 46 * clamp(u / 2.4) ** 1.4))
            caption(oc, f"PHOTOS: {n}", 560, 1.0, WHITE, 56)
        elif name == "mirror":
            ml, mt = cam.pt((0.3, 3.4))
            mr, mb = cam.pt((1.7, 0.12))
            e.drawRoundRect(skia.Rect(ml, mt, mr, mb), 16, 16, paint(WHITE, 0.9, 5))
            je = flex(EX, t)
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            hc.save()
            hc.clipRect(skia.Rect(ml, mt, mr, mb))
            refl = mirror({kk: vv + [1.0 - EX + 0.0, 0] for kk, vv in je.items()}, 1.0)
            refl = scale_pose(refl, 1.0, 1.08)
            draw_body(hc, refl, cam, WHITE, 1.0, 1.0)
            headband(hc, cam, refl)
            hc.restore()
            for k in range(3):
                if rng.random() < 0.5:
                    p = np.array([rng.uniform(0.4, 1.6), rng.uniform(0.5, 3.2)])
                    f_.drawCircle(*cam.pt(p), 4, paint(WHITE, 0.9))
            hx, hy = cam.pt(je["head"])
            bubble(oc, "BUILT DIFFERENT.", (hx, hy - 20), smoothstep(0.5, 0.6, u), RED, 38, -40, 80)
        elif name == "story":
            je = phone_pose(EX, t)
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            # story card (opaque, centred)
            pop = 1 + 0.06 * (1 - ease_out(min(1, u / 0.2)))
            cw, chh = 420 * pop, 700 * pop
            r = skia.Rect(CX - cw / 2, 560, CX + cw / 2, 560 + chh)
            oc.drawRoundRect(r, 30, 30, paint((0, 0, 0), 0.97))
            oc.drawRoundRect(r, 30, 30, paint(WHITE, 1.0, 4))
            oc.drawLine(r.left() + 20, 590, r.left() + 20 + (cw - 40) * min(1, u / 2.0), 590, paint(WHITE, 1.0, 5))
            sc_ = lane_cam(120, 560 + chh * 0.78)
            sc_.sx = CX
            sj = flex(0.0, t)
            draw_body(oc, sj, sc_, WHITE, 1.0, 0.0)
            headband(oc, sc_, sj)
            draw_spaced(oc, "NEW ME.", CX, 560 + chh * 0.88, font(56, "InterDisplay-Black"), 3, paint(WHITE, 1.0))
            draw_spaced(oc, "3 VIEWS", CX, 560 + chh * 0.96, font(26, "Inter-Bold"), 3, paint(GREY, 1.0))
            for k in range(3):
                hx = CX - 60 + 60 * k
                draw_heart(oc, hx, 640 + 10 * math.sin(t * 5 + k), 16, smoothstep(0.3 + 0.2 * k, 0.4 + 0.2 * k, u))
        elif name == "gear":
            je = stand(EX, -0.1, 0.9, 0.85, 0.4, 0.4, -0.25)
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            items = [("GLOVES", 0.0), ("BELT", 0.35), ("PRE-WORKOUT", 0.7), ("SHAKER XL", 1.05)]
            for k, (it, t0) in enumerate(items):
                if u >= t0:
                    pop = 1 + 0.5 * math.exp(-(u - t0) * 10)
                    draw_spaced(oc, "+ " + it, CX, 680 + 62 * k, font(36 * pop, "InterDisplay-Black"), 2, paint(WHITE, 1.0))
            for k in range(2):                      # shopping bags
                bx, by = cam.pt((EX + 0.55 - 1.1 * k, 0.9))
                bw = 0.45 * S
                hc.drawRect(skia.Rect(bx - bw / 2, by, bx + bw / 2, by + 0.5 * S), paint((0, 0, 0), 1.0))
                hc.drawRect(skia.Rect(bx - bw / 2, by, bx + bw / 2, by + 0.5 * S), paint(WHITE, 1.0, 3, cap=False))
            caption(oc, "$240 OF GEAR.", 600, smoothstep(1.3, 1.4, u), RED, 60)
        elif name == "day2":
            caption(oc, "DAY 2.", 560, 1.0, WHITE, 64)
            if u < 1.7:
                x = EX - 1.2 + 1.2 * (u / 1.7)
                stiff = stand(x, 0.0, 0.05, -0.05, 0.0, 0.0, 0.0)
                step = math.sin(u * 9) * 0.25
                stiff["foot1"] = stiff["foot1"] + [step, 0]
                stiff["foot2"] = stiff["foot2"] - [step, 0]
                stiff["knee1"] = (stiff["hip"] + stiff["foot1"]) / 2
                stiff["knee2"] = (stiff["hip"] + stiff["foot2"]) / 2
                je = stiff
                for k in range(3):                  # pain lines
                    px, py = cam.pt(je["shoulder"] + [0.1, 0.1])
                    ang = -0.6 + 0.6 * k
                    f_.drawLine(px + math.cos(ang) * 30, py - math.sin(ang) * 30, px + math.cos(ang) * 55, py - math.sin(ang) * 55,
                                paint(RED, 0.9, 4))
            else:
                # couch
                cl, ct = cam.pt((EX - 1.4, 1.0))
                cr, cb = cam.pt((EX + 1.0, 0.0))
                e.drawRoundRect(skia.Rect(cl, ct, cr, cb), 20, 20, paint(WHITE, 0.6, 4))
                je = sit(EX - 0.3, 0.6, t, 1.0)
            draw_body(hc, je, cam, WHITE, ea)
            headband(hc, cam, je)
            if u > 1.9:
                hx, hy = cam.pt(je["head"])
                bubble(oc, "NEVER AGAIN.", (hx, hy - 10), smoothstep(1.9, 2.0, u), RED, 40, 40, 80)
        elif name in ("meanwhile", "end"):
            je = sit(EX - 0.3, 0.6, t, 1.0)
            cl, ct = cam.pt((EX - 1.4, 1.0))
            cr, cb = cam.pt((EX + 1.0, 0.0))
            e.drawRoundRect(skia.Rect(cl, ct, cr, cb), 20, 20, paint(WHITE, 0.3, 4))
            draw_body(e, je, cam, GREY, 0.6)
            if name == "meanwhile":
                caption(oc, "MEANWHILE.", 560, smoothstep(0.1, 0.25, u), WHITE, 60)
            else:
                caption(oc, "SEE YOU NEXT JANUARY.", 560, smoothstep(0.05, 0.35, u), RED, 56)
        if name not in ("meanwhile", "end", "story"):
            lx, _ = cam.pt((EX if name != "walkin" else min(EX, -4.2 + 3.3 * ease_out(min(1, u / 1.6))), 0))
            draw_spaced(tc, "EGO", lx, GROUND + 46, font(28, "Inter-Bold"), 6, paint(RED, ea))
        # title
        if t < 2.2:
            caption(oc, "EGO AFTER 1 GYM SESSION", 470, smoothstep(0.05, 0.25, t) * (1 - smoothstep(1.9, 2.2, t)), WHITE, 48)
        v.compose(fi, t, white=0.25 * max(0.0, 1 - u / 0.12) if name != "walkin" else 0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR), gain=0.3, fade_in=0.5, fade_out=2.0, stop=DUR)
    # Discipline's quiet reps the whole time
    tt = 0.6
    while tt < DUR - 1:
        m.add(tt, sfx.plate_clank(int(tt * 10), 0.3) * 0.5, 0.18, 0.5, 0.2)
        tt += 1.25
    for t, kind, _, extra in events:
        if kind == "chapter":
            m.add(t, sfx.whoosh(0.3, 600, 9000, 0.5, seed=extra), 0.4, 0, 0.2)
            if extra == 0:
                for k in range(5):
                    m.add(t + 0.2 + k * 0.32, sfx.step_light(k), 0.4, -0.4, 0.1)
                m.add(t + 0.1, sfx.text_hit(5), 0.6, 0, 0.4)
            elif extra == 1:
                m.add(t + 0.2, sfx.breath(2, 1.0), 0.6, -0.2, 0.2)
                m.add(t + 1.25, sfx.text_hit(1), 0.5, 0, 0.3)
                m.add(t + 1.6, sfx.plate_clank(3, 0.3), 0.5, -0.2, 0.3)
            elif extra == 3:
                m.add(t, sfx.sparkle(1.6, 80, 4), 0.6, 0.2, 0.5)
                m.add(t + 0.5, sfx.chime(880, 0.3), 0.5, 0, 0.5)
            elif extra == 4:
                for k in range(3):
                    m.add(t + 0.35 + 0.2 * k, sfx.chime(990 + 120 * k, 0.25), 0.45, 0, 0.4)
            elif extra == 5:
                for k in range(4):
                    m.add(t + 0.35 * k, sfx.tick(2400 + 200 * k, 0.5), 0.5, 0.2, 0.1)
                m.add(t + 1.3, sfx.beep(1320, 0.25), 0.5, 0, 0.3)
            elif extra == 6:
                for k in range(6):
                    m.add(t + k * 0.28, sfx.step_heavy(k), 0.35, -0.3, 0.1)
                m.add(t + 0.3, sfx.glitch(2), 0.4, -0.3, 0.2)
                m.add(t + 1.8, sfx.body_fall() * 0.5, 0.6, -0.3, 0.3)
                m.add(t + 1.9, sfx.power_down(1.0), 0.4, -0.3, 0.3)
            elif extra == 7:
                m.add(t, sfx.text_hit(2), 0.6, 0.3, 0.4)
                m.add(t + 0.3, sfx.riser(1.5), 0.4, 0.3, 0.3)
            elif extra == 8:
                m.add(t, sfx.text_hit(3), 0.9, 0, 0.5)
                m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
        elif kind == "shutter":
            if extra < 18:
                m.add(t, sfx.shutter(extra), 0.4, -0.3, 0.2)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.0, 3.5, 4.0, 5.8, 8.3, 10.6, 13.0, 14.6, 16.2, 17.8, 20.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
