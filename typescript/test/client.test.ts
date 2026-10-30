import { test } from "node:test";
import assert from "node:assert/strict";
import { Sawalni } from "../src/client.ts";
test("missing API key fails before any request", () => {
  const previous = process.env.SAWALNI_API_KEY;
  delete process.env.SAWALNI_API_KEY;
  try {
    assert.throws(() => new Sawalni(), /Set SAWALNI_API_KEY/);
  } finally {
    if (previous !== undefined) process.env.SAWALNI_API_KEY = previous;
  }
});
