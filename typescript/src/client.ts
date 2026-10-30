export class Sawalni {
  private key: string | undefined;
  private base: string;
  constructor(
    key = process.env.SAWALNI_API_KEY,
    base = process.env.SAWALNI_BASE_URL || "https://api.sawalni.com/v1",
  ) {
    this.key = key;
    this.base = base;
    if (!key) throw new Error("Set SAWALNI_API_KEY");
  }
  async request(path: string, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${this.key}`);
    const response = await fetch(
      `${this.base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`,
      {
        ...init,
        headers,
        signal: AbortSignal.timeout(120_000),
      },
    );
    if (!response.ok) throw new Error(`Sawalni HTTP ${response.status}`);
    return response;
  }
  async json(path: string, body: unknown): Promise<any> {
    return (
      await this.request(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
    ).json();
  }
}
