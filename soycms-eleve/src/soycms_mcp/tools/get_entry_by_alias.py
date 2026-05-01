"""Tool: soy_get_entry_by_alias - スラッグから記事詳細取得 (Bridge)"""

from __future__ import annotations

from typing import Any

from ..client import SoyCmsClient, BridgeError


TOOL_NAME = "soy_get_entry_by_alias"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "alias": {
            "type": "string",
            "description": "記事のスラッグ (Entry.alias)",
            "minLength": 1,
        },
        "with_history": {
            "type": "boolean",
            "default": False,
            "description": "編集履歴も含めるか (eleve_bridge経由のみ)",
        },
    },
    "required": ["alias"],
    "additionalProperties": False,
}

DESCRIPTION = (
    "スラッグ (alias) から SOY CMS の記事詳細を取得する。"
    "Bridge API (要認証) 経由。draft 含む全記事を取得可能。"
    "公開記事のみで良ければ soy_list_blog_entries で alias で filter する方が認証不要。"
)


def execute(client: SoyCmsClient, args: dict[str, Any]) -> dict[str, Any]:
    alias = args["alias"]
    with_history = bool(args.get("with_history", False))

    # まず Bridge で取得 (認証あれば)
    if client.credentials:
        try:
            params: dict[str, Any] = {}
            if with_history:
                params["with_history"] = "1"
            result = client.bridge_get(f"/articles/by-alias/{alias}.json", params=params)
            return result
        except BridgeError as e:
            if e.status not in (401, 403):
                raise
            # 認証失敗時は public フォールバック

    # Public 経由 (認証なし) でフォールバック - alias で filter
    page = client.read_public_entries(limit=200)
    entries = page.get("entries", [])
    for e in entries:
        if e.get("alias") == alias:
            return {
                "source": "public_json",
                "id": e.get("id"),
                "title": e.get("title"),
                "alias": e.get("alias"),
                "cdate": e.get("cdate"),
                "udate": e.get("udate"),
                "note": "Bridge未認証のため公開JSONで取得。content/moreは取得できません",
            }
    return {
        "source": "not_found",
        "alias": alias,
        "note": f"記事が見つかりません: alias={alias}",
    }
