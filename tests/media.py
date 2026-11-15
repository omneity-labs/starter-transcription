"""Real FFmpeg preparation checks, without an API key or network request."""
import subprocess, sys, tempfile, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python/src"))
from media import prepare_audio

with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    source = folder / "source with spaces.wav"
    with wave.open(str(source), "wb") as f:
        f.setparams((2, 2, 44100, 0, "NONE", "not compressed"))
        f.writeframes(b"\0\0" * 2 * 44100)
    original = source.read_bytes()
    with prepare_audio(source) as audio:
        prepared = audio
        with wave.open(str(audio), "rb") as f:
            assert (f.getnchannels(), f.getframerate(), f.getsampwidth()) == (1, 16000, 2)
            assert abs(f.getnframes() / f.getframerate() - 1) < 0.01
    assert not prepared.exists() and source.read_bytes() == original
    try:
        with prepare_audio(source) as audio:
            prepared = audio
            raise RuntimeError("API failure fixture")
    except RuntimeError:
        pass
    assert not prepared.exists(), "Temporary audio must be removed on failure"
    delayed = folder / "delayed.mkv"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=size=16x16:duration=2", "-itsoffset", "0.5", "-i", str(source), "-c:a", "pcm_s16le", str(delayed)], check=True)
    with prepare_audio(delayed) as audio:
        with wave.open(str(audio), "rb") as f:
            assert abs(f.getnframes() / f.getframerate() - 1.5) < 0.03, "Keep initial audio delay on the video timeline"
    long = folder / "long.flac"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", "-t", "1801", str(long)], check=True)
    try:
        with prepare_audio(long):
            raise AssertionError("Long media must be rejected")
    except ValueError as e:
        assert "30 minutes" in str(e)
print("PASS PCM normalization, unchanged source, cleanup, video audio delay, duration rejection")
