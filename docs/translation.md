# Optional translation

Keep transcription and timing in the original spoken language. Translate the result afterward.

```sh
python python/src/main.py translate interview.wav --source ary_Arab --target eng_Latn --translation-output translated.txt
python python/src/main.py align interview.wav --text transcript.txt --output captions.srt --source ary_Arab --target eng_Latn --translation-output translated.srt
```

TypeScript accepts the same language options:

```sh
cd typescript
npm start -- translate ../interview.wav --source ary_Arab --target eng_Latn
npm start -- align ../interview.wav transcript.txt captions.srt --source ary_Arab --target eng_Latn
```

Translation preserves source cue timestamps. Translated words are not aligned as though they were spoken in the source audio. Review translation, line breaks and reading speed. Cue-by-cue translation can lose context.
