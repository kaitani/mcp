"""SOY CMS HTTPクライアント

- 公開JSON: https://eleve-organic.jp/{blog_page_id}.json (output_blog_entries_json)
- Bridge:   https://eleve-organic.jp/eleve_bridge/* (要認証 X-API-Key + HMAC-SHA256)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .auth import BridgeCredentials, load_bridge_credentials


DEFAULT_BASE_URL = "https://eleve-organic.jp"
DEFAULT_BLOG_PAGE_ID = 5


@dataclass
class SoyCmsConfig:
    base_url: str
    blog_page_id: int
    timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "SoyCmsConfig":
        return cls(
            base_url=os.environ.get("SOYCMS_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            blog_page_id=int(os.environ.get("SOYCMS_BLOG_PAGE_ID", str(DEFAULT_BLOG_PAGE_ID))),
            timeout=float(os.environ.get("SOYCMS_TIMEOUT", "10")),
        )


class SoyCmsClient:
    """SOY CMS への HTTP クライアント。

    - read_public_entries: output_blog_entries_json プラグイン (認証なし)
    - bridge_get / bridge_post / bridge_put: 自作 eleve_bridge プラグイン (HMAC認証)
    """

    def __init__(self, config: SoyCmsConfig | None = None, credentials: BridgeCredentials | None = None):
        self.config = config or SoyCmsConfig.from_env()
        self.credentials = credentials or load_bridge_credentials()
        self._client = httpx.Client(timeout=self.config.timeout, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------ #
    # 公開JSON (output_blog_entries_json)                                 #
    # ------------------------------------------------------------------ #

    def read_public_entries(self, *, limit: int = 30, offset: int = 0, customfield: str | None = None) -> dict[str, Any]:
        """ドメイン直下の {blog_page_id}.json から記事一覧を取得。

        URL: https://eleve-organic.jp/{blog_page_id}.json?limit=N&offset=N
        """
        url = f"{self.config.base_url}/{self.config.blog_page_id}.json"
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        if customfield:
            params["customfield"] = customfield
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # Bridge API (eleve_bridge プラグイン)                                #
    # ------------------------------------------------------------------ #

    def bridge_get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        return self._bridge_request("GET", path, params=params, body=None)

    def bridge_post(self, path: str, body: dict) -> dict[str, Any]:
        return self._bridge_request("POST", path, params=None, body=body)

    def bridge_put(self, path: str, body: dict) -> dict[str, Any]:
        return self._bridge_request("PUT", path, params=None, body=body)

    def _bridge_request(
        self,
        method: str,
        path: str,
        params: dict | None,
        body: dict | None,
    ) -> dict[str, Any]:
        if not self.credentials:
            raise RuntimeError(
                "Bridge API credentials not found. Set Keychain entry 'soycms-eleve-bridge' "
                "or SOYCMS_BRIDGE_API_KEY env var."
            )

        if not path.startswith("/"):
            path = "/" + path
        if not path.startswith("/eleve_bridge/"):
            path = "/eleve_bridge" + path

        url = f"{self.config.base_url}{path}"
        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":")) if body else ""
        timestamp = str(int(time.time()))

        # canonicalString: timestamp + "\n" + METHOD + "\n" + PATH + "\n" + sha256(body)
        body_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()
        canonical = f"{timestamp}\n{method.upper()}\n{path}\n{body_hash}"
        signature = hmac.new(
            self.credentials.secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "X-API-Key": self.credentials.api_key_full,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json; charset=utf-8",
        }

        resp = self._client.request(
            method.upper(),
            url,
            headers=headers,
            params=params,
            content=body_str.encode("utf-8") if body_str else None,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = {"raw": resp.text[:500]}
            raise BridgeError(resp.status_code, detail)
        return resp.json() if resp.text else {}


class BridgeError(Exception):
    def __init__(self, status: int, detail: Any):
        self.status = status
        self.detail = detail
        super().__init__(f"Bridge API error {status}: {detail}")
