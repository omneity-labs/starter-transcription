import argparse
import os
from sawalign import Sawalign
from daktilo import Daktilo
from pathlib import Path
from client import Sawalni
from translation import translate_text, translate_srt
from media import prepare_audio

parser = argparse.ArgumentParser(
    description="Transcribe recordings, align scripts, or create subtitles"
)
parser.add_argument("mode", choices=["transcribe", "align", "subtitles", "translate"])
parser.add_argument("audio", type=Path, help="Local audio or video file; FFmpeg extracts its first audio track")
parser.add_argument("--text", type=Path, help="Reviewed transcript for align mode")
parser.add_argument("--transcript-output", type=Path, help="Save recognized text for review before alignment")
parser.add_argument("--output", type=Path, default=Path("output.srt"))
parser.add_argument(
    "--source",
    default="ary_Arab",
    help="Transcript language code; default Moroccan Arabic",
)
parser.add_argument("--target", help="Translation target, such as eng_Latn")
parser.add_argument(
    "--translation-output", type=Path, help="Default translated.txt or translated.srt"
)
args = parser.parse_args()
if args.mode == "translate" and not args.target:
    parser.error("translate requires --target")
with prepare_audio(args.audio) as audio_path:
    client = Sawalni()
    if args.mode == "align" and not args.text:
        parser.error("align requires --text transcript.txt")
    if args.text and args.text.stat().st_size > 1_000_000:
        parser.error("Transcript exceeds 1,000,000 UTF-8 bytes")
    text = args.text.read_text(encoding="utf-8") if args.text else ""
    if args.mode != "align":
        with Daktilo(base_url=os.getenv("SAWALNI_BASE_URL", "https://api.sawalni.com/v1")) as transcriber:
            result = transcriber.transcribe(audio_path)
        text = result.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Transcription returned no text")
        if result.get("truncated") or any(x.get("truncated") for x in result.get("segments", [])):
            raise ValueError("Transcription was truncated; use a shorter audio recording")
        if args.transcript_output:
            args.transcript_output.write_text(text, encoding="utf-8")
        print(text)
    if args.mode in ["transcribe", "translate"] and args.target:
        translated = translate_text(client, text, args.source, args.target)
        (args.translation_output or Path("translated.txt")).write_text(
            translated, encoding="utf-8"
        )
        print(translated)
    if args.mode in ["align", "subtitles"]:
        if not text.strip():
            raise ValueError("No transcript to align")
        with Sawalign(base_url=os.getenv("SAWALNI_BASE_URL", "https://api.sawalni.com/v1")) as aligner:
            job = aligner.submit(audio_path, text)
            print("Alignment job:", job["job_id"], flush=True)
            aligner.wait(job["job_id"])
            srt = aligner.srt(job["job_id"])
        args.output.write_text(srt, encoding="utf-8")
        if args.target:
            translated = translate_srt(client, srt, args.source, args.target)
            (args.translation_output or Path("translated.srt")).write_text(translated, encoding="utf-8")
