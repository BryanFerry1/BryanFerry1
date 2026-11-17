"""EP21 - EGO VS TALENT VS OBSESSION  (what are you building?)

Three columns (split screen), moving from the first frame. 10 years.
EGO        builds a thin, tall tower very fast, plants a red flag, poses on top
           while the crowd below films him (flashes, hearts).
TALENT     builds a beautiful wide tower quickly... then falls asleep on it.
OBSESSION  for 5 years builds UNDERGROUND: foundations nobody sees
           ("NOTHING TO SHOW."). Then he builds up, block by block.
YEAR 10    THE STORM. Ego's tower sways and collapses. Talent's top half falls.
           Obsession's tower stands. Lightning.
END        THEY BUILT TO BE SEEN. / HE BUILT TO LAST. / WHAT ARE YOU BUILDING?
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from engine import FPS, H, RED, WHITE, W, Camera, clamp, draw_spaced, ease_out, font, mix, paint, rotate_pose, smoothstep
from kit import (CX, GREY, Log, Video, arms_up, blend, caption, crossed, draw_body, draw_heart, flex, kneel,
                 sit, stand)
import sfx
import skia

OUT = os.path.join(os.path.dirname(__file__), "out")
NAME = "ep21_what_are_you_building"
dt = 1 / FPS
GROUND = 1290.0
BH = 34.0                                  # block height (px)
COLS = {"EGO": 213.0, "TALENT": 480.0, "OBSESSION": 747.0}
FS = 62.0                                  # figure scale
Y_START, Y_END = 0.6, 10.6                 # timeline of years 1 -> 10
STORM = 11.0
EGO_FALL = 11.9
TAL_FALL = 12.5
P1, P2, P3 = 14.3, 15.1, 16.2
DUR = 19.2


def year(t):
    return 1 + int(9 * clamp((t - Y_START) / (Y_END - Y_START)))


def build_plan():
    """(column, row, width, appear_time). Row 0 = first row above ground; negative = underground."""
    blocks = []
    for r in range(18):                                    # EGO: fast, thin, tall
        blocks.append(("EGO", r, 58.0 - 0.6 * r, 0.25 + 0.30 * r))
    for r in range(9):                                     # TALENT: fast, wide, then stops
        blocks.append(("TALENT", r, 170.0 - 4 * r, 0.2 + 0.32 * r))
    for r in range(6):                                     # OBSESSION: foundations underground
        blocks.append(("OBSESSION", -6 + r, 210.0, 0.5 + 0.85 * r))
    for r in range(14):                                    # then up, steadily
        blocks.append(("OBSESSION", r, 190.0 - 5 * r, 5.8 + 0.34 * r))
    return blocks


BLOCKS = build_plan()


def top_row(col, t):
    rows = [r for c, r, w, ta in BLOCKS if c == col and ta <= t]
    return max(rows) if rows else (-7 if col == "OBSESSION" else -1)


def row_y(r):
    """screen y of the TOP of row r."""
    return GROUND - (r + 1) * BH


def figure_cam(col, base_y):
    c = Camera()
    c.s, c.sx, c.sy, c.wx, c.wy = FS, COLS[col], base_y, 0.0, 0.0
    return c


def draw_block(c, x, y_top, w, alpha, col=WHITE, fill=0.0, windows=False):
    r = skia.Rect(x - w / 2, y_top, x + w / 2, y_top + BH - 3)
    c.drawRect(r, paint((0, 0, 0), alpha))
    if fill > 0:
        c.drawRect(r, paint(col, fill * alpha))
    c.drawRect(r, paint(col, alpha, 3, cap=False))
    if windows:
        for k in range(3):
            wx = x - w / 2 + w * (0.22 + 0.28 * k)
            c.drawRect(skia.Rect(wx - 7, y_top + 9, wx + 7, y_top + BH - 12), paint(col, 0.6 * alpha))


def render(stills=None):
    v = Video(OUT, NAME, DUR, stills)
    log = Log()
    rng = np.random.default_rng(4)
    debris = {}            # block index -> [x, y, vx, vy, ang, av]
    flashes = []
    for fi in range(v.n):
        t = fi * dt
        # ---------- events
        for i, (c, r, w, ta) in enumerate(BLOCKS):
            if t >= ta:
                log.once(f"b{i}", ta, "block", (c, r))
        for key, tt, kind in (("flag", 18 * 0.30 + 0.3, "flag"), ("sleep", 3.4, "sleep"), ("storm", STORM, "storm"),
                              ("light1", STORM + 0.25, "thunder"), ("egofall", EGO_FALL, "collapse"),
                              ("talfall", TAL_FALL, "crack"), ("light2", 13.3, "thunder"), ("p1", P1, "p1"),
                              ("p2", P2, "p2"), ("p3", P3, "p3"), ("go", 0.0, "go")):
            if t >= tt:
                log.once(key, tt, kind)
        if 6.0 <= t < STORM and rng.random() < 0.18:
            flashes.append((t, rng.integers(5)))
            log.add(t, "shutter", len(flashes))
        # debris init
        if t >= EGO_FALL and "dbE" not in log.seen:
            log.seen.add("dbE")
            for i, (c, r, w, ta) in enumerate(BLOCKS):
                if c == "EGO":
                    debris[i] = [COLS["EGO"] + r * 3.0, row_y(r), rng.uniform(-160, 160), rng.uniform(-250, -60) * (r / 18),
                                 0.0, rng.uniform(-4, 4)]
        if t >= TAL_FALL and "dbT" not in log.seen:
            log.seen.add("dbT")
            for i, (c, r, w, ta) in enumerate(BLOCKS):
                if c == "TALENT" and r >= 4:
                    debris[i] = [COLS["TALENT"], row_y(r), rng.uniform(-60, 140), rng.uniform(-120, 0), 0.0, rng.uniform(-3, 3)]
        for d in debris.values():
            d[3] += 1400 * dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[4] += d[5] * dt
            if d[1] > GROUND - BH:
                d[1], d[3], d[2], d[5] = GROUND - BH + rng.uniform(-3, 0), -d[3] * 0.15, d[2] * 0.5, d[5] * 0.4
        if not v.wants(fi):
            continue

        v.clear()
        e, f_, tc, hc, oc = v.env.canvas, v.fig.canvas, v.txt.canvas, v.hero.canvas, v.over.canvas
        storm = smoothstep(STORM, STORM + 0.4, t)
        shake = storm * (1 - smoothstep(13.6, 14.2, t)) * 6 * math.sin(t * 70)
        e.save()
        hc.save()
        f_.save()
        for c_ in (e, hc, f_):
            c_.translate(shake, 0)
        # soil + ground
        soil = skia.Paint(AntiAlias=True)
        soil.setShader(skia.GradientShader.MakeLinear([skia.Point(0, GROUND), skia.Point(0, H)],
                                                      [skia.Color4f(0.07, 0.07, 0.08, 1), skia.Color4f(0.02, 0.02, 0.02, 1)]))
        e.drawRect(skia.Rect(60, GROUND, W - 60, H), soil)
        e.drawLine(60, GROUND, W - 60, GROUND, paint(WHITE, 0.6, 3))
        for xx in (346.0, 613.0):
            e.drawLine(xx, 560, xx, GROUND - 6, paint(WHITE, 0.08, 2))
        # Obsession's pit
        pit_rows = 6
        pl, pr = COLS["OBSESSION"] - 120, COLS["OBSESSION"] + 120
        dug = smoothstep(0.0, 0.4, t)
        e.drawRect(skia.Rect(pl, GROUND, pr, GROUND + pit_rows * BH * dug + 4), paint((0, 0, 0), 1.0))
        # blocks
        sway = 0.0
        if t >= STORM:
            sway = 0.035 * smoothstep(STORM, EGO_FALL, t) * math.sin(t * 9)
        for i, (c, r, w, ta) in enumerate(BLOCKS):
            if t < ta:
                continue
            drop = 1 - ease_out(min(1, (t - ta) / 0.18))
            x = COLS[c]
            y = row_y(r) - 60 * drop
            col = RED if c == "EGO" else WHITE
            if i in debris:
                dx, dy, _, _, ang, _ = debris[i]
                hc.save()
                hc.translate(dx, dy + BH / 2)
                hc.rotate(math.degrees(ang))
                draw_block(hc, 0, -BH / 2, w, 0.9, col)
                hc.restore()
                continue
            if c == "EGO" and t >= STORM:
                hc.save()
                hc.translate(COLS["EGO"], GROUND)
                hc.rotate(math.degrees(sway) * (r / 18) * 3)
                draw_block(hc, 0, row_y(r) - GROUND, w, 1.0, col)
                hc.restore()
                continue
            under = r < 0
            draw_block(hc, x, y, w, 1.0 if not under else 0.85, col, 0.08 if c == "OBSESSION" else 0.0,
                       windows=(c == "TALENT"))
        # Talent crack line
        if TAL_FALL - 0.4 <= t < TAL_FALL + 0.3:
            cx_, cy_ = COLS["TALENT"], row_y(4) + BH
            p = skia.Path()
            p.moveTo(cx_ - 85, cy_)
            for k in range(1, 7):
                p.lineTo(cx_ - 85 + 28 * k, cy_ + (-8 if k % 2 else 8))
            f_.drawPath(p, paint(RED, 1.0, 4))
        # Ego's flag
        flag_t = 18 * 0.30 + 0.3
        if flag_t <= t < EGO_FALL:
            ty = row_y(top_row("EGO", t))
            fx = COLS["EGO"] + math.sin(sway) * (GROUND - ty) * 1.0
            hc.drawLine(fx + 18, ty, fx + 18, ty - 110, paint(WHITE, 0.9, 4))
            p = skia.Path()
            p.moveTo(fx + 18, ty - 110)
            p.lineTo(fx + 78 + 6 * math.sin(t * 6), ty - 95)
            p.lineTo(fx + 18, ty - 78)
            p.close()
            hc.drawPath(p, paint(RED, 1.0))
        # ---------- figures
        for col in ("EGO", "TALENT", "OBSESSION"):
            tr = top_row(col, t)
            if tr >= 0:
                base = row_y(tr)
            elif col == "OBSESSION":
                base = row_y(tr) if tr >= -6 else GROUND + 6 * BH        # standing in his pit
            else:
                base = GROUND
            building = any(c == col and 0 <= t - ta < 0.5 for c, r, w, ta in BLOCKS)
            ph = t * 6 + len(col)
            carry = stand(0, 0.15, 1.2, 1.1, 0.6, 0.6, 0.2, 0.03 * math.sin(ph))
            fcol = RED if col == "EGO" else WHITE
            cam = figure_cam(col, base)
            alpha = 1.0
            if col == "EGO":
                if t < 6.0:
                    j = carry if building else stand(0)
                elif t < EGO_FALL:
                    j = flex(0, t)
                    cam.sx += math.sin(sway) * (GROUND - base)
                else:
                    u = (t - EGO_FALL) / 0.8
                    cam.sy = base + (GROUND - base) * min(1, u * u)
                    j = rotate_pose(flex(0, t), np.array([0.0, 0.8]), 2.5 * min(1, u))
                    if u >= 1:
                        j = kneel(0, t, 1.0)
                        cam.sy = GROUND
                    fcol = mix(RED, GREY, smoothstep(EGO_FALL, EGO_FALL + 1.5, t))
            elif col == "TALENT":
                if t < 3.4:
                    j = carry if building else stand(0)
                elif t < TAL_FALL:
                    j = sit(-0.3, 0.05, t, 0.9)
                    if t < STORM:
                        hx, hy = cam.pt(j["head"])
                        for zk in range(2):
                            draw_spaced(tc, "z", hx + 30 + 22 * zk, hy - 26 - 26 * zk - 6 * math.sin(t * 3 + zk),
                                        font(28 + 8 * zk, "InterDisplay-Bold"), 0, paint(WHITE, 0.85))
                    else:
                        j = stand(0, -0.1, 0.65, 0.6, 2.1, 2.15, 0.3)
                else:
                    u = (t - TAL_FALL) / 0.7
                    cam.sy = base + (row_y(3) - base) * min(1, u * u)
                    j = blend(stand(0, -0.1, 0.65, 0.6, 2.1, 2.15, 0.3), kneel(0, t, 1.0), min(1, u))
                    fcol = mix(WHITE, GREY, smoothstep(TAL_FALL, TAL_FALL + 1.5, t))
                    if u >= 1:
                        cam.sy = row_y(3)
            else:
                if t < STORM:
                    j = carry if building else stand(0, 0.1, 0.3, 0.2, 0.6, 0.6, 0.1)
                    if tr < 0 and not building:
                        j = carry
                else:
                    j = blend(stand(0), crossed(0), smoothstep(STORM, STORM + 0.5, t))
            draw_body(hc, j, cam, fcol, alpha, 0.3 if col == "OBSESSION" and t > 8 else 0.0)
            # carried block
            if building and t < 10.6:
                hx, hy = cam.pt((j["hand1"] + j["hand2"]) / 2)
                hc.drawRect(skia.Rect(hx - 20, hy - 26, hx + 20, hy - 2), paint(fcol, 0.9, 3, cap=False))
        # crowd under Ego (filming)
        for k in range(5):
            cx_ = 110 + 48 * k
            hy = GROUND + 120
            a = smoothstep(5.6, 6.2, t) * (1 - smoothstep(EGO_FALL + 0.3, EGO_FALL + 1.0, t))
            e.drawCircle(cx_, hy, 15, paint(GREY, 0.6 * a))
            hc.drawRoundRect(skia.Rect(cx_ - 8, hy - 52, cx_ + 8, hy - 26), 3, 3, paint(WHITE, 0.9 * a, 2))
            for ft, kk in flashes:
                if kk == k and 0 <= t - ft < 0.2:
                    f_.drawCircle(cx_, hy - 45, 24 * (1 - (t - ft) / 0.2) + 6, paint(WHITE, 0.9 * a))
        if 6.2 <= t < EGO_FALL:
            for k in range(4):
                age = (t - 6.2 - 0.5 * k) % 2.0
                hx = 120 + 50 * k + 10 * math.sin(t + k)
                draw_heart(f_, hx, GROUND - 20 - age * 120, 12, 0.9 * (1 - age / 2.0))
        # debris dust
        e.restore()
        hc.restore()
        f_.restore()
        # storm: rain + lightning
        if storm > 0.01 and t < 14.3:
            r2 = np.random.default_rng(fi)
            for k in range(70):
                x = r2.uniform(60, W - 60)
                y = r2.uniform(330, GROUND)
                f_.drawLine(x, y, x - 14, y + 46, paint(WHITE, 0.18 * storm, 2))
        light = 0.0
        for lt in (STORM + 0.25, 13.3):
            if lt <= t < lt + 0.25:
                light = max(light, 1 - (t - lt) / 0.25)
                bx = 640 if lt > 13 else 200
                p = skia.Path()
                p.moveTo(bx, 330)
                for k, (dx_, dy_) in enumerate(((30, 120), (-40, 230), (25, 360), (-20, 470))):
                    p.lineTo(bx + dx_, 330 + dy_)
                f_.drawPath(p, paint(WHITE, light, 5))
        # labels
        for col in ("EGO", "TALENT", "OBSESSION"):
            draw_spaced(tc, col, COLS[col], GROUND + 6 * BH + 40,
                        font(22, "Inter-Bold"), 3, paint(RED if col == "EGO" else WHITE, 1.0))
        if 1.5 <= t < 5.6:
            a = smoothstep(1.5, 1.8, t) * (1 - smoothstep(5.3, 5.6, t))
            draw_spaced(oc, "NOTHING TO SHOW.", COLS["OBSESSION"], GROUND - 230, font(22, "Inter-Bold"), 1, paint(WHITE, 0.8 * a))
        # HUD / title
        if t < 2.4:
            caption(oc, "EGO VS TALENT VS OBSESSION", 405, 1 - smoothstep(2.0, 2.4, t), WHITE, 44)
        else:
            ya = smoothstep(2.4, 2.7, t) * (1 - 0.6 * smoothstep(P1 - 0.3, P1 + 0.3, t))
            yv = year(t)
            draw_spaced(oc, "YEAR", CX, 360, font(24, "Inter-SemiBold"), 12, paint(WHITE, 0.7 * ya))
            draw_spaced(oc, str(yv), CX, 470, font(104, "InterDisplay-Bold"), 4, paint(RED if yv >= 10 else WHITE, ya))
        if STORM <= t < STORM + 1.6:
            caption(oc, "THE STORM.", 560, smoothstep(STORM, STORM + 0.2, t) * (1 - smoothstep(STORM + 1.3, STORM + 1.6, t)), RED, 56)
        if t >= P1:
            a = smoothstep(P1 - 0.2, P1 + 0.2, t)
            oc.drawRect(skia.Rect(0, 520, W, 900), paint((0, 0, 0), 0.82 * a))
            caption(oc, "THEY BUILT TO BE SEEN.", 620, smoothstep(P1, P1 + 0.3, t), WHITE, 54, band=False)
        if t >= P2:
            caption(oc, "HE BUILT TO LAST.", 720, smoothstep(P2, P2 + 0.3, t), RED, 64, band=False)
        if t >= P3:
            caption(oc, "WHAT ARE YOU BUILDING?", 830, smoothstep(P3, P3 + 0.3, t), WHITE, 40, band=False)
        v.compose(fi, t, dim=0.35 * storm * (1 - smoothstep(13.8, 14.3, t)), white=0.22 * light, fade_in=0.0)
    v.finish(build_audio, log.events)


def build_audio(events, path):
    m = sfx.Mixer(DUR)
    m.add_bed(sfx.drone(DUR, rise_at=STORM), gain=0.4, fade_in=0.3, fade_out=2.0, stop=DUR)
    m.add(0.02, sfx.text_hit(5), 0.6, 0, 0.4)
    for t, kind, _, extra in events:
        if kind == "block":
            c, r = extra
            pan = {"EGO": -0.6, "TALENT": 0.0, "OBSESSION": 0.6}[c]
            if c == "OBSESSION" and r < 0:
                m.add(t - 0.1, sfx.dig(int(t * 50), 0.8), 0.5, pan, 0.2)
            m.add(t + 0.15, sfx.plate_clank(int(t * 30) + r, 0.4) * 0.5, 0.3, pan, 0.2)
        elif kind == "flag":
            m.add(t, sfx.sparkle(1.0, 60, 2), 0.5, -0.6, 0.5)
            m.add(t, sfx.applause(2.0, 30, 3), 0.35, -0.6, 0.3)
        elif kind == "shutter":
            m.add(t, sfx.shutter(extra), 0.3, -0.6, 0.2)
        elif kind == "sleep":
            m.add(t, sfx.chime(440, 0.25), 0.4, 0.0, 0.6)
        elif kind == "storm":
            m.add(t, sfx.rain(4.0), 0.5, 0, 0.1)
            m.add(t, sfx.whoosh(1.0, 100, 3000, 0.6, seed=4), 0.6, 0, 0.3)
        elif kind == "thunder":
            m.add(t, sfx.thunder(int(t)), 0.9, 0, 0.3)
        elif kind == "collapse":
            m.add(t, sfx.shatter(3, 2.0), 0.9, -0.6, 0.4)
            for k in range(6):
                m.add(t + 0.25 + 0.09 * k, sfx.plate_clank(k, 0.8), 0.45, -0.6, 0.3)
            m.add(t + 0.6, sfx.body_fall(), 0.8, -0.6, 0.3)
            m.add(t, sfx.power_down(1.6), 0.4, -0.6, 0.4)
        elif kind == "crack":
            m.add(t - 0.4, sfx.heart_break(), 0.6, 0.0, 0.4)
            m.add(t, sfx.shatter(5, 1.2), 0.8, 0.0, 0.4)
            m.add(t + 0.5, sfx.body_fall() * 0.7, 0.6, 0.0, 0.3)
        elif kind in ("p1", "p2", "p3"):
            m.add(t, sfx.text_hit({"p1": 1, "p2": 3, "p3": 2}[kind]), 0.6 if kind != "p2" else 0.95, 0, 0.4)
            if kind == "p2":
                m.add(t, sfx.boom(2.5), 0.5, 0, 0.4)
    m.render(path)


if __name__ == "__main__":
    print(f"duration {DUR:.2f}")
    if "--stills" in sys.argv:
        ts = [0.1, 1.2, 2.8, 4.5, 6.5, 8.5, 10.4, 11.3, 12.2, 12.9, 13.6, 16.8]
        render(stills=sorted(set(int(x * FPS) for x in ts)))
    else:
        render()
