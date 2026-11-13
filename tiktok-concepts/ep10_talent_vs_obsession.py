"""EP10 - TALENT VS OBSESSION  (the prodigy)

Visual hook: AGE 1. Baby TALENT already walks, the crowd claps. Baby
OBSESSION falls on his bottom.
AGE 8 / 14 / 19: three races. TALENT wins them all (trophies pop), each time
lazier (the last one he checks his phone mid-race and still wins by a hair).
OBSESSION loses, every time a bit closer.
AGE 20-24: TALENT parties (red strobes, phone, his trophies fall off the
shelf and break). OBSESSION sprints on, gets stronger.
AGE 25: final race. TALENT gives up halfway. OBSESSION breaks the red tape in
slow motion. TALENT, in the back, claps.
PUNCH  TALENT WAS BORN. / OBSESSION WAS / BUILT.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, RED, WHITE, W, clamp, draw_figure, ease_out, mix, paint, run_pose, smoothstep
from kit import (CX, GREY, Log, Shards, Video, arms_up, blend, body_scale, clap, draw_body,
                 draw_phone_small, draw_trophy, hud, label, lane_cam, phone_pose, punch,
                 scale_pose, sit, stand, title)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep10_talent_vs_obsession"
dt = 1 / FPS
S = 105.0
GROUND = 1320.0
FIN = 18.0
STRIDE = 2.6

INTRO = (0.0, 2.7)
RACES = [  # start, age, talent speed fn, obsession speed
    (2.8, 8), (6.1, 14), (9.4, 19), (15.6, 25)]
RACE_LEN = 3.0
PARTY = (12.7, 15.4)
FALLS = [13.2, 13.8, 14.4]


def t_speed(i, u):
    if i == 0:
        return 7.6
    if i == 1:
        return 7.2
    if i == 2:
        return 7.6 if (u < 0.9 or u > 1.5) else 4.2     # checks his phone mid-race
    return 6.0 if u < 1.0 else max(0.0, 6.0 - (u - 1.0) * 9)  # gives up


def o_speed(i, u):
    return [5.0, 6.1, 6.7, 8.6][i]


def integ(fn, i, u):
    n = max(1, int(u / 0.01))
    return sum(fn(i, k * 0.01) for k in range(n)) * (u / n)


def rate(t):
    a = RACES[3][0] + FIN / 8.6 - 0.35
    w = smoothstep(a - 0.1, a, t) * (1 - smoothstep(a + 0.7, a + 0.9, t))
    return 1 - 0.65 * w


taus = [0.0]
END_RACE4 = RACES[3][0] + FIN / 8.6 + 0.6
while taus[-1] < END_RACE4:
    taus.append(taus[-1] + rate(taus[-1]) * dt)
T_END4 = len(taus) * dt
P1, P2, P3 = T_END4 + 0.9, T_END4 + 1.8, T_END4 + 2.3
DUR = P3 + 3.0
N = int(DUR * FPS)
while len(taus) < N:
    taus.append(taus[-1] + dt)
TAUS = np.array(taus)


def tt(tau):
    return int(np.searchsorted(TAUS, tau)) * dt


def age_of(tau):
    if tau < RACES[0][0]:
        return 1
    if tau < PARTY[0]:
        for st, age in reversed(RACES[:3]):
            if tau >= st:
                return age
    if tau < RACES[3][0]:
        return 20 + int(4 * clamp((tau - PARTY[0]) / (PARTY[1] - PARTY[0])))
    return 25


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    shards = Shards(7)
    trophies_t = 0
    ph = {"T": 0.0, "O": 0.4}
    prev = 0.0
    rng = np.random.default_rng(1)
    for fi in range(v.n):
        t = fi * dt
        tau = TAUS[fi]
        dtau = tau - prev
        prev = tau
        scene = "intro"
        ri = -1
        for k, (st, age) in enumerate(RACES):
            if st <= tau < st + RACE_LEN + (0.6 if k == 3 else 0):
                scene, ri = "race", k
        if PARTY[0] <= tau < PARTY[1]:
            scene = "party"
        if tau >= RACES[3][0] + RACE_LEN:
            scene, ri = "race", 3
        age = age_of(tau)
        g_o = 0.0 if tau < PARTY[0] else 0.75 * smoothstep(PARTY[0], PARTY[1], tau)
        # events
        for k, (st, _) in enumerate(RACES):
            if tau >= st:
                log.once(f"go{k}", t, "go", k)
        if tau >= PARTY[0]:
            log.once("party", t, "party")
        for k, ft in enumerate(FALLS):
            if tau >= ft:
                log.once(f"fall{k}", t, "trophyfall", k)
                if f"sh{k}" not in log.seen:
                    log.seen.add(f"sh{k}")
                    shards.burst(-2.3 + 0.75 * k - 0.15, -2.3 + 0.75 * k + 0.15, 0.05, 0.3, 18, vx=(-2, 2), vy=(1, 3.5), size=(0.05, 0.12))
        shards.step(dtau)
        if not v.wants(fi):
            continue
        v.clear()
        e, f_, tc, hc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas
        cam = lane_cam(S, GROUND)
        flash = 0.0
        if scene == "intro":
            cam.wx = 0.0
            e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))
            u = tau / INTRO[1]
            ph["T"] += 2 * math.pi * 1.4 * dtau
            jt = scale_pose(run_pose(-1.2 + 1.2 * u, ph["T"], 0.3), -1.2 + 1.2 * u, 0.45)
            draw_body(hc, jt, cam, WHITE, 1.0)
            fall = smoothstep(1.2, 1.5, tau)
            jo0 = scale_pose(stand(1.4, 0.1, 0.3, 0.2, 0.2, 0.2, 0.0), 1.4, 0.45)
            jo1 = scale_pose(sit(1.4, 0.05, t, 0.3), 1.4, 0.45)
            draw_body(hc, blend(jo0, jo1, fall), cam, WHITE, 0.85)
            for i in range(8):            # clapping crowd heads
                x = -3.6 + i * 1.0
                sx, sy = cam.pt((x, -1.0))
                bob = 4 * abs(math.sin(t * 9 + i))
                e.drawCircle(sx, sy - bob, 0.27 * S, paint(GREY, 0.45))
            label(tc, cam, -1.2 + 1.2 * u, "TALENT", smoothstep(2.4, 2.7, tau), WHITE, 40, 24)
            label(tc, cam, 1.6, "OBSESSION", smoothstep(2.4, 2.7, tau), WHITE, 40, 24)
            log.once("baby", t, "baby")
            log.once("bump", tt(1.3), "bump")
        elif scene == "race":
            st, rage = RACES[ri]
            u = tau - st
            xt = min(FIN + 2.5, integ(t_speed, ri, u))
            xo = min(FIN + (1.2 if ri == 3 else 2.5), integ(o_speed, ri, u))
            vt, vo = t_speed(ri, u), o_speed(ri, u)
            if xt >= FIN + 2.4:
                vt = 0
            if xo >= FIN + (1.1 if ri == 3 else 2.4):
                vo = 0
            ph["T"] += vt / STRIDE * 2 * math.pi * dtau
            ph["O"] += vo / STRIDE * 2 * math.pi * dtau
            lead = max(xt, xo)
            cam.wx = min(lead, FIN + 0.5) - 1.6
            if ri == 3:
                cam.wx = min(xo, FIN + 0.5) - 1.0
            # ground ticks + finish line
            e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))
            k0 = math.floor((cam.wx - 6) / 1.5)
            for k in range(k0, k0 + 10):
                sx, _ = cam.pt((k * 1.5, 0))
                if 80 < sx < W - 80:
                    e.drawLine(sx, GROUND + 10, sx - 20, GROUND + 26, paint(WHITE, 0.16, 2))
            fx, _ = cam.pt((FIN, 0))
            winner_x = xt if ri < 3 else xo
            broke = winner_x >= FIN - 0.3
            e.drawLine(*cam.pt((FIN + 0.35, 0)), *cam.pt((FIN + 0.35, 2.9)), paint(WHITE, 0.6, 4))
            e.drawLine(*cam.pt((FIN + 0.35, 2.9)), *cam.pt((FIN - 0.6, 2.9)), paint(WHITE, 0.6, 4))
            if not broke:
                # red finish tape (seen from the side: a fluttering ribbon)
                p_ = skia.Path()
                p_.moveTo(*cam.pt((FIN, 1.75)))
                for k in range(1, 9):
                    p_.lineTo(*cam.pt((FIN + 0.35 * k / 8, 1.75 + 0.06 * math.sin(t * 12 + k))))
                f_.drawPath(p_, paint(RED, 1.0, 6))
                f_.drawLine(*cam.pt((FIN, 0)), *cam.pt((FIN, 2.6)), paint(RED, 0.35, 3))
            else:
                if f"tapes{ri}" not in log.seen:
                    log.seen.add(f"tapes{ri}")
                    shards.burst(FIN - 0.1, FIN + 0.3, 1.5, 2.0, 26 if ri == 3 else 12, vx=(1, 5), vy=(0.5, 3.5), size=(0.06, 0.14))
                log.once(f"tape{ri}", t, "tape", ri)
            shards.draw(f_, cam, RED)
            # talent: back row
            bc = lane_cam(S * 0.86, GROUND - 60, cam.wx)
            e.drawLine(80, bc.sy, W - 80, bc.sy, paint(WHITE, 0.15, 1.5))
            if ri == 2 and 0.9 <= u <= 1.5:
                jt = blend(run_pose(xt, ph["T"], 0.5), phone_pose(xt, t), 0.6)
            elif ri == 3 and u > 1.0:
                tired = stand(xt, 0.95, 0.35, 0.3, 0.3, 0.35, 0.3, -0.25)
                jt = blend(run_pose(xt, ph["T"], 0.6), tired, smoothstep(1.0, 1.6, u))
                if tau > st + RACE_LEN:
                    jt = blend(jt, clap(xt, t), smoothstep(st + RACE_LEN, st + RACE_LEN + 0.4, tau))
            elif xt >= FIN + 1.0 and ri < 3:
                jt = blend(run_pose(xt, ph["T"], 0.9), arms_up(xt, t), smoothstep(FIN + 1.0, FIN + 2.2, xt))
            else:
                jt = run_pose(xt, ph["T"], 0.9)
            tcol = mix(WHITE, RED, 0.6 if ri == 3 else 0.0)
            draw_body(e, jt, bc, tcol if ri == 3 else WHITE, 0.75 if ri < 3 else 0.45)
            if ri == 2 and 0.9 <= u <= 1.5:
                draw_phone_small(f_, bc, jt["hand1"] + [0.05, 0.1], 0.9)
            label(tc, bc, xt, "TALENT", 0.8 if ri < 3 else 0.5, WHITE if ri < 3 else GREY, 30, 22)
            # obsession: front
            if xo >= FIN + 0.4 and ri == 3:
                jo = blend(run_pose(xo, ph["O"], 1.0), arms_up(xo, t), smoothstep(FIN + 0.4, FIN + 1.15, xo))
            elif xo >= FIN + 1.0:
                jo = blend(run_pose(xo, ph["O"], 0.9), stand(xo, 0.3, 0.05, 0.0, 0.1, 0.1, 0.8), smoothstep(FIN + 1.0, FIN + 2.2, xo))
            else:
                jo = run_pose(xo, ph["O"], 0.95)
            jo = scale_pose(jo, xo, body_scale(g_o))
            draw_body(hc, jo, cam, WHITE, 1.0, g_o)
            label(tc, cam, xo, "OBSESSION", 1.0, WHITE, 46, 26)
            # trophy pop for the winner
            if broke:
                bt = (winner_x - FIN + 0.3) / 6
                wx = xt if ri < 3 else xo
                camw = bc if ri < 3 else cam
                hx, hy = camw.pt(((jt if ri < 3 else jo)["head"][0], (jt if ri < 3 else jo)["head"][1] + 0.9))
                pop = 1 + 0.5 * math.exp(-bt * 30)
                draw_trophy(f_, hx, hy, 52 * pop * (1.6 if ri == 3 else 1), clamp(bt * 20), RED if ri == 3 else WHITE)
                flash = 0.4 * math.exp(-bt * 25) if ri == 3 else 0.0
            if ri == 3:
                age_k = tau - (st + RACE_LEN)
            # crowd heads
            for i in range(8):
                x = -3.6 + i * 1.0
                sx, sy = lane_cam(S, GROUND).pt((x, -1.0))
                bob = 4 * abs(math.sin(t * 9 + i)) if broke else 0
                e.drawCircle(sx, sy - bob, 0.27 * S, paint(GREY, 0.45))
        else:  # party
            u = (tau - PARTY[0]) / (PARTY[1] - PARTY[0])
            cam.wx = 0.0
            e.drawLine(80, GROUND, W - 80, GROUND, paint(WHITE, 0.5, 2.5))
            e.drawLine(80, CX + 0, 80, CX + 0, paint(WHITE, 0, 1))
            # strobe on Talent's side
            if int(t * 8) % 2 == 0:
                e.drawRect(skia.Rect(80, 600, CX - 20, GROUND), paint(RED, 0.10))
            e.drawLine(CX, 640, CX, GROUND, paint(WHITE, 0.15, 2))
            # shelf + trophies
            shelf_y = 3.3
            e.drawLine(*cam.pt((-3.1, shelf_y)), *cam.pt((-0.6, shelf_y)), paint(WHITE, 0.6, 4))
            for k in range(3):
                tx = -2.3 + 0.75 * k
                if tau < FALLS[k]:
                    sx, sy = cam.pt((tx, shelf_y))
                    draw_trophy(f_, sx, sy, 40, 0.9, WHITE)
                elif tau < FALLS[k] + 0.35:
                    y = shelf_y - shelf_y * ((tau - FALLS[k]) / 0.35) ** 2
                    sx, sy = cam.pt((tx, y))
                    draw_trophy(f_, sx, sy, 40, 0.9, RED)
            shards.draw(f_, cam, RED)
            dance = stand(-1.9, -0.1 + 0.15 * math.sin(t * 9), 2.6 + 0.4 * math.sin(t * 9), 0.9, 0.3, 1.4, -0.3, 0.05 * abs(math.sin(t * 9)))
            draw_body(hc, dance, cam, mix(WHITE, RED, 0.4), 0.9)
            draw_phone_small(f_, cam, dance["hand2"] + [0.05, 0.1], 0.9)
            label(tc, cam, -1.9, "TALENT", 1.0, WHITE, 46, 26)
            ph["O"] += 8.0 / STRIDE * 2 * math.pi * dtau
            jo = scale_pose(run_pose(1.9, ph["O"], 1.0), 1.9, body_scale(g_o))
            for k in range(6):
                y = 0.5 + k * 0.45
                sx, sy = cam.pt((1.2, y))
                L = 60 + 40 * math.sin(t * 7 + k)
                e.drawLine(sx - L, sy, sx, sy, paint(WHITE, 0.2, 2))
            draw_body(hc, jo, cam, WHITE, 1.0, g_o)
            label(tc, cam, 1.9, "OBSESSION", 1.0, WHITE, 46, 26)
            if rng.random() < 0.4:
                log.once(f"stomp{int(t * 4)}", t, "stomp")

        hud(tc, "AGE", age, smoothstep(2.6, 3.0, tau) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t)), age >= 25)
        title(tc, t, [([("TALENT", WHITE)], 140, 80), ([("VS", WHITE)], 48, 130), ([("OBSESSION", RED)], 130, 0)], y0=600)
        if t >= P1 - 0.3:
            tc.drawRect(skia.Rect(0, 520, W, 900), paint((0, 0, 0), 0.75 * smoothstep(P1 - 0.3, P1, t)))
        punch(tc, t, [(P1, [("TALENT", WHITE), (" WAS BORN.", WHITE)], 620, 60),
                      (P2, [("OBSESSION", RED), (" WAS", WHITE)], 720, 70),
                      (P3, [("BUILT.", WHITE)], 870, 150)])
        cut = 0.0
        for c_t in [RACES[k][0] for k in range(4)] + [PARTY[0]]:
            ct = tt(c_t)
            if ct - 0.08 <= t < ct + 0.2:
                cut = max(cut, 1 - abs(t - ct) / 0.2)
        tdim = 0.6 * smoothstep(0.1, 0.35, t) * (1 - smoothstep(2.4, 2.8, t))
        pdim = 0.6 * smoothstep(P1 - 0.3, P1, t)
        v.compose(fi, t, flash=flash, white=cut * 0.22, dim=max(tdim, pdim))
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=tt(RACES[3][0] + FIN / 8.6)), gain=0.42, fade_in=0.6, fade_out=2.5, stop=DUR)
    m.add(0.1, sfx.text_hit(5), 0.8, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "baby":
            m.add(t + 0.2, sfx.applause(2.4, 35, 2), 0.5, 0, 0.3)
        elif kind == "bump":
            m.add(t, sfx.step_light(5), 0.6, 0.3, 0.2)
        elif kind == "go":
            m.add(t - 0.15, sfx.whoosh(0.35, 400, 8000, 0.6, seed=extra), 0.5, 0, 0.2)
            m.add(t, sfx.beep(1320, 0.3), 0.5, 0, 0.3)
            for k in range(12 if extra < 3 else 14):
                m.add(t + 0.1 + k * 0.2, sfx.step_light(k + extra * 20), 0.2, -0.2, 0.1)
                m.add(t + 0.18 + k * 0.21, sfx.step_heavy(k + extra * 30), 0.22, 0.2, 0.15)
        elif kind == "tape":
            if extra < 3:
                m.add(t, sfx.text_hit(extra), 0.6, 0, 0.4)
                m.add(t + 0.05, sfx.applause(1.6, 40, extra), 0.45, 0, 0.3)
                m.add(t, sfx.chime(660, 0.3), 0.5, 0, 0.4)
            else:
                m.add(t, sfx.boom(4.0), 1.0, 0, 0.5)
                m.add(t, sfx.sparkle(2.0), 0.6, 0, 0.6)
                m.add(t + 0.3, sfx.applause(4.0, 55, 8), 0.6, 0, 0.35)
        elif kind == "party":
            for k in range(22):
                m.add(t + k * 0.125, sfx.step_heavy(k) * 0.8, 0.5 if k % 2 == 0 else 0.25, -0.3, 0.1)
        elif kind == "trophyfall":
            m.add(t + 0.32, sfx.shatter(extra, 0.6), 0.7, -0.3, 0.3)
            m.add(t + 0.32, sfx.plate_clank(extra, 0.4), 0.4, -0.3, 0.3)
        elif kind == "stomp":
            m.add(t, sfx.step_heavy(int(t * 7)), 0.25, 0.3, 0.1)
    m.add(tt(RACES[3][0] + FIN / 8.6) - 2.2, sfx.riser(2.2), 0.5, 0, 0.3)
    m.add(tt(RACES[3][0] + FIN / 8.6) - 0.6, sfx.heartbeat(), 0.8, 0, 0.3)
    m.add(P1, sfx.text_hit(1), 0.5, 0, 0.4)
    m.add(P2, sfx.text_hit(2), 0.6, 0, 0.4)
    m.add(P3, sfx.text_hit(3), 0.95, 0, 0.5)
    m.add(P3, sfx.boom(2.0), 0.45, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [1.6, 4.0, 5.6, 7.9, 10.6, 11.9, 13.5, 14.6, tt(17.0), tt(RACES[3][0] + FIN / 8.6) + 0.2, P3 + 1.0]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
