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

# 本文バイト上限（正本 = Bridge plugin ArticlesEndpoint.php の MAX_CONTENT_BYTES /
# MAX_MORE_BYTES / MAX_TOTAL_BYTES と**必ず一致**させること。
# ここは Bridge へ送る前の事前 check。Bridge より厳しくすると本文が正当でも弾かれる
# （2026-07-08 #1946: MCP=4000 が Bridge=8000 より厳しく、フル版ピラー記事を誤拒否した）。
# SQLite の VARCHAR(4000) は長さ非強制（型ヒント）のため DB 側の実上限ではない。
MAX_CONTENT_BYTES = 8000
MAX_MORE_BYTES = 8000
MAX_TOTAL_BYTES = 16000

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

    # バイト上限チェック（Bridge側が正本。ここは事前確認で Bridge と同値に揃える）
    content_bytes = len(content_html.encode("utf-8"))
    more_bytes = len(more_html.encode("utf-8"))
    if content_bytes > MAX_CONTENT_BYTES:
        return {
            "error": "content_too_long",
            "bytes": content_bytes,
            "limit": MAX_CONTENT_BYTES,
            "hint": "BODY_MAIN を分割するか、記事を分割してください",
        }
    if more_bytes > MAX_MORE_BYTES:
        return {
            "error": "more_too_long",
            "bytes": more_bytes,
            "limit": MAX_MORE_BYTES,
            "hint": "BODY_MORE を分割するか、記事を分割してください",
        }
    if content_bytes + more_bytes > MAX_TOTAL_BYTES:
        return {
            "error": "total_too_long",
            "bytes": content_bytes + more_bytes,
            "limit": MAX_TOTAL_BYTES,
            "hint": "content+more の合計が上限超過。記事を分割してください",
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
