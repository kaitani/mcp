"""Keychain (macOS) から Bridge API キーを取得するユーティリティ。

サイト切替対応:
- 環境変数 SOYSHOP_BRIDGE_KEYCHAIN_SERVICE で Keychain サービス名を指定可能
  デフォルト: soyshop-bridge-komodaru
- フォールバック: 環境変数 SOYSHOP_BRIDGE_API_KEY
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass


DEFAULT_KEYCHAIN_SERVICE = "soyshop-bridge-komodaru"


@dataclass
class BridgeCredentials:
    api_key_full: str  # "{key_id}.{secret}"

    @property
    def key_id(self) -> str:
        return self.api_key_full.split(".", 1)[0]

    @property
    def secret(self) -> str:
        parts = self.api_key_full.split(".", 1)
        return parts[1] if len(parts) == 2 else ""


def load_bridge_credentials() -> BridgeCredentials | None:
    """Keychain (macOS) から Bridge APIキーを取得。
    fallback として環境変数 SOYSHOP_BRIDGE_API_KEY を見る。
    """
    env = os.environ.get("SOYSHOP_BRIDGE_API_KEY", "").strip()
    if env:
        return BridgeCredentials(api_key_full=env)

    if sys.platform != "darwin":
        return None

    user = os.environ.get("USER", "")
    if not user:
        return None

    service = os.environ.get("SOYSHOP_BRIDGE_KEYCHAIN_SERVICE", DEFAULT_KEYCHAIN_SERVICE)
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", user, "-w"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if out.returncode == 0:
            key = out.stdout.strip()
            if key:
                return BridgeCredentials(api_key_full=key)
    except Exception:
        pass
    return None
