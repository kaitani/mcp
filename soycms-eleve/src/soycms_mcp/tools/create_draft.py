"""Tool: soy_create_draft - SOY CMS 下書き登録 (Bridge POST /articles/draft)"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..client import SoyCmsClient


TOOL_NAME = "soy_create_draft"

# Bridge plugin の ALLOWED_CATEGORIES と一致させる（component/ArticlesEndpoint.php）
ALLOWED_LABELS = [
    # 既存（2026-05-01時点の本番ラベル）
    "moringa",
    "moringa_music",
    "コラム",
    "お知らせ",
    # 設計上の追加予定
    "nutrition",
    "recipes",
    "comparison",
    "brand",
]

# 全記事に必須付与するラベル（オーナー指示・2026-05-02）
REQUIRED_LABELS = ["コラム"]

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "記事タイトル (1-255字)",
        },
        "alias": {
            "type": "string",
            "description": "記事スラッグ (ASCII小文字・数字・ハイフンのみ・2-80字)",
            "pattern": "^[a-z0-9][a-z0-9-]{1,80}$",
        },
        "content_html_path": {
            "type": "string",
            "description": "exports/soycms-html/{slug}.content.html のパス",
        },
        "more_html_path": {
            "type": "string",
            "description": "exports/soycms-html/{slug}.more.html のパス",
        },
        "description": {
            "type": "string",
            "description": "meta description (4000字以内)",
        },
        "label_aliases": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ALLOWED_LABELS,
            },
            "description": (
                f"カテゴリラベルのalias (allowlist={ALLOWED_LABELS})。"
                f"'コラム' は指定しなくても自動付与される（REQUIRED_LABELS={REQUIRED_LABELS}）。"
            ),
        },
        "author": {
            "type": "string",
            "default": "kaitani",
        },
    },
    "required": ["title", "alias", "content_html_path", "more_html_path"],
    "additionalProperties": False,
}

DESCRIPTION = (
    "SOY CMS に下書き (is_published=0) として記事を登録する。"
    "Bridge API 経由。**公開** はオーナーが管理画面で人間判断（このツールでは公開できない）。"
    "1日10件まで。本文は事前に exports/soycms-html/ に書き出されたHTMLを参照する。"
    f"全記事に '{','.join(REQUIRED_LABELS)}' ラベルを自動付与する（オーナーの運用ルール）。"
)


def _merge_required_labels(user_labels: list[str]) -> list[str]:
    """ユーザー指定の label_aliases に REQUIRED_LABELS を必ず追加（順序保持・重複排除）"""
    merged: list[str] = []
    for label in list(user_labels) + REQUIRED_LABELS:
        if label not in merged:
            merged.append(label)
    return merged


def execute(client: SoyCmsClient, args: dict[str, Any]) -> dict[str, Any]:
    if not client.credentials:
        return {
            "error": "no_credentials",
            "detail": (
                "Bridge API キーが Keychain にありません。"
                "管理画面でAPIキー発行 → "
                "security add-generic-password -s soycms-eleve-bridge -a $USER -w '<key_id>.<secret>'"
            ),
        }

    content_path = Path(args["content_html_path"])
    more_path = Path(args["more_html_path"])
    if not content_path.exists():
        return {"error": "content_html_not_found", "path": str(content_path)}
    if not more_path.exists():
        return {"error": "more_html_not_found", "path": str(more_path)}

    content_html = content_path.read_text(encoding="utf-8")
    more_html = more_path.read_text(encoding="utf-8")

    # 4000バイト チェック (Bridge側でも検証されるが事前確認)
    if len(content_html.encode("utf-8")) > 4000:
        return {
            "error": "content_too_long",
            "bytes": len(content_html.encode("utf-8")),
            "limit": 4000,
            "hint": "BODY_MAIN を分割するか、記事を分割してください",
        }
    if len(more_html.encode("utf-8")) > 4000:
        return {
            "error": "more_too_long",
            "bytes": len(more_html.encode("utf-8")),
            "limit": 4000,
            "hint": "BODY_MORE を分割するか、記事を分割してください",
        }

    label_aliases = _merge_required_labels(args.get("label_aliases", []))

    payload = {
        "title": args["title"],
        "alias": args["alias"],
        "content": content_html,
        "more": more_html,
        "description": args.get("description", ""),
        "author": args.get("author", "kaitani"),
        "label_aliases": label_aliases,
    }

    result = client.bridge_post("/articles/draft", body=payload)
    return {
        "ok": result.get("ok", False),
        "entry_id": result.get("entry_id"),
        "alias": result.get("alias"),
        "is_published": result.get("is_published"),
        "applied_labels": label_aliases,
        "next_action": (
            "SOY CMS管理画面で内容確認 → 「公開」ボタンを押してください。"
            "公開URLは https://eleve-organic.jp/moringa/article/{alias} になります。"
        ),
    }
