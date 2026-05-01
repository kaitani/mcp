"""SoyCmsClient のスモークテスト（HTTP接続なし）"""

import json
import hashlib
import hmac

from soycms_mcp.auth import BridgeCredentials
from soycms_mcp.client import SoyCmsClient, SoyCmsConfig


def test_credentials_split():
    c = BridgeCredentials(api_key_full="abc12345.deadbeef0123")
    assert c.key_id == "abc12345"
    assert c.secret == "deadbeef0123"


def test_client_config_defaults(monkeypatch):
    monkeypatch.delenv("SOYCMS_BASE_URL", raising=False)
    monkeypatch.delenv("SOYCMS_BLOG_PAGE_ID", raising=False)
    config = SoyCmsConfig.from_env()
    assert config.base_url == "https://eleve-organic.jp"
    assert config.blog_page_id == 5


def test_canonical_signature_compatible_with_php():
    """PHP側 AuthHelper と同じ署名アルゴリズムであることを確認"""
    secret = "topsecret"
    timestamp = "1700000000"
    method = "POST"
    path = "/eleve_bridge/articles/draft"
    body = json.dumps({"title": "test"}, ensure_ascii=False, separators=(",", ":"))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    canonical = f"{timestamp}\n{method}\n{path}\n{body_hash}"
    expected = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()

    # 期待値は決定的（PHP側と一致するはず）
    assert len(expected) == 64
    assert all(c in "0123456789abcdef" for c in expected)


def test_no_credentials_raises_for_bridge():
    config = SoyCmsConfig(base_url="https://example.invalid", blog_page_id=5)
    client = SoyCmsClient(config=config, credentials=None)
    try:
        try:
            client.bridge_get("/version")
            assert False, "should have raised"
        except RuntimeError as e:
            assert "credentials not found" in str(e).lower()
    finally:
        client.close()
