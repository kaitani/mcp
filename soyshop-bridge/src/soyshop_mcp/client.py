"""SoyShop Bridge HTTPクライアント。

URLパス: https://{base}/soyshop_bridge/...
認証:    X-API-Key + X-Timestamp + X-Signature(HMAC-SHA256)

サイト切替:
- SOYSHOP_BRIDGE_BASE_URL 環境変数（デフォルト https://komodaru-ya.com）
- SOYSHOP_BRIDGE_KEYCHAIN_SERVICE で Keychain サービス名を指定可能
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


DEFAULT_BASE_URL = "https://komodaru-ya.com"


@dataclass
class SoyShopConfig:
    base_url: str
    timeout: float = 15.0

    @classmethod
    def from_env(cls) -> "SoyShopConfig":
        return cls(
            base_url=os.environ.get("SOYSHOP_BRIDGE_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            timeout=float(os.environ.get("SOYSHOP_BRIDGE_TIMEOUT", "15")),
        )


class SoyShopClient:
    """SoyShop Bridge への HTTP クライアント。HMAC認証付き。"""

    def __init__(
        self,
        config: SoyShopConfig | None = None,
        credentials: BridgeCredentials | None = None,
    ):
        self.config = config or SoyShopConfig.from_env()
        self.credentials = credentials or load_bridge_credentials()
        self._client = httpx.Client(timeout=self.config.timeout, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------ #
    # Bridge API                                                          #
    # ------------------------------------------------------------------ #

    def bridge_get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        return self._bridge_request("GET", path, params=params, body=None)

    def bridge_post(self, path: str, body: dict | None = None) -> dict[str, Any]:
        return self._bridge_request("POST", path, params=None, body=body)

    def bridge_put(self, path: str, body: dict | None = None) -> dict[str, Any]:
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
                "SoyShop Bridge credentials not found. "
                "Set Keychain entry (default 'soyshop-bridge-komodaru') "
                "or SOYSHOP_BRIDGE_API_KEY env var."
            )

        if not path.startswith("/"):
            path = "/" + path
        if not path.startswith("/soyshop_bridge/"):
            path = "/soyshop_bridge" + path

        url = f"{self.config.base_url}{path}"
        # 署名は path（クエリ抜き）で計算する（PHP側 parse_url(PHP_URL_PATH) と整合）
        body_str = (
            json.dumps(body, ensure_ascii=False, separators=(",", ":")) if body is not None else ""
        )
        timestamp = str(int(time.time()))

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
        super().__init__(f"SoyShop Bridge error {status}: {detail}")
