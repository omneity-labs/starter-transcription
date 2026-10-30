"""Translate transcripts or subtitle cue text. Keep source-audio timing unchanged."""

import re


def translate_text(client, text, source, target):
    data = client.request(
        "POST",
        "language/translate",
        json={
            "model": "tarjamli-mini-v4",
            "text": text,
            "source": source,
            "target": target,
        },
    ).json()["data"]
    if data.get("complete") is False or not data.get("translated", "").strip():
        raise ValueError("Translation was incomplete. Shorten or split the transcript.")
    return data["translated"]


def translate_srt(client, srt, source, target):
    cues = []
    for block in re.split(r"\n\s*\n", srt.replace("\r\n", "\n").strip()):
        lines = block.split("\n")
        if len(lines) < 3 or not lines[0].isdigit() or " --> " not in lines[1]:
            raise ValueError("Invalid SRT cue")
        translated = translate_text(client, "\n".join(lines[2:]), source, target)
        cues.append(
            "\n".join([lines[0], lines[1], translated.replace("\r", "").strip()])
        )
    return "\n\n".join(cues) + "\n"
