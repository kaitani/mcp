"""Tool: soy_compare_markdown_with_soycms - MarkdownローカルとSOY CMS公開版の差分照合"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ..client import SoyCmsClient, BridgeError


TOOL_NAME = "soy_compare_markdown_with_soycms"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "markdown_path": {
            "type": "string",
            "description": "ローカルMarkdownファイルの絶対パス",
        },
    },
    "required": ["markdown_path"],
    "additionalProperties": False,
}

DESCRIPTION = (
    "ローカルMarkdown原稿と SOY CMS 公開版を slug (=alias) キーで照合し、"
    "タイトル・更新日時・字数の差分を返す。リライト判断のヒント生成用。"
)


def _read_markdown(path: Path) -> tuple[dict, str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"frontmatter なし: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"frontmatter終端なし: {path}")
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    body_main = ""
    body_more = ""
    m1 = re.search(r"<!--\s*BODY_MAIN.*?-->(.*?)<!--\s*/BODY_MAIN\s*-->", body, re.DOTALL)
    m2 = re.search(r"<!--\s*BODY_MORE.*?-->(.*?)<!--\s*/BODY_MORE\s*-->", body, re.DOTALL)
    if m1:
        body_main = m1.group(1).strip()
    if m2:
        body_more = m2.group(1).strip()
    return fm, body_main, body_more


def execute(client: SoyCmsClient, args: dict[str, Any]) -> dict[str, Any]:
    path = Path(args["markdown_path"]).resolve()
    if not path.exists():
        return {"error": "file_not_found", "path": str(path)}

    fm, body_main, body_more = _read_markdown(path)
    slug = fm.get("slug") or fm.get("soycms_alias")
    if not slug:
        return {"error": "no_slug_in_frontmatter", "path": str(path)}

    # SOY CMS から該当記事取得
    page = client.read_public_entries(limit=200)
    matched = None
    for e in page.get("entries", []):
        if e.get("alias") == slug:
            matched = e
            break

    local = {
        "slug": slug,
        "title": fm.get("title", ""),
        "status": fm.get("status", ""),
        "body_main_chars": len(body_main),
        "body_more_chars": len(body_more),
        "total_chars": len(body_main) + len(body_more),
    }

    if not matched:
        return {
            "found_in_soycms": False,
            "local": local,
            "diff": "SOY CMS 側に該当 alias の記事なし。新規公開候補",
        }

    soycms_data = {
        "id": matched.get("id"),
        "title": matched.get("title"),
        "alias": matched.get("alias"),
        "cdate": matched.get("cdate"),
        "udate": matched.get("udate"),
    }

    diffs: list[str] = []
    if local["title"] != soycms_data["title"]:
        diffs.append(f"title不一致: local='{local['title']}' / soycms='{soycms_data['title']}'")

    return {
        "found_in_soycms": True,
        "local": local,
        "soycms": soycms_data,
        "diffs": diffs,
        "suggest": "差分があれば updateDraft で更新候補。または管理画面で手動更新。",
    }
