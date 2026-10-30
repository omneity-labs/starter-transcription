import argparse
import time
from pathlib import Path
from client import Sawalni
from translation import translate_text, translate_srt

parser = argparse.ArgumentParser(
    description="Transcribe recordings, align scripts, or create subtitles"
)
parser.add_argument("mode", choices=["transcribe", "align", "subtitles", "translate"])
parser.add_argument("audio", type=Path)
parser.add_argument("--text", type=Path, help="Reviewed transcript for align mode")
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
client = Sawalni()
if args.mode == "align" and not args.text:
    parser.error("align requires --text transcript.txt")
text = args.text.read_text() if args.text else ""
if args.mode != "align":
    result = client.request(
        "POST",
        "speech/transcribe",
        files={"audio": (args.audio.name, args.audio.read_bytes())},
        data={"model": "daktilo"},
    ).json()
    text = result["text"]
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
    job = client.request(
        "POST",
        "speech/align",
        files={"audio": (args.audio.name, args.audio.read_bytes())},
        data={"text": text},
    ).json()["job_id"]
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        status = client.request("GET", f"speech/align/job/{job}").json()
        print(status["status"], status.get("step", ""))
        if status["status"] == "done":
            srt = client.request("GET", f"speech/align/job/{job}/srt").text
            args.output.write_text(srt, encoding="utf-8")
            if args.target:
                translated = translate_srt(client, srt, args.source, args.target)
                (args.translation_output or Path("translated.srt")).write_text(
                    translated, encoding="utf-8"
                )
            break
        if status["status"] in ["error", "failed", "cancelled"]:
            raise RuntimeError("Alignment failed")
        time.sleep(2)
    else:
        raise TimeoutError(f"Alignment timed out; resume polling job {job}")
