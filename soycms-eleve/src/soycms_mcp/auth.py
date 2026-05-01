"""Keychain (macOS) からBridge APIキーを取得するユーティリティ"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass


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
    """Keychain (macOS) から SOYCMS_BRIDGE_API_KEY を取得。
    fallback として環境変数 SOYCMS_BRIDGE_API_KEY を見る。
    """
    env = os.environ.get("SOYCMS_BRIDGE_API_KEY", "").strip()
    if env:
        return BridgeCredentials(api_key_full=env)

    # Keychain (macOS only)
    if sys.platform != "darwin":
        return None

    user = os.environ.get("USER", "")
    if not user:
        return None
    try:
        out = subprocess.run(
            [
                "security", "find-generic-password",
                "-s", "soycms-eleve-bridge",
                "-a", user,
                "-w",
            ],
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


def has_bridge_credentials() -> bool:
    return load_bridge_credentials() is not None
