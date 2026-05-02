"""Tool: soyshop_list_categories - カテゴリ一覧取得（read-only）"""

from __future__ import annotations

from typing import Any

from ..client import SoyShopClient


TOOL_NAME = "soyshop_list_categories"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

DESCRIPTION = (
    "SoyShop のカテゴリ一覧を取得する（read-only）。"
    "返り値: id / name / alias / parent_id（親カテゴリ）/ order / is_open。"
    "parent_id を辿れば階層構造を再構築可能（komodaru-ya.com の場合は地方→都道府県の2階層など）。"
    "商品の categories パラメータに渡す ID をここから取得する。"
)


def execute(client: SoyShopClient, args: dict[str, Any]) -> dict[str, Any]:
    return client.bridge_get("/categories.json")
