"""Inspect the saved demo without an API key or paid request."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent/'demo'
d=json.loads((p/'recorded-example.json').read_text())
print('TRANSCRIPT EXCERPT\n'+(p/'transcript.txt').read_text())
print('REVIEWED TEXT\n'+(p/'reviewed-transcript.txt').read_text())
print('SRT\n'+(p/'captions.srt').read_text())
