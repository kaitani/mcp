"""Tool: soyshop_get_item - 商品詳細取得（id または code 経由）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_get_item"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "description": "SoyShop 内部の商品ID",
        },
        "code": {
            "type": "string",
            "description": "商品コード(item_code = Easy My Shop紐付けキー)",
        },
    },
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop の商品詳細を取得する。id か code のどちらかを指定。"
    "code は Easy My Shop の外部カゴIDと一致する商品コード（例: 'sikiza-honj-k42'）。"
    "返り値: id, code, name, subtitle, alias, type, price(参考値), stock(参考値), is_open, categories[]"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    item_id = args.get("id")
    code = args.get("code")
    if item_id is None and not code:
        return {"error": "either 'id' or 'code' is required"}
    if item_id is not None:
        return client.bridge_get(f"/items/{int(item_id)}.json")
    return client.bridge_get(f"/items/by-code/{code}.json")
