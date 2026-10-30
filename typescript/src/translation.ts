import { Sawalni } from "./client.ts";

export async function translateText(
  client: Sawalni,
  text: string,
  source: string,
  target: string,
): Promise<string> {
  const { data } = await client.json("language/translate", {
    model: "tarjamli-mini-v4",
    text,
    source,
    target,
  });
  if (data.complete === false || !data.translated?.trim())
    throw new Error(
      "Translation was incomplete. Shorten or split the transcript.",
    );
  return data.translated;
}

export async function translateSrt(
  client: Sawalni,
  srt: string,
  source: string,
  target: string,
): Promise<string> {
  const cues: string[] = [];
  for (const block of srt
    .replace(/\r\n/g, "\n")
    .trim()
    .split(/\n\s*\n/)) {
    const [index, timing, ...lines] = block.split("\n");
    if (!/^\d+$/.test(index) || !timing?.includes(" --> ") || !lines.length)
      throw new Error("Invalid SRT cue");
    const translated = await translateText(
      client,
      lines.join("\n"),
      source,
      target,
    );
    cues.push([index, timing, translated.replace(/\r/g, "").trim()].join("\n"));
  }
  return cues.join("\n\n") + "\n";
}
