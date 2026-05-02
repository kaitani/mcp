"""Tool: soyshop_create_draft_item - 新規商品 draft 作成（is_open=0強制）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_create_draft_item"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "商品名（255字以内）",
        },
        "code": {
            "type": "string",
            "description": "商品コード(item_code)。**Easy My Shop の外部カゴIDをここに入れる**。100字以内",
        },
        "subtitle": {
            "type": "string",
            "description": "サブタイトル（255字以内）",
        },
        "alias": {
            "type": "string",
            "description": "URLスラッグ（英数・ハイフン・アンダースコア、1-80字）",
            "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_-]{0,80}$",
        },
        "description": {
            "type": "string",
            "description": "商品説明（HTML可）",
        },
        "description_more": {
            "type": "string",
            "description": "詳細説明（HTML可）",
        },
        "categories": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "紐付けるカテゴリID配列（soyshop_list_categories で取得可能）",
        },
    },
    "anyOf": [
        {"required": ["name"]},
        {"required": ["code"]},
    ],
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop に新規商品を draft 状態で登録する（is_open=0=非公開で固定）。"
    "価格・在庫はBridge経由では設定不可（Easy My Shop側で管理する設計）。"
    "公開はオーナーが管理画面で人間判断、または soyshop_change_open ツールで明示的に切替。"
    "**name か code のいずれか必須**。code は Easy My Shop紐付けキー（例: 'WINE-2024-A'）。"
    "日次create上限デフォルト200件（プラグイン設定でキー単位上書き可）。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    if not client.credentials:
        return {
            "error": "no_credentials",
            "detail": (
                "SoyShop Bridge APIキーが Keychain にありません。"
                "管理画面でAPIキー発行 → "
                "security add-generic-password -s soyshop-bridge-komodaru -a $USER -w '<key_id>.<secret>'"
            ),
        }

    payload: dict[str, Any] = {}
    for key in [
        "name", "code", "subtitle", "alias", "description", "description_more", "categories",
    ]:
        if key in args and args[key] not in (None, ""):
            payload[key] = args[key]

    if "name" not in payload and "code" not in payload:
        return {"error": "either 'name' or 'code' is required"}

    return client.bridge_post("/items", body=payload)
