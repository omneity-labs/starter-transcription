import os
import httpx


class Sawalni:
    """Server-side client. Never send your API key to a browser."""

    def __init__(self):
        key = os.environ.get("SAWALNI_API_KEY")
        if not key:
            raise ValueError("Set SAWALNI_API_KEY")
        self.http = httpx.Client(
            base_url=os.getenv("SAWALNI_BASE_URL", "https://api.sawalni.com/v1").rstrip(
                "/"
            )
            + "/",
            headers={"Authorization": f"Bearer {key}"},
            timeout=120,
        )

    def request(self, method, path, **kwargs):
        response = self.http.request(method, path.lstrip("/"), **kwargs)
        response.raise_for_status()
        return response
