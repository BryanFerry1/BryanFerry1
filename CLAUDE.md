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
