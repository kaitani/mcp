"""soy_create_draft の本文バイト上限ゲートのテスト（HTTP接続なし）。

由来: cc-company #1946 — MCP の事前 check が 4000 で、正本 Bridge の 8000 より
厳しく、フル版ピラー記事（各セクション 4000〜8000 バイト）を誤って弾いていた。
上限は Bridge plugin ArticlesEndpoint.php と同期必須。
"""

from types import SimpleNamespace

from soycms_mcp.tools import create_draft
from soycms_mcp.tools.create_draft import (
    MAX_CONTENT_BYTES,
    MAX_MORE_BYTES,
    MAX_TOTAL_BYTES,
    execute,
)


class _StubClient:
    """bridge_post を記録するだけのスタブ（ネットワークを叩かない）。"""

    def __init__(self):
        self.credentials = SimpleNamespace(key_id="k", secret="s")
        self.posted = None

    def bridge_post(self, path, body):
        self.posted = {"path": path, "body": body}
        return {"ok": True, "entry_id": 13, "alias": body["alias"], "is_published": 0}


def _write(tmp_path, name, byte_len):
    """UTF-8 で厳密に byte_len バイトの HTML ファイルを作る（ASCII なので 1文字=1バイト）。"""
    p = tmp_path / name
    p.write_text("a" * byte_len, encoding="utf-8")
    return str(p)


def _args(tmp_path, content_bytes, more_bytes):
    return {
        "title": "テスト記事",
        "alias": "test-article",
        "content_html_path": _write(tmp_path, "c.html", content_bytes),
        "more_html_path": _write(tmp_path, "m.html", more_bytes),
    }


def test_bridge_limits_are_in_sync_with_plugin():
    # 正本 Bridge (ArticlesEndpoint.php) と同値であることの明示的な固定
    assert MAX_CONTENT_BYTES == 8000
    assert MAX_MORE_BYTES == 8000
    assert MAX_TOTAL_BYTES == 16000


def test_content_between_4000_and_8000_now_passes(tmp_path):
    """#1946 回帰: 旧 4000 上限では弾かれていた 6000 バイトが通ること。"""
    client = _StubClient()
    result = execute(client, _args(tmp_path, content_bytes=6000, more_bytes=3000))
    assert result["ok"] is True
    assert result["entry_id"] == 13
    assert client.posted is not None  # bridge_post まで到達


def test_content_over_limit_rejected(tmp_path):
    client = _StubClient()
    result = execute(client, _args(tmp_path, content_bytes=MAX_CONTENT_BYTES + 1, more_bytes=100))
    assert result["error"] == "content_too_long"
    assert result["limit"] == MAX_CONTENT_BYTES
    assert client.posted is None  # Bridge へ送らない


def test_more_over_limit_rejected(tmp_path):
    client = _StubClient()
    result = execute(client, _args(tmp_path, content_bytes=100, more_bytes=MAX_MORE_BYTES + 1))
    assert result["error"] == "more_too_long"
    assert client.posted is None


def test_both_sections_at_limit_pass(tmp_path):
    """各セクション上限ちょうど(8000+8000=16000)は通る。

    総量チェック(> MAX_TOTAL_BYTES)は各セクション上限の合計と一致するため
    実質は防御的パリティ（正本 Bridge と同構造）。境界がちょうど通ることを固定。
    """
    client = _StubClient()
    result = execute(
        client, _args(tmp_path, content_bytes=MAX_CONTENT_BYTES, more_bytes=MAX_MORE_BYTES)
    )
    assert result["ok"] is True
    assert client.posted is not None
    assert MAX_CONTENT_BYTES + MAX_MORE_BYTES == MAX_TOTAL_BYTES
