"""End-to-end starter checks against a local API fixture. No paid requests."""

import io, json, os, subprocess, threading, wave, tempfile, sys, shutil
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

repo_root = Path(__file__).resolve().parents[1]
r = repo_root.parent
node = shutil.which("node")
assert node, "Install Node.js 24 or newer"
python = sys.executable
seen = []
return_empty = False


class API(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, status=200, kind="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(
            json.dumps(body).encode() if kind == "application/json" else body
        )

    def do_POST(self):
        assert self.headers["Authorization"] == "Bearer fixture-key"
        body = self.rfile.read(int(self.headers["Content-Length"]))
        seen.append(self.path)
        if self.path.endswith("/speech/transcribe"):
            assert (
                b'name="audio"' in body
                and b'name="model"' in body
                and b"daktilo" in body
            )
            if return_empty:
                self.reply({"text": ""})
            else:
                self.reply({"text": "A fixture transcript"})
        elif self.path.endswith("/speech/align"):
            assert b'name="audio"' in body and b'name="text"' in body
            self.reply({"job_id": "fixture1", "status": "queued"}, 202)
        elif self.path.endswith("/language/translate"):
            data = json.loads(body)
            assert data["source"] == "ary_Arab" and data["target"] == "eng_Latn"
            self.reply({"data": {"translated": "Translated fixture", "complete": True}})
        else:
            self.reply({"error": "unexpected path"}, 404)

    def do_GET(self):
        seen.append(self.path)
        if self.path.endswith("/srt"):
            self.reply(b"1\n00:00:00,000 --> 00:00:01,000\nHello\n", kind="text/plain")
        else:
            self.reply({"job_id": "fixture1", "status": "done"})


server = ThreadingHTTPServer(("127.0.0.1", 0), API)
threading.Thread(target=server.serve_forever, daemon=True).start()
env = {
    **os.environ,
    "SAWALNI_API_KEY": "fixture-key",
    "SAWALNI_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
}
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    audio = folder / "recording.wav"
    text = folder / "transcript.txt"
    text.write_text("Reviewed script")
    with wave.open(str(audio), "wb") as w:
        w.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        w.writeframes(b"\0\0" * 3200)
    for repo in ["starter-transcription"]:
        for lang in ["python", "typescript"]:
            cwd = repo_root / lang

            def run(args):
                cmd = (
                    [python, "src/main.py"]
                    if lang == "python"
                    else [node, "src/main.ts"]
                )
                result = subprocess.run(
                    cmd + args,
                    cwd=cwd,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=30,
                )
                assert result.returncode == 0, (repo, lang, result.stderr)
                return result.stdout

            transcript_output = folder / f"{lang}-recognized.txt"
            assert "fixture transcript" in run(["transcribe", str(audio), "--transcript-output", str(transcript_output)])
            assert transcript_output.read_text() == "A fixture transcript"
            # User reviews the saved text before the alignment request.
            transcript_output.write_text("Reviewed script")
            empty = folder / "empty.wav"; empty.write_bytes(audio.read_bytes())
            cmd = [python, "src/main.py"] if lang == "python" else [node, "src/main.ts"]
            before = len(seen)
            return_empty = True
            failed = subprocess.run(cmd + ["subtitles", str(empty)], cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
            return_empty = False
            assert failed.returncode != 0 and "no text" in failed.stderr
            assert not any("/speech/align" in p for p in seen[before:])
            output = folder / f"{lang}.srt"
            args = (
                ["align", str(audio), "--text", str(transcript_output), "--output", str(output)]
                if lang == "python"
                else ["align", str(audio), str(transcript_output), str(output)]
            )
            run(args)
            assert "-->" in output.read_text()
            run(["subtitles", str(audio)])
            generated = cwd / "output.srt"
            assert "-->" in generated.read_text()
            generated.unlink()
            translated = folder / f"{lang}-translated.txt"
            assert "Translated fixture" in run(
                [
                    "translate",
                    str(audio),
                    "--source",
                    "ary_Arab",
                    "--target",
                    "eng_Latn",
                    "--translation-output",
                    str(translated),
                ]
            )
            assert translated.read_text() == "Translated fixture"
            translated_srt = folder / f"{lang}-translated.srt"
            run(
                [
                    "subtitles",
                    str(audio),
                    "--target",
                    "eng_Latn",
                    "--translation-output",
                    str(translated_srt),
                ]
            )
            original = (cwd / "output.srt").read_text()
            assert (
                original.splitlines()[1]
                == translated_srt.read_text().splitlines()[1]
            )
            assert "Translated fixture" in translated_srt.read_text()
            (cwd / "output.srt").unlink()
            # Exercise real containers through each CLI and the local API fixture.
            for suffix in ["mp3", "mp4", "webm"]:
                media = folder / f"clip.{suffix}"
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(audio), str(media)], check=True)
                assert "fixture transcript" in run(["transcribe", str(media)])
            silent = folder / "silent.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=size=16x16:duration=0.1", "-an", str(silent)], check=True)
            before = len(seen)
            failed = subprocess.run(cmd + ["transcribe", str(silent)], cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
            assert failed.returncode != 0 and "audio track" in failed.stderr
            assert len(seen) == before, "Invalid media must fail before an API request"
            print("PASS", repo, lang)
server.shutdown()
print("PASS HTTP fixture workflows for", repo_root.name)
