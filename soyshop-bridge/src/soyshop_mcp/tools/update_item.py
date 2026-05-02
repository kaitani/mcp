"""Tool: soyshop_update_item - 商品更新（限定フィールドのみ。価格・在庫は不可）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_update_item"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "description": "SoyShop 内部の商品ID（id か code のどちらか必須）",
        },
        "code": {
            "type": "string",
            "description": "商品コード(item_code) で対象指定。Easy My Shop紐付けキー。",
        },
        "name": {"type": "string"},
        "new_code": {
            "type": "string",
            "description": "商品コード自体を変更したい場合（Easy My Shop紐付け先の付け替え）",
        },
        "subtitle": {"type": "string"},
        "alias": {"type": "string"},
        "description": {"type": "string"},
        "description_more": {"type": "string"},
        "categories": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "紐付けカテゴリID配列（既存紐付けは置換される）",
        },
    },
    "anyOf": [
        {"required": ["id"]},
        {"required": ["code"]},
    ],
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop 商品の **限定フィールド** を更新する。"
    "更新可能: name / code / subtitle / alias / description / description_more / categories。"
    "**更新不可**（送るとエラー）: price / stock / sale_price / purchase_price / is_open / is_disabled / sale_flag / open_period_*。"
    "価格・在庫は Easy My Shop 側で管理される設計。"
    "is_open（公開非公開）は soyshop_change_open ツールから切替する。"
    "id か code どちらかで対象指定。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    if not client.credentials:
        return {"error": "no_credentials"}

    item_id = args.get("id")
    code = args.get("code")
    if item_id is None and not code:
        return {"error": "either 'id' or 'code' is required"}

    payload: dict[str, Any] = {}
    # new_code → bridge には "code" として送る
    if "new_code" in args and args["new_code"]:
        payload["code"] = args["new_code"]
    for key in ["name", "subtitle", "alias", "description", "description_more", "categories"]:
        if key in args and args[key] is not None:
            payload[key] = args[key]

    if not payload:
        return {"error": "no fields to update"}

    if item_id is not None:
        return client.bridge_put(f"/items/{int(item_id)}", body=payload)
    return client.bridge_put(f"/items/by-code/{code}", body=payload)
