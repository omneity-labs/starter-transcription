import { readFile, writeFile } from "node:fs/promises";
import { Sawalni } from "./client.ts";
import { parseArgs } from "node:util";
import { translateText, translateSrt } from "./translation.ts";
const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    source: { type: "string", default: "ary_Arab" },
    target: { type: "string" },
    "translation-output": { type: "string" },
  },
});
const [mode, path, transcriptPath, output = "output.srt"] = positionals;
if (
  !["transcribe", "align", "subtitles", "translate"].includes(mode) ||
  !path ||
  (mode === "align" && !transcriptPath) ||
  (mode === "translate" && !values.target)
) {
  throw new Error(
    "Usage: npm start -- transcribe|subtitles|translate audio.wav [--source ary_Arab --target eng_Latn] OR align audio.wav transcript.txt [output.srt] [--target eng_Latn]",
  );
}
const client = new Sawalni(),
  audio = await readFile(path);
const form = () => {
  const f = new FormData();
  f.append("audio", new Blob([audio]), path.split("/").pop()!);
  return f;
};
let text = mode === "align" ? await readFile(transcriptPath, "utf8") : "";
if (mode !== "align") {
  const body = form();
  body.append("model", "daktilo");
  const result = await (
    await client.request("speech/transcribe", { method: "POST", body })
  ).json();
  text = result.text;
  console.log(text);
}
if (["transcribe", "translate"].includes(mode) && values.target) {
  const translated = await translateText(
    client,
    text,
    values.source,
    values.target,
  );
  await writeFile(values["translation-output"] || "translated.txt", translated);
  console.log(translated);
}
if (["align", "subtitles"].includes(mode)) {
  if (!text?.trim()) throw new Error("No transcript to align");
  const body = form();
  body.append("text", text);
  const { job_id } = await (
    await client.request("speech/align", { method: "POST", body })
  ).json();
  const path = `speech/align/job/${encodeURIComponent(job_id)}`;
  const deadline = Date.now() + 600_000;
  let done = false;
  while (Date.now() < deadline) {
    const status = await (await client.request(path)).json();
    console.log(status.status, status.step || "");
    if (status.status === "done") {
      const srt = await (await client.request(`${path}/srt`)).text();
      await writeFile(output, srt);
      if (values.target) {
        await writeFile(
          values["translation-output"] || "translated.srt",
          await translateSrt(client, srt, values.source, values.target),
        );
      }
      done = true;
      break;
    }
    if (["error", "failed", "cancelled"].includes(status.status))
      throw new Error("Alignment failed");
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  if (!done)
    throw new Error(`Alignment timed out; resume polling job ${job_id}`);
}
