# Timed captions with Sawalign

[**Read the example guide →**](https://api.sawalni.com/examples/darija-captions) See the real audio excerpt, reviewed transcript, word timings, and downloadable captions.

Python uses [Daktilo](https://pypi.org/project/daktilo/) for transcription and [Sawalign](https://pypi.org/project/sawalign/) for alignment. TypeScript calls the same endpoints directly. Both use [Sawalni API](https://api.sawalni.com). Daktilo recognizes the words in an audio recording. Sawalign places a transcript against that audio and exports timed subtitles.

```sh
pip install sawalign
```

If you already have a reviewed transcript:

```sh
export SAWALNI_API_KEY="your-key"
sawalign align interview.wav --text transcript.txt --output captions.srt
```

## Languages and scripts

**100+ core languages, with extended compatibility across 400+ languages.** Built on [Sawtone](https://www.omneitylabs.com/models/sawtone), Sawalign works across languages and scripts, including Moroccan Arabic (Darija) and Amazigh, including Tachelhit. Workflows can span Arabic, Latin and Tifinagh scripts.

Use a transcript that matches the speech, including language switches. For Latin-script Darija (often called Arabizi), keep spelling consistent and review the resulting word timings. There is no need to translate it into English. Alignment quality can vary by language, accent and audio quality, particularly beyond the core languages.

## Audio and video input

Pass a local audio or video file directly to either starter. Common inputs include WAV, MP3, M4A, FLAC, OGG, MP4, MOV, MKV and WebM. Decoder support depends on your FFmpeg build. Install [FFmpeg](https://ffmpeg.org/download.html), then check `ffmpeg -version`.

Both starters select the first audio track and convert it locally to mono 16 kHz PCM WAV. Only that prepared audio is uploaded. The original file is unchanged. A temporary directory holds the WAV and is removed after success or failure. Normal process termination runs cleanup; a forced kill can leave temporary files.

The starter preserves the media timeline, including an initial audio delay. Use the same unchanged source for transcription and alignment. Files with no audio track or an unsupported decoder fail before an API request. Choose the intended track externally if the first track is not suitable. Local file paths are accepted; remote URLs are not.

The 128 MiB upload limit applies to prepared audio, not to the video container. Prepared audio must be at most 30 minutes. Longer input is rejected, not silently shortened. Conversion stops after a five-minute timeout. Split longer media first. The standalone `sawalign` package command above does not use this starter's conversion helper.

## Python

This starter pins `daktilo==0.1.1` and `sawalign==0.1.2`.

Use Python 3.11+, FFmpeg on PATH, and your own audio or video file:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r python/requirements.txt
export SAWALNI_API_KEY="your-key"
python python/src/main.py transcribe interview.mp4 --transcript-output transcript.txt
```

Open `transcript.txt` and review the words. Then align the reviewed text:

```sh
python python/src/main.py align interview.mp4 --text transcript.txt --output captions.srt
```

Use the same media file for both steps. Alignment times the text you supply; it does not correct recognition errors.

## TypeScript

Use Node 24+ and FFmpeg on PATH:

```sh
cd typescript
npm ci
export SAWALNI_API_KEY="your-key"
npm start -- transcribe ../interview.mp4 --transcript-output transcript.txt
# Review transcript.txt, then:
npm start -- align ../interview.mp4 transcript.txt captions.srt
```

Both entry points accept your file paths. `SAWALNI_API_KEY` comes from the environment; the scripts do not load `.env` automatically. Create a key and enable model access at [api.sawalni.com](https://api.sawalni.com). Live requests use API credits.

## How it works

![Transcription and subtitle workflow](docs/architecture.svg)

The Python transcribe command uses `Daktilo.transcribe()`. It sends audio to `POST /v1/speech/transcribe` with `model=daktilo`. The Python align command uses `Sawalign.submit()`, `wait()` and `srt()`. TypeScript uses direct HTTP calls. Both send audio and text to `POST /v1/speech/align`, polls the returned job, and downloads SRT when it is done. Credentials stay in your terminal or server process.

## Try the same example as the walkthrough

No key needed to inspect the saved result:

```sh
python3 examples/preview.py
```

`examples/demo/` contains a real Darija audio excerpt, transcript, reviewed text and SRT. Play `audio.wav`, inspect the text and open `captions.srt`. [Audio source and license](examples/demo/README.md).

To run it live, pass `examples/demo/audio.wav` to the same commands above. Saved text/timings are excerpts from the longer recorded run; a new request can return different results.

## Other commands

For a quick draft without a review step:

```sh
python python/src/main.py subtitles interview.mp4 --output draft.srt
```

For translated text or captions, add `--source ary_Arab --target eng_Latn` to the existing translation commands. See [translation examples](docs/translation.md). Translation is optional; the core workflow above keeps the source language.

## Files and checks

- `python/src/main.py`, `typescript/src/main.ts`: CLI workflows to adapt.
- `python/src/media.py`, `typescript/src/media.ts`: local FFmpeg extraction and cleanup.
- `python/src/client.py`, `typescript/src/client.ts`: HTTP transport.
- `examples/demo/`: saved demonstration.

Requests are not automatically retried. Alignment polling stops after ten minutes and reports the job ID. HTTP errors, failed jobs, empty or truncated transcripts stop the workflow. Prepared audio uploads are limited to 128 MiB and 30 minutes; transcript inputs to 1,000,000 UTF-8 bytes in the Python client.

```sh
python tests/media.py
python tests/smoke.py
cd typescript
npm test
npm run check
```

The smoke test uses a local HTTP fixture and makes no paid requests. [API reference](https://api.sawalni.com/docs) · [MIT code license](LICENSE).
