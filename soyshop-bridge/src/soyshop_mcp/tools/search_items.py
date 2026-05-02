"""Tool: soyshop_search_items - 商品一覧・検索"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_search_items"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "q": {
            "type": "string",
            "description": "商品名・コード・サブタイトルを部分一致検索",
        },
        "code": {
            "type": "string",
            "description": "商品コード(item_code)の前方/部分一致パターン。'*' をワイルドカードとして使える（例: 'WINE-*'）",
        },
        "open": {
            "type": "string",
            "enum": ["all", "open", "closed"],
            "default": "all",
            "description": "公開状態フィルタ。open=公開中のみ / closed=非公開のみ / all=両方",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 200,
            "default": 30,
        },
        "offset": {
            "type": "integer",
            "minimum": 0,
            "default": 0,
        },
    },
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop の商品マスタから商品を検索する。"
    "商品名キーワード(q)・商品コードパターン(code, '*'ワイルドカード可)・公開状態(open)で絞り込み可能。"
    "返り値には id・code(=Easy My Shop紐付けキー)・name・price(参考値)・stock(参考値)・is_open を含む。"
    "価格・在庫はEasy My Shop側が真実（SoyShopのpriceは参考値）。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {
        "limit": int(args.get("limit", 30)),
        "offset": int(args.get("offset", 0)),
        "open": args.get("open", "all"),
    }
    if "q" in args and args["q"]:
        params["q"] = args["q"]
    if "code" in args and args["code"]:
        params["code"] = args["code"]
    return client.bridge_get("/items.json", params=params)
