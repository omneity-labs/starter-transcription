# Daktilo transcription + Sawalign alignment

Editable source in **[python/src](python/src)** and **[typescript/src](typescript/src)**. Pick either language. No generated bundle is needed.

## Setup

Create an API key at https://api.sawalni.com. Enable the models used below and add credits. Requests consume credits.

```sh
cp .env.example .env
# Edit .env and set SAWALNI_API_KEY.
```

### Python 3.11+

```sh
cd python
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
set -a; . ../.env; set +a
python src/main.py subtitles recording.wav
```

### TypeScript / Node.js 24+

```sh
cd typescript
npm ci
npm run check
npm start -- subtitles recording.wav
```

## Extend it

Edit `src/main` for the entry point and `src/client` for API transport. The key stays in the backend process. Requests have a 120-second timeout. HTTP errors stop the flow. These are local developer starters. Add authentication, rate limits, persistence and deployment settings before exposing a service publicly.

API reference: https://api.sawalni.com/docs

## Workflows

- **Transcribe**: meeting notes, interviews and searchable recordings. Runs Daktilo and prints text.
- **Align**: timing for an existing reviewed transcript, dubbing scripts or read-along content. Runs Sawalign with `--text transcript.txt` (Python), or `align audio.wav transcript.txt` (TypeScript).
- **Subtitles**: runs Daktilo, then submits its transcript to Sawalign and saves SRT. Review recognition errors before publishing. Use `align` with corrected text for final timing.

Alignment is asynchronous. The source polls pending/processing states, checks failures, and downloads SRT only when done. Polling stops after ten minutes and reports the job ID. Preserve that ID to resume later. Set Python `--output captions.srt`; the TypeScript align command accepts output as the fourth argument. The starter uses the API's 128 MB audio and 1 MB transcript limits; validate uploads in your application before sending them.

Run `python tests/smoke.py` from the repository root with Python dependencies installed and Node.js 24 on PATH. It checks both languages against a local HTTP fixture. It does not call the paid API.

## Translate transcripts and subtitles with Tarjamli

Translate a recording into English after transcription:

```sh
# Python (from python/)
python src/main.py translate recording.wav --source ary_Arab --target eng_Latn
# TypeScript (from typescript/)
npm start -- translate recording.wav --source ary_Arab --target eng_Latn
```

Both commands save `translated.txt`. Use `--translation-output path.txt` to choose the file.

Generate source-language and translated subtitles:

```sh
# Python
python src/main.py subtitles recording.wav --source ary_Arab --target eng_Latn
# TypeScript
npm start -- subtitles recording.wav --source ary_Arab --target eng_Latn
```

Both save `output.srt` and `translated.srt`. Translation keeps each source cue number and timestamp. Sawalign aligns the original transcript to the source audio; the translated text is not aligned as if it were spoken in that audio. Review the translation, line breaks and reading speed before publishing. Cue-by-cue translation can lose context across cues. For best results, correct the source transcript and use `align` with `--target`.

Set `--source` to the actual spoken language. It defaults to `ary_Arab` (Moroccan Arabic). Target examples: `eng_Latn` English, `fra_Latn` French, `shi_Latn` Tachelhit (Latin), `zgh_Tfng` Standard Moroccan Amazigh (Tifinagh). Tarjamli needs model access and uses credits in addition to transcription and alignment.
