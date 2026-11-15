# Verification

Run these commands with Node.js 24 and Python 3.11 or newer:

```sh
pip install -r python/requirements.txt
python -m compileall -q python/src
(cd typescript && npm ci && npm run check && npm test)
python tests/smoke.py
```

The smoke test uses a local API fixture. It does not use your API key or spend credits.

## Audio and video input — 15 November 2026

Real FFmpeg checks pass for WAV, MP3, MP4 and WebM in both CLI workflows against a local HTTP fixture. No paid API request was used. Separate checks cover mono 16 kHz PCM output, filenames with spaces, preservation of initial video audio delay, rejection beyond 30 minutes, missing FFmpeg, invalid media, video without audio, and temporary-file cleanup. TypeScript tests and type checks pass.
