"""Tool: soy_list_blog_entries - ブログ記事一覧取得 (output_blog_entries_json経由)"""

from __future__ import annotations

from typing import Any

from ..client import SoyCmsClient


TOOL_NAME = "soy_list_blog_entries"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 200,
            "default": 30,
            "description": "取得件数",
        },
        "offset": {
            "type": "integer",
            "minimum": 0,
            "default": 0,
            "description": "オフセット",
        },
    },
    "additionalProperties": False,
}

DESCRIPTION = (
    "エルヴェのSOY CMSブログ記事一覧を取得する。"
    "公開済記事のみ。limit/offsetでページング可能。"
    "認証なしの公式 output_blog_entries_json プラグイン経由。"
)


def execute(client: SoyCmsClient, args: dict[str, Any]) -> dict[str, Any]:
    limit = int(args.get("limit", 30))
    offset = int(args.get("offset", 0))
    result = client.read_public_entries(limit=limit, offset=offset)
    return {
        "total": result.get("total", 0),
        "is_next": result.get("is_next", 0),
        "count": len(result.get("entries", [])),
        "entries": [
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "alias": e.get("alias"),
                "cdate": e.get("cdate"),
                "udate": e.get("udate"),
            }
            for e in result.get("entries", [])
        ],
    }
