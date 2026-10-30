# Verification

Run these commands with Node.js 24 and Python 3.11 or newer:

```sh
pip install -r python/requirements.txt
python -m compileall -q python/src
(cd typescript && npm ci && npm run check && npm test)
python tests/smoke.py
```

The smoke test uses a local API fixture. It does not use your API key or spend credits.
