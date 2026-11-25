"""Official Logo.dev v2 adapter; credentials remain environment-only."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.logo.dev"


def load_workspace_environment():
    """Load only Logo.dev variables from the skill-local .env when absent."""
    environment = Path(__file__).resolve().parents[2] / ".env"
    try:
        lines = environment.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in {"LOGO_DEV_SECRET_KEY", "LOGO_DEV_PUBLISHABLE_KEY"}:
            continue
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key, value)


class LogoDev:
    def __init__(self, key=None, transport=None):
        load_workspace_environment()
        self.key = key or os.getenv("LOGO_DEV_SECRET_KEY")
        self.transport = transport or urllib.request.urlopen

    def configured(self):
        return bool(self.key)

    def request(self, path, params=None):
        if not self.key:
            return {"ok": False, "state": "blocked", "reason": "LOGO_DEV_SECRET_KEY is not configured"}
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        request = urllib.request.Request(url, headers={"Authorization": "Bearer " + self.key, "Accept": "application/json", "User-Agent": "transcript-to-visual/1.0"})
        try:
            with self.transport(request, timeout=15) as response:
                return {"ok": True, "data": json.loads(response.read()), "status": getattr(response, "status", 200)}
        except urllib.error.HTTPError as error:
            categories = {401: "unauthorized", 402: "insufficient_credits", 403: "forbidden", 404: "not_found", 429: "rate_limited"}
            try:
                detail = json.loads(error.read().decode("utf-8", "replace"))
            except Exception:
                detail = None
            return {"ok": False, "state": categories.get(error.code, "failed"), "http_status": error.code, "provider_error": detail}
        except (urllib.error.URLError, TimeoutError) as error:
            return {"ok": False, "state": "network_failure", "reason": error.__class__.__name__}
        except Exception as error:
            return {"ok": False, "state": "failed", "reason": error.__class__.__name__}

    def search(self, name, method="match", limit=10):
        # Logo.dev v2 requires q (not query).
        return self.request("/v2/search", {"q": name, "method": method, "limit": limit})

    def brand(self, identifier, identifier_type=None):
        # /v2/brands accepts exactly one named identifier, never `identifier`.
        kind = identifier_type or ("domain" if "." in identifier else "name")
        if kind not in {"domain", "ticker", "isin", "crypto", "name"}:
            raise ValueError("unsupported Logo.dev identifier type")
        return self.request("/v2/brands", {kind: identifier, "nosubscribe": "true"})
