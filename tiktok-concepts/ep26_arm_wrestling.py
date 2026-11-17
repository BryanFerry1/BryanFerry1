"""EP26 - TALENT VS OBSESSION  (arm wrestling)

One shared scene, moving from the first frame, camera alternating wide shots
and zooms (EP25 format). A timer at the top builds the tension.
  GO     TALENT slams OBSESSION's hand to 2 CM from the table (zoom on hands).
  zoom   OBSESSION's face: shaking, sweating. He holds.
  wide   time flies 0:10 -> 1:30. Talent relaxed, waves at the crowd.
  zoom   TALENT checks his watch, bored.
  zoom   hands: inch by inch, Obsession comes back (red aura).
  zoom   TALENT's face: panic, sweat.
  wide   past the middle...
  slow   zoom on hands: SLAM, Talent's hand on the table, the table cracks red.
END (black, centred) TALENT WINS / THE FIRST MINUTE. / OBSESSION WINS / THE LAST ONE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import (FPS, H, L_FARM, L_UARM, RED, WHITE, W, Camera, Particles, build_pose, clamp, draw_spaced,
                    ease_out, font, ik, mix, paint, smoothstep)
from kit import CX, GREY, Log, Video, arms_up, blend, caption, draw_body, ending, mirror, stand
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep26_arm_wrestling"
dt = 1 / FPS
TABLE_Y = 1.0
ELB = 0.46                    # elbow distance from centre
FORE = 0.78                   # forearm length
HX_T, HX_O = -1.45, 1.45        # hips
GO = 2.0
SLAM_T = 13.4
END_T = 15.6
DUR = 19.6
PIN = 1.42                    # angle where a hand touches the table

# theta > 0: hands lean towards OBSESSION (he is losing); theta < 0: towards TALENT
TH_KF = [(0.0, 0.0), (GO, 0.0), (GO + 0.6, 1.30), (5.0, 1.33), (8.6, 1.33), (10.0, 0.75), (11.6, 0.0),
         (12.8, -0.75), (SLAM_T, -PIN), (99, -PIN)]
SHOTS = [(0.0, "wide", 140), (GO + 0.5, "HANDS", 250), (3.6, "FACE_O", 230), (5.0, "wide", 140),
         (7.0, "FACE_T", 230), (8.6, "HANDS", 250), (10.0, "FACE_T", 235), (11.4, "wide", 145),
         (12.8, "HANDS", 270), (14.0, "wide", 140)]


def keys(t, kf):
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * u * u * (3 - 2 * u)
    return kf[-1][1]


def theta(t):
    th = keys(t, TH_KF)
    if GO + 0.6 < t < SLAM_T:
        th += 0.025 * math.sin(t * 31) + 0.015 * math.sin(t * 53)
    return th


def timer_secs(t):
    if t < GO:
        return 0
    u = clamp((t - GO) / (SLAM_T - GO))
    return int(192 * u ** 1.15)


def joined(th):
    return np.array([math.sin(th) * FORE, TABLE_Y + math.cos(th) * FORE])


def wrestler(hip_x, t, th, side, free="table", tremble=0.0):
    """side -1 = TALENT on the left (facing right), +1 = OBSESSION on the right (facing left)."""
    # build facing right around x=0, then mirror for Obsession
    hip = np.array([0.0, 1.32])
    j = build_pose(hip, np.array([0.3, 0.02]), np.array([-0.4, 0.02]), 0.42, 1.2, 0.9, 0.6, 1.6, 0.15)
    jx = hip_x if side < 0 else -hip_x
    j = {k: vv + [jx + 0.0, 0] for k, vv in j.items()}
    h = joined(th if side < 0 else -th)
    elbow = np.array([-ELB, TABLE_Y + 0.02])
    sh = j["shoulder"]
    j["elbow1"] = elbow
    j["hand1"] = h
    if free == "table":
        j["hand2"] = np.array([-0.7, TABLE_Y + 0.03])
        j["elbow2"] = (sh + j["hand2"]) / 2 + np.array([0.05, -0.15])
    elif free == "watch":
        j["hand2"] = j["head"] + np.array([0.15, -0.25])
        j["elbow2"] = sh + np.array([0.45, -0.35])
    elif free == "wave":
        j["hand2"] = sh + np.array([-0.25, 0.9 + 0.1 * math.sin(t * 14)])
        j["elbow2"] = sh + np.array([-0.2, 0.45])
    if tremble > 0:
        for k in ("head", "neck", "shoulder"):
            j[k] = j[k] + np.array([tremble * 0.02 * math.sin(t * 47), tremble * 0.015 * math.sin(t * 59)])
    if side > 0:
        j = mirror(j, 0.0)
    return j


def target(t, th):
    cur = SHOTS[0]
    for s in SHOTS:
        if t >= s[0]:
            cur = s
    _, who, s = cur
    h = joined(th)
    if who == "wide":
        return 0.0, 1.35, s
    if who == "HANDS":
        return h[0] * 0.6, (h[1] + TABLE_Y) / 2, s
    if who == "FACE_O":
        return 0.9, 1.9, s
    if who == "FACE_T":
        return -0.9, 1.9, s
    return 0.0, 1.35, s


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    sweat = Particles(4)
    aura = Particles(5)
    rng = np.random.default_rng(3)
    cam = Camera()
    cam.sx, cam.sy = CX, 1010.0
    cam.wx, cam.wy, cam.s = target(0.0, 0.0)
    for fi in range(v.n):
        t = fi * dt
        th = theta(t)
        for k, (ts, who, s) in enumerate(SHOTS[1:], 1):
            if t >= ts:
                log.once(f"cut{k}", ts, "cut", k)
        for key, tt, kind in (("go", GO, "go"), ("slam1", GO + 0.6, "slam1"), ("hold", 3.6, "hold"),
                              ("bored", 7.0, "bored"), ("back", 8.6, "back"), ("panic", 10.0, "panic"),
                              ("slam", SLAM_T, "slam"), ("end", END_T, "end"), ("end2", END_T + 0.9, "end2")):
            if t >= tt:
                log.once(key, tt, kind)
        secs = timer_secs(t)
        if secs and secs % 10 == 0:
            log.once(f"tick{secs}", t, "tick")
        # sweat: obsession while holding, talent when panicking
        if 3.0 < t < 8.6 and rng.random() < 0.5:
            sweat.emit(np.array([[0.75 + rng.normal(0, 0.08), 2.25 + rng.normal(0, 0.05)]]), vel=(0.3, -0.6), spread=0.3,
                       life=(0.4, 0.8), size=(0.02, 0.035))
        if 10.0 < t < SLAM_T and rng.random() < 0.6:
            sweat.emit(np.array([[-0.75 + rng.normal(0, 0.08), 2.25 + rng.normal(0, 0.05)]]), vel=(-0.3, -0.6), spread=0.3,
                       life=(0.4, 0.8), size=(0.02, 0.035))
        if 8.6 <= t < SLAM_T + 1.0 and rng.random() < 0.7:
            aura.emit(np.array([[HX_O - 0.2 + rng.normal(0, 0.35), rng.uniform(0.4, 2.4)]]), vel=(0, 1.2), spread=0.4,
                      life=(0.5, 1.0), size=(0.02, 0.05))
        sweat.step(dt)
        aura.step(dt)
        wx, wy, s = target(t, th)
        snap = any(abs(t - ts) < dt * 0.6 for ts, _, _ in SHOTS[1:])
        k_ = 0.5 if snap else 0.2
        cam.wx += (wx - cam.wx) * k_
        cam.wy += (wy - cam.wy) * k_
        cam.s = math.exp(math.log(cam.s) + (math.log(s) - math.log(cam.s)) * k_)
        shake = 0.0
        for tt, a in ((GO + 0.6, 8.0), (SLAM_T, 16.0)):
            if t >= tt:
                shake = max(shake, a * math.exp(-(t - tt) * 5))
        cam.sx = CX + shake * math.sin(t * 85)
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        gy = cam.pt((0, 0))[1]
        e.drawLine(0, gy, W, gy, paint(WHITE, 0.45, 2.5))
        # crowd (back row)
        for k in range(8):
            cx_ = -3.3 + 0.95 * k
            if abs(cx_) < 0.6:
                continue
            hop = 0.07 * abs(math.sin(t * 8 + k)) * (1 if (t > 11.4) else 0.3)
            hx, hy = cam.pt((cx_, 2.05 + hop))
            e.drawCircle(hx, hy, 0.22 * cam.s, paint(GREY, 0.35))
            bl, bt = cam.pt((cx_ - 0.28, 1.8 + hop))
            br, bb = cam.pt((cx_ + 0.28, 0.9))
            e.drawRoundRect(skia.Rect(bl, bt, br, bb), 0.12 * cam.s, 0.12 * cam.s, paint(GREY, 0.25))
        # table
        crack = smoothstep(SLAM_T, SLAM_T + 0.15, t)
        tl, ttop = cam.pt((-0.95, TABLE_Y))
        tr, _ = cam.pt((0.95, TABLE_Y))
        e.drawLine(tl, ttop, tr, ttop, paint(WHITE, 0.85, max(3, 0.06 * cam.s)))
        for lx in (-0.8, 0.8):
            e.drawLine(*cam.pt((lx, TABLE_Y)), *cam.pt((lx, 0)), paint(WHITE, 0.55, max(2, 0.04 * cam.s)))
        if crack > 0:
            cx_, cy_ = cam.pt((-0.55, TABLE_Y))
            p = skia.Path()
            p.moveTo(cx_, cy_)
            for q in range(5):
                p.lineTo(cx_ + (q + 1) * 0.07 * cam.s * (1 if q % 2 else -0.6), cy_ + (q + 1) * 0.12 * cam.s * crack)
            f_.drawPath(p, paint(RED, 1.0, 4))
        # "2 CM" marker when Obsession is near the table
        if GO + 0.7 < t < 8.6:
            hcur = joined(th)
            a = smoothstep(GO + 0.7, GO + 0.9, t)
            p1 = cam.pt((hcur[0] + 0.12, hcur[1] - 0.05))
            p2 = cam.pt((hcur[0] + 0.12, TABLE_Y))
            oc.drawLine(p1[0], p1[1], p2[0], p2[1], paint(RED, a, 4))
            for py in (p1[1], p2[1]):
                oc.drawLine(p1[0] - 12, py, p1[0] + 12, py, paint(RED, a, 4))
            lx_, ly_ = p1[0] + 0.9 * cam.s, p1[1] - 0.75 * cam.s
            oc.drawLine(lx_ - 40, ly_ + 14, p1[0] + 14, (p1[1] + p2[1]) / 2, paint(RED, a, 4))
            sz = 64 if cam.s > 200 else 44
            draw_spaced(oc, "2 CM", min(lx_ + 30, 800), ly_, font(sz, "InterDisplay-Black"), 2, paint(RED, a))
        # wrestlers
        free_t = "table"
        if 5.4 <= t < 7.0:
            free_t = "wave"
        elif 7.0 <= t < 8.6:
            free_t = "watch"
        trem_o = smoothstep(GO + 0.6, 3.2, t) * (1 - smoothstep(8.6, 9.6, t)) + 0.6 * smoothstep(11.4, 12.8, t)
        trem_t = smoothstep(9.6, 10.4, t)
        jt = wrestler(HX_T, t, th, -1, free_t, trem_t)
        jo = wrestler(HX_O, t, th, +1, "table", trem_o)
        lost = smoothstep(SLAM_T + 0.3, SLAM_T + 1.0, t)
        if lost > 0:
            jo = blend(jo, arms_up(HX_O, t), lost)
        col_t = mix(WHITE, GREY, 0.6 * smoothstep(SLAM_T, SLAM_T + 1.0, t))
        col_o = mix(WHITE, RED, 0.45 * smoothstep(8.6, 10.0, t))
        draw_body(hc, jt, cam, col_t, 1.0, 0.0)
        draw_body(hc, jo, cam, col_o, 1.0, 0.12)
        if free_t == "watch":
            wx_, wy_ = cam.pt(jt["hand2"] + [0.0, -0.08])
            f_.drawCircle(wx_, wy_, 0.07 * cam.s, paint(WHITE, 1.0, 3))
        # the two wrestling arms, drawn on top in distinct colours (Talent white, Obsession red)
        if lost <= 0:
            lw = max(4, 0.15 * cam.s)
            for j_, col_ in ((jt, WHITE), (jo, RED)):
                hc.drawLine(*cam.pt(j_["shoulder"]), *cam.pt(j_["elbow1"]), paint(col_, 1.0, lw))
                hc.drawLine(*cam.pt(j_["elbow1"]), *cam.pt(j_["hand1"]), paint(col_, 1.0, lw))
                hc.drawCircle(*cam.pt(j_["elbow1"]), lw * 0.7, paint(col_, 1.0))
            h = joined(th)
            d = np.array([math.cos(th), -math.sin(th)]) * 0.07       # two fists side by side across the grip
            hc.drawCircle(*cam.pt(h - d), 0.12 * cam.s, paint(WHITE, 1.0))
            hc.drawCircle(*cam.pt(h + d), 0.12 * cam.s, paint(RED, 1.0))
        sweat.draw(f_, cam, WHITE, WHITE)
        aura.draw(f_, cam, RED, RED)
        # panic marks / boredom
        if 10.0 <= t < SLAM_T:
            hx_, hy_ = cam.pt(jt["head"])
            for q in range(3):
                ang = -2.2 + 0.5 * q
                f_.drawLine(hx_ + math.cos(ang) * 0.38 * cam.s, hy_ + math.sin(ang) * 0.38 * cam.s,
                            hx_ + math.cos(ang) * 0.55 * cam.s, hy_ + math.sin(ang) * 0.55 * cam.s, paint(RED, 0.9, 4))
        if 7.0 <= t < 8.6:
            hx_, hy_ = cam.pt(jt["head"])
            draw_spaced(tc, "*YAWN*", hx_ - 0.1 * cam.s, hy_ - 0.55 * cam.s, font(min(40, max(24, 0.13 * cam.s)), "InterDisplay-Black"), 2,
                        paint(WHITE, 0.9))
        # labels
        for j, nme, col in ((jt, "TALENT", WHITE), (jo, "OBSESSION", RED)):
            fxx = (j["foot1"][0] + j["foot2"][0]) / 2
            sx, sy = cam.pt((fxx, 0))
            la = 1 - smoothstep(160, 200, cam.s)
            draw_spaced(tc, nme, sx, sy + 38, font(26, "Inter-Bold"), 4, paint(col, la))
        # timer
        ta = smoothstep(GO - 0.2, GO, t) * (1 - smoothstep(END_T - 0.6, END_T - 0.3, t))
        if ta > 0.01:
            draw_spaced(oc, "TIME", CX, 360, font(24, "Inter-SemiBold"), 12, paint(WHITE, 0.7 * ta))
            draw_spaced(oc, f"{secs // 60}:{secs % 60:02d}", CX, 470, font(104, "InterDisplay-Bold"), 4,
                        paint(RED if t >= SLAM_T else WHITE, ta))
            # tug gauge: half circle, needle = who is winning (left TALENT / right OBSESSION)
            gx, gy_, gr = CX, 1500, 95
            oc.drawRoundRect(skia.Rect(gx - 250, gy_ - gr - 25, gx + 250, gy_ + 50), 20, 20, paint((0, 0, 0), 0.85 * ta))
            arc = skia.Path()
            arc.addArc(skia.Rect(gx - gr, gy_ - gr, gx + gr, gy_ + gr), 180, 180)
            oc.drawPath(arc, paint(WHITE, 0.6 * ta, 5))
            ang = -th / PIN * (math.pi / 2) - math.pi / 2           # th>0 (Talent winning) -> needle to the left
            ang = -math.pi / 2 + clamp(-th / PIN, -1, 1) * (math.pi / 2)
            oc.drawLine(gx, gy_, gx + math.cos(ang) * gr * 0.9, gy_ + math.sin(ang) * gr * 0.9, paint(RED, ta, 6))
            oc.drawCircle(gx, gy_, 10, paint(RED, ta))
            draw_spaced(oc, "TALENT", gx - gr - 10, gy_ + 34, font(22, "Inter-Bold"), 2, paint(WHITE, ta))
            draw_spaced(oc, "OBSESSION", gx + gr + 10, gy_ + 34, font(22, "Inter-Bold"), 2, paint(RED, ta))
        if t < GO:
            caption(oc, "TALENT VS OBSESSION", 600, 1 - smoothstep(GO - 0.3, GO, t), WHITE, 60)
        if GO - 0.05 <= t < GO + 0.5:
            pop = 1 + 0.4 * math.exp(-(t - GO) * 10)
            draw_spaced(oc, "GO!", CX, 640, font(150 * pop, "InterDisplay-Black"), 6, paint(RED, 1 - smoothstep(GO + 0.3, GO + 0.5, t)))
        ending(oc, t, END_T - 0.3, [(END_T, "TALENT WINS", WHITE, 88), (END_T + 0.25, "THE FIRST MINUTE.", WHITE, 88),
                                    (END_T + 1.0, "OBSESSION WINS", RED, 88), (END_T + 1.25, "THE LAST ONE.", RED, 88)],
               gap=118)
        flash = math.exp(-(t - SLAM_T) * 3) if t >= SLAM_T else 0.0
        white = 0.08 * max(0.0, 1 - min(abs(t - ts) for ts, _, _ in SHOTS[1:]) / 0.05)
        v.compose(fi, t, flash=flash, white=white, glow=0.25 * smoothstep(8.6, 10, t), fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=SLAM_T), gain=0.42, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(GO + 0.6, sfx.rattle(SLAM_T - GO - 0.6, 3), 0.4, 0, 0.2)       # creaking table / strain
    t_ = 0.2
    while t_ < GO:                                                        # countdown ticks
        m.add(t_, sfx.tick(1800, 0.5), 0.4, 0, 0.1)
        t_ += 0.6
    for t, kind, _, extra in events:
        if kind == "go":
            m.add(t, sfx.text_hit(5), 0.9, 0, 0.4)
            m.add(t, sfx.bell(), 0.5, 0, 0.5)
        elif kind == "slam1":
            m.add(t, sfx.punch_hit(5, 1.6), 0.9, 0.2, 0.4)
            m.add(t, sfx.boom(1.6), 0.5, 0, 0.4)
        elif kind == "cut":
            m.add(t - 0.05, sfx.whoosh(0.25, 500, 9000, 0.6, seed=extra), 0.4, 0, 0.2)
        elif kind == "hold":
            m.add(t, sfx.breath(4, 1.0), 0.6, 0.3, 0.2)
            m.add(t + 0.3, sfx.heartbeat(), 0.8, 0.3, 0.3)
            m.add(t + 1.1, sfx.heartbeat(), 0.8, 0.3, 0.3)
        elif kind == "bored":
            m.add(t, sfx.chime(660, 0.25), 0.4, -0.3, 0.4)
        elif kind == "back":
            m.add(t, sfx.power_up(70), 0.9, 0.3, 0.4)
            m.add(t + 0.5, sfx.riser(SLAM_T - t - 0.5), 0.5, 0, 0.3)
        elif kind == "panic":
            m.add(t, sfx.glitch(3), 0.5, -0.3, 0.2)
            for q in range(4):
                m.add(t + 0.3 + 0.7 * q, sfx.heartbeat(), 0.6 + 0.08 * q, -0.3, 0.3)
        elif kind == "tick":
            m.add(t, sfx.tick(2600, 0.35), 0.4, 0, 0.05)
        elif kind == "slam":
            m.add(t, sfx.punch_hit(77, 2.4), 1.0, -0.2, 0.5)
            m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
            m.add(t + 0.05, sfx.shatter(4, 1.0), 0.6, -0.2, 0.4)
            m.add(t + 0.4, sfx.applause(3.0, 55, 5), 0.55, 0, 0.3)
        elif kind == "end":
            m.add(t, sfx.text_hit(1), 0.7, 0, 0.4)
        elif kind == "end2":
            m.add(t, sfx.text_hit(3), 0.95, 0, 0.5)
            m.add(t, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.5, 2.1, 3.0, 4.3, 5.8, 7.6, 9.3, 10.6, 12.0, 13.1, 13.6, 14.6, 17.5]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
