"""Tool: soyshop_version - Bridge APIバージョン・SoyShopバージョン・サイトIDの取得（健康確認用）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_version"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop Bridge API のバージョン情報を取得する（健康確認用）。"
    "Bridge プラグインバージョン、SoyShop本体バージョン、サイトID(soyshop_id)、DB種別を返す。"
    "MCPサーバ起動時の動作確認に使用。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    return client.bridge_get("/version")
