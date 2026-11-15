import { mkdtemp, rm, stat, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
const exec = promisify(execFile);

/** Extract the first audio track. The caller must dispose after all API steps. */
export async function prepareAudio(source: string) {
  source = resolve(source);
  if (!(await stat(source)).isFile()) throw new Error("Input must be a local audio or video file");
  const folder = await mkdtemp(join(tmpdir(), "sawalni-media-"));
  const path = join(folder, "audio.wav");
  const dispose = () => rm(folder, { recursive: true, force: true });
  try {
    try {
      await exec("ffmpeg", [
        "-nostdin", "-hide_banner", "-loglevel", "error",
        "-protocol_whitelist", "file,pipe", "-copyts", "-start_at_zero",
        "-i", source, "-map", "0:a:0", "-vn", "-sn", "-dn",
        "-af", "aresample=async=1:first_pts=0", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", "-t", "1800.1", "-y", path,
      ], { timeout: 300_000, maxBuffer: 1024 * 1024 });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT")
        throw new Error("Install FFmpeg and put ffmpeg on PATH before running this starter");
      throw new Error("Cannot prepare an audio track. Check the file and its first audio track with FFmpeg; preparation has a five-minute timeout");
    }
    const audio = await readFile(path);
    // FFmpeg writes RIFF PCM WAV. Find the data chunk instead of assuming a 44-byte header.
    let offset = 12, bytes = 0;
    while (offset + 8 <= audio.length) {
      const size = audio.readUInt32LE(offset + 4);
      if (audio.toString("ascii", offset, offset + 4) === "data") { bytes = size; break; }
      offset += 8 + size + (size % 2);
    }
    const duration = bytes / (16000 * 2);
    if (duration <= 0 || duration > 1800)
      throw new Error("Audio must contain speech and be at most 30 minutes; split longer media first");
    if (audio.length > 128 * 1024 * 1024) throw new Error("Prepared audio exceeds 128 MiB");
    return { audio, dispose };
  } catch (error) {
    await dispose();
    throw error;
  }
}
