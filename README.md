# Sugilite Swing

Full-colour Python 3 neon grappling arcade for [ElbowOS](https://x.com/ElbowOS).

A violet miner hooks gold crystal anchors, swings down a sugilite shaft, and snags mint, gold, and magenta shards. Coral spikes sting the score. Not a clone of the volley, pinball, light-cycle, or tide-hopper packs.

## Play

```bash
pip install -r requirements.txt
python3 sugilite_swing.py --play
```

A / Left and D / Right pump the swing. Space releases the hook. R restarts.

## Record a 9:16 reel

```bash
python3 sugilite_swing.py --record
```

Headless autoplay writes a 15s 1080x1920 H.264 MP4 (`SDL_VIDEODRIVER=dummy`, libx264 yuv420p, CRF 20, +faststart).

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/1o_HR12m_UGeft5E6j2_pGL5pUQOm6aQR/view
