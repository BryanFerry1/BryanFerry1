# TikTok concept shorts — notes for Claude

Series of 15–30 s vertical videos (1080×1920, 30 fps) about mindset concepts
(ego, discipline, obsession, consistency…). Each concept is a little glowing
stick figure with a label. Code and episodes live in `tiktok-concepts/`; see
`tiktok-concepts/README.md` for the episode list, descriptions and polls.

## Art direction
- Pure black background, white glowing pictogram figures, **red** is the only
  accent (ego, failure, pain, finish line, REC dots, counters at the climax).
- English on screen, no voice. Sound design only (synthesised in `lib/sfx.py`);
  the user adds a trending TikTok sound himself.

## Series rules (from the user)
- No sentence hook. The hook is **visual** (something in the animation).
  The only text at the start is the concept name(s), big and centred:
  `OBSESSION` or `EGO VS OBSESSION`.
- Opposition format (two concepts) is the default.
- A punchline only at the end / resolution.
- For every episode also deliver: a TikTok description (one punchy line +
  5 hashtags, 2–3 options with a recommendation) and a comment poll
  (question + 2–4 short options). Add both to the README tables.
- The user speaks French; answer in French. Video text stays in English.

## TikTok safe zone (1080×1920) — mandatory from EP06 on
The TikTok UI covers parts of the frame (seen on EP05: the DAY counter sat
under the "Suivis / Pour toi" tabs, and the doubters were hidden behind the
like/comment/share column).
- **Top:** nothing important above **y ≈ 320**. HUD counters (DAY, KG, RANK…):
  small caption around y ≈ 360, big number baseline around y ≈ 470.
- **Right:** keep characters, labels and text **left of x ≈ 880** (the icon
  column takes the right ~200 px). Centre the scene slightly left instead of
  using the full width.
- **Left:** keep a ~80 px margin.
- **Bottom:** nothing important below **y ≈ 1560** (username + description).
- Check the `--stills` contact sheet against these limits before the full render.

## Workflow (keep it cheap)
- Build new episodes from the shared engine (`lib/engine.py`: figures, poses,
  run cycle, camera, bloom, text; `lib/sfx.py`: all sounds). Reuse patterns
  from the existing `epXX_*.py` scripts instead of rewriting from scratch.
- One `--stills` contact sheet to check layout, fix, then one full render.
  Avoid many preview rounds.
- `python tiktok-concepts/epXX_name.py --stills` then `python tiktok-concepts/epXX_name.py`
  → `tiktok-concepts/out/epXX_name.mp4`. Commit the script, README and mp4.

## Setup (if not already installed)
```bash
apt-get install -y libegl1
pip install skia-python opencv-python-headless numpy pillow
```
