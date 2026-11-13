"""EP15 - WHO DROPS IT LAST?  (bucket hold - same storyline as the user's reference, our DA)

Four figures under spotlights, each holding a bucket at arm's length:
MOTIVATION, EGO, DISCIPLINE, OBSESSION. Timer 0:00 -> 5:00.
~1:00 EGO's arm shakes, the bucket drops, he folds over.
~2:00 MOTIVATION drops too.
3:00+ DISCIPLINE's arm sinks and shakes, his hand turns red... but he holds.
OBSESSION never moves.
END   MOTIVATION GETS YOU STARTED. / OBSESSION KEEPS YOU GOING. (typed)
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, RED, WHITE, W, Camera, build_pose, clamp, draw_figure, draw_spaced,
                    ease_out, font, mix, paint, smoothstep)
from kit import CX, GREY, Log, Video, blend, lane_cam
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep15_who_drops_it_last"
dt = 1 / FPS
S = 108.0
FLOOR = 1240.0
NAMES = ["MOTIVATION", "EGO", "DISCIPLINE", "OBSESSION"]
XS = [-3.25, -1.32, 0.61, 2.54]
T_END = 12.4                 # timer reaches 5:00
SEC_PER_T = 300 / T_END
DROP = {"EGO": 2.45, "MOTIVATION": 4.85}
SHAKE_FROM = {"EGO": 1.4, "MOTIVATION": 3.6, "DISCIPLINE": 6.8}
SAG = (7.0, 9.8)             # discipline's arm sinks
TXT1, TXT2 = 7.6, 8.4
DUR = T_END + 2.4
MONO = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf")


def mono(size):
    f = skia.Font(MONO, size)
    f.setSubpixel(True)
    return f


def hold_pose(x, t, i, sag=0.0, shake=0.0):
    br = 0.012 * math.sin(t * 2.2 + i)
    a = 1.57 - 0.55 * sag + shake * 0.06 * math.sin(t * 43 + i)
    return build_pose(np.array([x, 1.55 + br]), np.array([x + 0.12, 0.02]), np.array([x - 0.12, 0.02]),
                      0.0, a, 0.05, 0.02 + 0.15 * sag, 0.1, 0.05 + 0.1 * sag)


def folded_pose(x, t):
    """Bent over, hands on the knees, head hanging (the 'gave up' pose)."""
    hip = np.array([x, 1.15])
    lean = 1.35
    j = build_pose(hip, np.array([x + 0.45, 0.02]), np.array([x + 0.2, 0.02]), lean, 0.25, 0.2, 0.25, 0.2, 0.8)
    knee = j["knee1"]
    j["hand1"] = knee + [0.08, 0.05]
    j["hand2"] = knee + [0.0, 0.0]
    j["elbow1"] = (j["shoulder"] + j["hand1"]) / 2 + [0.1, 0.05]
    j["elbow2"] = (j["shoulder"] + j["hand2"]) / 2 + [0.05, 0.05]
    return j


def draw_bucket(c, cam, hand, alpha, col=WHITE, swing=0.0, ground=False, glow=0.0):
    hx, hy = hand
    if ground:
        top = np.array([hx, 0.4])
    else:
        top = np.array([hx + swing, hy - 0.32])
    tw, bw, h = 0.24, 0.17, 0.4
    p = skia.Path()
    p.moveTo(*cam.pt(top + [-tw, 0]))
    p.lineTo(*cam.pt(top + [tw, 0]))
    p.lineTo(*cam.pt(top + [bw, -h]))
    p.lineTo(*cam.pt(top + [-bw, -h]))
    p.close()
    c.drawPath(p, paint((0, 0, 0), 1.0))
    c.drawPath(p, paint(col, alpha, max(2, 0.04 * cam.s)))
    c.drawLine(*cam.pt(top + [-tw, -0.08]), *cam.pt(top + [tw, -0.08]), paint(col, 0.5 * alpha, 2))
    if not ground:
        hp = skia.Path()
        hp.moveTo(*cam.pt(top + [-tw * 0.9, 0]))
        hp.quadTo(*cam.pt((hx, hy + 0.08)), *cam.pt(top + [tw * 0.9, 0]))
        c.drawPath(hp, paint(col, alpha, 2))
    if glow > 0:
        c.drawCircle(*cam.pt(hand), 0.35 * cam.s, paint(RED, 0.25 * glow))


def spotlight(c, cam, x, alpha):
    if alpha < 0.01:
        return
    sx, _ = cam.pt((x + 0.35, 0))
    top_y = 300
    p = skia.Path()
    p.moveTo(sx - 18, top_y)
    p.lineTo(sx + 18, top_y)
    p.lineTo(sx + 0.75 * cam.s, FLOOR)
    p.lineTo(sx - 0.75 * cam.s, FLOOR)
    p.close()
    pt = skia.Paint(AntiAlias=True)
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, top_y), skia.Point(0, FLOOR)],
                                                [skia.Color4f(1, 1, 1, 0.0), skia.Color4f(1, 1, 1, 0.11 * alpha)]))
    c.drawPath(p, pt)
    c.drawOval(skia.Rect(sx - 0.8 * cam.s, FLOOR - 14, sx + 0.8 * cam.s, FLOOR + 14), paint(WHITE, 0.12 * alpha))


def reflect(j):
    return {k: np.array([v[0], -v[1]]) for k, v in j.items()}


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    cam = lane_cam(S, FLOOR)
    for fi in range(v.n):
        t = fi * dt
        secs = min(300, int(t * SEC_PER_T))
        # events
        for n, td in DROP.items():
            if t >= td:
                log.once(f"drop{n}", t, "drop", NAMES.index(n))
            if t >= SHAKE_FROM[n]:
                log.once(f"shake{n}", t, "shake", NAMES.index(n))
        if t >= SHAKE_FROM["DISCIPLINE"]:
            log.once("shakeD", t, "shake", 2)
        if t >= TXT1:
            log.once("txt1", t, "type", 1)
        if t >= TXT2:
            log.once("txt2", t, "type", 2)
        if t >= T_END:
            log.once("end", t, "end")
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        e.drawLine(80, FLOOR, W - 80, FLOOR, paint(WHITE, 0.35, 2))
        for i, n in enumerate(NAMES):
            x = XS[i]
            dropped = n in DROP and t >= DROP[n]
            spot_a = 1.0 if not dropped else 1 - 0.6 * smoothstep(DROP[n], DROP[n] + 0.6, t)
            spotlight(e, cam, x, spot_a)
            shake = smoothstep(SHAKE_FROM.get(n, 99), SHAKE_FROM.get(n, 99) + 0.8, t)
            sag = smoothstep(*SAG, t) if n == "DISCIPLINE" else 0.0
            j = hold_pose(x, t, i, sag, shake * (0.6 if n == "DISCIPLINE" else 1.0))
            col = WHITE
            if dropped:
                w = smoothstep(DROP[n], DROP[n] + 0.45, t)
                j = blend(j, folded_pose(x, t), ease_out(w))
                col = mix(WHITE, GREY, 0.5 * w)
            # floor reflection
            draw_figure(e, reflect(j), cam, col, 0.045, 1.0, thick=1.35)
            # figure
            draw_figure(hc, j, cam, col, 1.0, 0.75, thick=1.35)
            if n == "OBSESSION":                    # red stripe: front arm + front leg
                lw = 0.19 * S * 1.35 * 0.55
                for a_, b_ in (("hip", "knee1"), ("knee1", "foot1"), ("shoulder", "elbow1"), ("elbow1", "hand1")):
                    hc.drawLine(*cam.pt(j[a_]), *cam.pt(j[b_]), paint(RED, 1.0, lw))
            # bucket
            hand = j["hand1"]
            if dropped:
                u = clamp((t - DROP[n]) / 0.3)
                fall_y = hand[1] - 0.32 - (hand[1] - 0.32 - 0.4) * u * u
                if u < 1:
                    draw_bucket(f_, cam, (hand[0] + 0.15 * u, fall_y + 0.32), 1.0, col)
                else:
                    draw_bucket(f_, cam, (hand[0] + 0.15, 0), 0.85, GREY, ground=True)
            else:
                glow = smoothstep(SAG[0] + 1.0, SAG[1], t) if n == "DISCIPLINE" else 0.0
                swing = 0.03 * math.sin(t * 2.5 + i) + shake * 0.04 * math.sin(t * 37 + i)
                bcol = mix(WHITE, RED, glow) if n == "DISCIPLINE" else (RED if n == "OBSESSION" else WHITE)
                draw_bucket(f_, cam, hand, 1.0, bcol, swing, glow=glow)
                if n == "DISCIPLINE" and glow > 0:
                    hc.drawCircle(*cam.pt(hand), 0.11 * S, paint(RED, glow))
            # labels (row above the figures)
            la = 1.0 if not dropped else 1 - 0.75 * smoothstep(DROP[n], DROP[n] + 0.5, t)
            lcol = RED if (n == "OBSESSION" and t >= TXT2) else WHITE
            sx, _ = cam.pt((x + 0.3, 0))
            draw_spaced(tc, n, sx, 700, mono(24), 3, paint(lcol, la))
        # timer
        draw_spaced(tc, f"{secs // 60}:{secs % 60:02d}", CX, 600, mono(56), 2, paint(WHITE, 0.85))
        # title + typed lines
        ta = 1 - 0.55 * smoothstep(TXT1 - 0.2, TXT1, t)
        draw_spaced(oc, "WHO DROPS IT LAST?", CX, 400, font(46, "InterDisplay-Black"), 2, paint(WHITE, ta))
        for t0, txt, col, y in ((TXT1, "MOTIVATION GETS YOU STARTED.", WHITE, 456),
                                (TXT2, "OBSESSION KEEPS YOU GOING.", RED, 508)):
            if t >= t0:
                n_ch = min(len(txt), int((t - t0) / 0.028))
                draw_spaced(oc, txt[:n_ch], CX - (len(txt) - n_ch) * 0, y, font(38, "InterDisplay-Black"), 1, paint(col, 1.0))
        v.compose(fi, t)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=T_END), gain=0.45, fade_in=0.4, fade_out=2.0, stop=DUR)
    m.add(0.05, sfx.spot_on(), 0.8, 0, 0.4)
    k = 0
    tt = 0.3
    while tt < T_END:                       # clock ticking, slowly speeding up
        m.add(tt, sfx.tick(2600 if k % 2 else 2000, 0.35), 0.35, 0, 0.05)
        tt += 0.5 - 0.25 * (tt / T_END)
        k += 1
    for t, kind, _, extra in events:
        pan = -0.6 + 0.4 * extra
        if kind == "shake":
            dur = (DROP[["MOTIVATION", "EGO"][0 if extra == 0 else 1]] - t) if extra in (0, 1) else T_END - t
            m.add(t, sfx.rattle(max(0.5, dur), extra + 3), 0.5, pan, 0.2)
            m.add(t, sfx.breath(extra, 0.8), 0.4, pan, 0.2)
        elif kind == "drop":
            m.add(t + 0.28, sfx.plate_clank(extra * 7, 0.9), 0.8, pan, 0.4)
            m.add(t + 0.2, sfx.body_fall() * 0.6, 0.6, pan, 0.3)
            m.add(t, sfx.power_down(1.2), 0.35, pan, 0.4)
        elif kind == "type":
            txt = "MOTIVATION GETS YOU STARTED." if extra == 1 else "OBSESSION KEEPS YOU GOING."
            for k in range(len(txt)):
                if txt[k] != " ":
                    m.add(t + k * 0.028, sfx.tick(3200 + 300 * (k % 3), 0.25), 0.4, 0, 0.05)
            m.add(t + len(txt) * 0.028, sfx.text_hit(extra), 0.6 if extra == 1 else 0.9, 0, 0.4)
        elif kind == "end":
            m.add(t, sfx.boom(2.5), 0.7, 0, 0.5)
            m.add(t, sfx.bell(900, 2.0), 0.5, 0, 0.5)
    m.add(SAG[0], sfx.heartbeat(), 0.6, 0, 0.3)
    m.add(SAG[0] + 1.2, sfx.heartbeat(), 0.7, 0, 0.3)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.3, 2.2, 2.9, 5.3, 8.0, 9.2, 12.0, 13.8]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
