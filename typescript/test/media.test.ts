import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { prepareAudio } from '../src/media.ts';
const ffmpeg = (...args: string[]) => execFileSync('ffmpeg', ['-nostdin', '-loglevel', 'error', '-y', ...args]);
function duration(audio: Buffer) {
  let at = 12;
  while (at + 8 <= audio.length) {
    const size = audio.readUInt32LE(at + 4);
    if (audio.toString('ascii', at, at + 4) === 'data') return size / 32000;
    at += 8 + size + size % 2;
  }
  throw new Error('No PCM data');
}
test('media preparation preserves delayed audio, rejects long or invalid input, and cleans temporary files', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'media-test-'));
  const before = (await readdir(tmpdir())).filter(x => x.startsWith('sawalni-media-')).sort();
  try {
    const source = join(folder, 'audio with spaces.wav');
    ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1', source);
    const video = join(folder, 'delayed.mkv');
    ffmpeg('-f','lavfi','-i','color=size=16x16:duration=2','-itsoffset','0.5','-i',source,'-c:a','pcm_s16le',video);
    const prepared = await prepareAudio(video);
    try { assert.ok(Math.abs(duration(prepared.audio) - 1.5) < 0.03); }
    finally { await prepared.dispose(); }
    const long = join(folder, 'long.flac');
    ffmpeg('-f','lavfi','-i','anullsrc=r=8000:cl=mono','-t','1801',long);
    await assert.rejects(prepareAudio(long), /30 minutes/);
    const invalid = join(folder, 'invalid.mp4');
    await writeFile(invalid, 'not media');
    await assert.rejects(prepareAudio(invalid), /audio track/);
    const oldPath = process.env.PATH;
    try {
      process.env.PATH = folder;
      await assert.rejects(prepareAudio(source), /Install FFmpeg/);
    } finally { process.env.PATH = oldPath; }
    assert.deepEqual((await readdir(tmpdir())).filter(x => x.startsWith('sawalni-media-')).sort(), before);
  } finally { await rm(folder, {recursive:true,force:true}); }
});
