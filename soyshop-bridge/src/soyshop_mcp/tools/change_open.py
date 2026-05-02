"""Tool: soyshop_change_open - 商品の公開非公開切替（複数IDまたはコードで一括）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_change_open"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "open": {
            "type": "integer",
            "enum": [0, 1],
            "description": "0=非公開にする / 1=公開にする",
        },
        "ids": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1},
            "description": "対象の商品ID配列（ids と codes は併用可）",
        },
        "codes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "対象の商品コード(item_code)配列。Easy My Shop紐付けキーで指定可能",
        },
    },
    "required": ["open"],
    "anyOf": [
        {"required": ["ids"]},
        {"required": ["codes"]},
    ],
    "additionalProperties": False,
}

DESCRIPTION = (
    "商品の **公開/非公開** を一括切替する。最大500件/コール。"
    "用途例: Easy My Shop で売り切れた商品を SoyShop 側でも非公開に / 入荷時に公開に戻す。"
    "ids（商品ID）または codes（商品コード）で対象指定。両方併用も可。"
    "open=0 で非公開、open=1 で公開。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    if not client.credentials:
        return {"error": "no_credentials"}

    open_val = args.get("open")
    if open_val not in (0, 1):
        return {"error": "open must be 0 or 1"}

    ids = args.get("ids") or []
    codes = args.get("codes") or []
    if not ids and not codes:
        return {"error": "either 'ids' or 'codes' is required"}

    payload: dict[str, Any] = {"open": int(open_val)}
    if ids:
        payload["ids"] = [int(i) for i in ids]
    if codes:
        payload["codes"] = [str(c) for c in codes]

    return client.bridge_post("/items/change-open", body=payload)
