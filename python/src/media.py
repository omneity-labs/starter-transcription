"""Prepare a local audio/video file. Never modify the source."""
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave


@contextmanager
def prepare_audio(source: Path):
    source = source.resolve(strict=True)
    if not source.is_file():
        raise ValueError("Input must be a local audio or video file")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Install FFmpeg and put ffmpeg on PATH before running this starter")
    with tempfile.TemporaryDirectory(prefix="sawalni-media-") as folder:
        output = Path(folder) / "audio.wav"
        try:
            result = subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-protocol_whitelist", "file,pipe", "-copyts", "-start_at_zero",
                "-i", str(source), "-map", "0:a:0", "-vn", "-sn", "-dn",
                "-af", "aresample=async=1:first_pts=0", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", "-t", "1800.1", "-y", str(output),
            ], capture_output=True, timeout=300)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Audio preparation timed out; use a shorter or simpler file") from exc
        if result.returncode:
            raise ValueError("Cannot decode an audio track. Check the file and its first audio track with FFmpeg")
        with wave.open(str(output), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
        if duration <= 0 or duration > 1800:
            raise ValueError("Audio must contain speech and be at most 30 minutes; split longer media first")
        if output.stat().st_size > 128 * 1024 * 1024:
            raise ValueError("Prepared audio exceeds 128 MiB")
        yield output
